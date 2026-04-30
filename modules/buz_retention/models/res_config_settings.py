# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    retention_journal_id = fields.Many2one(
        'account.journal',
        string='Retention Journal',
        domain="[('type', '=', 'general')]",
        check_company=True,
        help='General journal used to post the retention offset entry.',
    )

    def _retention_param_key(self, company):
        return f'buz_retention.retention_journal_id_{company.id}'

    def get_values(self):
        res = super().get_values()
        company = self.company_id or self.env.company
        journal_id = int(self.env['ir.config_parameter'].sudo().get_param(
            self._retention_param_key(company),
            default='0',
        ) or 0)
        res.update(retention_journal_id=journal_id)
        return res

    def set_values(self):
        super().set_values()
        company = self.company_id or self.env.company
        key = self._retention_param_key(company)
        journal_id = self.retention_journal_id.id if self.retention_journal_id else 0
        self.env['ir.config_parameter'].sudo().set_param(key, journal_id)
