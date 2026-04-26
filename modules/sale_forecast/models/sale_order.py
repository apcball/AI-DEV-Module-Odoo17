from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    forecast_allocation_ids = fields.One2many(
        "forecast.allocation", "sale_order_id", string="Forecast Allocations"
    )
    forecast_allocation_count = fields.Integer(compute="_compute_forecast_allocation_count")

    @api.depends("forecast_allocation_ids")
    def _compute_forecast_allocation_count(self):
        for rec in self:
            rec.forecast_allocation_count = len(rec.forecast_allocation_ids)

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
