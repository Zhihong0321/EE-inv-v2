from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.config import settings
from app.database import engine, Base
from app.api import auth, customers, templates, invoices, old_invoices, public_invoice, migration

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="EE Invoicing System",
    description="Modern invoicing system with WhatsApp authentication",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(templates.router)
app.include_router(invoices.router)
app.include_router(old_invoices.router)
app.include_router(public_invoice.router)
app.include_router(migration.router)


# Health check
@app.get("/api/v1/health")
def health_check():
    """Health check endpoint"""
    from app.database import check_database_health

    db_health = check_database_health()

    return {
        "status": "healthy" if db_health else "unhealthy",
        "version": "1.0.0",
        "database": "connected" if db_health else "disconnected",
    }


# Database connection info
@app.get("/api/v1/db-info")
def db_info():
    """Get database connection information (sanitized)"""
    from app.database import get_connection_info

    return get_connection_info()


# Root redirect to admin
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - redirect to admin UI"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EE Invoicing System</title>
        <meta http-equiv="refresh" content="0; url=/admin/">
    </head>
    <body>
        <p>Redirecting to admin dashboard...</p>
    </body>
    </html>
    """


# Admin UI (placeholder - will be implemented with HTML templates)
@app.get("/admin/", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EE Invoicing - Admin Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <nav class="bg-blue-600 text-white p-4">
            <div class="container mx-auto flex justify-between items-center">
                <h1 class="text-xl font-bold">EE Invoicing System</h1>
                <div>
                    <span id="user-info" class="mr-4"></span>
                    <button onclick="logout()" class="bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded">Logout</button>
                </div>
            </div>
        </nav>

        <div class="container mx-auto p-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-white p-6 rounded-lg shadow">
                    <h2 class="text-gray-500 text-sm">Total Invoices</h2>
                    <p id="total-invoices" class="text-3xl font-bold">-</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <h2 class="text-gray-500 text-sm">Total Customers</h2>
                    <p id="total-customers" class="text-3xl font-bold">-</p>
                </div>
                <div class="bg-white p-6 rounded-lg shadow">
                    <h2 class="text-gray-500 text-sm">Migrated Invoices</h2>
                    <p id="migrated-invoices" class="text-3xl font-bold">-</p>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white p-6 rounded-lg shadow">
                    <h2 class="text-lg font-bold mb-4">Quick Actions</h2>
                    <div class="space-y-2">
                        <a href="/admin/invoices" class="block bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">Manage Invoices</a>
                        <a href="/admin/templates" class="block bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">Manage Templates</a>
                        <a href="/admin/customers" class="block bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded">Manage Customers</a>
                        <a href="/admin/migration" class="block bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded">Data Migration</a>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-lg shadow">
                    <h2 class="text-lg font-bold mb-4">Migration Status</h2>
                    <div id="migration-status" class="space-y-2">
                        <p>Loading migration status...</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const API_BASE = '/api/v1';
            let token = localStorage.getItem('access_token');

            async function fetchData(endpoint) {
                const response = await fetch(API_BASE + endpoint, {
                    headers: token ? { 'Authorization': 'Bearer ' + token } : {}
                });
                if (response.ok) return await response.json();
                return null;
            }

            async function loadDashboard() {
                // Check auth
                if (!token) {
                    window.location.href = '/admin/login.html';
                    return;
                }

                // Load user info
                const user = await fetchData('/auth/me');
                if (user) {
                    document.getElementById('user-info').textContent = user.name || user.whatsapp_number;
                } else {
                    logout();
                    return;
                }

                // Load stats
                const invoices = await fetchData('/invoices?limit=1');
                if (invoices) document.getElementById('total-invoices').textContent = invoices.total || 0;

                const customers = await fetchData('/customers?limit=1');
                if (customers) document.getElementById('total-customers').textContent = customers.total || 0;

                const migration = await fetchData('/migration/status');
                if (migration) {
                    document.getElementById('migrated-invoices').textContent = migration.migrated_count || 0;
                    document.getElementById('migration-status').innerHTML = `
                        <p>Old Invoices: ${migration.old_invoice_count}</p>
                        <p>Migrated: ${migration.migrated_count}</p>
                        <p>Unmigrated: ${migration.unmigrated_count}</p>
                        <p>Progress: ${migration.migration_percentage}%</p>
                    `;
                }
            }

            function logout() {
                localStorage.removeItem('access_token');
                window.location.href = '/';
            }

            loadDashboard();
        </script>
    </body>
    </html>
    """


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login():
    """Login page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EE Invoicing - Login</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center">
        <div class="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
            <h1 class="text-2xl font-bold mb-6 text-center">EE Invoicing System</h1>
            <p class="text-gray-600 mb-4 text-center">Login with WhatsApp</p>

            <div id="step-1" class="space-y-4">
                <input type="tel" id="phone" placeholder="WhatsApp number (e.g., 60123456789)" 
                    class="w-full border p-3 rounded" pattern="[0-9]*">
                <button onclick="sendOTP()" class="w-full bg-blue-500 hover:bg-blue-600 text-white p-3 rounded">
                    Send OTP
                </button>
                <p id="error" class="text-red-500 text-center hidden"></p>
            </div>

            <div id="step-2" class="space-y-4 hidden">
                <p class="text-gray-600 text-center">Enter the 6-digit code sent to your WhatsApp</p>
                <input type="text" id="otp" placeholder="OTP Code" maxlength="6" 
                    class="w-full border p-3 rounded text-center text-2xl tracking-widest">
                <input type="text" id="name" placeholder="Your Name (optional)" 
                    class="w-full border p-3 rounded">
                <button onclick="verifyOTP()" class="w-full bg-green-500 hover:bg-green-600 text-white p-3 rounded">
                    Verify & Login
                </button>
                <button onclick="backToStep1()" class="w-full bg-gray-500 hover:bg-gray-600 text-white p-3 rounded">
                    Back
                </button>
            </div>
        </div>

        <script>
            const API_BASE = '/api/v1';

            async function sendOTP() {
                const phone = document.getElementById('phone').value.trim();
                if (!phone || phone.length < 10) {
                    showError('Please enter a valid phone number');
                    return;
                }

                try {
                    const response = await fetch(API_BASE + '/auth/whatsapp/send-otp', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ whatsapp_number: phone })
                    });
                    const data = await response.json();

                    if (response.ok) {
                        document.getElementById('step-1').classList.add('hidden');
                        document.getElementById('step-2').classList.remove('hidden');
                        document.getElementById('error').classList.add('hidden');
                    } else {
                        showError(data.detail || 'Failed to send OTP');
                    }
                } catch (e) {
                    showError('Failed to connect to server');
                }
            }

            async function verifyOTP() {
                const phone = document.getElementById('phone').value.trim();
                const otp = document.getElementById('otp').value.trim();
                const name = document.getElementById('name').value.trim();

                if (otp.length !== 6) {
                    showError('Please enter 6-digit OTP');
                    return;
                }

                try {
                    const response = await fetch(API_BASE + '/auth/whatsapp/verify', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ whatsapp_number: phone, otp_code: otp, name: name })
                    });
                    const data = await response.json();

                    if (response.ok && data.success) {
                        localStorage.setItem('access_token', data.token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                        window.location.href = '/admin/';
                    } else {
                        showError(data.message || 'Invalid OTP');
                    }
                } catch (e) {
                    showError('Failed to verify OTP');
                }
            }

            function backToStep1() {
                document.getElementById('step-1').classList.remove('hidden');
                document.getElementById('step-2').classList.add('hidden');
            }

            function showError(msg) {
                document.getElementById('error').textContent = msg;
                document.getElementById('error').classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
