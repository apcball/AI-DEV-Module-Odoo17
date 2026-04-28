# -*- coding: utf-8 -*-
from odoo import fields, models


class MailChannel(models.Model):
    _inherit = 'mail.channel'

    is_ai_bot_channel = fields.Boolean(string='AI Bot Channel', default=False, index=True)
    ai_bot_partner_id = fields.Many2one('res.partner', string='AI Bot Partner', readonly=True, ondelete='set null')
