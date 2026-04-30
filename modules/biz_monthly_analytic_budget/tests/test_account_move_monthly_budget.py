# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestAccountMoveMonthlyBudget(TransactionCase):

    def test_bill_target_date_prefers_related_po_payment_date(self):
        bill = self.env['account.move'].new({
            'move_type': 'in_invoice',
            'invoice_date_due': fields.Date.to_date('2026-04-30'),
            'invoice_date': fields.Date.to_date('2026-04-20'),
            'date': fields.Date.to_date('2026-04-18'),
        })
        related_po = Mock(
            payment_date=fields.Date.to_date('2026-04-10'),
            date_order=False,
        )

        with patch.object(type(bill), '_get_related_purchase_order', return_value=related_po):
            self.assertEqual(
                bill._get_bill_target_date(),
                fields.Date.to_date('2026-04-10'),
            )

    def test_bill_target_date_falls_back_to_po_date_order(self):
        bill = self.env['account.move'].new({
            'move_type': 'in_invoice',
            'invoice_date_due': fields.Date.to_date('2026-04-30'),
            'invoice_date': fields.Date.to_date('2026-04-20'),
            'date': fields.Date.to_date('2026-04-18'),
        })
        related_po = Mock(
            payment_date=False,
            date_order=fields.Datetime.to_datetime('2026-04-12 00:00:00'),
        )

        with patch.object(type(bill), '_get_related_purchase_order', return_value=related_po):
            self.assertEqual(
                bill._get_bill_target_date(),
                fields.Date.to_date('2026-04-12'),
            )

    def test_bill_target_date_uses_bill_dates_when_no_related_po_date_exists(self):
        bill = self.env['account.move'].new({
            'move_type': 'in_invoice',
            'invoice_date_due': fields.Date.to_date('2026-04-30'),
            'invoice_date': fields.Date.to_date('2026-04-20'),
            'date': fields.Date.to_date('2026-04-18'),
        })
        related_po = Mock(payment_date=False, date_order=False)

        with patch.object(type(bill), '_get_related_purchase_order', return_value=related_po):
            self.assertEqual(
                bill._get_bill_target_date(),
                fields.Date.to_date('2026-04-30'),
            )

    def test_related_purchase_order_prefers_purchase_id_if_present(self):
        partner = self.env['res.partner'].create({'name': 'Test Vendor'})
        expected_po = self.env['purchase.order'].create({
            'partner_id': partner.id,
        })
        bill = self.env['account.move'].new({'move_type': 'in_invoice'})
        bill.purchase_id = expected_po

        with patch.object(type(bill), 'sudo', side_effect=AssertionError('sudo search fallback should not run')):
            self.assertIs(bill._get_related_purchase_order(), expected_po)

    def test_related_purchase_order_falls_back_to_invoice_origin_search(self):
        bill = self.env['account.move'].new({
            'move_type': 'in_invoice',
            'invoice_origin': 'PO00042',
        })
        expected_po = Mock(exists=lambda: True)
        purchase_model = self.env['purchase.order']

        with patch.object(type(purchase_model), 'sudo', return_value=purchase_model):
            with patch.object(type(purchase_model), 'search', return_value=expected_po):
                self.assertIs(bill._get_related_purchase_order(), expected_po)

    def test_sync_monthly_bill_budget_skips_po_linked_bills(self):
        bill = self.env['account.move'].new({
            'move_type': 'in_invoice',
            'invoice_date_due': fields.Date.to_date('2026-04-30'),
            'invoice_date': fields.Date.to_date('2026-04-20'),
            'date': fields.Date.to_date('2026-04-18'),
        })
        related_po = Mock(
            payment_date=fields.Date.to_date('2026-04-10'),
            date_order=False,
        )

        with patch.object(type(bill), '_get_related_purchase_order', return_value=related_po):
            with patch.object(type(bill), '_get_bill_target_date', side_effect=AssertionError(
                'PO-linked bills should not create a separate bill-level commitment'
            )):
                bill._sync_monthly_bill_budget()
