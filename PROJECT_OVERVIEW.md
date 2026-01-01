# Project Overview: EE Invoicing System v2

## Introduction
The EE Invoicing System v2 is a modern backend application built with FastAPI to manage invoices, customers, and templates. It features a unique authentication flow using WhatsApp OTP and is designed to integrate with a legacy system (referred to as the "old system" or "Bubble system").

## Tech Stack
- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migration**: Alembic
- **Authentication**: JWT (JSON Web Tokens) + WhatsApp OTP
- **PDF Generation**: WeasyPrint
- **Deployment**: Optimized for Railway (with resilient DB connection logic)

## Core Components

### 1. Authentication (`app/api/auth.py`, `app/services/whatsapp_service.py`)
- **WhatsApp Login**: Users log in by providing their WhatsApp number.
- **OTP Verification**: A 6-digit OTP is sent via an external WhatsApp API.
- **JWT**: Upon verification, a JWT token is issued for subsequent requests.
- **API Keys**: Supports API key generation for microservice-to-microservice authentication.

### 2. Database & Models (`app/models/`, `app/database.py`)
- **Resilient Connections**: `app/railway_db.py` handles connection retries and internal networking for Railway.
- **Invoice (`InvoiceNew`)**: Stores invoice details, snapshots of customer/agent/package info, and links to the legacy system.
- **Customer (`Customer`)**: Manages customer profiles.
- **Template (`InvoiceTemplate`)**: Custom invoice templates with company details and SST settings.
- **Package & Agent**: Referenced from the old system.

### 3. Invoicing Logic (`app/api/invoices.py`, `app/repositories/invoice_repo.py`)
- **Auto-numbering**: Invoices follow a configurable prefix (e.g., `INV-000001`).
- **On-the-Fly Creation**: New endpoint `POST /api/v1/invoices/on-the-fly` allows rapid invoice generation from packages with support for:
  - **Package Selection**: Uses `package_id` from the legacy system.
  - **Discounts**: Supports both fixed amount and percentage discounts.
  - **SST Toggle**: Can be explicitly turned on/off (defaults to 8% if on).
  - **Template Selection**: Allows choosing a specific company template for branding.
  - **Voucher Application**: Validates and applies vouchers (percent or fixed) from the legacy system.
  - **Hidden Agent Markup**: Adds an invisible markup to package items, visible only to authenticated users (JWT or API Key).
  - **Customer Profile**: Automatically creates a new customer profile or uses existing one. If no name is provided, marks invoice as "Sample Quotation".
- **Snapshots**: When an invoice is created, it takes a "snapshot" of customer and agent data to ensure historical accuracy even if profiles change.
- **SST Calculation**: Automatic calculation based on template settings (defaulting to 8%).
- **Shareable Links**: Invoices can be shared via unique tokens with expiration dates. The public view `/view/{token}` renders a professional HTML invoice based on the selected template.

### 4. Integration with Legacy System
- The system maintains references to an "old system" via `bubble_id` and `linked_old_invoice`.
- It includes migration tools (`app/api/migration.py`) to transition data from the legacy database.
- Packages and Vouchers are fetched directly from the legacy tables when creating invoices on the fly.

## Directory Structure
- `app/api/`: API route definitions (FastAPI routers).
- `app/models/`: SQLAlchemy database models.
- `app/schemas/`: Pydantic models for request/response validation.
- `app/repositories/`: Data access layer (encapsulates DB queries).
- `app/services/`: External integrations (e.g., WhatsApp).
- `app/utils/`: Helper functions for security, HTML generation, and formatting.
- `app/middleware/`: Authentication and logging middleware.

## Getting Started
- API Documentation is available at `/docs` (Swagger UI) or `/redoc` (ReDoc).
- Environment variables are managed in `app/config.py` and `.env`.
