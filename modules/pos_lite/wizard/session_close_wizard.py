# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosLiteSessionCloseWizard(models.TransientModel):
    _name = 'pos.lite.session.close.wizard'
    _description = 'POS Lite Session Close Wizard'

    session_id = fields.Many2one('pos.lite.session', required=True, readonly=True)
    company_id = fields.Many2one(related='session_id.company_id', readonly=True)
    currency_id = fields.Many2one(related='session_id.currency_id', readonly=True)
    state = fields.Selection(related='session_id.state', readonly=True)
    date_start = fields.Datetime(related='session_id.date_start', readonly=True)
    date_end = fields.Datetime(related='session_id.date_end', readonly=True)
    note = fields.Text(related='session_id.note', readonly=True)

    order_count = fields.Integer(compute='_compute_summary', readonly=True)
    draft_order_count = fields.Integer(compute='_compute_summary', readonly=True)
    paid_order_count = fields.Integer(compute='_compute_summary', readonly=True)
    done_order_count = fields.Integer(compute='_compute_summary', readonly=True)
    cancelled_order_count = fields.Integer(compute='_compute_summary', readonly=True)
    return_order_count = fields.Integer(compute='_compute_summary', readonly=True)

    gross_sales = fields.Monetary(compute='_compute_summary', readonly=True)
    return_amount = fields.Monetary(compute='_compute_summary', readonly=True)
    net_sales = fields.Monetary(compute='_compute_summary', readonly=True)
    gross_paid = fields.Monetary(compute='_compute_summary', readonly=True)
    net_paid = fields.Monetary(compute='_compute_summary', readonly=True)
    residual_amount = fields.Monetary(compute='_compute_summary', readonly=True)
    change_amount = fields.Monetary(compute='_compute_summary', readonly=True)
    cash_amount = fields.Monetary(compute='_compute_summary', readonly=True)
    transfer_amount = fields.Monetary(compute='_compute_summary', readonly=True)
    card_amount = fields.Monetary(compute='_compute_summary', readonly=True)

    @api.depends('session_id', 'session_id.order_ids.state', 'session_id.order_ids.amount_total', 'session_id.order_ids.amount_paid', 'session_id.order_ids.amount_residual', 'session_id.order_ids.amount_change', 'session_id.order_ids.is_return', 'session_id.order_ids.payment_ids.amount', 'session_id.order_ids.payment_ids.payment_method')
    def _compute_summary(self):
        for wizard in self:
            if not wizard.session_id:
                wizard.order_count = 0
                wizard.draft_order_count = 0
                wizard.paid_order_count = 0
                wizard.done_order_count = 0
                wizard.cancelled_order_count = 0
                wizard.return_order_count = 0
                wizard.gross_sales = 0.0
                wizard.return_amount = 0.0
                wizard.net_sales = 0.0
                wizard.gross_paid = 0.0
                wizard.net_paid = 0.0
                wizard.residual_amount = 0.0
                wizard.change_amount = 0.0
                wizard.cash_amount = 0.0
                wizard.transfer_amount = 0.0
                wizard.card_amount = 0.0
                continue
            summary = wizard.session_id._get_close_summary()
            wizard.order_count = summary['order_count']
            wizard.draft_order_count = summary['draft_order_count']
            wizard.paid_order_count = summary['paid_order_count']
            wizard.done_order_count = summary['done_order_count']
            wizard.cancelled_order_count = summary['cancelled_order_count']
            wizard.return_order_count = summary['return_order_count']
            wizard.gross_sales = summary['gross_sales']
            wizard.return_amount = summary['return_amount']
            wizard.net_sales = summary['net_sales']
            wizard.gross_paid = summary['gross_paid']
            wizard.net_paid = summary['net_paid']
            wizard.residual_amount = summary['residual_amount']
            wizard.change_amount = summary['change_amount']
            wizard.cash_amount = summary['cash_amount']
            wizard.transfer_amount = summary['transfer_amount']
            wizard.card_amount = summary['card_amount']

    def action_confirm_close_session(self):
        self.ensure_one()
        self.session_id.action_do_close_session()
        return self.session_id.action_print_close_summary()
