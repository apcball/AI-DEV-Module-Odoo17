# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosLiteSession(models.Model):
    _name = 'pos.lite.session'
    _description = 'POS Lite Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(default='/', copy=False, readonly=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    config_id = fields.Many2one(
        'pos.lite.config',
        required=True,
        domain="[('company_id', '=', company_id), ('active', '=', True)]",
        tracking=True,
        check_company=True,
    )
    warehouse_id = fields.Many2one(related='config_id.warehouse_id', store=True, readonly=True)
    pricelist_id = fields.Many2one(related='config_id.pricelist_id', store=True, readonly=True)
    journal_id = fields.Many2one(related='config_id.journal_id', store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
    ], default='draft', required=True, tracking=True)
    date_start = fields.Datetime(readonly=True, copy=False)
    date_end = fields.Datetime(readonly=True, copy=False)
    note = fields.Text()
    order_ids = fields.One2many('pos.lite.order', 'session_id', string='Orders')
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, readonly=True)
    order_count = fields.Integer(compute='_compute_stats')
    draft_order_count = fields.Integer(compute='_compute_stats')
    paid_order_count = fields.Integer(compute='_compute_stats')
    done_order_count = fields.Integer(compute='_compute_stats')
    cancelled_order_count = fields.Integer(compute='_compute_stats')
    return_order_count = fields.Integer(compute='_compute_stats')
    amount_total = fields.Monetary(compute='_compute_stats')
    amount_paid = fields.Monetary(compute='_compute_stats')
    amount_residual = fields.Monetary(compute='_compute_stats')
    amount_change = fields.Monetary(compute='_compute_stats')
    amount_return = fields.Monetary(compute='_compute_stats')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Session number must be unique.'),
    ]

    @api.model
    def _next_session_name(self):
        return self.env['ir.sequence'].next_by_code('pos.lite.session') or '/'

    @api.model
    def get_open_session(self, company=None, config=None, create=False):
        company = company or self.env.company
        domain = [('company_id', '=', company.id), ('state', '=', 'open')]
        if config:
            domain.append(('config_id', '=', config.id))
        session = self.search(domain, order='id desc', limit=1)
        if session or not create:
            return session

        config = config or self.env['pos.lite.config'].get_default_config(company)
        if not config:
            return self.browse()
        session = self.create({
            'company_id': company.id,
            'config_id': config.id,
            'user_id': self.env.user.id,
        })
        session.action_open_session()
        return session

    @api.depends('order_ids.state', 'order_ids.amount_total', 'order_ids.amount_paid', 'order_ids.amount_residual', 'order_ids.amount_change', 'order_ids.is_return')
    def _compute_stats(self):
        for session in self:
            summary = session._get_close_summary()
            session.order_count = summary['order_count']
            session.draft_order_count = summary['draft_order_count']
            session.paid_order_count = summary['paid_order_count']
            session.done_order_count = summary['done_order_count']
            session.cancelled_order_count = summary['cancelled_order_count']
            session.return_order_count = summary['return_order_count']
            session.amount_total = summary['net_sales']
            session.amount_paid = summary['net_paid']
            session.amount_residual = summary['residual_amount']
            session.amount_change = summary['change_amount']
            session.amount_return = summary['return_amount']

    def _get_close_summary(self):
        self.ensure_one()
        orders = self.order_ids.filtered(lambda order: order.state != 'cancelled')
        sales_orders = orders.filtered(lambda order: not order.is_return)
        return_orders = orders.filtered(lambda order: order.is_return)
        payments = orders.mapped('payment_ids')
        return {
            'order_count': len(self.order_ids),
            'draft_order_count': len(self.order_ids.filtered(lambda order: order.state == 'draft')),
            'paid_order_count': len(self.order_ids.filtered(lambda order: order.state == 'paid')),
            'done_order_count': len(self.order_ids.filtered(lambda order: order.state == 'done')),
            'cancelled_order_count': len(self.order_ids.filtered(lambda order: order.state == 'cancelled')),
            'return_order_count': len(return_orders),
            'gross_sales': sum(sales_orders.mapped('amount_total')),
            'return_amount': sum(return_orders.mapped('amount_total')),
            'net_sales': sum(sales_orders.mapped('amount_total')) - sum(return_orders.mapped('amount_total')),
            'gross_paid': sum(sales_orders.mapped('amount_paid')),
            'net_paid': sum(sales_orders.mapped('amount_paid')) - sum(return_orders.mapped('amount_paid')),
            'residual_amount': sum(orders.mapped('amount_residual')),
            'change_amount': sum(orders.mapped('amount_change')),
            'cash_amount': sum(payments.filtered(lambda payment: payment.payment_method == 'cash').mapped('amount')),
            'transfer_amount': sum(payments.filtered(lambda payment: payment.payment_method == 'transfer').mapped('amount')),
            'card_amount': sum(payments.filtered(lambda payment: payment.payment_method == 'card').mapped('amount')),
        }

    def action_do_close_session(self):
        for session in self:
            if session.state != 'open':
                raise UserError(_('Only open sessions can be closed.'))
            draft_orders = session.order_ids.filtered(lambda order: order.state == 'draft')
            if draft_orders:
                raise UserError(_('Please process or cancel all draft orders before closing the session.'))
            session.write({
                'state': 'closed',
                'date_end': fields.Datetime.now(),
            })
        return True

    def action_open_session(self):
        for session in self:
            if session.state == 'closed':
                raise UserError(_('Cannot reopen a closed session.'))
            vals = {'state': 'open'}
            if not session.name or session.name == '/':
                vals['name'] = session._next_session_name()
            if not session.date_start:
                vals['date_start'] = fields.Datetime.now()
            session.write(vals)
        return True

    def action_close_session(self):
        self.ensure_one()
        if self.state != 'open':
            raise UserError(_('Only open sessions can be closed.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Close Session Summary'),
            'res_model': 'pos.lite.session.close.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_session_id': self.id,
            },
        }

    def action_print_close_summary(self):
        self.ensure_one()
        return self.env.ref('pos_lite.action_report_pos_lite_session_close_summary').report_action(self)

    def action_view_orders(self):
        self.ensure_one()
        action = self.env.ref('pos_lite.action_pos_lite_orders').read()[0]
        action['domain'] = [('session_id', '=', self.id)]
        action['context'] = {
            'default_session_id': self.id,
            'default_company_id': self.company_id.id,
            'default_pricelist_id': self.pricelist_id.id,
            'default_warehouse_id': self.warehouse_id.id,
        }
        return action
