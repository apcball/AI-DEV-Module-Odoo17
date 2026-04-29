# POS Lite Module for Odoo 17

**Lightweight form-based order entry for phone, LINE, and walk-in orders**

---

## 📋 Overview

POS Lite is a simplified Point-of-Sale module designed for manual order entry scenarios including:

- 📞 **Phone orders** — Taking orders over the phone
- 💬 **LINE orders** — Processing orders from LINE messaging
- 🚶 **Walk-in customers** — In-store walk-in sales
- 🖥️ **Back-office** — Manual order processing by staff

Unlike the standard Odoo POS, POS Lite operates entirely in the backend with a clean form-based interface. It automatically generates invoices, stock pickings, receipts, and supports session-based operation with full return/refund capabilities.

---

## 🎯 Features

| Category | Features |
|----------|----------|
| **Order Management** | Multi-channel, customer info, salesperson tracking, pricelist, order lines, auto-calculations |
| **Session Management** | Session-based workflow, kanban UI, smart buttons, user-level security |
| **Payment Processing** | Cash/Transfer/Card, payment wizard, journal selection |
| **Document Generation** | Invoice, stock picking, receipt printing (58mm/80mm/A4) |
| **Return/Refund** | Full/partial return, credit note, stock return, refund tracking |
| **Close Session** | Sales summary wizard, payment breakdown, PDF report for accounting |
| **Document Locking** | Locked after payment, safe state transitions |
| **Security** | User groups, record rules, multi-company support |

---

## 🔄 Complete Workflow

### 1. Order Lifecycle

```
┌──────────┐    Register     ┌──────────┐    Process     ┌──────────┐
│  Draft   │ ───Payment───→ │   Paid   │ ───Order────→ │   Done   │
└──────────┘                 └──────────┘                 └──────────┘
     │                             │
     │                             │
     └───────────Cancel─────────────┘
```

**States:**

| State | Description | Actions Available |
|-------|-------------|-------------------|
| **Draft** | Initial state, order being prepared | Edit lines, register payment, cancel |
| **Paid** | Payment received, order locked | Process order, cancel (if no invoice/picking) |
| **Done** | Order completed, documents created | Print receipt, create return |
| **Cancelled** | Order cancelled | View only |

### 2. Session Lifecycle

```
┌──────────┐    Open      ┌──────────┐    Orders     ┌──────────┐
│  Draft   │ ──────────→  │   Open   │ ──────────→   │  Closed  │
└──────────┘               └──────────┘               └──────────┘
                               │
                               │  Close Session
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Sales Summary      │
                    │  Wizard             │
                    │  ─────────────────  │
                    │  • Order counts     │
                    │  • Sales totals     │
                    │  • Payment breakdown│
                    │  • Print PDF report │
                    └─────────────────────┘
```

**Session States:**

| State | Description | Actions Available |
|-------|-------------|-------------------|
| **Draft** | Session prepared but not active | Open session |
| **Open** | Active session, accepting orders | View orders, close session |
| **Closed** | Session completed, summary generated | View report, view orders |

### 3. Return/Refund Flow

```
┌─────────────────┐     Create Return     ┌─────────────────┐
│   Done Order    │ ────────────────────→ │  Return Wizard  │
│                 │                        │  ─────────────  │
│  (Original)     │                        │  • Select items │
│                 │                        │  • Enter qty    │
└─────────────────┘                        │  • Add reason   │
                                           └────────┬────────┘
                                                    │
                                                    ▼
                                    ┌──────────────────────────┐
                                    │  Return Order Created    │
                                    │  ──────────────────────  │
                                    │  • Credit Note (refund)  │
                                    │  • Incoming Picking      │
                                    │  • Refund Payment        │
                                    │  • Linked to Original    │
                                    └──────────────────────────┘
```

**Return Features:**

- ✅ **Full return** — Return all items from original order
- ✅ **Partial return** — Return specific quantities per item
- ✅ **Cash refund** — Refund to cash/bank journal
- ✅ **Credit note** — Automatic `out_refund` invoice generation
- ✅ **Stock return** — Incoming picking for warehouse
- ✅ **Return tracking** — Track returned quantity per line

### 4. Payment Flow

```
┌─────────────────┐     Register Payment  ┌─────────────────┐
│   Draft Order   │ ────────────────────→ │ Payment Wizard  │
│                 │                        │  ─────────────  │
│  (Add items)    │                        │  • Cash         │
│                 │                        │  • Transfer     │
└─────────────────┘                        │  • Card         │
                                           └────────┬────────┘
                                                    │
                                                    ▼
                                    ┌──────────────────────────┐
                                    │  Payment Recorded        │
                                    │  ──────────────────────  │
                                    │  • Order → Paid state    │
                                    │  • Payment journal       │
                                    │  • Amount tracking       │
                                    └──────────────────────────┘
```

### 5. Session Close & Summary

```
┌─────────────────┐     Close Session    ┌─────────────────┐
│  Open Session   │ ──────────────────→  │  Close Summary  │
│                 │                       │  Wizard         │
│  (Has orders)   │                       │  ─────────────  │
└─────────────────┘                       │  • Order counts │
                                          │  • Sales totals │
                                          │  • Breakdown    │
                                          └────────┬────────┘
                                                   │
                                                   ▼
                                    ┌──────────────────────────┐
                                    │  Session Closed          │
                                    │  + PDF Summary Report    │
                                    │  ──────────────────────  │
                                    │  Ready for accounting    │
                                    └──────────────────────────┘
```

**Summary Report Includes:**

| Section | Details |
|---------|---------|
| **Order Counts** | Draft, Paid, Done, Cancelled, Return |
| **Sales Totals** | Gross Sales, Return Amount, Net Sales |
| **Payment Totals** | Gross Paid, Net Paid, Residual, Change |
| **Payment Breakdown** | Cash, Transfer, Card |

---

## 🏗️ Module Structure

```
pos_lite/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   └── sequence_data.xml          # Order and session sequences
├── models/
│   ├── __init__.py
│   ├── pos_config.py              # pos.lite.config
│   ├── pos_session.py             # pos.lite.session
│   ├── pos_order.py               # pos.lite.order
│   ├── pos_order_line.py          # pos.lite.order.line
│   ├── pos_payment.py             # pos.lite.payment
│   ├── product_product.py         # Product search enhancement
│   └── res_partner.py             # Partner search enhancement
├── report/
│   ├── __init__.py
│   ├── receipt_report.py          # Receipt report model
│   ├── receipt_report.xml         # Receipt templates (58mm/80mm/A4)
│   ├── session_close_summary_report.py   # Close summary model
│   └── session_close_summary_report.xml  # Close summary template
├── security/
│   ├── ir.model.access.csv        # Access control lists
│   └── security.xml               # User groups & record rules
├── views/
│   ├── menu.xml                   # Menu items
│   ├── pos_config_view.xml        # Configuration views
│   ├── pos_order_view.xml         # Order form/tree/search views
│   └── pos_session_view.xml       # Session kanban/tree/form views
├── wizard/
│   ├── __init__.py
│   ├── payment_wizard.py          # Payment wizard model
│   ├── payment_wizard_view.xml    # Payment wizard form
│   ├── return_wizard.py           # Return/refund wizard model
│   ├── return_wizard_view.xml     # Return/refund wizard form
│   ├── session_close_wizard.py    # Session close wizard model
│   └── session_close_wizard_view.xml  # Session close wizard form
└── static/
    └── description/
        └── icon.png               # Module icon
```

---

## 📊 Data Models

### `pos.lite.config` (Configuration)

| Field | Type | Description |
|-------|------|-------------|
| name | Char | Configuration name |
| company_id | Many2one | Company |
| warehouse_id | Many2one | Default warehouse |
| pricelist_id | Many2one | Default pricelist |
| journal_id | Many2one | Default payment journal |
| session_ids | One2many | Sessions using this config |
| open_session_count | Integer | Number of open sessions |
| session_count | Integer | Total sessions |

### `pos.lite.session` (Session)

| Field | Type | Description |
|-------|------|-------------|
| name | Char | Session number (auto-generated: SES0001) |
| company_id | Many2one | Company |
| user_id | Many2one | Responsible user |
| config_id | Many2one | Linked POS Lite config |
| state | Selection | Draft → Open → Closed |
| date_start | Datetime | Session start time |
| date_end | Datetime | Session close time |
| note | Text | Session notes |
| order_ids | One2many | Orders in the session |
| order_count | Integer | Total orders |
| draft_order_count | Integer | Draft orders |
| paid_order_count | Integer | Paid orders |
| done_order_count | Integer | Done orders |
| cancelled_order_count | Integer | Cancelled orders |
| return_order_count | Integer | Return orders |
| amount_total | Monetary | Net sales |
| amount_paid | Monetary | Total paid |
| amount_residual | Monetary | Remaining balance |
| amount_change | Monetary | Change amount |
| amount_return | Monetary | Total returns |

### `pos.lite.order` (Order)

| Field | Type | Description |
|-------|------|-------------|
| name | Char | Order number (auto-generated: POS0001) |
| company_id | Many2one | Company |
| state | Selection | Draft → Paid → Done → Cancelled |
| user_id | Many2one | Salesperson / responsible user |
| session_id | Many2one | Linked session |
| channel | Selection | Phone, LINE, Walk-in, Other |
| customer_name | Char | Customer name |
| partner_id | Many2one | Linked partner |
| partner_phone | Char | Customer phone |
| partner_address | Char | Customer address |
| partner_tax_id | Char | Customer tax ID |
| warehouse_id | Many2one | Warehouse |
| pricelist_id | Many2one | Pricelist |
| line_ids | One2many | Order lines |
| payment_ids | One2many | Payments |
| amount_untaxed | Monetary | Subtotal |
| amount_tax | Monetary | Tax amount |
| amount_total | Monetary | Total |
| amount_paid | Monetary | Paid amount |
| amount_residual | Monetary | Remaining balance |
| amount_change | Monetary | Change amount |
| invoice_id | Many2one | Created invoice |
| picking_id | Many2one | Created stock picking |
| is_return | Boolean | Return order flag |
| return_of_order_id | Many2one | Original order (for returns) |
| return_order_ids | One2many | Return orders linked to original |
| return_reason | Text | Return reason |
| note | Text | Internal notes |

### `pos.lite.order.line` (Order Line)

| Field | Type | Description |
|-------|------|-------------|
| order_id | Many2one | Parent order |
| product_id | Many2one | Product |
| description | Char | Product description |
| qty | Float | Quantity |
| price_unit | Monetary | Unit price |
| discount | Float | Discount % |
| price_subtotal | Monetary | Subtotal (computed) |
| price_tax | Monetary | Tax (computed) |
| price_total | Monetary | Total (computed) |

### `pos.lite.payment` (Payment)

| Field | Type | Description |
|-------|------|-------------|
| order_id | Many2one | Parent order |
| payment_method | Selection | Cash, Transfer, Card |
| amount | Monetary | Payment amount |
| journal_id | Many2one | Account journal |
| note | Char | Payment note |

---

## 🛡️ Security

### User Groups

| Group | Permissions |
|-------|-------------|
| **POS Lite User** | Create/Edit orders, order lines, payments; Read-only config |
| **POS Lite Manager** | Full access including configuration management |

### Record Rules

| Model | Rule |
|-------|------|
| Orders | `[('company_id', 'in', company_ids)]` |
| Order Lines | `[('company_id', 'in', company_ids)]` |
| Payments | `[('company_id', 'in', company_ids)]` |
| Config | `[('company_id', 'in', company_ids)]` |
| Sessions | Users see only own sessions: `[('user_id', '=', user.id)]` + company rule |

### Document Locking

- Orders are **locked after payment** (state != draft)
- Only `state` field can be modified on locked orders
- Safe state transitions enforced (e.g., only paid → done or cancelled)

---

## 📦 Dependencies

```python
'depends': [
    'base',
    'mail',            # chatter/messaging
    'contacts',        # partner management
    'product',         # product catalog
    'stock',           # inventory/picking
    'account',         # invoicing
    'sale_management', # pricelists
]
```

---

## 🚀 Installation

1. Copy `pos_lite` folder to your Odoo addons path
2. Update module list in Odoo
3. Install "POS Lite" module
4. Configure default settings in **POS Lite > Configuration**
5. Open a session from **POS Lite > Sessions**

---

## ⚙️ Configuration

### Default Settings

Navigate to **POS Lite > Configuration** to set:

| Field | Description |
|-------|-------------|
| Warehouse | Default warehouse for orders |
| Pricelist | Default pricing |
| Payment Journal | Default cash/bank journal |

### Sequence Configuration

| Sequence | Format | Example |
|----------|--------|---------|
| Orders | POS + 4 digits | POS0001, POS0002 |
| Sessions | SES + 4 digits | SES0001, SES0002 |

---

## 🖨️ Receipt Printing

Three receipt formats available:

| Format | Paper Size | DPI | Best For |
|--------|------------|-----|----------|
| Thermal 58mm | 58mm width | 90 | Small thermal printers |
| Thermal 80mm | 80mm width | 90 | Standard thermal printers |
| A4 | Standard A4 | 90 | Regular paper printing |

---

## 📝 Usage Guide

### Creating an Order

1. Navigate to **POS Lite > Orders**
2. Click **Create**
3. Fill in:
   - **Session**: Auto-assigned or select open session
   - **Salesperson**: Auto-assigned to current user
   - **Channel**: Phone/LINE/Walk-in/Other
   - **Customer**: Select existing or enter name/phone
   - **Warehouse**: Select delivery warehouse
   - **Pricelist**: Select pricing
4. Add order lines:
   - Select product
   - Enter quantity
   - Price auto-fills from pricelist
   - Apply discount if needed
5. Click **Register Payment**
6. Enter payment amount and method
7. Click **Confirm**

### Processing the Order

1. Open the paid order
2. Click **Process Order**
3. System automatically:
   - Creates customer invoice
   - Posts the invoice
   - Creates stock picking
   - Validates the picking
4. Order moves to **Done** state

### Creating a Return

1. Open completed order (`state = Done`)
2. Click **Create Return**
3. Return wizard opens:
   - Select products to return
   - Enter return quantity (full or partial)
   - Add return reason (optional)
4. Click **Create Return**
5. System automatically:
   - Creates return order linked to original
   - Creates Credit Note (`out_refund`)
   - Creates incoming picking for stock return
   - Processes refund payment
6. Return order moves to **Done** state

### Closing a Session

1. Open session (`state = Open`)
2. Click **Close Session**
3. Sales Summary Wizard opens showing:
   - Order counts (Draft/Paid/Done/Cancelled/Return)
   - Gross Sales / Return Amount / Net Sales
   - Gross Paid / Net Paid / Residual / Change
   - Payment breakdown (Cash/Transfer/Card)
4. Click **Close & Print Summary**
5. Session closes and PDF report opens
6. PDF ready to send to accounting

### Printing Receipt

1. Open completed order
2. Click receipt button (58mm/80mm/A4)
3. Print or save PDF

---

## 🔧 Technical Notes

### Model Naming

Models use `pos.lite.*` naming convention to avoid conflicts with standard Odoo POS module (`pos.order`, `pos.payment`, `pos.config`).

### Company Isolation

All models use `check_company=True` on relational fields and have record rules for multi-company data isolation.

### Performance

Product and partner search enhancements are context-aware — only activates when `pos_lite_search` or `pos_lite_partner_search` context is set.

---

## 📄 License

LGPL-3

## 👥 Authors

- AI-DEV-Module-Odoo17
- Website: https://github.com/apcball/AI-DEV-Module-Odoo17

---

*Last updated: 2026-04-29*
