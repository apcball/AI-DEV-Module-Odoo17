# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosLitePayment(models.Model):
    _name = 'pos.lite.payment'
    _description = 'POS Lite Payment'
    _order = 'id desc'

    order_id = fields.Many2one(
        'pos.lite.order',
        required=True,
        ondelete='cascade',
        check_company=True,
    )
    company_id = fields.Many2one(related='order_id.company_id', store=True, readonly=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('transfer', 'Transfer'),
        ('card', 'Card'),
    ], default='cash', required=True)
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, readonly=True)
    journal_id = fields.Many2one(
        'account.journal',
        domain="[('type', 'in', ('cash', 'bank')), ('company_id', '=', company_id)]",
        check_company=True,
    )
    note = fields.Char()

    _sql_constraints = [
        ('order_unique_payment', 'unique(order_id)', 'Split payment is out of scope. Use a single payment per order.'),
    ]

    def _check_locked_parent(self):
        if self.env.context.get('pos_lite_allow_locked_write'):
            return
        locked_orders = self.mapped('order_id').filtered(lambda order: order.state != 'draft')
        if locked_orders:
            raise ValidationError(_('This order is locked after payment and the payment cannot be modified.'))

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('pos_lite_allow_locked_write'):
            order_ids = [vals.get('order_id') for vals in vals_list if vals.get('order_id')]
            if order_ids:
                locked_orders = self.env['pos.lite.order'].browse(order_ids).filtered(lambda order: order.state != 'draft')
                if locked_orders:
                    raise ValidationError(_('This order is locked after payment and the payment cannot be modified.'))
        return super().create(vals_list)

    def write(self, vals):
        self._check_locked_parent()
        return super().write(vals)

    def unlink(self):
        self._check_locked_parent()
        return super().unlink()

    @api.onchange('payment_method')
    def _onchange_payment_method(self):
        if self.payment_method and not self.journal_id and self.order_id:
            self.journal_id = self.order_id._get_default_payment_journal()

    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.order_id and payment.order_id.is_return:
                if payment.amount >= 0:
                    raise ValidationError(_('Refund payment amount must be less than zero.'))
            elif payment.amount <= 0:
                raise ValidationError(_('Payment amount must be greater than zero.'))
