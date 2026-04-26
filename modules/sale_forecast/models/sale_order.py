from collections import defaultdict

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    forecast_allocation_ids = fields.One2many(
        "forecast.allocation", "sale_order_id", string="Forecast Allocations"
    )
    forecast_allocation_count = fields.Integer(compute="_compute_forecast_allocation_count")

    def action_confirm(self):
        res = super().action_confirm()
        self._auto_allocate_forecast_from_sale()
        return res

    @api.depends("forecast_allocation_ids")
    def _compute_forecast_allocation_count(self):
        for rec in self:
            rec.forecast_allocation_count = len(rec.forecast_allocation_ids)

    def _auto_allocate_forecast_from_sale(self):
        ForecastPlan = self.env["forecast.plan"].sudo()
        ForecastAllocation = self.env["forecast.allocation"].sudo()
        for order in self.filtered(lambda o: o.state in ("sale", "done") and o.user_id):
            month_start = fields.Date.start_of(fields.Date.context_today(order), "month")
            plan = ForecastPlan.search(
                [
                    ("user_id", "=", order.user_id.id),
                    ("start_date", "=", month_start),
                    ("company_id", "=", order.company_id.id),
                    ("state", "!=", "cancel"),
                ],
                limit=1,
            )
            allocated_totals = defaultdict(float)
            for existing_alloc in ForecastAllocation.search(
                [("plan_line_id", "in", plan.line_ids.ids), ("state", "!=", "cancel"), ("is_non_forecast", "=", False)]
            ):
                allocated_totals[existing_alloc.plan_line_id.id] += existing_alloc.allocated_qty

            for line in order.order_line.filtered(lambda l: not l.display_type and l.product_id and l.product_uom_qty > 0):
                if ForecastAllocation.search(
                    [("sale_order_line_id", "=", line.id), ("state", "!=", "cancel")], limit=1
                ):
                    continue

                remaining_qty = line.product_uom_qty
                first_allocation = False
                line_is_non_forecast = False

                forecast_lines = plan.line_ids.filtered(
                    lambda pl: pl.product_id == line.product_id
                    and pl.arrival_month
                    and fields.Date.start_of(pl.arrival_month, "month") == month_start
                ) if plan else self.env["forecast.line"]

                for forecast_line in forecast_lines:
                    if remaining_qty <= 0:
                        break
                    available_qty = forecast_line.forecast_qty - allocated_totals[forecast_line.id]
                    if available_qty <= 0:
                        continue
                    alloc_qty = min(remaining_qty, available_qty)
                    allocation = ForecastAllocation.create(
                        {
                            "plan_id": plan.id,
                            "plan_line_id": forecast_line.id,
                            "product_id": line.product_id.id,
                            "allocated_qty": alloc_qty,
                            "sale_order_id": order.id,
                            "sale_order_line_id": line.id,
                            "is_non_forecast": False,
                        }
                    )
                    allocated_totals[forecast_line.id] += alloc_qty
                    remaining_qty -= alloc_qty
                    if not first_allocation:
                        first_allocation = allocation
                    line.is_forecast_allocation = True

                if remaining_qty > 0:
                    line_is_non_forecast = True
                    if plan:
                        target_line = forecast_lines[:1]
                        allocation_vals = {
                            "plan_id": plan.id,
                            "product_id": line.product_id.id,
                            "allocated_qty": remaining_qty,
                            "sale_order_id": order.id,
                            "sale_order_line_id": line.id,
                            "is_non_forecast": True,
                        }
                        if target_line:
                            allocation_vals["plan_line_id"] = target_line.id
                        allocation = ForecastAllocation.create(allocation_vals)
                        if not first_allocation:
                            first_allocation = allocation
                    else:
                        line_is_non_forecast = True

                line.is_non_forecast = line_is_non_forecast
                line.forecast_allocation_id = first_allocation.id if first_allocation else False

    def action_view_forecast_allocations(self):
        self.ensure_one()
        action = self.env.ref("sale_forecast.action_forecast_allocation").read()[0]
        action["domain"] = [("sale_order_id", "=", self.id)]
        action["context"] = {
            "default_sale_order_id": self.id,
            "default_plan_id": self.forecast_allocation_ids[:1].plan_id.id,
        }
        return action


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    forecast_allocation_id = fields.Many2one("forecast.allocation", string="Forecast Allocation", index=True)
    is_forecast_allocation = fields.Boolean(string="From Forecast Allocation", default=False)
    is_non_forecast = fields.Boolean(string="Non-Forecast", default=False)
