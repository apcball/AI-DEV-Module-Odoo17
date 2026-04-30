# -*- coding: utf-8 -*-
{
    'name': 'Buz Retention',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Apply retention vendor bills against customer invoices',
    'description': 'Retention offset module for Odoo 17. This module creates a posted vendor bill first and later applies that bill to a posted customer invoice by creating a balancing journal entry and reconciling both sides.',
    'author': 'Apichart',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
