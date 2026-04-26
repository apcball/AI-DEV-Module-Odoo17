# sale_forecast (Odoo 17)

Sales Forecast module for 3-month demand planning, allocation to sale orders, and forecast-vs-actual tracking.

## Features

- Create **Forecast Plans** (`forecast.plan`) for current month + next 2 months
- Add **Forecast Lines** (`forecast.line`) by product and arrival month/week
- Optional manual reference to blanket PO (`blanket_reference`)
- Weekly delivery balancing: split monthly forecast qty evenly into week buckets (W1..W5)
- Create **Forecast Allocations** (`forecast.allocation`) linked to a specific Sale Order
- Auto-create/update Sale Order line from each allocation
- Prevent over-allocation beyond forecast availability
- KPI dashboard views:
  - Forecast Qty vs Allocated Qty vs Actual Sold Qty (product/month)
  - Allocation performance by salesperson/month
- Sale Order extension shows linked forecast allocations

## Business Rules Implemented

1. Forecast horizon is limited to **3 months** (current month + next 2 months)
2. Allocation cannot exceed forecast remaining quantity
3. Allocation must link to a specific Sale Order
4. Weekly schedule distribution balances arrivals across weeks

## Security / Roles

Three module roles are provided:

- **Forecast Planner**
  - Create/Edit Forecast Plans and Lines
  - Read allocations
- **Forecast Sales Allocator**
  - Read plans/lines
  - Create/Edit allocations
- **Forecast Manager**
  - Full access + dashboard menu

## Installation

1. Copy module into Odoo addons path:

```bash
cp -r modules/sale_forecast /path/to/odoo/addons/
```

2. Restart Odoo and update apps list.
3. Install module **Sales Forecast Planning**.

CLI example:

```bash
./odoo-bin -c odoo.conf -u sale_forecast --stop-after-init
```

## Usage

1. Go to **Sales ▸ Sales Forecast ▸ Forecast Plans**
2. Create a plan (start date should be first day of month)
3. Add forecast lines with product, quantity, arrival month, expected week
4. Click **Distribute All Lines Weekly** to auto-balance weekly buckets
5. Confirm the plan
6. Go to **Forecast Allocations** and create allocation records:
   - Select plan + forecast line
   - Select sale order
   - Enter allocated quantity
7. Module creates/updates sale order line automatically
8. Use **Forecast Dashboard** and allocation pivot/graph for KPI analysis

## Notes

- Blanket PO integration is currently **manual reference only** (phase 2 integration excluded)
- Budget integration is intentionally out of scope

## Technical Objects

- Models:
  - `forecast.plan`
  - `forecast.line`
  - `forecast.allocation`
  - Inherited: `sale.order`, `sale.order.line`
- Sequences:
  - `forecast.plan`
  - `forecast.allocation`
- Data files:
  - `security/sale_forecast_security.xml`
  - `security/ir.model.access.csv`
  - `data/sequence_data.xml`
