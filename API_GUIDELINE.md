# EE Invoicing System - API Guideline for App Developers

## Introduction
This document provides technical details for integrating with the EE Invoicing System API. The system is designed to handle on-the-fly invoice generation, customer management, and professional branding for microservices within the ecosystem.

## Base URL
- **Staging/Local**: `http://localhost:8000/api/v1`
- **Production**: `[Production URL]/api/v1`

---

## Authentication

The API supports two types of authentication. All authenticated requests must include the `Authorization` header.

### 1. API Key (Recommended for Microservices)
Used for server-to-server communication.
- **Header**: `Authorization: Bearer sk_[your_api_key]`
- **Note**: API keys always start with `sk_`.

### 2. JWT Token
Used for client-side applications after a user logs in via WhatsApp.
- **Header**: `Authorization: Bearer [jwt_token]`

---

## Endpoint: Create Invoice On-The-Fly

Creates a new invoice based on a package and returns a shareable link.

- **Method**: `POST`
- **URL**: `/invoices/on-the-fly`
- **Auth**: Optional (Required only if you want to see `agent_markup` in the response).

### Request Body (JSON)

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `package_id` | `string` | **Yes** | The UID of the package from the legacy system. |
| `customer_name` | `string` | No | Customer's full name. If omitted, invoice is marked as **"Sample Quotation"**. |
| `customer_phone` | `string` | No | Customer's phone number. |
| `customer_address` | `string` | No | Customer's physical address. |
| `discount_fixed` | `number` | No | Fixed amount discount (e.g., `50.00`). Default: `0`. |
| `discount_percent` | `number` | No | Percentage discount (0-100). Default: `0`. |
| `apply_sst` | `boolean` | No | Whether to apply SST (8%). Default: `true`. |
| `template_id` | `string` | No | UID of the company template to use for branding. |
| `voucher_code` | `string` | No | Active voucher code to apply. |
| `agent_markup` | `number` | No | Hidden markup amount to add to package total. Visible only to authenticated agents. |

### Example Request
```json
{
  "package_id": "1703833647950x572894707690242050",
  "customer_name": "John Doe",
  "customer_phone": "60123456789",
  "discount_fixed": 100.0,
  "voucher_code": "PROMO2024",
  "apply_sst": true,
  "agent_markup": 500.0
}
```

---

## Response Structure

### Success Response (200 OK)

| Field | Type | Description |
| :--- | :--- | :--- |
| `success` | `boolean` | Indicates if the creation was successful. |
| `invoice_link` | `string` | Publicly shareable URL to view the professional HTML invoice. |
| `invoice_number` | `string` | The generated unique invoice number (e.g., `INV-000021`). |
| `bubble_id` | `string` | Unique internal ID for the invoice. |
| `total_amount` | `number` | The final total amount after discounts and SST. |
| `agent_markup`* | `number` | The markup amount (Only returned if authenticated). |
| `subtotal_with_markup`* | `number` | Subtotal including the agent markup (Only returned if authenticated). |

*\* Fields marked with an asterisk are only available for authenticated requests.*

### Error Responses

- **400 Bad Request**: Invalid parameters (e.g., package not found, invalid discount percentage).
- **401 Unauthorized**: Invalid or expired API key/JWT token.
- **500 Internal Server Error**: Unexpected server error.

---

## Professional HTML View

The `invoice_link` returned in the response (e.g., `.../view/[token]`) is designed for browsers.
- **Browsers**: Will render a high-professional, business-oriented HTML invoice.
- **API Clients**: If you request this link with `Accept: application/json`, it will return the raw invoice data instead of HTML.

---

## Best Practices

1. **Snapshots**: The system takes a snapshot of customer and package data at the time of creation. Changing the package price in the legacy system later will NOT affect already created invoices.
2. **SST**: If `apply_sst` is `true`, the system applies the default 8% rate. Ensure your team confirms the tax requirements before toggling this.
3. **Markup Visibility**: If your app needs to display the markup to the agent, ensure you are passing the `Authorization` header. For public client views, always use the `invoice_link` directly.
