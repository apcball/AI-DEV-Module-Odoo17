# POS Lite Module for Odoo 17

**Lightweight form-based order entry for phone, LINE, and walk-in orders**

## 📋 Overview

POS Lite is a simplified Point-of-Sale module for manual order entry scenarios such as phone orders, LINE orders, walk-in customers, and back-office sales processing.

It combines a clean backend form with a modern kanban/session dashboard, smart buttons, automatic document generation, refund handling, and session-based operation. The module is designed to be fast to use on desktop while still remaining simple enough for frontline staff.

## 🎯 Features

### Order Management
- **Multi-channel support**: Phone, LINE, Walk-in, Other
- **Customer information**: Name, phone, address, tax ID
- **Salesperson**: `user_id` on each order
- **Warehouse selection**: Per-order warehouse assignment
- **Pricelist support**: Automatic price calculation based on pricelist
- **Order lines**: Add products with quantity, price, discount
- **Automatic calculations**: Subtotal, tax, total, paid amount, change

### Session Management
- **Session-based workflow**: Orders are grouped into `pos.lite.session`
- **Modern UI**: Kanban view, status colors, and smart buttons
- **Session smart buttons**: Quick access to session orders and totals
- **Responsible user**: Session owner tracked with `user_id`
- **Open / Close control**: Draft → Open → Closed lifecycle

### Payment Processing
- **Single payment per order**: Cash, Transfer, or Card
- **Payment wizard**: Easy payment registration
- **Journal selection**: Auto-select cash/bank journal from config

### Document Generation
- **Invoice creation**: Automatic `account.move` (`out_invoice`)
- **Stock picking**: Automatic `stock.picking` for product delivery
- **Receipt printing**: Three formats available
  - Thermal 58mm
  - Thermal 80mm
  - A4 PDF

### Return / Refund
- **Return wizard**: Create a return from completed orders
- **Credit note**: Automatic `out_refund` generation
- **Stock return**: Incoming picking for returned products
- **Refund payment**: Supports refund registration and tracking
- **Partial or full return**: Return specific quantities or the full order

### Document Locking
- **Locked after payment**: Paid orders cannot be edited like drafts
- **Safe state transitions**: Only valid status changes are allowed
- **Controlled cancellation**: Completed orders cannot be cancelled

### Security & Permissions
- **POS Lite User**: Can create/edit orders, register payments
- **POS Lite Manager**: Full access including configuration
- **Session user rule**: Users can only access their own sessions
- **Multi-company support**: Record rules for data isolation

## 🏗️ Module Structure

```
pos_lite/
├── __init__.py
├── __manifest__.py
├── README.md
├── data/
│   └── sequence_data.xml          # Order and session sequence configuration
├── models/
│   ├── __init__.py
│   ├── pos_order.py               # Main order model (pos.lite.order)
│   ├── pos_payment.py             # Payment model (pos.lite.payment)
│   ├── pos_config.py              # Configuration model (pos.lite.config)
│   ├── pos_session.py             # Session model (pos.lite.session)
│   ├── product_product.py         # Product search enhancement
│   └── res_partner.py             # Partner search enhancement
├── report/
│   ├── __init__.py
│   ├── receipt_report.py          # Receipt report model
│   └── receipt_report.xml         # Receipt templates & paper formats
├── security/
│   ├── ir.model.access.csv        # Access control lists
│   └── security.xml               # User groups & record rules
├── views/
│   ├── menu.xml                   # Menu items
│   ├── pos_order_view.xml         # Order form/tree/search views
│   ├── pos_config_view.xml        # Configuration views
│   └── pos_session_view.xml       # Session kanban/tree/form views
├── wizard/
│   ├── __init__.py
│   ├── payment_wizard.py          # Payment wizard model
│   ├── payment_wizard_view.xml    # Payment wizard form
│   ├── return_wizard.py           # Return/refund wizard model
│   └── return_wizard_view.xml     # Return/refund wizard form
└── static/
    └── description/
        └── icon.png               # Module icon
```

## 📊 Data Models

### `pos.lite.order` (POS Lite Order)
Main order model with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| name | Char | Order number (auto-generated) |
| company_id | Many2one | Company |
| currency_id | Many2one | Company currency |
| state | Selection | Draft → Paid → Done → Cancelled |
| user_id | Many2one | Salesperson / responsible user |
| session_id | Many2one | Linked session |
| channel | Selection | Phone, LINE, Walk-in, Other |
| customer_name | Char | Customer name (for walk-in) |
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
| is_return | Boolean | Marks return/refund order |
| return_of_order_id | Many2one | Original order for the return |
| return_order_ids | One2many | Return orders linked to the original |
| return_reason | Text | Return reason |
| note | Text | Internal notes |

### `pos.lite.order.line` (Order Line)
| Field | Type | Description |
|-------|------|-------------|
| order_id | Many2one | Parent order |
| company_id | Many2one | Company |
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

### `pos.lite.config` (Configuration)
| Field | Type | Description |
|-------|------|-------------|
| name | Char | Config name |
| company_id | Many2one | Company |
| warehouse_id | Many2one | Default warehouse |
| pricelist_id | Many2one | Default pricelist |
| journal_id | Many2one | Default payment journal |

### `pos.lite.session` (Session Management)
Session model used to group and control order processing.

| Field | Type | Description |
|-------|------|-------------|
| name | Char | Session number (auto-generated) |
| company_id | Many2one | Company |
| user_id | Many2one | Responsible user |
| config_id | Many2one | Linked POS Lite config |
| warehouse_id | Many2one | Related warehouse |
| pricelist_id | Many2one | Related pricelist |
| journal_id | Many2one | Related payment journal |
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

## 🔄 Session Management

### Overview
A POS Lite session represents an operational working period for a cashier or salesperson. Orders are attached to an open session automatically so that sales activity can be tracked by shift, user, and configuration.

The session dashboard provides a modern kanban view with quick status recognition and smart buttons for fast navigation.

### Session Workflow
1. **Draft**: Session is prepared but not yet in use
2. **Open**: Session becomes active and can accept orders
3. **Order capture**: New orders are linked to the open session automatically
4. **Close**: Session can be closed once draft orders are processed or cancelled

### Session Fields
Key session fields include:
- `name`
- `company_id`
- `user_id`
- `config_id`
- `state`
- `date_start`
- `date_end`
- `order_ids`
- summary counters and totals such as `order_count`, `amount_total`, `amount_paid`, `amount_residual`, and `amount_return`

### Session Security (user rule)
Session access is protected by a user rule:
- Users can only see sessions where `user_id = current user`
- Multi-company record rules still apply
- Managers inherit user access and can manage sessions across allowed companies

## 🔄 Order Workflow

```
┌─────────┐    Register     ┌─────────┐    Process     ┌─────────┐
│  Draft  │ ───Payment───→ │  Paid   │ ───Order────→ │  Done   │
└─────────┘                 └─────────┘                 └─────────┘
     │                           │
     │                           │
     └───────────Cancel──────────┘
```

### States:
1. **Draft**: Initial state, can edit order lines and register payment
2. **Paid**: Payment received, order is locked from normal editing
3. **Done**: Order completed, invoice and picking created
4. **Cancelled**: Order cancelled (cannot cancel if invoice posted or picking done)

## 🛡️ Security

### User Groups
- **POS Lite User** (`group_pos_lite_user`):
  - Create/Edit orders, order lines, payments
  - Read-only access to configuration
  - Cannot delete records

- **POS Lite Manager** (`group_pos_lite_manager`):
  - Full access to all models including configuration
  - Inherits User permissions

### Record Rules
All models have company-based record rules:
- Orders: `[('company_id', 'in', company_ids)]`
- Order Lines: `[('company_id', 'in', company_ids)]`
- Payments: `[('company_id', 'in', company_ids)]`
- Config: `[('company_id', 'in', company_ids)]`
- Sessions: `[('company_id', 'in', company_ids)]`

### Session User Rule
- Session users are restricted to their own sessions
- This keeps shift ownership clear and prevents cross-user session editing

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

## 🚀 Installation

1. Copy `pos_lite` folder to your Odoo addons path
2. Update module list in Odoo
3. Install "POS Lite" module
4. Configure default settings in POS Lite Config and open a session

## ⚙️ Configuration

### Default Settings (Optional)
Navigate to **POS Lite > Configuration** to set default:
- Warehouse
- Pricelist
- Payment Journal

This allows faster order creation by pre-filling these fields.

### Session Setup
Create or open a session from **POS Lite > Sessions** before processing orders.

### Sequence Configuration
Order and session numbers are auto-generated using their sequences.
- Order default format: `POL00001`, `POL00002`, etc.
- Session numbering is handled automatically from `pos.lite.session`

## 🖨️ Receipt Printing

Three receipt formats are available:

### Thermal 58mm
- Paper width: 58mm
- Margins: 2mm all sides
- DPI: 90
- Best for: Small thermal printers

### Thermal 80mm
- Paper width: 80mm
- Margins: 3mm left/right, 2mm top/bottom
- DPI: 90
- Best for: Standard thermal printers

### A4
- Standard A4 paper
- Margins: 10mm left/right, 12mm top/bottom
- DPI: 90
- Best for: Printing on regular paper

## 📝 Usage Guide

### Creating an Order

1. Navigate to **POS Lite > Orders**
2. Click **Create**
3. Fill in:
   - **Session**: Select an open session or let the system assign one
   - **Salesperson**: Assigned automatically to the current user by default
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

### Return Features
- **Full return**: Return all items from original order
- **Partial return**: Return specific quantities
- **Cash refund**: Refund to cash/bank journal
- **Credit note**: Automatic credit note generation
- **Stock return**: Incoming picking for warehouse
- **Return tracking**: Track returned quantity per line

### Printing Receipt

1. Open completed order
2. Click receipt button (58mm/80mm/A4)
3. Print or save PDF

## 🔧 Technical Notes

### Model Naming
Models use `pos.lite.*` naming convention to avoid conflicts with standard Odoo POS module (`pos.order`, `pos.payment`, `pos.config`).

### Company Isolation
All models use `check_company=True` on relational fields and have record rules for multi-company data isolation.

### Performance
- Product and partner search enhancements are context-aware
- Only activates when `pos_lite_search` or `pos_lite_partner_search` context is set

## 📄 License

LGPL-3

## 👥 Authors

- AI-DEV-Module-Odoo17
- Website: https://github.com/apcball/AI-DEV-Module-Odoo17

---

*Last updated: 2026-04-29*