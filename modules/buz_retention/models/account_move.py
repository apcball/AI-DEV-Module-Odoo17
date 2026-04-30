# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class AccountMove(models.Model):
    _inherit = 'account.move'

    retention_bill_ids = fields.Many2many(
        'account.move',
        'buz_retention_invoice_bill_rel',
        'invoice_id',
        'bill_id',
        string='Retention Vendor Bills',
        copy=False,
        check_company=True,
        help='Posted vendor bills that will be offset against this customer invoice.',
    )
    retention_total_amount = fields.Monetary(
        string='Retention Total',
        compute='_compute_retention_total_amount',
        currency_field='currency_id',
        store=False,
    )
    retention_offset_move_id = fields.Many2one(
        'account.move',
        string='Retention Offset Entry',
        copy=False,
        readonly=True,
        check_company=True,
    )

    @api.depends('retention_bill_ids', 'retention_bill_ids.amount_residual', 'retention_bill_ids.state')
    def _compute_retention_total_amount(self):
        for move in self:
            bills = move.retention_bill_ids.filtered(lambda bill: bill.state == 'posted')
            move.retention_total_amount = sum(bills.mapped('amount_residual'))

    def _get_retention_journal(self):
        self.ensure_one()
        icp = self.env['ir.config_parameter'].sudo()
        key = f'buz_retention.retention_journal_id_{self.company_id.id}'
        journal_id = int(icp.get_param(key, default='0') or 0)
        journal = self.env['account.journal'].browse(journal_id).exists()
        if not journal:
            raise UserError(_(
                'Please configure a Retention Journal in Accounting > Settings before applying retention.'
            ))
        return journal

    def _get_move_line(self, move, account_type):
        line = move.line_ids.filtered(
            lambda l: not l.display_type and l.account_id.account_type == account_type and not l.reconciled
        )[:1]
        if not line:
            raise UserError(_(
                'Move %(move)s does not have an open %(account_type)s line to reconcile.'
            ) % {
                'move': move.display_name,
                'account_type': account_type,
            })
        return line

    def _prepare_retention_offset_lines(self, bills):
        self.ensure_one()
        lines = []
        for bill in bills:
            bill_line = self._get_move_line(bill, 'liability_payable')
            lines.append(Command.create({
                'name': _('Retention offset for %s') % (bill.name or bill.ref or bill.display_name),
                'partner_id': bill.partner_id.id,
                'account_id': bill_line.account_id.id,
                'debit': bill.amount_residual,
                'credit': 0.0,
            }))

        invoice_receivable_line = self._get_move_line(self, 'asset_receivable')
        total_amount = sum(bills.mapped('amount_residual'))
        lines.append(Command.create({
            'name': _('Retention offset for %s') % (self.name or self.ref or self.display_name),
            'partner_id': self.partner_id.id,
            'account_id': invoice_receivable_line.account_id.id,
            'debit': 0.0,
            'credit': total_amount,
        }))
        return lines

    def _validate_retention_application(self, bills):
        self.ensure_one()
        if self.move_type != 'out_invoice':
            raise UserError(_('Retention can only be applied on posted customer invoices.'))
        if self.state != 'posted':
            raise UserError(_('Please post the customer invoice before applying retention.'))
        if self.retention_offset_move_id:
            raise UserError(_('Retention has already been applied on this invoice.'))
        if not bills:
            raise UserError(_('Please select at least one posted vendor bill.'))
        if any(bill.company_id != self.company_id for bill in bills):
            raise UserError(_('All retention bills must belong to the same company as the invoice.'))
        if any(bill.move_type != 'in_invoice' for bill in bills):
            raise UserError(_('Only posted vendor bills can be used as retention bills.'))
        if any(bill.state != 'posted' for bill in bills):
            raise UserError(_('All retention bills must be posted first.'))
        if any(bill.currency_id != self.company_currency_id for bill in bills) or self.currency_id != self.company_currency_id:
            raise UserError(_('This retention V1 only supports company-currency invoices and vendor bills.'))

        total_amount = sum(bills.mapped('amount_residual'))
        if float_compare(total_amount, self.amount_residual, precision_rounding=self.company_currency_id.rounding) != 0:
            raise UserError(_(
                'The total retention bill amount (%(bill_amount).2f) must exactly match the invoice residual (%(invoice_amount).2f).'
            ) % {
                'bill_amount': total_amount,
                'invoice_amount': self.amount_residual,
            })
        return total_amount

    def _reconcile_retention_lines(self, offset_move, bills):
        self.ensure_one()
        for bill in bills:
            bill_payable = self._get_move_line(bill, 'liability_payable')
            offset_payable = offset_move.line_ids.filtered(
                lambda l: not l.display_type
                and l.account_id == bill_payable.account_id
                and l.partner_id == bill.partner_id
                and l.debit > 0
                and not l.reconciled
            )[:1]
            if not offset_payable:
                raise UserError(_('Could not find the offset payable line for bill %s.') % bill.display_name)
            (bill_payable + offset_payable).reconcile()

        invoice_receivable = self._get_move_line(self, 'asset_receivable')
        offset_receivable = offset_move.line_ids.filtered(
            lambda l: not l.display_type
            and l.account_id == invoice_receivable.account_id
            and l.partner_id == self.partner_id
            and l.credit > 0
            and not l.reconciled
        )[:1]
        if not offset_receivable:
            raise UserError(_('Could not find the offset receivable line for invoice %s.') % self.display_name)
        (invoice_receivable + offset_receivable).reconcile()

    def action_apply_retention_bill(self):
        self.ensure_one()
        bills = self.retention_bill_ids.filtered(lambda bill: bill.state == 'posted')
        self._validate_retention_application(bills)
        journal = self._get_retention_journal()
        offset_move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': self.invoice_date or fields.Date.context_today(self),
            'ref': _('Retention offset for %s') % (self.name or self.ref or self.display_name),
            'company_id': self.company_id.id,
            'line_ids': self._prepare_retention_offset_lines(bills),
        })
        offset_move.action_post()
        self._reconcile_retention_lines(offset_move, bills)
        self.retention_offset_move_id = offset_move.id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Retention Offset Entry'),
            'res_model': 'account.move',
            'res_id': offset_move.id,
            'view_mode': 'form',
            'target': 'current',
        }
