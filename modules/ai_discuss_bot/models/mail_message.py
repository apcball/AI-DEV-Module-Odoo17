# -*- coding: utf-8 -*-
from collections import defaultdict
import re
from html import unescape

from markupsafe import escape

from odoo import api, models, _
from odoo.tools import float_round


THAI_HINT_RE = re.compile(r'[฀-๿]')
HTML_TAG_RE = re.compile(r'<[^>]+>')


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)
        if self.env.context.get('skip_ai_discuss_bot'):
            return messages
        for message in messages:
            message._ai_discuss_bot_handle_message()
        return messages

    def _ai_discuss_bot_handle_message(self):
        self.ensure_one()
        if self.model != 'mail.channel' or not self.res_id:
            return
        if self.message_type not in ('comment', 'email'):
            return
        if self.env.context.get('skip_ai_discuss_bot'):
            return

        channel = self.env['mail.channel'].sudo().browse(self.res_id)
        if not channel.exists() or not channel.is_ai_bot_channel:
            return

        bot_partner = channel.ai_bot_partner_id
        if bot_partner and self.author_id and self.author_id.id == bot_partner.id:
            return

        query = self._ai_discuss_bot_extract_query(channel)
        if not query:
            return

        response = self._ai_discuss_bot_generate_response(query)
        if not response:
            return

        channel.sudo().with_context(skip_ai_discuss_bot=True).message_post(
            body=response,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            author_id=bot_partner.id if bot_partner else False,
        )

    def _ai_discuss_bot_extract_query(self, channel):
        self.ensure_one()
        body = self.body or ''
        text = HTML_TAG_RE.sub(' ', body)
        text = unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            return ''
        bot_name = channel.ai_bot_partner_id.name if channel.ai_bot_partner_id else 'AI Bot'
        text = re.sub(rf'@?{re.escape(bot_name)}', ' ', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _ai_discuss_bot_generate_response(self, query):
        intent = self._ai_discuss_bot_detect_intent(query)
        language = 'th' if THAI_HINT_RE.search(query or '') else 'en'
        if intent == 'stock':
            stock_lines = self._ai_discuss_bot_search_stock(query)
            title = '📦 Stock Results:' if language == 'en' else '📦 ผลการค้นหาสต็อก:'
            if stock_lines:
                return self._ai_discuss_bot_wrap_response(title, stock_lines)
            no_result = 'No matching products found.' if language == 'en' else 'ไม่พบสินค้าที่ตรงกับคำค้น'
            return self._ai_discuss_bot_wrap_response(title, [no_result])
        if intent == 'document':
            doc_lines = self._ai_discuss_bot_search_documents(query)
            title = '📄 Document Results:' if language == 'en' else '📄 ผลการค้นหาเอกสาร:'
            if doc_lines:
                return self._ai_discuss_bot_wrap_response(title, doc_lines)
            no_result = 'No matching documents found.' if language == 'en' else 'ไม่พบเอกสารที่ตรงกับคำค้น'
            return self._ai_discuss_bot_wrap_response(title, [no_result])
        title = 'AI Bot'
        guidance = 'Try asking for stock or document numbers.' if language == 'en' else 'ลองถามเกี่ยวกับสต็อกหรือเลขที่เอกสาร'
        return self._ai_discuss_bot_wrap_response(title, [guidance])

    def _ai_discuss_bot_detect_intent(self, query):
        q = (query or '').lower()
        document_keywords = [
            'so', 'po', 'inv', 'invoice', 'dn', 'delivery', 'document', 'number', 'เลขที่', 'เอกสาร',
            'หาเลขที่', 'ค้นหา', 'บิล', 'ใบสั่งขาย', 'ใบสั่งซื้อ', 'ใบแจ้งหนี้', 'ใบส่งของ',
        ]
        stock_keywords = [
            'stock', 'quantity', 'qty', 'inventory', 'on hand', 'available',
            'กี่', 'ชิ้น', 'คงเหลือ', 'สต็อก', 'จำนวน', 'เหลือ',
        ]
        if any(keyword in q for keyword in document_keywords):
            return 'document'
        if any(keyword in q for keyword in stock_keywords):
            return 'stock'
        return 'general'

    def _ai_discuss_bot_search_stock(self, query):
        Product = self.env['product.product'].sudo()
        cleaned = self._ai_discuss_bot_clean_query(query, intent='stock')
        search_terms = self._ai_discuss_bot_tokenize(cleaned)
        candidates = Product.browse()
        for term in search_terms:
            if len(term) < 2:
                continue
            candidates |= Product.search([
                '|', ('name', 'ilike', term), ('default_code', 'ilike', term),
            ], limit=20)
        if not candidates and cleaned:
            candidates = Product.search([
                '|', ('name', 'ilike', cleaned), ('default_code', 'ilike', cleaned),
            ], limit=20)
        if not candidates:
            return []

        Quant = self.env['stock.quant'].sudo()
        quants = Quant.search([
            ('product_id', 'in', candidates.ids),
            ('quantity', '!=', 0),
        ])
        grouped = defaultdict(lambda: defaultdict(float))
        for quant in quants:
            warehouse_name = self._ai_discuss_bot_get_warehouse_name(quant.location_id)
            grouped[quant.product_id.id][warehouse_name] += quant.quantity

        lines = []
        for product in candidates.sorted(lambda p: (p.default_code or '', p.display_name or '')):
            warehouses = grouped.get(product.id, {})
            if not warehouses:
                continue
            for warehouse_name, qty in sorted(warehouses.items()):
                qty_display = float_round(qty, precision_rounding=product.uom_id.rounding if product.uom_id else 0.01)
                uom = product.uom_name or ''
                suffix = f' {uom}' if uom else ''
                lines.append(
                    f"• {escape(product.display_name)} ({escape(warehouse_name)}): {qty_display}{suffix}"
                )
        return lines

    def _ai_discuss_bot_get_warehouse_name(self, location):
        if not location:
            return _('Unknown Warehouse')
        if location._fields.get('warehouse_id') and location.warehouse_id:
            return location.warehouse_id.display_name
        if location.location_id:
            return self._ai_discuss_bot_get_warehouse_name(location.location_id)
        return location.display_name or _('Unknown Warehouse')

    def _ai_discuss_bot_search_documents(self, query):
        cleaned = self._ai_discuss_bot_clean_query(query, intent='document')
        search_terms = self._ai_discuss_bot_tokenize(cleaned)
        config = [
            ('sale.order', 'SO', 'date_order', 'state', ['name', 'partner_id.name', 'client_order_ref']),
            ('purchase.order', 'PO', 'date_order', 'state', ['name', 'partner_id.name', 'partner_ref']),
            ('account.move', 'INV', 'invoice_date', 'state', ['name', 'partner_id.name', 'payment_reference', 'ref']),
            ('stock.picking', 'DN', 'scheduled_date', 'state', ['name', 'partner_id.name', 'origin']),
        ]
        lines = []
        for model_name, doc_label, date_field, state_field, fields_to_match in config:
            if model_name not in self.env.registry.models:
                continue
            Model = self.env[model_name].sudo()
            records = Model.browse()
            if search_terms:
                for term in search_terms:
                    if len(term) < 2:
                        continue
                    records |= Model.search(self._ai_discuss_bot_build_or_domain(fields_to_match, term), limit=10)
            if not records and cleaned:
                records = Model.search(self._ai_discuss_bot_build_or_domain(fields_to_match, cleaned), limit=10)
            for record in records.sorted(lambda r: (getattr(r, date_field, False) or False, r.display_name or '')):
                partner = getattr(record, 'partner_id', False)
                record_date = getattr(record, date_field, False)
                state_value = getattr(record, state_field, '')
                state_field_obj = record._fields.get(state_field)
                if state_field_obj and getattr(state_field_obj, 'selection', None):
                    state_value = dict(state_field_obj.selection).get(state_value, state_value)
                date_text = str(record_date) if record_date else ''
                lines.append(
                    f"• {escape(doc_label)} {escape(record.name or record.display_name or '')} - {escape(partner.display_name if partner else '')} - {escape(date_text)} - {escape(state_value)}"
                )
        return lines

    def _ai_discuss_bot_build_or_domain(self, fields_to_match, term):
        domain = []
        for idx, field in enumerate(fields_to_match):
            if idx:
                domain.insert(0, '|')
            domain.append((field, 'ilike', term))
        return domain

    def _ai_discuss_bot_wrap_response(self, title, lines):
        items = ''.join(f'<li>{line}</li>' for line in lines)
        return f'<p><strong>{escape(title)}</strong></p><ul>{items}</ul>'

    def _ai_discuss_bot_clean_query(self, query, intent):
        q = (query or '').lower()
        if intent == 'stock':
            stopwords = [
                'stock', 'quantity', 'qty', 'inventory', 'on', 'hand', 'available', 'check', 'please', 'how', 'many',
                'สินค้า', 'มีกี่ชิ้น', 'กี่ชิ้น', 'คงเหลือ', 'สต็อก', 'จำนวน', 'เหลือ', 'เช็ค', 'ตรวจ',
            ]
        else:
            stopwords = [
                'find', 'search', 'document', 'number', 'invoice', 'bill', 'order', 'เลขที่', 'เอกสาร', 'หาเลขที่',
                'ค้นหา', 'เลข', 'so', 'po', 'inv', 'dn',
            ]
        for word in stopwords:
            if ' ' in word or any(ord(ch) > 127 for ch in word):
                q = q.replace(word, ' ')
            else:
                q = re.sub(rf'\b{re.escape(word)}\b', ' ', q)
        q = re.sub(r'[^\w฀-๿\-/\. ]+', ' ', q)
        q = re.sub(r'\s+', ' ', q).strip()
        return q

    def _ai_discuss_bot_tokenize(self, query):
        if not query:
            return []
        tokens = []
        for token in re.split(r'\s+', query):
            token = token.strip().strip(".,()[]{}:;\"'")
            if token:
                tokens.append(token)
        if len(query) >= 3 and query not in tokens:
            tokens.insert(0, query)
        return tokens[:6]
