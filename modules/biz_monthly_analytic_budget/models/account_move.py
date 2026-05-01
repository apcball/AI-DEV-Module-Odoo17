# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

from .budget_utils import (
    extract_analytic_amounts,
    filter_analytic_totals_for_plan,
    find_active_monthly_plan,
)

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    monthly_bill_due_date_from_po = fields.Boolean(
        string='Bill Due Date Auto-filled from PO',
        copy=False,
        default=False,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._sync_monthly_bill_budget()
        return moves

    def write(self, vals):
        prev_states = {rec.id: rec.state for rec in self}
        if 'invoice_date_due' in vals and not self.env.context.get('skip_monthly_bill_budget_sync'):
            vals = dict(vals)
            vals['monthly_bill_due_date_from_po'] = False
        result = super().write(vals)
        if not self.env.context.get('skip_monthly_bill_budget_sync') and any(key in vals for key in (
            'state',
            'invoice_date_due',
            'invoice_date',
            'date',
            'invoice_line_ids',
            'line_ids',
            'invoice_origin',
            'purchase_id',
        )):
            for move in self:
                prev_state = prev_states.get(move.id)
                move._sync_monthly_bill_budget(previous_state=prev_state)
        return result

    def action_post(self):
        """Synchronize monthly budget when vendor bills are posted."""
        return super().action_post()

    def button_draft(self):
        """Synchronize monthly budget when a bill is reset to draft."""
        return super().button_draft()

    def unlink(self):
        """Release monthly budget commitments before deleting bills."""
        bills = self.filtered(lambda move: move.move_type in ('in_invoice', 'in_refund'))
        for move in bills:
            move._release_monthly_bill_budget_by_state()
        return super().unlink()

    def _sync_monthly_bill_budget(self, previous_state=None):
        """Synchronize bill commitments based on source and current state."""
        BudgetLine = self.env['monthly.budget.line']
        engine = self.env['budget.engine']
        for move in self:
            if move.move_type not in ('in_invoice', 'in_refund'):
                continue

            source_po = move._get_related_purchase_order()
            if source_po:
                po_target_date = move._get_purchase_order_target_date(source_po)
                if move.state == 'draft' and po_target_date and (
                    not move.invoice_date_due or move.monthly_bill_due_date_from_po
                ):
                    move.with_context(skip_monthly_bill_budget_sync=True).write({
                        'invoice_date_due': po_target_date,
                        'monthly_bill_due_date_from_po': True,
                    })
                # PO-linked bills already have their monthly budget consumed
                # when the PO is confirmed. Keeping a second bill-level
                # commitment here would double count the same spend.
                engine.release_budget({
                    'budget_source': 'monthly',
                    'document_model': move._name,
                    'document_id': move.id,
                    'amount': 0,
                    'company_id': move.company_id.id,
                })
                continue

            target_date = move._get_bill_target_date()
            if not target_date:
                continue

            plan = find_active_monthly_plan(self.env, target_date, move.company_id.id)
            if not plan:
                continue

            analytic_totals = {}
            for line in move.invoice_line_ids:
                for account_id, amount in extract_analytic_amounts(line, BudgetLine):
                    analytic_totals[account_id] = analytic_totals.get(account_id, 0.0) + amount

            analytic_totals, _ignored_totals = filter_analytic_totals_for_plan(plan, analytic_totals)
            if not analytic_totals:
                continue

            if move.state == 'cancel':
                move._release_monthly_bill_budget(plan, analytic_totals, target_date)
                continue

            if move.state == 'draft':
                move._sync_monthly_bill_reservation(plan, analytic_totals, target_date)
            elif move.state == 'posted':
                move._sync_monthly_bill_usage(plan, analytic_totals, target_date)

    def _get_related_purchase_order(self):
        """Return the PO linked to this bill, if any."""
        self.ensure_one()
        purchase = getattr(self, 'purchase_id', self.env['purchase.order'].browse())
        if purchase and purchase.exists():
            return purchase

        origin = (self.invoice_origin or '').strip()
        if not origin:
            return self.env['purchase.order'].browse()

        return self.env['purchase.order'].sudo().search([
            '|',
            ('name', '=', origin),
            ('requisition_order', '=', origin),
        ], limit=1)

    def _get_purchase_order_target_date(self, source_po=None):
        """Return the PO's expected payment date for budget alignment."""
        self.ensure_one()
        source_po = source_po or self._get_related_purchase_order()
        if not source_po:
            return False
        return source_po.payment_date or (source_po.date_order.date() if source_po.date_order else False)

    def _get_bill_target_date(self):
        """Return the date used to match the bill against a budget plan."""
        self.ensure_one()
        if self.invoice_date_due:
            return self.invoice_date_due

        source_po = self._get_related_purchase_order()
        if source_po:
            return self._get_purchase_order_target_date(source_po)

        return False

    def _sync_monthly_bill_reservation(self, plan, analytic_totals, target_date):
        """Keep draft direct bills as reserved commitments."""
        BudgetLine = self.env['monthly.budget.line']
        engine = self.env['budget.engine']
        Commitment = self.env['budget.commitment'].sudo()
        AnalyticAccount = self.env['account.analytic.account']

        BudgetLine._lock_budget_lines(list(analytic_totals.keys()), plan.id)
        plan._refresh_budget_snapshot(refresh_report=False)

        # Make the sync idempotent: wipe the bill's previous monthly commitments
        # first, then recreate the current snapshot for the latest state.
        engine.release_budget({
            'budget_source': 'monthly',
            'document_model': self._name,
            'document_id': self.id,
            'amount': 0,
            'company_id': self.company_id.id,
        })

        for account_id, amount in analytic_totals.items():
            if not amount:
                continue
            analytic = AnalyticAccount.browse(account_id)
            if not analytic.exists():
                continue
            if not BudgetLine._find_budget_line(plan, {'analytic_account_id': account_id}, log_fallback=False):
                continue

            existing_reserved = Commitment.search([
                ('document_model', '=', self._name),
                ('document_id', '=', self.id),
                ('analytic_account_id', '=', account_id),
                ('budget_source', '=', 'monthly'),
                ('state', '=', 'reserved'),
            ], limit=1)
            if existing_reserved:
                if existing_reserved.amount != amount or existing_reserved.date != target_date:
                    existing_reserved.write({
                        'amount': amount,
                        'date': target_date,
                        'note': 'Reserved from Bill %s - %s' % (self.name, analytic.name),
                    })
                continue

            existing_used = Commitment.search([
                ('document_model', '=', self._name),
                ('document_id', '=', self.id),
                ('analytic_account_id', '=', account_id),
                ('budget_source', '=', 'monthly'),
                ('state', '=', 'used'),
            ], limit=1)
            if existing_used:
                existing_used.write({
                    'amount': amount,
                    'date': target_date,
                    'state': 'reserved',
                    'note': 'Reserved from Bill %s - %s' % (self.name, analytic.name),
                })
                continue

            engine.reserve_budget({
                'budget_source': 'monthly',
                'document_model': self._name,
                'document_id': self.id,
                'amount': amount,
                'date': target_date,
                'company_id': self.company_id.id,
                'analytic_account_id': account_id,
                'note': 'Reserved from Bill %s - %s' % (self.name, analytic.name),
            })

        plan._refresh_budget_snapshot(refresh_report=True)

    def _sync_monthly_bill_usage(self, plan, analytic_totals, target_date):
        """Keep bills in used state, converting any draft reservation if needed."""
        BudgetLine = self.env['monthly.budget.line']
        engine = self.env['budget.engine']
        Commitment = self.env['budget.commitment'].sudo()
        AnalyticAccount = self.env['account.analytic.account']

        BudgetLine._lock_budget_lines(list(analytic_totals.keys()), plan.id)
        plan._refresh_budget_snapshot(refresh_report=False)

        # Make the sync idempotent: remove any prior reserved/used commitments
        # for this bill before rebuilding the current state.
        engine.release_budget({
            'budget_source': 'monthly',
            'document_model': self._name,
            'document_id': self.id,
            'amount': 0,
            'company_id': self.company_id.id,
        })

        for account_id, amount in analytic_totals.items():
            if not amount:
                continue
            analytic = AnalyticAccount.browse(account_id)
            if not analytic.exists():
                continue
            if not BudgetLine._find_budget_line(plan, {'analytic_account_id': account_id}, log_fallback=False):
                continue

            existing_used = Commitment.search([
                ('document_model', '=', self._name),
                ('document_id', '=', self.id),
                ('analytic_account_id', '=', account_id),
                ('budget_source', '=', 'monthly'),
                ('state', '=', 'used'),
            ], limit=1)
            if existing_used:
                if existing_used.amount != amount or existing_used.date != target_date:
                    existing_used.write({
                        'amount': amount,
                        'date': target_date,
                        'note': 'Consumed by Bill %s - %s' % (self.name, analytic.name),
                    })
                continue

            existing_reserved = Commitment.search([
                ('document_model', '=', self._name),
                ('document_id', '=', self.id),
                ('analytic_account_id', '=', account_id),
                ('budget_source', '=', 'monthly'),
                ('state', '=', 'reserved'),
            ], limit=1)
            if existing_reserved:
                existing_reserved.write({
                    'amount': amount,
                    'date': target_date,
                    'state': 'used',
                    'note': 'Consumed by Bill %s - %s' % (self.name, analytic.name),
                })
                continue

            engine.consume_budget({
                'budget_source': 'monthly',
                'document_model': self._name,
                'document_id': self.id,
                'amount': amount,
                'date': target_date,
                'company_id': self.company_id.id,
                'analytic_account_id': account_id,
                'note': 'Consumed by Bill %s - %s' % (self.name, analytic.name),
            })

        plan._refresh_budget_snapshot(refresh_report=True)

    def _release_monthly_bill_budget(self, plan, analytic_totals, target_date):
        BudgetLine = self.env['monthly.budget.line']
        engine = self.env['budget.engine']

        BudgetLine._lock_budget_lines(list(analytic_totals.keys()), plan.id)
        plan._refresh_budget_snapshot(refresh_report=False)

        engine.release_budget({
            'budget_source': 'monthly',
            'document_model': self._name,
            'document_id': self.id,
            'amount': 0,
            'company_id': self.company_id.id,
        })

        plan._refresh_budget_snapshot(refresh_report=True)

    def _release_monthly_bill_budget_by_state(self):
        """Release all monthly bill commitments regardless of current amount/state."""
        for move in self:
            target_date = move._get_bill_target_date()
            if not target_date:
                target_date = fields.Date.context_today(move)
            plan = find_active_monthly_plan(self.env, target_date, move.company_id.id)
            analytic_totals = {}
            if plan:
                BudgetLine = self.env['monthly.budget.line']
                for line in move.invoice_line_ids:
                    for account_id, amount in extract_analytic_amounts(line, BudgetLine):
                        analytic_totals[account_id] = analytic_totals.get(account_id, 0.0) + amount
                analytic_totals, _ignored_totals = filter_analytic_totals_for_plan(plan, analytic_totals)
            if not plan or not analytic_totals:
                self.env['budget.engine'].release_budget({
                    'budget_source': 'monthly',
                    'document_model': move._name,
                    'document_id': move.id,
                    'amount': 0,
                    'company_id': move.company_id.id,
                })
                continue

            move._release_monthly_bill_budget(plan, analytic_totals, target_date)
