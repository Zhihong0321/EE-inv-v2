# Invoice System Schema Reference (Legacy & Production)

This document provides a comprehensive reference for the `invoice` and `invoice_item` tables, which serve as the core of the EE Invoicing ERP system. These tables use the schema originally established in Bubble.io, now running on a production PostgreSQL database.

## 1. Invoice Table (`invoice`)
The primary table tracking sales, payments, statuses, and solar project metadata.

### Core Identification & Metadata
| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key (Auto-increment). |
| `bubble_id` | `text` | Unique string ID used for relationships across the system. |
| `invoice_id` | `integer` | Human-readable sequence number (e.g., 1000042). |
| `created_date` | `timestamp` | Original creation timestamp. |
| `modified_date` | `timestamp` | Last modification timestamp. |
| `last_synced_at` | `timestamp` | Last sync between systems. |
| `created_by` | `text` | User ID of the creator. |

### Financials & Calculations
| Column | Type | Description |
|--------|------|-------------|
| `amount` | `numeric` | Total invoice amount. |
| `stamp_cash_price`| `numeric` | Base price before adjustments. |
| `discount_amount` | `numeric` | (Calculated) Total discounts applied. |
| `eligible_amount_description` | `text` | Break-down of financials in text format. |
| `percent_of_total_amount` | `numeric` | Percentage tracking. |

### Payment Tracking
| Column | Type | Description |
|--------|------|-------------|
| `paid` | `boolean` | Overall payment status. |
| `1st_payment` | `integer` | First milestone percentage (e.g., 5). |
| `1st_payment_date`| `timestamp` | Date first payment was received. |
| `2nd_payment` | `integer` | Second milestone percentage (e.g., 65). |
| `last_payment_date`| `timestamp` | Date of the most recent payment. |
| `full_payment_date`| `timestamp` | Date the invoice was fully settled. |
| `linked_payment` | `ARRAY(text)` | List of `bubble_id`s from the payment table. |

### Solar Project Details
| Column | Type | Description |
|--------|------|-------------|
| `panel_qty` | `integer` | Number of solar panels. |
| `panel_rating` | `integer` | Wattage rating per panel. |
| `estimated_saving`| `numeric` | Calculated monthly savings for the client. |
| `estimated_new_bill_amount` | `numeric` | Predicted TNB bill after installation. |
| `achieved_monthly_anp` | `numeric` | Annualized Net Profit metrics. |

### Status & Workflow
| Column | Type | Description |
|--------|------|-------------|
| `approval_status` | `text` | Workflow state (e.g., "Approved", "Draft"). |
| `case_status` | `text` | Project execution status. |
| `stock_status_inv`| `text` | Inventory/stock tracking status. |
| `need_approval` | `boolean` | Flag for admin review. |

### Relationships (linked via `bubble_id`)
| Column | Type | Links To |
|--------|------|----------|
| `linked_customer` | `text` | `customer.bubble_id` |
| `linked_agent` | `text` | `agent.bubble_id` |
| `linked_package` | `text` | `package.bubble_id` |
| `linked_seda_registration` | `text` | `seda_registration.bubble_id` |
| `linked_invoice_item` | `ARRAY(text)` | `invoice_item.bubble_id` |

---

## 2. Invoice Item Table (`invoice_item`)
Tracks individual line items, including packages, products, and adjustments.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key. |
| `bubble_id` | `text` | Unique ID. |
| `linked_invoice` | `text` | Reference to `invoice.bubble_id`. |
| `description` | `text` | Line item text. |
| `qty` | `integer` | Quantity. |
| `unit_price` | `numeric` | Price per unit. |
| `amount` | `numeric` | Total for this line (qty * unit_price). |
| `is_a_package` | `boolean` | If true, links to a `package` record. |
| `inv_item_type` | `text` | Categorization (e.g., "Discount", "EPP Fee"). |
| `linked_package` | `text` | `package.bubble_id` |
| `sort` | `integer` | Display order. |

---

## 3. Related Tables

### Package Table (`package`)
Defines pre-bundled solar solutions.
- `bubble_id`: Unique ID.
- `name`: Package title.
- `price`: Total package cost.
- `invoice_desc`: The text used when this package is added to an invoice.
- `items`: JSON array of components (legacy).
- `linked_package_item`: ARRAY of `package_item.bubble_id`s.

### Customer Table (`customer`)
- `customer_id`: Unique string ID.
- `name`, `phone`, `email`: Contact details.
- `address`, `city`, `state`, `postcode`: Location details.
- `ic_number`: ID verification.

---

## 4. Key Findings & Business Logic
1.  **Immutability Strategy:** When creating new invoices, the system snapshots agent and package names into `_snapshot` columns in the new tables to preserve historical accuracy.
2.  **Milestone Payments:** Most solar projects follow a 5% (1st) and 65% (2nd) payment structure, which is tracked via specific integer columns and date fields.
3.  **Relational Model:** The database relies heavily on the `bubble_id` (a string) rather than standard integer Foreign Keys. This must be respected when performing JOINs.
4.  **Legacy Integration:** Even in the "New" system components, reading from these legacy tables is essential for historical data and cross-referencing old project registrations.

