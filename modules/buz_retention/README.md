# buz_retention

Odoo 17 module for retention settlement between a Customer Invoice and one or more Vendor Bills.

## Purpose

This module does **not** deduct retention from invoice lines.
Instead, it works in two steps:

1. Create a retention vendor bill from a posted customer invoice.
2. Apply posted retention bill(s) back to the customer invoice by creating a balancing journal entry and reconciling both sides.

## How It Works

### 1) Create Retention Bill
From a posted customer invoice, click **Create Retention Bill**.
The module will:

- create a vendor bill in the same company
- use the configured Retention Account on the bill line
- post the bill automatically
- link the new bill back to the customer invoice

### 2) Apply Retention Bill
Select one or more posted retention bills on the customer invoice, then click **Apply Retention Bill**.
The module will:

- create a balancing journal entry in the configured Retention Journal
- debit Accounts Payable
- credit Accounts Receivable
- reconcile the vendor bill payable line(s)
- reconcile the customer invoice receivable line

## Features

- Create retention vendor bill from posted customer invoice
- Select existing posted retention bills on invoice
- Apply retention bill(s) with one click
- Automatic journal entry creation
- Automatic reconciliation on both payable and receivable sides
- Per-company Retention Journal setting
- Per-company Retention Account setting

## Settings

Configure the following in **Accounting > Settings**:

- **Retention Journal**: general journal used for the offset entry
- **Retention Account**: expense or clearing account used when creating the retention vendor bill

Both settings are stored per company.

## Requirements

- Odoo 17
- Module dependency: `account`

## Limitations

V1 supports only:

- company-currency customer invoices
- company-currency vendor bills
- exact amount match between invoice residual and selected retention bill residual(s)
- posted records only

## Installation

1. Copy the module into your Odoo addons path.
2. Update the apps list.
3. Install **Buz Retention**.
4. Configure the retention settings in Accounting.

## Usage Example

1. Open a posted customer invoice.
2. Click **Create Retention Bill** if you want the module to generate the bill automatically.
3. Or select an existing posted retention bill.
4. Click **Apply Retention Bill**.
5. Review the created offset journal entry and reconciliations.

## Module Structure

```text
buz_retention/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── account_move.py
│   └── res_config_settings.py
├── views/
│   ├── account_move_views.xml
│   └── res_config_settings_views.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

## Notes

- No Odoo core files are modified.
- The module uses standard Odoo accounting models and views.
- If you need partial retention support or multi-currency support, that can be added in a later version.
