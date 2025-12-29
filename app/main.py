from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from app.config import settings
from app.api import auth, customers, templates, invoices, old_invoices, public_invoice, migration
from contextlib import asynccontextmanager
import os
import sys
import asyncio
import logging

# Lazy imports for DB to prevent import-time crashes
def get_db_resources():
    from app.database import engine, Base, connect_with_retry, SessionLocal
    return engine, Base, connect_with_retry, SessionLocal

# Configure logging
logger = logging.getLogger(__name__)

async def initialize_db():
    """Background task to initialize DB without blocking app startup"""
    if os.getenv("SKIP_DB_INIT"):
        logger.info("Skipping database initialization (SKIP_DB_INIT set)")
        return

    engine, Base, connect_with_retry, _ = get_db_resources()

    # Deep Root Cause: We must wait for the database to be reachable before trying create_all
    logger.info("Database warming up... waiting for internal network.")
    if await asyncio.to_thread(connect_with_retry, max_retries=15, delay=3):
        try:
            logger.info("Internal network ready. Syncing models...")
            # Import models to ensure they are registered with Base
            from app.models.auth import AuthUser
            from app.models.customer import Customer
            from app.models.invoice import InvoiceNew
            from app.models.template import InvoiceTemplate
            
            await asyncio.to_thread(Base.metadata.create_all, bind=engine)
            logger.info("Database schema is up to date.")
        except Exception as e:
            logger.error(f"SCHEMA ERROR: {e}")
    else:
        logger.error("Could not initialize database: Connection failed after retries.")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Handles database initialization gracefully.
    """
    import time
    app.state.start_time = time.time()
    
    # Start DB initialization in background
    asyncio.create_task(initialize_db())
    
    yield

# Create FastAPI app
app = FastAPI(
    title="EE Invoicing System",
    description="Modern invoicing system with WhatsApp authentication",
    version="1.0.0",
    lifespan=lifespan
)

# Global Exception Handler to prevent raw text "Internal Server Error"
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"GLOBAL ERROR: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__, "status": "error"}
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
def health_check(response: Response):
    """Health check endpoint"""
    from app.railway_db import check_database_health

    db_health = check_database_health()
    
    # If we are in Railway and DB is not ready, we still return 200 during the first 2 minutes
    # to allow the internal network to stabilize without Railway killing the container.
    # After that, we return 503 if the DB is still down.
    import time
    app_start_time = getattr(app.state, "start_time", time.time())
    uptime = time.time() - app_start_time
    
    if not db_health and uptime > 120:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if (db_health or uptime <= 120) else "unhealthy",
        "version": "1.0.0",
        "database": "connected" if db_health else "disconnected",
        "uptime": int(uptime)
    }


# Sniper-level debug endpoint
@app.get("/api/v1/debug")
async def sniper_debug(request: Request):
    """Comprehensive debug endpoint to investigate Railway deployment issues"""
    from app.railway_db import check_database_health, get_connection_info
    from app.services.whatsapp_service import whatsapp_service
    import socket

    db_health = check_database_health()
    db_info = get_connection_info()
    wa_status = await whatsapp_service.check_status()
    
    # Check DNS resolution for railway.internal
    internal_dns = "unknown"
    try:
        internal_dns = socket.gethostbyname("postgres.railway.internal")
    except Exception as e:
        internal_dns = f"failed: {str(e)}"

    return {
        "app_status": "online",
        "python": sys.version,
        "environment": {
            "PORT": os.getenv("PORT"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
            "RAILWAY_STATIC_URL": os.getenv("RAILWAY_STATIC_URL"),
            "HAS_DATABASE_URL": bool(os.getenv("DATABASE_URL")),
            "DATABASE_URL_PREVIEW": os.getenv("DATABASE_URL")[:15] + "..." if os.getenv("DATABASE_URL") else None,
            "HOSTNAME": socket.gethostname(),
            "INTERNAL_DNS_CHECK": internal_dns
        },
        "database": {
            "connected": db_health,
            "info": db_info
        },
        "whatsapp_service": wa_status,
        "headers": dict(request.headers)
    }


# Admin creation endpoint (Security: should be disabled or protected after first use)
@app.get("/api/v1/setup-admin/{whatsapp_number}")
def setup_admin(whatsapp_number: str):
    """Seed the first admin user via WhatsApp number"""
    from app.railway_db import get_session_local, get_engine, Base
    from app.models.auth import AuthUser
    import uuid

    # Use lazy session
    Session = get_session_local()
    db = Session()
    try:
        # Ensure tables exist for this specific request
        Base.metadata.create_all(bind=get_engine())
        
        user = db.query(AuthUser).filter(AuthUser.whatsapp_number == whatsapp_number).first()
        if user:
            user.role = "admin"
            user.active = True
            db.commit()
            return {"message": f"User {whatsapp_number} updated to admin"}

        # Create new admin user
        new_admin = AuthUser(
            user_id=str(uuid.uuid4()),
            whatsapp_number=whatsapp_number,
            whatsapp_formatted=f"+{whatsapp_number}",
            name="Super Admin",
            role="admin",
            active=True,
            app_permissions=["*"]
        )
        db.add(new_admin)
        db.commit()
        return {"message": f"Super Admin {whatsapp_number} created successfully"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


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
                    window.location.href = '/admin/login';
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
                    
                    const text = await response.text();
                    let data;
                    try {
                        data = JSON.parse(text);
                    } catch (e) {
                        showError('Server Error: ' + text.substring(0, 100));
                        return;
                    }

                    if (response.ok) {
                        document.getElementById('step-1').classList.add('hidden');
                        document.getElementById('step-2').classList.remove('hidden');
                        document.getElementById('error').classList.add('hidden');
                    } else {
                        showError(data.detail || data.message || 'Error ' + response.status);
                    }
                } catch (e) {
                    showError('Network Error: ' + e.message);
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
                    
                    const text = await response.text();
                    let data;
                    try {
                        data = JSON.parse(text);
                    } catch (e) {
                        showError('Verify Server Error: ' + text.substring(0, 100));
                        return;
                    }

                    if (response.ok && data.success) {
                        localStorage.setItem('access_token', data.token);
                        localStorage.setItem('user', JSON.stringify(data.user));
                        window.location.href = '/admin/';
                    } else {
                        showError(data.message || data.detail || 'Invalid OTP');
                    }
                } catch (e) {
                    showError('Verify Network Error: ' + e.message);
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
    import os
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
