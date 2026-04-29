# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosLiteConfig(models.Model):
    _name = 'pos.lite.config'
    _description = 'POS Lite Configuration'
    _order = 'id desc'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        required=True,
        domain="[('company_id', '=', company_id)]",
        check_company=True,
    )
    pricelist_id = fields.Many2one(
        'product.pricelist',
        required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        required=True,
        domain="[('type', 'in', ('cash', 'bank')), ('company_id', '=', company_id)]",
        help='Default cash/bank journal for POS Lite payments',
        check_company=True,
    )
    session_ids = fields.One2many('pos.lite.session', 'config_id', string='Sessions')
    open_session_count = fields.Integer(compute='_compute_session_stats')
    session_count = fields.Integer(compute='_compute_session_stats')

    @api.depends('session_ids.state')
    def _compute_session_stats(self):
        for config in self:
            config.session_count = len(config.session_ids)
            config.open_session_count = len(config.session_ids.filtered(lambda session: session.state == 'open'))

    @api.model
    def get_default_config(self, company=None):
        company = company or self.env.company
        return self.search([
            ('company_id', '=', company.id),
            ('active', '=', True),
        ], order='id desc', limit=1)

    def action_view_sessions(self):
        self.ensure_one()
        action = self.env.ref('pos_lite.action_pos_lite_sessions').read()[0]
        action['domain'] = [('config_id', '=', self.id)]
        action['context'] = {
            'default_config_id': self.id,
            'default_company_id': self.company_id.id,
        }
        return action

    def action_open_session(self):
        self.ensure_one()
        session = self.env['pos.lite.session'].search([
            ('company_id', '=', self.company_id.id),
            ('config_id', '=', self.id),
            ('state', 'in', ('draft', 'open')),
        ], order='id desc', limit=1)
        if not session:
            session = self.env['pos.lite.session'].create({
                'company_id': self.company_id.id,
                'config_id': self.id,
                'user_id': self.env.user.id,
            })
        if session.state != 'open':
            session.action_open_session()
        return {
            'type': 'ir.actions.act_window',
            'name': _('POS Lite Session'),
            'res_model': 'pos.lite.session',
            'view_mode': 'form',
            'res_id': session.id,
            'target': 'current',
        }
