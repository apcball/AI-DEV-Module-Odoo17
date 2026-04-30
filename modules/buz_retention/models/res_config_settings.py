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
    retention_account_id = fields.Many2one(
        'account.account',
        string='Retention Account',
        check_company=True,
        help='Expense or clearing account used when creating a retention vendor bill.',
    )

    def _retention_param_key(self, company, field_name):
        return f'buz_retention.{field_name}_{company.id}'

    def get_values(self):
        res = super().get_values()
        company = self.company_id or self.env.company
        icp = self.env['ir.config_parameter'].sudo()
        journal_id = int(icp.get_param(self._retention_param_key(company, 'retention_journal_id'), default='0') or 0)
        account_id = int(icp.get_param(self._retention_param_key(company, 'retention_account_id'), default='0') or 0)
        res.update(
            retention_journal_id=journal_id,
            retention_account_id=account_id,
        )
        return res

    def set_values(self):
        super().set_values()
        company = self.company_id or self.env.company
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param(
            self._retention_param_key(company, 'retention_journal_id'),
            self.retention_journal_id.id if self.retention_journal_id else 0,
        )
        icp.set_param(
            self._retention_param_key(company, 'retention_account_id'),
            self.retention_account_id.id if self.retention_account_id else 0,
        )
