# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def _get_channel_partner_field(channel):
    if 'channel_partner_ids' in channel._fields:
        return 'channel_partner_ids'
    if 'channel_member_ids' in channel._fields:
        return 'channel_member_ids'
    return None


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Partner = env['res.partner'].sudo()
    Channel = env['mail.channel'].sudo()

    bot_partner = Partner.search([('is_ai_bot', '=', True)], limit=1)
    if not bot_partner:
        bot_partner = Partner.create({
            'name': 'AI Bot',
            'is_ai_bot': True,
            'active': True,
        })
    else:
        bot_partner.write({'name': 'AI Bot', 'is_ai_bot': True, 'active': True})

    channel = Channel.search([('is_ai_bot_channel', '=', True)], limit=1)
    channel_vals = {
        'name': 'AI Bot',
        'channel_type': 'channel',
        'public': 'public',
        'is_ai_bot_channel': True,
        'ai_bot_partner_id': bot_partner.id,
    }
    if not channel:
        channel = Channel.create(channel_vals)
    else:
        channel.write(channel_vals)

    partner_field = _get_channel_partner_field(channel)
    if partner_field:
        current_partners = set(channel[partner_field].ids)
        if bot_partner.id not in current_partners:
            channel.write({partner_field: [(4, bot_partner.id)]})

        user_partners = env['res.users'].sudo().search([
            ('share', '=', False),
            ('active', '=', True),
            ('partner_id', '!=', False),
        ]).mapped('partner_id')
        to_add = [partner.id for partner in user_partners if partner.id not in current_partners and partner.id != bot_partner.id]
        if to_add:
            channel.write({partner_field: [(4, pid) for pid in to_add]})
