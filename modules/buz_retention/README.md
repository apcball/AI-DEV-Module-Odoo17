# buz_retention

Odoo 17 module for retention offset between a Vendor Bill and a Customer Invoice.

## Purpose

This module does **not** deduct retention from invoice lines.
Instead, it:

1. Creates a posted vendor bill that represents the retention amount.
2. Later, applies that bill against a posted customer invoice.
3. Creates a balancing journal entry and reconciles both sides.

## Business Flow

- Post a vendor bill for the retention amount.
- Open the customer invoice.
- Select one or more posted retention bills.
- Click **Apply Retention Bill**.
- The system creates an offset journal entry:
  - Dr Accounts Payable
  - Cr Accounts Receivable
- The payable line on each retention bill is reconciled.
- The receivable line on the customer invoice is reconciled.

## Features

- Customer invoice field for selecting retention bills
- Apply button on posted customer invoices
- Retention total display
- Per-company retention journal setting
- Journal entry creation and reconciliation

## Settings

Configure the **Retention Journal** in Accounting > Settings.
The journal is stored per company.

## Technical Notes

- Depends on `account`
- Uses standard Odoo models only
- No core files are modified
- V1 limitation: only company-currency invoices and vendor bills are supported

## Install

1. Copy the module into the Odoo addons path.
2. Update apps list.
3. Install **Buz Retention**.
4. Configure the Retention Journal in Accounting settings.

## Usage

1. Create and post a Vendor Bill for the retention amount.
2. Create and post the Customer Invoice.
3. On the invoice, select the retention bill(s).
4. Click **Apply Retention Bill**.

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
