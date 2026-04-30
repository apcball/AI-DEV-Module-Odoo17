# buz_retention

Odoo 17 module for retention offset between a Vendor Bill and a Customer Invoice.

## Purpose

This module does **not** deduct retention from invoice lines.
Instead, it:

1. Creates a retention vendor bill from the customer invoice, if needed.
2. Later, applies that bill against a posted customer invoice.
3. Creates a balancing journal entry and reconciles both sides.

## Business Flow

- Create or post a vendor bill for the retention amount.
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
- Create button on posted customer invoices
- Apply button on posted customer invoices
- Retention total display
- Per-company retention journal setting
- Per-company retention account setting
- Journal entry creation and reconciliation

## Settings

Configure the **Retention Journal** and **Retention Account** in Accounting > Settings.
The values are stored per company.

## Technical Notes

- Depends on `account`
- Uses standard Odoo models only
- No core files are modified
- V1 limitation: only company-currency invoices and vendor bills are supported

## Install

1. Copy the module into the Odoo addons path.
2. Update apps list.
3. Install **Buz Retention**.
4. Configure the Retention Journal and Retention Account in Accounting settings.

## Usage

1. Open the Customer Invoice.
2. Click **Create Retention Bill** if you want the module to generate the vendor bill automatically.
3. Or select an existing posted retention bill.
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
