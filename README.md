# EE Invoicing System v2

Modern invoicing system with WhatsApp authentication, template management, and API access for microservices.

## Features

- **WhatsApp Authentication** - Login using 6-digit OTP sent via WhatsApp
- **Template Management** - Create and manage invoice templates with company details
- **Customer Management** - Full CRUD for customers
- **Invoice System** - Create, update, and manage invoices
- **API Key Authentication** - For microservice integration
- **Shareable Links** - Public invoice view and edit via share links
- **Legacy Data Access** - Read-only access to old invoice system
- **Migration Service** - Manual migration of old invoices to new system

## Quick Start

### Railway Deployment (Recommended)

See `DEPLOYMENT_INSTRUCTIONS.md` for step-by-step deployment guide.

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/Zhihong0321/EE-inv-v2.git
   git push -u origin main
   ```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `Zhihong0321/EE-inv-v2` repository
   - Add PostgreSQL service
   - Configure environment variables (see DEPLOYMENT_INSTRUCTIONS.md)
   - Deploy!

3. **Access Application:**
   - Your app URL: `https://quote.atap.solar`
   - API Docs: `/docs`
   - Admin Dashboard: `/admin/`

## Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Authentication**: JWT + WhatsApp OTP
- **Frontend**: HTML + TailwindCSS (Admin UI)
- **PDF Generation**: WeasyPrint
- **Deployment**: Railway

## API Documentation

Once running, visit:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`

## Authentication Flow

### User Login (WhatsApp)

1. User enters WhatsApp number
2. System generates 6-digit OTP
3. OTP sent via WhatsApp
4. User enters OTP
5. System returns JWT token
6. Token used for subsequent API calls

### Microservice Login (API Key)

1. Admin generates API key via `/api/v1/auth/api-key/generate`
2. Microservice uses API key in `Authorization` header
3. System validates API key and grants access

## Core API Endpoints

### Authentication
- `POST /api/v1/auth/whatsapp/send-otp` - Send OTP to WhatsApp
- `POST /api/v1/auth/whatsapp/verify` - Verify OTP and get JWT
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/api-key/generate` - Generate API key
- `GET /api/v1/auth/api-keys` - List API keys
- `DELETE /api/v1/auth/api-keys/{id}` - Revoke API key

### Customers
- `POST /api/v1/customers` - Create customer
- `GET /api/v1/customers` - List customers
- `GET /api/v1/customers/{id}` - Get customer
- `PUT /api/v1/customers/{id}` - Update customer
- `DELETE /api/v1/customers/{id}` - Delete customer

### Templates
- `POST /api/v1/templates` - Create template
- `GET /api/v1/templates` - List templates
- `GET /api/v1/templates/{id}` - Get template
- `PUT /api/v1/templates/{id}` - Update template
- `DELETE /api/v1/templates/{id}` - Delete template
- `POST /api/v1/templates/{id}/set-default` - Set as default

### Invoices
- `POST /api/v1/invoices` - Create invoice
- `GET /api/v1/invoices` - List invoices
- `GET /api/v1/invoices/{id}` - Get invoice
- `PUT /api/v1/invoices/{id}` - Update invoice
- `DELETE /api/v1/invoices/{id}` - Delete invoice
- `POST /api/v1/invoices/{id}/items` - Add item
- `PUT /api/v1/invoices/{id}/items/{item_id}` - Update item
- `DELETE /api/v1/invoices/{id}/items/{item_id}` - Delete item
- `POST /api/v1/invoices/{id}/payments` - Add payment
- `POST /api/v1/invoices/{id}/share` - Generate share link
- `POST /api/v1/invoices/{id}/mark-sent` - Mark as sent
- `POST /api/v1/invoices/{id}/mark-paid` - Mark as paid

### Legacy Data (Read-Only)
- `GET /api/v1/legacy/invoices` - List old invoices
- `GET /api/v1/legacy/invoices/{id}` - Get old invoice
- `GET /api/v1/legacy/agents` - List agents
- `GET /api/v1/legacy/packages` - List packages
- `GET /api/v1/legacy/products` - List products

### Migration
- `POST /api/v1/migration/migrate-old-invoices` - Migrate old invoices
- `GET /api/v1/migration/status` - Get migration status

### Public Share Links
- `GET /invoice/view/{share_token}` - Public invoice view
- `POST /invoice/edit/{share_token}` - Request edit OTP
- `POST /invoice/edit/{share_token}/verify` - Verify edit OTP

## Project Structure

```
ee-invoicing/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings
│   ├── database.py             # DB connection
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── api/                   # API routes
│   ├── services/              # Business logic
│   ├── repositories/          # Database access
│   ├── middleware/            # Auth middleware
│   └── utils/                # Utilities
├── requirements.txt
├── Dockerfile
├── railway.json
├── .env.example
├── DEPLOYMENT_INSTRUCTIONS.md
└── README.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | (Railway auto-links) |
| JWT_SECRET_KEY | JWT signing secret | (Required) |
| JWT_ALGORITHM | JWT algorithm | HS256 |
| JWT_EXPIRE_MINUTES | JWT expiry time | 43200 (30 days) |
| WHATSAPP_API_URL | WhatsApp API base URL | (Required) |
| OTP_EXPIRE_SECONDS | OTP validity duration | 1800 (30 min) |
| OTP_LENGTH | OTP digit count | 6 |
| INVOICE_NUMBER_PREFIX | Invoice number prefix | INV |
| INVOICE_NUMBER_LENGTH | Invoice number padding | 6 |
| DEFAULT_SST_RATE | Default SST rate | 8.0 |
| SHARE_LINK_EXPIRY_DAYS | Share link expiry | 7 |
| CORS_ORIGINS | Allowed CORS origins | * |

## First-Time Setup

After deployment:

1. **Login with WhatsApp** - Visit `/admin/login` and enter your WhatsApp number
2. **Set Admin Role** - Update your user role via Railway database query
3. **Create Default Template** - Set up company details and invoice template
4. **Migrate Old Invoices** - Use migration endpoint to migrate old data

## Migration Guide

1. Check migration status: `GET /api/v1/migration/status`
2. Trigger migration: `POST /api/v1/migration/migrate-old-invoices?limit=100`
3. Repeat until all invoices are migrated

## Security

- JWT-based authentication
- API key authentication for microservices
- OTP-based login (no passwords)
- Share link expiry
- Audit logging

## License

MIT License - Free for commercial and personal use

## Support

- GitHub: [Zhihong0321/EE-inv-v2](https://github.com/Zhihong0321/EE-inv-v2)
- API Docs: Visit `/docs` on your deployed app
