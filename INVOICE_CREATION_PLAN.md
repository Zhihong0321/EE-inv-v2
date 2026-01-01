# Invoice Creation via URL Parameters - Implementation Plan

## Overview

Create a new invoice creation flow where an external microservice (ERP) generates a link with parameters, and sales agents visit this invoicing app to create new invoices.

### Business Type: Solar
- Required parameters: Panel Qty, Panel Rating, Discount Given
- Customer info: Optional (if blank = demo quotation)
- Must be linked to logged-in User

### Business Type: EV Charging
- Different link, different form
- **NOT IN SCOPE** - Skip for now

---

## Current Codebase Investigation Results

### A. Database Schema Analysis

#### Current Key Tables

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `auth_user` | `user_id`, `whatsapp_number`, `name`, `role` | WhatsApp OTP login |
| `agent` | `bubble_id`, `name`, `contact`, `email`, `address` | Legacy agent profiles |
| `user` (legacy) | `linked_agent_profile`, `agent_code` | Links to agent |
| `invoice_new` | `bubble_id`, `created_by`, `customer_id` | Invoice records |
| `package` | `bubble_id`, `panel_qty`, `panel`, `price`, `type` | Solar packages |

#### Auth/User Findings
- ✅ `auth_user` table has `whatsapp_number` field for mobile-based authentication
- ✅ `agent` table has `contact` field for phone/mobile
- ✅ `user` (legacy) has `linked_agent_profile` linking to agent
- Current auth: WhatsApp OTP → JWT token

#### Sample Data from Test Database

**Packages (Solar):**
```
ID: 1703833647950x572894707690242050 | Name: STRING SAJ JINKO 8 PCS | Type: Residential | Price: 18276
ID: 1703833688009x793606512485335000 | Name: STRING SAJ JINKO 9 PCS | Type: Residential | Price: 19282
ID: 1703833788622x969335742275256300 | Name: STRING SAJ JINKO 10 PCS | Type: Residential | Price: 20289
```

**Agents:**
```
ID: 1694840888929x299556294496878600 | Name: GAN ZHI HONG | Contact: 01121000099
ID: 1694841837042x277767932428681200 | Name: GAN LAI SOON | Contact: 0127299201
```

### B. Existing Authentication Flow

1. **Send OTP:** `POST /api/v1/auth/whatsapp/send-otp`
   - Input: `whatsapp_number`
   - Creates user if not exists
   - Sends 6-digit OTP via WhatsApp

2. **Verify OTP:** `POST /api/v1/auth/whatsapp/verify`
   - Input: `whatsapp_number`, `otp_code`, `name` (optional)
   - Returns JWT token

3. **Get Current User:** `GET /api/v1/auth/me`
   - Requires Bearer token
   - Returns user info

### C. Existing Invoice Creation

**POST /api/v1/invoices/on-the-fly** - Quick invoice creation from packages
- Supports: Package selection, discounts, SST toggle, template selection, voucher application, agent markup
- Auto-creates customer profile or marks as "Sample Quotation"
- Snapshots customer and agent data for historical accuracy
- Returns shareable URL

---

## Preparation List

### Required Schema Updates
**NONE** - Existing schema supports all requirements:
- `invoice_new.created_by` links to `auth_user.user_id` ✅
- `package.panel_qty` stores panel quantity ✅
- `package.panel` stores panel rating/info ✅
- `invoice_new.customer_name_snapshot` can store "Sample Quotation" ✅

### Code References for This Task

| File | Purpose | Key Functions |
|------|---------|--------------|
| `app/main.py` | Add new route | Add `/create-invoice` GET/POST route |
| `app/api/invoices.py` | Invoice creation | `create_invoice_on_the_fly()` reference |
| `app/repositories/invoice_repo.py` | Invoice logic | `create_on_the_fly()` method |
| `app/middleware/auth.py` | User auth | `get_current_user()` or `get_optional_user()` |
| `app/schemas/invoice.py` | Validation schemas | Add new schema for URL-based creation |

### Environment Variables Required
Current `.env` already has:
```
JWT_SECRET_KEY
DEFAULT_SST_RATE=8.0
SHARE_LINK_EXPIRY_DAYS=7
```
**No new environment variables needed.**

### Test Database Connection
```
postgresql://postgres:OOQTkeMhuPRXJpCWuncoPgzUJNvJzdPC@crossover.proxy.rlwy.net:42492/railway
```
**⚠️ IMPORTANT:** This is for LOCAL DEV ONLY - must not be pushed to production!

---

## Mobile-First Design Principles ⚡ PRIORITY

**Design Goal:** The invoice creation page MUST be optimized for mobile users first, as sales agents will primarily use smartphones to create invoices.

### Key Mobile UX Requirements

| Requirement | Implementation |
|-------------|----------------|
| **Touch-Friendly Inputs** | Large tap targets (min 44x44px), proper spacing |
| **Single Column Layout** | Stack all form fields vertically on mobile |
| **Sticky Action Button** | "Create Invoice" button always visible at bottom |
| **Minimal Scrolling** | Group related info, minimize unnecessary fields |
| **Fast Loading** | Lightweight, no heavy assets |
| **Progressive Disclosure** | Show essential info first, optional fields expandable |
| **Thumb-Zone Optimization** | Primary actions in bottom thumb zone |
| **Auto-Focus** | Automatically focus first editable field |
| **Numeric Keypad** | Use `type="tel"` for phone, `type="number"` for qty |
| **Pre-Filled Smart Defaults** | Most fields auto-filled from URL params |

### Mobile Breakpoints

```
Mobile (Portrait):  < 640px   - Single column, stacked
Mobile (Landscape): 640px - 768px - Compact cards
Tablet:             768px - 1024px - 2 columns
Desktop:            > 1024px  - Max-width container
```

---

## Master Build Plan

### PHASE 1: API Endpoint for Invoice Creation from URL Parameters

**Goal:** Create a GET endpoint that accepts URL parameters and returns an HTML page for invoice creation.

#### Step 1.1: Create Pydantic Schema for URL Parameters
**File:** `app/schemas/invoice.py`

```python
class InvoiceFromURLRequest(BaseModel):
    """Schema for invoice creation from URL parameters (Solar Business)"""
    # Required Solar Business parameters
    package_id: str
    panel_qty: Optional[int] = None
    panel_rating: Optional[str] = None  # e.g., "450W"
    discount_given: Optional[Decimal] = None  # Discount amount or percent

    # Optional customer info
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None

    # Other options
    template_id: Optional[str] = None
```

#### Step 1.2: Create GET Route in Main App
**File:** `app/main.py`

```python
@app.get("/create-invoice", response_class=HTMLResponse)
async def create_invoice_page(
    request: Request,
    package_id: str = Query(..., description="Package ID from package table"),
    panel_qty: Optional[int] = Query(None, description="Panel quantity"),
    panel_rating: Optional[str] = Query(None, description="Panel rating"),
    discount_given: Optional[str] = Query(None, description="Discount amount or percent"),
    customer_name: Optional[str] = Query(None, description="Customer name (optional)"),
    customer_phone: Optional[str] = Query(None, description="Customer phone (optional)"),
    customer_address: Optional[str] = Query(None, description="Customer address (optional)"),
    template_id: Optional[str] = Query(None, description="Template ID (optional)"),
    current_user: Optional[AuthUser] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Invoice creation page accessible via URL with parameters.

    Sample URL: https://yourdomain.com/create-invoice?package_id=1703833647950x572894707690242050&panel_qty=8&panel_rating=450W&discount_given=500

    Workflow:
    1. Validate package_id exists
    2. If user not logged in, redirect to login with return URL
    3. Return HTML form with pre-filled data from URL parameters
    4. Allow sales agent to edit customer info (optional)
    5. Submit creates invoice linked to logged-in user
    """
    # Fetch package data
    package = db.query(Package).filter(Package.bubble_id == package_id).first()
    if not package:
        return HTMLResponse(content="<h1>Package not found</h1>", status_code=404)

    # Check authentication
    if not current_user:
        return RedirectResponse(
            url=f"/admin/login?return_url={request.url}",
            status_code=302
        )

    # Return HTML template with pre-filled data
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")

    return templates.TemplateResponse(
        "create_invoice.html",
        {
            "request": request,
            "user": current_user,
            "package": package,
            "panel_qty": panel_qty,
            "panel_rating": panel_rating,
            "discount_given": discount_given,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "customer_address": customer_address,
            "template_id": template_id
        }
    )
```

#### Step 1.3: Create HTML Template for Invoice Creation Page (MOBILE-FIRST)
**File:** `app/templates/create_invoice.html` (new file)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <title>Create Invoice - EE Invoicing</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        * { -webkit-tap-highlight-color: transparent; }
        body {
            font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, sans-serif;
            -webkit-font-smoothing: antialiased;
            padding-bottom: 80px; /* Space for sticky button */
        }
        input, textarea {
            font-size: 16px; /* Prevents iOS zoom */
        }
        .input-field {
            min-height: 48px; /* Touch-friendly tap target */
        }
        .btn-primary {
            min-height: 48px;
            transition: transform 0.1s ease;
        }
        .btn-primary:active {
            transform: scale(0.98);
        }
        /* Hide scrollbar but allow scroll */
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Mobile Navigation (Compact) -->
    <nav class="bg-blue-600 text-white px-4 py-3 sticky top-0 z-50 shadow-md">
        <div class="flex justify-between items-center max-w-4xl mx-auto">
            <div class="flex items-center">
                <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
                <h1 class="text-lg font-semibold truncate">Create Invoice</h1>
            </div>
            <button onclick="logout()" class="text-sm bg-blue-700 hover:bg-blue-800 px-3 py-2 rounded-lg">
                Logout
            </button>
        </div>
    </nav>

    <!-- User Info Banner -->
    <div class="bg-blue-50 border-b border-blue-100 px-4 py-2">
        <div class="max-w-4xl mx-auto flex items-center justify-between">
            <div class="flex items-center text-sm text-blue-800">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                </svg>
                <span class="truncate">{{ user.name or user.whatsapp_number }}</span>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-4 py-6 space-y-4">
        <!-- Package Card -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div class="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-3">
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                    </svg>
                    <h2 class="font-semibold">Package Information</h2>
                </div>
            </div>
            <div class="p-4 space-y-3">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Package Name</label>
                        <input type="text" id="package_name" value="{{ package.name }}"
                            class="input-field w-full border border-gray-300 rounded-lg px-3 py-2 bg-gray-50 text-gray-700" readonly>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Package Price</label>
                        <input type="text" id="package_price" value="RM {{ package.price }}"
                            class="input-field w-full border border-gray-300 rounded-lg px-3 py-2 bg-gray-50 text-gray-700" readonly>
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Panel Quantity</label>
                        <input type="number" id="panel_qty" name="panel_qty"
                            value="{{ panel_qty or package.panel_qty or '' }}"
                            class="input-field w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="Enter quantity">
                    </div>
                    <div>
                        <label class="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Panel Rating</label>
                        <input type="text" id="panel_rating" name="panel_rating"
                            value="{{ panel_rating or package.panel or '' }}"
                            class="input-field w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            placeholder="e.g., 450W">
                    </div>
                </div>
            </div>
        </div>

        <!-- Customer Info Card (Collapsible on Mobile) -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <button onclick="toggleSection('customer-section')" class="w-full bg-gradient-to-r from-purple-500 to-purple-600 text-white px-4 py-3 flex items-center justify-between">
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                    <h2 class="font-semibold">Customer Information <span class="text-purple-200 text-sm">(Optional)</span></h2>
                </div>
                <svg id="customer-chevron" class="w-5 h-5 transform rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                </svg>
            </button>
            <div id="customer-section" class="p-4 space-y-3">
                <p class="text-sm text-gray-500 flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    Leave blank to create a "Sample Quotation"
                </p>
                <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Customer Name</label>
                    <input type="text" id="customer_name" name="customer_name"
                        value="{{ customer_name or '' }}"
                        class="input-field w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                        placeholder="Leave blank for sample quotation">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Phone Number</label>
                    <input type="tel" id="customer_phone" name="customer_phone"
                        value="{{ customer_phone or '' }}"
                        class="input-field w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                        placeholder="e.g., 0123456789">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Address</label>
                    <textarea id="customer_address" name="customer_address" rows="2"
                        class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none"
                        placeholder="Customer address (optional)">{{ customer_address or '' }}</textarea>
                </div>
            </div>
        </div>

        <!-- Discount Card -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div class="bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-3">
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <h2 class="font-semibold">Discount</h2>
                </div>
            </div>
            <div class="p-4">
                <div>
                    <label class="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">Discount Amount / Percentage</label>
                    <div class="flex gap-2">
                        <input type="text" id="discount_given" name="discount_given"
                            value="{{ discount_given or '' }}"
                            class="input-field flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-green-500"
                            placeholder="e.g., 500 or 10%">
                    </div>
                    <p class="text-xs text-gray-500 mt-1">Enter amount (RM) or percentage (%)</p>
                </div>
            </div>
        </div>

        <!-- Quick Summary (Mobile Only) -->
        <div class="bg-blue-50 rounded-lg p-4 border border-blue-200 md:hidden">
            <div class="flex items-center text-sm text-blue-800">
                <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <span>Review details above before creating invoice</span>
            </div>
        </div>

        <!-- Extra padding for sticky button -->
        <div class="h-8"></div>
    </main>

    <!-- Sticky Action Bar (Bottom) -->
    <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg px-4 py-3 z-50">
        <div class="max-w-4xl mx-auto flex gap-3">
            <a href="/admin/"
                class="flex-1 btn-primary border border-gray-300 text-gray-700 rounded-lg px-4 py-3 font-medium text-center">
                Cancel
            </a>
            <button onclick="createInvoice()" id="submit-btn"
                class="flex-2 btn-primary bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-lg px-6 py-3 font-medium flex items-center justify-center">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Create Invoice
            </button>
        </div>
    </div>

    <!-- Loading Overlay -->
    <div id="loading" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden">
        <div class="bg-white rounded-xl p-6 mx-4 flex flex-col items-center">
            <svg class="animate-spin h-8 w-8 text-blue-600 mb-3" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="text-gray-700 font-medium">Creating invoice...</p>
        </div>
    </div>

    <script>
        const API_BASE = '/api/v1';
        const PACKAGE_ID = '{{ package.bubble_id }}';
        const TEMPLATE_ID = '{{ template_id or '' }}';
        let token = localStorage.getItem('access_token');

        // Toggle collapsible sections
        function toggleSection(sectionId) {
            const section = document.getElementById(sectionId);
            const chevron = document.getElementById(sectionId.replace('-section', '-chevron'));
            if (section.classList.contains('hidden')) {
                section.classList.remove('hidden');
                chevron.classList.add('rotate-180');
            } else {
                section.classList.add('hidden');
                chevron.classList.remove('rotate-180');
            }
        }

        // Auto-focus first editable field on load
        document.addEventListener('DOMContentLoaded', function() {
            const firstInput = document.querySelector('#panel_qty');
            if (firstInput && !firstInput.value) {
                firstInput.focus();
            }
        });

        async function createInvoice() {
            const submitBtn = document.getElementById('submit-btn');
            const loading = document.getElementById('loading');

            const customerName = document.getElementById('customer_name').value.trim();
            const customerPhone = document.getElementById('customer_phone').value.trim();
            const customerAddress = document.getElementById('customer_address').value.trim();
            const panelQty = document.getElementById('panel_qty').value;
            const panelRating = document.getElementById('panel_rating').value;
            const discountGiven = document.getElementById('discount_given').value.trim();

            // Validate panel quantity
            if (!panelQty) {
                alert('Please enter panel quantity');
                document.getElementById('panel_qty').focus();
                return;
            }

            // Parse discount
            let discountFixed = 0;
            let discountPercent = 0;

            if (discountGiven) {
                if (discountGiven.includes('%')) {
                    discountPercent = parseFloat(discountGiven.replace('%', ''));
                } else {
                    discountFixed = parseFloat(discountGiven);
                }
            }

            const payload = {
                package_id: PACKAGE_ID,
                discount_fixed: discountFixed,
                discount_percent: discountPercent,
                apply_sst: true,
                template_id: TEMPLATE_ID || null,
                customer_name: customerName || null,
                customer_phone: customerPhone || null,
                customer_address: customerAddress || null
            };

            // Show loading
            loading.classList.remove('hidden');
            submitBtn.disabled = true;

            try {
                const response = await fetch(API_BASE + '/invoices/on-the-fly', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    // Redirect to preview
                    window.location.href = data.invoice_link;
                } else {
                    alert('Error: ' + (data.detail || data.message || 'Failed to create invoice'));
                    loading.classList.add('hidden');
                    submitBtn.disabled = false;
                }
            } catch (e) {
                alert('Network Error: ' + e.message);
                loading.classList.add('hidden');
                submitBtn.disabled = false;
            }
        }

        function logout() {
            localStorage.removeItem('access_token');
            window.location.href = '/admin/login';
        }
    </script>
</body>
</html>
```

#### Step 1.4: Update Login Page to Handle Return URL
**File:** `app/main.py` - Modify `/admin/login` route

Add support for `return_url` query parameter to redirect back after login.

---

### PHASE 2: Authentication Integration

#### Step 2.1: Redirect Unauthenticated Users
- If user not logged in → redirect to `/admin/login?return_url={current_url}`
- Store intended URL in session/localStorage for redirect after login

#### Step 2.2: Link Invoice to User
- Use `invoice_repo.create_on_the_fly(created_by=current_user.user_id)`
- This ensures invoice is linked to logged-in user

#### Step 2.3: Handle "Sample Quotation"
- If `customer_name` is blank/None → set `customer_name_snapshot = "Sample Quotation"`
- Create without `customer_id` (no customer record created)

---

### PHASE 3: Preview Link Generation

#### Step 3.1: Auto-Generate Share Link
- After invoice creation, generate share token (already exists in `create_on_the_fly`)
- Return URL: `/view/{share_token}` (already exists in `public_invoice.py`)

#### Step 3.2: Display Preview Link
- Show link in success page
- Copy to clipboard button
- "Open Preview" button

---

### PHASE 4: Testing (Using Test Postgres DB)

#### Step 4.1: Test Scenarios

**Desktop Tests:**
1. **Happy Path:** Logged-in user creates invoice with all parameters
   - URL: `/create-invoice?package_id=xxx&panel_qty=8&panel_rating=450W&discount_given=500`
   - Expected: Invoice created with preview link

2. **Sample Quotation:** Logged-in user with blank customer info
   - URL: `/create-invoice?package_id=xxx&panel_qty=8&panel_rating=450W`
   - Expected: Invoice with "Sample Quotation" as customer name

3. **With Customer Info:**
   - URL: `/create-invoice?package_id=xxx&panel_qty=8&customer_name=John%20Doe&customer_phone=0123456789`
   - Expected: Invoice created with customer profile

4. **Invalid Package ID:** Show error message
   - URL: `/create-invoice?package_id=invalid_id`
   - Expected: "Package not found" error page

5. **Unauthenticated:** Redirect to login, then redirect back to creation page
   - URL: `/create-invoice?package_id=xxx` (without login)
   - Expected: Redirect to `/admin/login?return_url=...`

**Mobile Tests (⚡ CRITICAL):**

| Test | Device | Expected Behavior |
|------|--------|-------------------|
| **iPhone SE (375x667)** | Small mobile | All cards stack vertically, sticky button at bottom |
| **iPhone 12 (390x844)** | Medium mobile | Proper spacing, 16px font on inputs (no zoom) |
| **Android (414x896)** | Large mobile | Touch targets 48px minimum |
| **Tablet Portrait (768px)** | iPad mini | 2-column grid for package info |
| **Landscape Mode (844x390)** | Mobile rotated | Compact cards, navigation still visible |

**Mobile-Specific Tests:**

1. **Touch Input Test**
   - Verify all input fields have min-height 48px
   - Verify buttons have proper touch feedback
   - Test with both iOS Safari and Chrome Android

2. **Sticky Button Test**
   - Scroll page, verify "Create Invoice" button stays at bottom
   - Verify button is always in thumb zone (bottom 1/3 of screen)

3. **Collapsible Customer Section**
   - Tap customer info header → should expand/collapse
   - Verify chevron animation works smoothly

4. **Auto-Focus Test**
   - Load page → should auto-focus "Panel Quantity" field
   - On mobile, keyboard should appear automatically

5. **Numeric Keypad Test**
   - Tap "Panel Quantity" → should show numeric keypad
   - Tap "Phone Number" → should show phone keypad

6. **Loading Overlay Test**
   - Click "Create Invoice" → show loading overlay
   - Verify overlay blocks all interactions

7. **iOS Zoom Prevention Test**
   - Input font-size must be 16px to prevent auto-zoom
   - Verify no zoom occurs when tapping inputs

8. **Safe Area Test (iPhone X+)**
   - Verify content doesn't overlap with notch/home indicator
   - Verify sticky button respects safe area insets

#### Step 4.2: Verify Invoice Linked to User

```sql
SELECT
    i.invoice_number,
    i.customer_name_snapshot,
    i.total_amount,
    u.whatsapp_number,
    u.name as agent_name,
    i.created_at
FROM invoice_new i
JOIN auth_user u ON i.created_by = u.user_id
ORDER BY i.created_at DESC
LIMIT 10;
```

---

### PHASE 5: Deployment Preparation

#### Step 5.1: Environment Protection
- Ensure test DB URL is NOT in `railway.json` or `.env` for production
- Use Railway environment variables in production
- Test database connection string should only be in local development

#### Step 5.2: Testing Commands

**Local Development:**
```bash
# Start local server with test DB
DATABASE_URL="postgresql://postgres:OOQTkeMhuPRXJpCWuncoPgzUJNvJzdPC@crossover.proxy.rlwy.net:42492/railway" python -m uvicorn app.main:app --reload

# Test URLs in browser:
http://localhost:8000/create-invoice?package_id=1703833647950x572894707690242050&panel_qty=8&panel_rating=450W&discount_given=500

# With customer info:
http://localhost:8000/create-invoice?package_id=1703833647950x572894707690242050&panel_qty=8&customer_name=John%20Doe&customer_phone=0123456789
```

---

## Sample URL Formats

### Solar Business Invoice Creation (Basic)
```
https://your-domain.com/create-invoice?package_id=1703833647950x572894707690242050&panel_qty=8&panel_rating=450W&discount_given=500
```

### With Customer Info (Optional)
```
https://your-domain.com/create-invoice?package_id=1703833647950x572894707690242050&panel_qty=8&panel_rating=450W&discount_given=500&customer_name=John%20Doe&customer_phone=0123456789&customer_address=123%20Main%20Street
```

### With Template Override
```
https://your-domain.com/create-invoice?package_id=1703833647950x572894707690242050&panel_qty=8&discount_given=10%25&template_id=template_bubble_id
```

### Sample Quotation (No Customer Info)
```
https://your-domain.com/create-invoice?package_id=1703833647950x572894707690242050&panel_qty=10
```

---

## Acceptance Criteria Checklist

### Functional Criteria

| Criteria | Status | Implementation Notes |
|----------|--------|---------------------|
| URL path takes required parameters (Panel Qty, Panel Rating, Discount) | ⏳ TO IMPLEMENT | Via `/create-invoice` GET route with Query parameters |
| URL leads to invoice creation page | ⏳ TO IMPLEMENT | HTML form with pre-filled data from URL |
| Sales agent can input optional customer info | ⏳ TO IMPLEMENT | Form fields for name, phone, address |
| Blank customer = demo quotation | ⏳ TO IMPLEMENT | Set `customer_name_snapshot = "Sample Quotation"` |
| Generate preview link | ⏳ TO IMPLEMENT | Share token already exists in `create_on_the_fly()` |
| Invoice linked to logged-in User | ⏳ TO IMPLEMENT | Use `created_by` field with `get_current_user()` |
| Auth uses WhatsApp OTP | ✅ EXISTS | `/api/v1/auth/whatsapp/send-otp` and `/verify` |
| User table has mobile/whatsapp_number | ✅ EXISTS | `auth_user.whatsapp_number` field |
| Test with Postgres DB | ⏳ TO IMPLEMENT | Use test DB connection for local testing |

### Mobile-First Criteria (⚡ TOP PRIORITY)

| Criteria | Implementation |
|----------|----------------|
| **Touch-Friendly Inputs** | Minimum 48px height, proper spacing for thumb interaction |
| **Sticky Action Button** | "Create Invoice" always visible at bottom, in thumb zone |
| **Single Column Layout** | All fields stack vertically on mobile (< 640px) |
| **iOS Zoom Prevention** | Input font-size 16px, viewport settings disable zoom |
| **Auto-Focus First Field** | "Panel Quantity" auto-focused on page load |
| **Numeric Keypad** | `type="number"` for qty, `type="tel"` for phone |
| **Loading Overlay** | Full-screen overlay with spinner during submission |
| **Progressive Disclosure** | Customer info collapsible to save vertical space |
| **Visual Hierarchy** | Color-coded cards, gradient headers for easy scanning |
| **Fast Loading** | Lightweight, no heavy assets, CDN for Tailwind |
| **Responsive Breakpoints** | Mobile (<640px), Tablet (768px-1024px), Desktop (>1024px) |
| **Safe Area Support** | Respect iPhone notch/home indicator spacing |
| **No Horizontal Scroll** | Content fits viewport width at all sizes |
| **Button Press Feedback** | Visual feedback (scale) on button tap |

---

## Technical Architecture

```
┌─────────────────┐
│  ERP System     │
│  (External)     │
└────────┬────────┘
         │ 1. Generate URL with parameters
         │    ?package_id=xxx&panel_qty=8&...
         ▼
┌───────────────────────────────────────┐
│  GET /create-invoice?package_id=...   │
│  ┌─────────────────────────────────┐  │
│  │ Check Authentication            │  │
│  └────────┬────────────────────────┘  │
└───────────┼───────────────────────────┘
            │
            ├─ Not Logged In ──────────▶ POST /admin/login (WhatsApp OTP)
            │                                   │
            │                                   ▼
            │                          ┌─────────────────┐
            │                          │  Verify OTP    │
            │                          │  Get JWT Token │
            │                          └────────┬────────┘
            │                                   │
            └───────────────────────────────────┤
                                                ▼
                                    ┌───────────────────────┐
                                    │  Render HTML Form      │
                                    │  (Pre-filled with URL  │
                                    │   parameters)          │
                                    └───────────┬───────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │  Sales Agent Edits   │
                                    │  Customer Info (opt)  │
                                    └───────────┬───────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │  POST /api/v1/       │
                                    │  invoices/on-the-fly  │
                                    └───────────┬───────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │  Invoice Created     │
                                    │  - Linked to User    │
                                    │  - Share Token Gen   │
                                    └───────────┬───────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │  Redirect to         │
                                    │  /view/{share_token} │
                                    │  (Preview Invoice)   │
                                    └───────────────────────┘
```

---

## Database Schema Confirmation

### auth_user (Authentication)
```
user_id (String, PK)
whatsapp_number (String, Unique)
whatsapp_formatted (String)
name (String)
role (String)
active (Boolean)
app_permissions (Array)
created_at (DateTime)
last_login_at (DateTime)
```

### package (Solar Packages)
```
id (Integer, PK)
bubble_id (String, Unique)
package_name (String)
price (Numeric)
panel_qty (Integer)
panel (String)  // Panel rating
type (String)   // Business type (Residential, etc.)
active (Boolean)
```

### invoice_new (Invoices)
```
id (Integer, PK)
bubble_id (String, Unique)
customer_id (Integer, FK)
customer_name_snapshot (String)
customer_phone_snapshot (String)
customer_address_snapshot (String)
package_id (String)
package_name_snapshot (String)
subtotal (Numeric)
discount_amount (Numeric)
discount_fixed (Numeric)
discount_percent (Numeric)
total_amount (Numeric)
status (String)
created_by (String, FK to auth_user.user_id)  <-- LINKED TO USER
share_token (String)
share_enabled (Boolean)
created_at (DateTime)
```

---

## Security Considerations

1. **Authentication Required:** Invoice creation MUST require logged-in user
2. **Package Validation:** Verify package_id exists before rendering form
3. **Rate Limiting:** Consider rate limiting for invoice creation
4. **CORS:** Ensure proper CORS configuration for cross-origin requests
5. **Input Validation:** Sanitize all user inputs
6. **Share Link Expiry:** Share links have 7-day expiry (configurable)

---

## Future Enhancements (Out of Scope)

- EV Charging business type (different form/parameters)
- Bulk invoice creation
- Invoice template selection in URL
- Custom discount calculation rules per package type
- Integration with WhatsApp for sending invoice directly to customer

---

## Deployment Notes

### Production Environment Variables
```
DATABASE_URL=<Railway Postgres URL>
JWT_SECRET_KEY=<Strong secret key>
WHATSAPP_API_URL=<WhatsApp API URL>
```

### Test Environment (Local Only)
```
DATABASE_URL=postgresql://postgres:OOQTkeMhuPRXJpCWuncoPgzUJNvJzdPC@crossover.proxy.rlwy.net:42492/railway
```

**⚠️ WARNING:** Never commit test database credentials to repository!

---

## Summary

This plan provides a complete roadmap for implementing URL-based invoice creation for the Solar business line. The existing infrastructure (WhatsApp OTP auth, invoice creation, shareable links) will be leveraged to minimize development effort.

**Key Features:**
- ✅ URL parameters for package, panel qty, panel rating, discount
- ✅ Optional customer info (blank = sample quotation)
- ✅ Invoice linked to logged-in user via `created_by`
- ✅ Preview link generation using existing share token system
- ✅ WhatsApp OTP authentication flow
- ✅ Mobile-friendly responsive design

**Estimated Implementation Time:** 4-6 hours
