# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from decimal import Decimal
from markupsafe import escape
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

from .budget_utils import (
    RESERVED_PR_STATES,
    extract_analytic_amounts,
    filter_analytic_totals_for_plan,
    find_active_monthly_plan,
    format_ignored_analytic_accounts_message,
    format_missing_budget_line_message,
    format_no_analytic_distribution_message,
)

_logger = logging.getLogger(__name__)


class EmployeePurchaseRequisitionMonthly(models.Model):
    """
    Extend employee.purchase.requisition with monthly analytic budget validation.
    Budget check happens at head approval stage.
    """
    _inherit = 'employee.purchase.requisition'

    payment_date = fields.Date(
        string="Expected Payment",
        compute="_compute_payment_date",
        inverse="_inverse_payment_date",
        store=True,
        readonly=False
    )
    payment_date_manual = fields.Date(
        string="Manual Expected Payment",
        copy=False,
    )

    monthly_budget_check_result = fields.Html(
        string='Monthly Budget Check',
        compute='_compute_monthly_budget_check',
    )

    buz_budget_approval_id = fields.Many2one(
        'buz.monthly.budget.approval.request',
        string='Monthly Budget Approval Request',
        compute='_compute_budget_approval_id',
        store=False,
    )
    buz_budget_approval_state = fields.Selection(
        related='buz_budget_approval_id.state',
        string='Monthly Budget Approval Status',
    )
    budget_warning = fields.Boolean(
        string='Budget Warning',
        compute='_compute_monthly_budget_check'
    )

    def _compute_budget_approval_id(self):
        ApprovalReq = self.env['buz.monthly.budget.approval.request'].sudo()
        for rec in self:
            req = ApprovalReq.search([
                ('document_type', '=', 'pr'),
                ('ref_pr_id', '=', rec.id),
            ], limit=1, order='id desc')
            rec.buz_budget_approval_id = req

    @api.depends('requisition_deadline', 'request_date', 'vendor_id', 'vendor_id.property_supplier_payment_term_id', 'requisition_order_ids.partner_id')
    def _compute_payment_date(self):
        for req in self:
            if req.payment_date_manual:
                req.payment_date = req.payment_date_manual
                continue

            # Priority logic:
            # 1. Vendor payment term from header (if used)
            payment_term = req.vendor_id.property_supplier_payment_term_id
            
            # 2. Vendor payment term from the first line that has one
            if not payment_term and req.requisition_order_ids:
                for line in req.requisition_order_ids:
                    if line.partner_id and line.partner_id.property_supplier_payment_term_id:
                        payment_term = line.partner_id.property_supplier_payment_term_id
                        break
                        
            if payment_term:
                p_date = req.request_date or fields.Date.today()
                
                # Check method availability directly to avoid exception overhead
                if hasattr(payment_term, 'compute'):
                    res = payment_term.compute(value=1, date_ref=p_date)
                    if res and res[0] and res[0][0]:
                        req.payment_date = res[0][0]
                        continue
                elif hasattr(payment_term, '_compute_terms'):
                    try:
                        res = payment_term._compute_terms(
                            date_ref=p_date,
                            currency=req.company_id.currency_id,
                            company=req.company_id,
                            taxes_and_subtotals=[{'name': '', 'tax_amount': 0.0, 'base_amount': 1.0}],
                            untaxed_amount=1.0,
                            empty_taxes=True,
                            sign=1
                        )
                        if res and getattr(res, 'get', None) and res.get('line_ids'):
                            # Odoo 17 returns a dict containing line_ids list
                            lines = res.get('line_ids')
                            req.payment_date = lines[-1].get('date') if lines else p_date
                            continue
                        elif res and isinstance(res, list):
                            # Other versions might return list of dicts directly
                            req.payment_date = res[-1].get('date') if res else p_date
                            continue
                    except Exception as e:
                        _logger.warning("biz_monthly_analytic_budget _compute_terms failed: %s", e)
                        
                # Ultimate fallback: manual parsing of days
                max_days = 0
                for line in payment_term.line_ids:
                    days = getattr(line, 'days', getattr(line, 'nb_days', 0))
                    months = getattr(line, 'months', 0)
                    total_days = (months * 30) + days
                    if total_days > max_days:
                        max_days = total_days
                if max_days > 0:
                    req.payment_date = p_date + timedelta(days=max_days)
                    continue
            
            # 3. Requisition deadline + 30 days
            if req.requisition_deadline:
                req.payment_date = req.requisition_deadline + timedelta(days=30)
            else:
                req.payment_date = (req.request_date or fields.Date.today()) + timedelta(days=30)

    def _inverse_payment_date(self):
        for req in self:
            req.payment_date_manual = req.payment_date

    # ── Computed preview ─────────────────────────────────────────

    @api.depends(
        'requisition_order_ids.price_subtotal',
        'requisition_order_ids.analytic_distribution',
        'payment_date',
    )
    def _compute_monthly_budget_check(self):
        for req in self:
            target_date = req.payment_date
            if not target_date or not req.requisition_order_ids:
                req.monthly_budget_check_result = ''
                req.budget_warning = False
                continue

            plan = find_active_monthly_plan(self.env, target_date, req.company_id.id)
            if not plan:
                req.monthly_budget_check_result = _(
                    '<div class="alert alert-info">'
                    'No active monthly analytic budget plan found for the expected payment date.'
                    '</div>'
                )
                req.budget_warning = False
                continue

            analytic_totals = {}  # {account_id: total_amount}
            for line in req.requisition_order_ids:
                for account_id, amount in extract_analytic_amounts(line):
                    analytic_totals[account_id] = analytic_totals.get(account_id, 0.0) + amount

            analytic_totals, ignored_totals = filter_analytic_totals_for_plan(plan, analytic_totals)

            if not analytic_totals:
                if ignored_totals:
                    ignored_names = ', '.join(
                        escape(name)
                        for name in self.env['account.analytic.account'].browse(
                            list(ignored_totals.keys())
                        ).mapped('display_name')
                    )
                    req.monthly_budget_check_result = _(
                        '<div class="alert alert-info">%s</div>'
                    ) % format_ignored_analytic_accounts_message(ignored_names)
                else:
                    req.monthly_budget_check_result = _(
                        '<div class="alert alert-info">'
                        '%s'
                        '</div>'
                    ) % format_no_analytic_distribution_message()
                req.budget_warning = False
                continue

            html_parts = []
            has_warning = False
            AnalyticAccount = self.env['account.analytic.account']
            BudgetLine = self.env['monthly.budget.line']
            for account_id, pr_amt in analytic_totals.items():
                analytic = AnalyticAccount.browse(account_id)
                if not analytic.exists():
                    continue
                dims = {'analytic_account_id': account_id}
                budget_line = BudgetLine._find_budget_line(plan, dims, log_fallback=False)
                if not budget_line:
                    html_parts.append(
                        '<div class="alert alert-warning">No monthly budget line for: %s</div>'
                        % analytic.name
                    )
                    continue
                budget_line = budget_line[0]
                total_after = budget_line.reserved_amount + budget_line.used_amount + pr_amt
                remaining = budget_line.budget_amount - total_after
                is_over = remaining < 0
                if is_over:
                    has_warning = True
                status_class = 'danger' if is_over else 'success'
                status_icon = '&#10060;' if is_over else '&#9989;'
                html_parts.append(
                    '<div class="card mb-2 border-%s">'
                    '<div class="card-body p-2">'
                    '<h6 class="card-title">%s %s</h6>'
                    '<table class="table table-sm table-borderless mb-0">'
                    '<tr><td>%s</td><td class="text-end">%s</td></tr>'
                    '<tr><td>%s</td><td class="text-end">%s</td></tr>'
                    '<tr><td>%s</td><td class="text-end">%s</td></tr>'
                    '<tr class="border-top"><td><strong>%s</strong></td>'
                    '<td class="text-end text-%s"><strong>%s %s</strong></td></tr>'
                    '</table></div></div>' % (
                        status_class, status_icon, analytic.name,
                        _('Monthly Budget'), '{:,.2f}'.format(budget_line.budget_amount),
                        _('Reserved + Used'), '{:,.2f}'.format(budget_line.reserved_amount + budget_line.used_amount),
                        _('This PR'), '{:,.2f}'.format(pr_amt),
                        _('Remaining After'), status_class,
                        '{:,.2f}'.format(remaining),
                        _('OK') if not is_over else _('Exceeded!'),
                    )
                )
            req.monthly_budget_check_result = ''.join(html_parts)
            req.budget_warning = has_warning

    def action_check_monthly_budget(self):
        """Button action to trigger monthly budget check recomputation."""
        self.ensure_one()
        self._compute_monthly_budget_check()
        return True

    def action_request_monthly_budget_approval(self):
        """Submit a monthly budget approval request when budget is exceeded."""
        self.ensure_one()
        target_date = self.payment_date
        plan = find_active_monthly_plan(self.env, target_date, self.company_id.id)
        if not plan:
            return

        analytic_totals = {}
        for line in self.requisition_order_ids:
            for account_id, amount in extract_analytic_amounts(line):
                analytic_totals[account_id] = analytic_totals.get(account_id, 0.0) + amount

        analytic_totals, _ignored_totals = filter_analytic_totals_for_plan(plan, analytic_totals)

        if not analytic_totals:
            return

        pr_amount = sum(analytic_totals.values())
        
        # We can't link to a single budget line if there are multiple.
        # We find the total limits, used, etc across the affected analytics for this PR
        limit_amt = 0.0
        used = 0.0
        reserved = 0.0
        AnalyticAccount = self.env['account.analytic.account']
        BudgetLine = self.env['monthly.budget.line']
        budget_line_names = []
        
        for account_id, amt in analytic_totals.items():
            analytic = AnalyticAccount.browse(account_id)
            if not analytic.exists():
                continue
            dims = {'analytic_account_id': account_id}
            bl = BudgetLine._find_budget_line(plan, dims, log_fallback=False)
            if bl:
                limit_amt += bl.budget_amount
                used += bl.used_amount
                reserved += bl.reserved_amount
                budget_line_names.append(bl.analytic_account_id.name)
                
        overage = max(0.0, used + reserved + pr_amount - limit_amt)

        return {
            'name': _('Request Monthly Budget Approval'),
            'type': 'ir.actions.act_window',
            'res_model': 'monthly.budget.request.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_type': 'pr',
                'default_ref_id': self.id,
                'default_budget_line_names': ', '.join(budget_line_names),
                'default_amount_requested': pr_amount,
                'default_amount_used': used,
                'default_amount_reserved': reserved,
                'default_amount_limit': limit_amt,
                'default_amount_overage': overage,
            }
        }

    # ── Budget enforcement ───────────────────────────────────────

    def action_confirm_requisition(self):
        """Override: check monthly analytic budget upon PR submission."""
        for req in self:
            req._check_monthly_analytic_budget()
        return super().action_confirm_requisition()

    def action_head_approval(self):
        """Override: check budget on head approval."""
        for req in self:
            req._check_monthly_analytic_budget()
        return super().action_head_approval()

    def action_purchase_approval(self):
        """Override: check budget on purchase approval."""
        for req in self:
            req._check_monthly_analytic_budget()
        return super().action_purchase_approval()

    def write(self, vals):
        prev_states = {rec.id: rec.state for rec in self}
        result = super().write(vals)
        if 'state' in vals:
            for rec in self:
                if rec.state in RESERVED_PR_STATES and prev_states.get(rec.id) != rec.state:
                    rec._reserve_monthly_analytic_budget()
        return result

    def _check_monthly_analytic_budget(self):
        """Verify each PR line's analytic distribution has sufficient monthly budget."""
        self.ensure_one()
        target_date = self.payment_date
        if not target_date or not self.requisition_order_ids:
            return

        # Check if an approved budget request exists
        approved = self.env['buz.monthly.budget.approval.request'].sudo().search([
            ('document_type', '=', 'pr'),
            ('ref_pr_id', '=', self.id),
            ('state', '=', 'approved'),
        ], limit=1)
        if approved:
            return  # Bypass budget check – approved

        plan = find_active_monthly_plan(self.env, target_date, self.company_id.id)
        if not plan:
            return  # No monthly plan active — allow

        # Aggregate by analytic account
        analytic_totals = {}
        for line in self.requisition_order_ids:
            for account_id, amount in extract_analytic_amounts(line):
                analytic_totals[account_id] = analytic_totals.get(account_id, 0.0) + amount

        analytic_totals, ignored_totals = filter_analytic_totals_for_plan(plan, analytic_totals)

        if not analytic_totals:
            if ignored_totals:
                ignored_names = ', '.join(
                    self.env['account.analytic.account'].browse(list(ignored_totals.keys())).mapped('display_name')
                )
                _logger.info(
                    'PR %s analytics ignored because they are not configured on plan %s: %s',
                    self.name,
                    plan.name,
                    ignored_names,
                )
            return  # No plan-configured analytic distribution to check

        AnalyticAccount = self.env['account.analytic.account']
        BudgetLine = self.env['monthly.budget.line']
        violations = []
        for account_id, pr_amt in analytic_totals.items():
            analytic = AnalyticAccount.browse(account_id)
            if not analytic.exists():
                continue
            dims = {'analytic_account_id': account_id}
            budget_line = BudgetLine._find_budget_line(plan, dims)
            if not budget_line:
                raise UserError(format_missing_budget_line_message(analytic.name, plan.name))

            budget_line = budget_line[:1] if len(budget_line) > 1 else budget_line
            
            total_committed = budget_line.reserved_amount + budget_line.used_amount
            
            # If not yet actively reserved by THIS document, add pr_amt
            # IMPORTANT: filter by active states only — released/cancelled commitments
            # from prior attempts must NOT suppress the overage check.
            active_commitment = self.env['budget.commitment'].sudo().search([
                ('document_model', '=', self._name),
                ('document_id', '=', self.id),
                ('analytic_account_id', '=', account_id),
                ('budget_source', '=', 'monthly'),
                ('state', 'in', ('reserved', 'used')),
            ], limit=1)

            if not active_commitment:
                total_committed += pr_amt

            overage = total_committed - budget_line.budget_amount

            if overage > 0:
                violations.append({
                    'analytic': analytic.name,
                    'budget': budget_line.budget_amount,
                    'committed': total_committed,
                    'pr_amt': pr_amt,
                    'overage': overage,
                })

        if violations:
            msg_lines = [_('Monthly Analytic Budget Exceeded!\n')]
            for v in violations:
                msg_lines.append(_(
                    'Analytic: %s\n'
                    '  Budget: %s | Committed: %s | This PR: %s | Over by: %s\n'
                ) % (
                    v['analytic'],
                    '{:,.2f}'.format(v['budget']),
                    '{:,.2f}'.format(v['committed']),
                    '{:,.2f}'.format(v['pr_amt']),
                    '{:,.2f}'.format(v['overage']),
                ))
            
            msg_lines.append(_('\nPlease click "Request Budget Approval" button to submit an approval request.'))
            raise UserError('\n'.join(msg_lines))

    def _reserve_monthly_analytic_budget(self):
        """
        Reserve monthly analytic budget for this PR.

        Flow (concurrency-safe):
        1. Determine analytic IDs from PR lines.
        2. Acquire FOR UPDATE row-level lock on matching budget lines.
        3. Re-read fresh budget data AFTER lock.
        4. Check for existing reservation (idempotency).
        5. Create commitment audit record.
        """
        self.ensure_one()
        target_date = self.payment_date
        if not target_date or not self.requisition_order_ids:
            return

        plan = find_active_monthly_plan(self.env, target_date, self.company_id.id)
        if not plan:
            return

        BudgetLine = self.env['monthly.budget.line']
        engine = self.env['budget.engine']
        AnalyticAccount = self.env['account.analytic.account']

        analytic_totals = {}
        for line in self.requisition_order_ids:
            for account_id, amount in extract_analytic_amounts(line, BudgetLine):
                analytic_totals[account_id] = analytic_totals.get(account_id, 0.0) + amount

        analytic_totals, _ignored_totals = filter_analytic_totals_for_plan(plan, analytic_totals)

        if not analytic_totals:
            return

        # --- Concurrency: acquire row-level lock BEFORE reading budget values ---
        BudgetLine._lock_budget_lines(list(analytic_totals.keys()), plan.id)

        # Re-read the current snapshot AFTER acquiring the lock
        plan._refresh_budget_snapshot(refresh_report=False)

        for account_id, total_amt in analytic_totals.items():
            analytic = AnalyticAccount.browse(account_id)
            if not analytic.exists() or not total_amt:
                continue

            dims = {'analytic_account_id': account_id}
            budget_line = BudgetLine._find_budget_line(plan, dims)
            if not budget_line:
                continue
            budget_line = budget_line[0]

            # Idempotency: keep one active reservation per document/analytic.
            commitment = self.env['budget.commitment'].sudo().search([
                ('document_model', '=', self._name),
                ('document_id', '=', self.id),
                ('analytic_account_id', '=', account_id),
                ('budget_source', '=', 'monthly'),
                ('state', '=', 'reserved'),
            ], limit=1)
            if commitment:
                if commitment.amount != total_amt:
                    commitment.write({
                        'amount': total_amt,
                        'date': target_date,
                        'note': _('Reserved from PR %s - %s') % (self.name, analytic.name),
                    })
                _logger.debug(
                    'PR %s already has reservation for analytic %s — updated/skipping duplicate',
                    self.name, analytic.name,
                )
                continue

            # Create commitment audit record
            engine.reserve_budget({
                'budget_source': 'monthly',
                'document_model': self._name,
                'document_id': self.id,
                'amount': total_amt,
                'date': target_date,
                'company_id': self.company_id.id,
                'analytic_account_id': account_id,
                'note': _('Reserved from PR %s - %s') % (self.name, analytic.name),
            })
            _logger.info(
                'Monthly budget reserved: PR=%s analytic=%s amount=%.4f plan=%s',
                self.name, analytic.name, total_amt, plan.name,
            )

        plan._refresh_budget_snapshot(refresh_report=True)

    def action_head_cancel(self):
        """Release monthly budget reservations when head cancels PR."""
        result = super().action_head_cancel()
        for req in self:
            req._release_monthly_analytic_budget()
        return result

    def action_purchase_cancel(self):
        """Release monthly budget reservations when purchase cancels PR."""
        result = super().action_purchase_cancel()
        for req in self:
            req._release_monthly_analytic_budget()
        return result

    def action_cancel_requisition(self):
        """Release monthly budget reservations when requester cancels PR."""
        result = super().action_cancel_requisition()
        for req in self:
            req._release_monthly_analytic_budget()
        return result

    def _release_monthly_analytic_budget(self):
        """Release previously reserved monthly budget amounts."""
        self.ensure_one()
        engine = self.env['budget.engine']
        document_model = self._name
        document_id = self.id
        plan = find_active_monthly_plan(self.env, self.payment_date, self.company_id.id)

        # Release all commitment records for this document
        engine.release_budget({
            'budget_source': 'monthly',
            'document_model': document_model,
            'document_id': document_id,
            'amount': 0,
            'company_id': self.company_id.id,
        })

        if plan:
            plan._refresh_budget_snapshot(refresh_report=True)
