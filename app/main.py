from typing import Optional
from fastapi import FastAPI, Request, Response, status, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.config import settings
# CRITICAL: Don't import routers at top level - they might fail and prevent app from starting
# from app.api import auth, customers, templates, invoices, old_invoices, public_invoice, migration, demo
from app.database import get_db
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
            # CRITICAL: Import ALL models here to ensure Base knows about them
            import app.models.auth
            import app.models.customer
            import app.models.invoice
            import app.models.template
            import app.models.package
            import app.models.voucher
            
            # Explicitly reference models to avoid 'unused' removal by linters
            _ = [app.models.auth.AuthUser, app.models.customer.Customer, 
                 app.models.invoice.InvoiceNew, app.models.template.InvoiceTemplate, 
                 app.models.package.Package, app.models.voucher.Voucher]
            
            await asyncio.to_thread(Base.metadata.create_all, bind=engine)
            logger.info("Database schema is up to date.")
        except Exception as e:
            logger.error(f"SCHEMA ERROR: {e}")
    else:
        logger.critical("DATABASE UNREACHABLE: Background initialization failed.")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Handles database initialization gracefully.
    """
    import time
    import logging
    logger = logging.getLogger(__name__)
    
    app.state.start_time = time.time()
    
    # Log all registered routes BEFORE accepting requests
    logger.info("=" * 80)
    logger.info("REGISTERED ROUTES AT STARTUP:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            logger.info(f"  {list(route.methods)} {route.path}")
    logger.info("=" * 80)
    create_invoice_registered = '/create-invoice' in [r.path for r in app.routes if hasattr(r, 'path')]
    logger.info(f"✅ /create-invoice route registered: {create_invoice_registered}")
    if not create_invoice_registered:
        logger.error("❌ CRITICAL: /create-invoice route NOT FOUND in registered routes!")
    
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

# CRITICAL: Add absolute minimal route FIRST to test if routes work at all
@app.get("/test-route-works")
async def test_route_works():
    """Absolute minimal test route - no dependencies"""
    logger.info("✅ /test-route-works HIT!")
    return {"status": "OK", "message": "Routes are working!", "route": "/test-route-works"}

# Railway deployment verification route
@app.get("/railway-deploy-check")
async def railway_deploy_check():
    """Verify Railway deployment is using latest code"""
    all_routes = [r.path for r in app.routes if hasattr(r, 'path')]
    return {
        "status": "OK",
        "deployment": "latest",
        "timestamp": __import__("time").time(),
        "routes_registered": len(all_routes),
        "create_invoice_route": "/create-invoice" in all_routes,
        "test_route": "/test-create-invoice-simple" in all_routes,
        "sample_routes": [r for r in all_routes if "create-invoice" in r or "test" in r][:10]
    }

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


# SIMPLE TEST ROUTE - No dependencies, always works
@app.get("/test-create-invoice-simple", response_class=HTMLResponse)
async def test_create_invoice_simple():
    """Super simple test route - no dependencies"""
    logger.info("✅ /test-create-invoice-simple HIT!")
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head><title>Test Route Working</title></head>
        <body>
            <h1>✅ Test Route Working!</h1>
            <p>If you see this, routes are registering correctly.</p>
            <p><a href="/create-invoice">Try /create-invoice</a></p>
        </body>
        </html>
        """,
        status_code=200
    )

# Invoice creation page route - MUST be registered BEFORE routers to avoid conflicts
@app.get("/create-invoice", response_class=HTMLResponse)
async def create_invoice_page(
    request: Request,
    package_id: Optional[str] = Query(None, description="Package ID from package table"),
    panel_qty: Optional[int] = Query(None, description="Panel quantity"),
    panel_rating: Optional[str] = Query(None, description="Panel rating"),
    discount_given: Optional[str] = Query(None, description="Discount amount or percent"),
    customer_name: Optional[str] = Query(None, description="Customer name (optional)"),
    customer_phone: Optional[str] = Query(None, description="Customer phone (optional)"),
    customer_address: Optional[str] = Query(None, description="Customer address (optional)"),
    template_id: Optional[str] = Query(None, description="Template ID (optional)")
):
    """
    Invoice creation page - ALWAYS shows the page, even with errors.
    Clear error messages and full visibility.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔍 /create-invoice route HIT! URL: {request.url}, package_id: {package_id}")
    
    from urllib.parse import unquote, parse_qs
    import os
    import traceback
    
    # Initialize variables with defaults
    package = None
    error_message = None
    warning_message = None
    debug_info = []
    debug_info.append(f"✅ Route accessed successfully")
    debug_info.append(f"URL: {request.url}")
    debug_info.append(f"Method: {request.method}")
    debug_info.append(f"Package ID from query: {package_id}")
    
    try:
        # Handle double-encoded URLs
        if not package_id and request.url.query:
            query_str = str(request.url.query)
            if '%3D' in query_str or '%26' in query_str:
                try:
                    decoded = unquote(query_str)
                    parsed = parse_qs(decoded, keep_blank_values=True)
                    if 'package_id' in parsed and parsed['package_id']:
                        package_id = parsed['package_id'][0]
                    if 'discount_given' in parsed and parsed['discount_given'] and not discount_given:
                        discount_given = parsed['discount_given'][0]
                    if 'panel_qty' in parsed and parsed['panel_qty'] and not panel_qty:
                        try:
                            panel_qty = int(parsed['panel_qty'][0])
                        except:
                            pass
                    if 'panel_rating' in parsed and parsed['panel_rating'] and not panel_rating:
                        panel_rating = parsed['panel_rating'][0]
                    if 'customer_name' in parsed and parsed['customer_name'] and not customer_name:
                        customer_name = parsed['customer_name'][0]
                    if 'customer_phone' in parsed and parsed['customer_phone'] and not customer_phone:
                        customer_phone = parsed['customer_phone'][0]
                    if 'customer_address' in parsed and parsed['customer_address'] and not customer_address:
                        customer_address = parsed['customer_address'][0]
                    if 'template_id' in parsed and parsed['template_id'] and not template_id:
                        template_id = parsed['template_id'][0]
                except Exception as e:
                    warning_message = f"URL parsing warning: {str(e)}"
        
        # Try to get database session (optional - route works without it)
        db = None
        try:
            from app.database import get_db
            db = next(get_db())
            debug_info.append("✅ Database connection successful")
        except Exception as db_error:
            logger.warning(f"Database connection failed: {db_error}")
            debug_info.append(f"⚠️ Database connection failed: {str(db_error)}")
            warning_message = "Database connection unavailable. Some features may be limited."
        
        # Try to fetch package if package_id provided
        if package_id:
            if db:
                try:
                    from app.models.package import Package
                    package = db.query(Package).filter(Package.bubble_id == package_id).first()
                    if not package:
                        error_message = f"⚠️ Package Not Found: The Package ID '{package_id}' does not exist in the database."
                        debug_info.append(f"Package ID searched: {package_id}")
                        debug_info.append("Possible causes: Package ID is incorrect, package was deleted, or database connection issue")
                    else:
                        debug_info.append(f"✅ Package found: {package.package_name}")
                except Exception as e:
                    error_message = f"⚠️ Database Error: Failed to check package. Error: {str(e)}"
                    debug_info.append(f"Database error details: {traceback.format_exc()}")
            else:
                error_message = f"⚠️ Cannot check package: Database connection unavailable. Package ID provided: {package_id}"
                debug_info.append("Database connection is required to verify package ID")
        else:
            warning_message = "ℹ️ No Package ID provided. You can enter a Package ID below or continue without one."
        
        # Try to render template
        try:
            from fastapi.templating import Jinja2Templates
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_dir = os.path.join(base_dir, "app", "templates")
            
            # Verify template directory exists
            if not os.path.exists(template_dir):
                raise FileNotFoundError(f"Template directory not found: {template_dir}")
            
            template_file = os.path.join(template_dir, "create_invoice.html")
            if not os.path.exists(template_file):
                raise FileNotFoundError(f"Template file not found: {template_file}")
            
            templates = Jinja2Templates(directory=template_dir)
            debug_info.append(f"✅ Template directory: {template_dir}")
            debug_info.append(f"✅ Template file exists: {template_file}")
            
            return templates.TemplateResponse(
                "create_invoice.html",
                {
                    "request": request,
                    "user": None,
                    "package": package,
                    "package_id": package_id,
                    "error_message": error_message,
                    "warning_message": warning_message,
                    "debug_info": debug_info,
                    "panel_qty": panel_qty,
                    "panel_rating": panel_rating,
                    "discount_given": discount_given,
                    "customer_name": customer_name,
                    "customer_phone": customer_phone,
                    "customer_address": customer_address,
                    "template_id": template_id
                }
            )
        except FileNotFoundError as e:
            # Template file missing - show helpful error page
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Template Error - Invoice Creation</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script src="https://cdn.tailwindcss.com"></script>
                </head>
                <body class="bg-gray-100 min-h-screen p-4">
                    <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-6">
                        <h1 class="text-2xl font-bold text-red-600 mb-4">❌ Template File Missing</h1>
                        <div class="bg-red-50 border-2 border-red-300 rounded p-4 mb-4">
                            <p class="font-semibold text-red-900 mb-2">Error Details:</p>
                            <p class="text-red-800">{str(e)}</p>
                        </div>
                        <div class="bg-yellow-50 border-2 border-yellow-300 rounded p-4 mb-4">
                            <p class="font-semibold text-yellow-900 mb-2">What This Means:</p>
                            <p class="text-yellow-800">The invoice creation form template file is missing from the server.</p>
                        </div>
                        <div class="bg-blue-50 border-2 border-blue-300 rounded p-4">
                            <p class="font-semibold text-blue-900 mb-2">Debug Information:</p>
                            <ul class="list-disc list-inside text-blue-800 space-y-1">
                                {"".join([f"<li>{info}</li>" for info in debug_info])}
                            </ul>
                        </div>
                        <div class="mt-6">
                            <a href="/admin/" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold">
                                Go to Dashboard
                            </a>
                        </div>
                    </div>
                </body>
                </html>
                """,
                status_code=200  # Still return 200 so page shows
            )
        except Exception as e:
            # Template rendering error - show helpful error page
            error_trace = traceback.format_exc()
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Template Error - Invoice Creation</title>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <script src="https://cdn.tailwindcss.com"></script>
                </head>
                <body class="bg-gray-100 min-h-screen p-4">
                    <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-6">
                        <h1 class="text-2xl font-bold text-red-600 mb-4">❌ Template Rendering Error</h1>
                        <div class="bg-red-50 border-2 border-red-300 rounded p-4 mb-4">
                            <p class="font-semibold text-red-900 mb-2">Error:</p>
                            <p class="text-red-800 font-mono">{str(e)}</p>
                        </div>
                        <div class="bg-yellow-50 border-2 border-yellow-300 rounded p-4 mb-4">
                            <p class="font-semibold text-yellow-900 mb-2">What This Means:</p>
                            <p class="text-yellow-800">The server encountered an error while trying to load the invoice creation form.</p>
                        </div>
                        <div class="bg-gray-50 border-2 border-gray-300 rounded p-4 mb-4">
                            <p class="font-semibold text-gray-900 mb-2">Technical Details:</p>
                            <pre class="text-xs overflow-auto bg-gray-900 text-green-400 p-4 rounded">{error_trace}</pre>
                        </div>
                        <div class="bg-blue-50 border-2 border-blue-300 rounded p-4 mb-4">
                            <p class="font-semibold text-blue-900 mb-2">Debug Information:</p>
                            <ul class="list-disc list-inside text-blue-800 space-y-1">
                                {"".join([f"<li>{info}</li>" for info in debug_info]) if debug_info else "<li>No debug info available</li>"}
                            </ul>
                        </div>
                        <div class="mt-6 space-x-4">
                            <a href="/admin/" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold">
                                Go to Dashboard
                            </a>
                            <a href="/create-invoice" class="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold">
                                Try Again
                            </a>
                        </div>
                    </div>
                </body>
                </html>
                """,
                status_code=200  # Still return 200 so page shows
            )
    except Exception as e:
        # Critical error - show error page but still return 200
        error_trace = traceback.format_exc()
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Critical Error - Invoice Creation</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 min-h-screen p-4">
                <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-6">
                    <h1 class="text-2xl font-bold text-red-600 mb-4">❌ Critical Error</h1>
                    <div class="bg-red-50 border-2 border-red-300 rounded p-4 mb-4">
                        <p class="font-semibold text-red-900 mb-2">Error:</p>
                        <p class="text-red-800 font-mono">{str(e)}</p>
                    </div>
                    <div class="bg-gray-50 border-2 border-gray-300 rounded p-4 mb-4">
                        <p class="font-semibold text-gray-900 mb-2">Full Error Trace:</p>
                        <pre class="text-xs overflow-auto bg-gray-900 text-green-400 p-4 rounded">{error_trace}</pre>
                    </div>
                    <div class="mt-6">
                        <a href="/admin/" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold">
                            Go to Dashboard
                        </a>
                    </div>
                </div>
            </body>
                </html>
            """,
            status_code=200  # Always return 200 - never return 404 or 500
        )
    finally:
        # Close database session if it was opened
        if 'db' in locals() and db:
            try:
                db.close()
            except:
                pass


# Include routers - LAZY IMPORT to prevent app crash if routers fail
try:
    from app.api import auth
app.include_router(auth.router)
except Exception as e:
    logger.error(f"Failed to load auth router: {e}")

try:
    from app.api import customers
app.include_router(customers.router)
except Exception as e:
    logger.error(f"Failed to load customers router: {e}")

try:
    from app.api import templates
app.include_router(templates.router)
except Exception as e:
    logger.error(f"Failed to load templates router: {e}")

try:
    from app.api import invoices
app.include_router(invoices.router)
except Exception as e:
    logger.error(f"Failed to load invoices router: {e}")

try:
    from app.api import old_invoices
app.include_router(old_invoices.router)
except Exception as e:
    logger.error(f"Failed to load old_invoices router: {e}")

try:
    from app.api import public_invoice
app.include_router(public_invoice.router)
except Exception as e:
    logger.error(f"Failed to load public_invoice router: {e}")

try:
    from app.api import migration
app.include_router(migration.router)
except Exception as e:
    logger.error(f"Failed to load migration router: {e}")

try:
    from app.api import demo
app.include_router(demo.router)
except Exception as e:
    logger.error(f"Failed to load demo router: {e}")


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
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { font-family: 'Open Sans', ui-sans-serif, system-ui, -apple-system, sans-serif; }
        </style>
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
                        <a href="/admin/guides" class="block bg-teal-500 hover:bg-teal-600 text-white px-4 py-2 rounded">📚 Documentation & Guides</a>
                        <a href="/demo/generate-invoice" target="_blank" class="block bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded">Preview Demo Invoice</a>
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
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { font-family: 'Open Sans', ui-sans-serif, system-ui, -apple-system, sans-serif; }
        </style>
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

            // Handle return URL from query parameter
            const urlParams = new URLSearchParams(window.location.search);
            const returnUrl = urlParams.get('return_url') || '/admin/';

            // Override default redirect if return_url exists
            if (returnUrl !== '/admin/') {
                const originalVerifyOTP = verifyOTP;
                verifyOTP = async function() {
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
                            window.location.href = decodeURIComponent(returnUrl);
                        } else {
                            showError(data.message || data.detail || 'Invalid OTP');
                        }
                    } catch (e) {
                        showError('Verify Network Error: ' + e.message);
                    }
                };
            }
        </script>
    </body>
    </html>
    """


@app.get("/admin/templates", response_class=HTMLResponse)
async def admin_templates():
    """Admin Templates Management"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EE Invoicing - Manage Templates</title>
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body { font-family: 'Open Sans', ui-sans-serif, system-ui, -apple-system, sans-serif; }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
    </head>
    <body class="bg-gray-100 min-h-screen">
        <nav class="bg-blue-600 text-white p-4">
            <div class="container mx-auto flex justify-between items-center">
                <a href="/admin/" class="text-xl font-bold hover:text-blue-100">EE Invoicing System</a>
                <div>
                    <a href="/admin/" class="mr-4 hover:underline">Dashboard</a>
                    <button onclick="logout()" class="bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded">Logout</button>
                </div>
            </div>
        </nav>

        <div class="container mx-auto p-6">
            <div class="flex justify-between items-center mb-6">
                <h1 class="text-2xl font-bold text-gray-800">Manage Templates</h1>
                <div class="flex space-x-2">
                    <a href="/demo/generate-invoice" target="_blank" class="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded flex items-center">
                        <i class="fas fa-eye mr-2"></i> Preview Demo
                    </a>
                    <button onclick="openModal()" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded flex items-center">
                        <i class="fas fa-plus mr-2"></i> New Template
                    </button>
                </div>
            </div>

            <div id="loading" class="text-center py-8">
                <i class="fas fa-spinner fa-spin text-4xl text-blue-500"></i>
            </div>

            <div id="templates-list" class="grid grid-cols-1 md:grid-cols-2 gap-6 hidden">
                <!-- Templates will be injected here -->
            </div>
        </div>

        <!-- Modal -->
        <div id="modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center p-4 z-50">
            <div class="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-6">
                        <h2 id="modal-title" class="text-xl font-bold">New Template</h2>
                        <button onclick="closeModal()" class="text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>

                    <form id="template-form" onsubmit="handleFormSubmit(event)" class="space-y-4">
                        <input type="hidden" id="bubble_id">
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Template Name *</label>
                                <input type="text" id="template_name" required class="w-full border p-2 rounded mt-1">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Company Name *</label>
                                <input type="text" id="company_name" required class="w-full border p-2 rounded mt-1">
                            </div>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700">Company Address *</label>
                            <textarea id="company_address" required rows="3" class="w-full border p-2 rounded mt-1"></textarea>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Phone</label>
                                <input type="text" id="company_phone" class="w-full border p-2 rounded mt-1">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Email</label>
                                <input type="email" id="company_email" class="w-full border p-2 rounded mt-1">
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">SST Registration No</label>
                                <input type="text" id="sst_registration_no" 
                                    placeholder="ST1234567890" title="Format: ST followed by 10-12 digits"
                                    class="w-full border p-2 rounded mt-1">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Logo URL</label>
                                <input type="url" id="logo_url" class="w-full border p-2 rounded mt-1">
                            </div>
                        </div>

                        <div class="border-t pt-4 mt-4">
                            <h3 class="font-medium mb-2">Bank Details</h3>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700">Bank Name</label>
                                    <input type="text" id="bank_name" class="w-full border p-2 rounded mt-1">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700">Account No</label>
                                    <input type="text" id="bank_account_no" class="w-full border p-2 rounded mt-1">
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700">Account Name</label>
                                    <input type="text" id="bank_account_name" class="w-full border p-2 rounded mt-1">
                                </div>
                            </div>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700">Terms & Conditions</label>
                            <textarea id="terms_and_conditions" rows="3" class="w-full border p-2 rounded mt-1"></textarea>
                        </div>

                        <div class="flex items-center space-x-6">
                            <div class="flex items-center">
                                <input type="checkbox" id="apply_sst" class="mr-2">
                                <label for="apply_sst" class="text-sm font-medium text-gray-700">Apply SST (8%)</label>
                            </div>
                            <div class="flex items-center">
                                <input type="checkbox" id="is_default" class="mr-2">
                                <label for="is_default" class="text-sm font-medium text-gray-700">Set as Default Template</label>
                            </div>
                        </div>

                        <div class="flex justify-end pt-4 space-x-3">
                            <button type="button" onclick="closeModal()" class="px-4 py-2 border rounded hover:bg-gray-100">Cancel</button>
                            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Save Template</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <script>
            const API_BASE = '/api/v1';
            let token = localStorage.getItem('access_token');

            if (!token) window.location.href = '/admin/login';

            // Fields to map for form
            const fields = [
                'template_name', 'company_name', 'company_address', 'company_phone', 
                'company_email', 'sst_registration_no', 'bank_name', 'bank_account_no', 
                'bank_account_name', 'logo_url', 'terms_and_conditions', 'apply_sst', 'is_default'
            ];

            async function fetchTemplates() {
                try {
                    const response = await fetch(`${API_BASE}/templates?limit=100`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (!response.ok) throw new Error('Failed to fetch templates');
                    
                    const data = await response.json();
                    renderTemplates(data.templates);
                } catch (e) {
                    console.error(e);
                    alert('Error loading templates');
                } finally {
                    document.getElementById('loading').classList.add('hidden');
                    document.getElementById('templates-list').classList.remove('hidden');
                }
            }

            function renderTemplates(templates) {
                const container = document.getElementById('templates-list');
                container.innerHTML = '';

                if (templates.length === 0) {
                    container.innerHTML = '<p class="col-span-2 text-center text-gray-500">No templates found. Create one to get started.</p>';
                    return;
                }

                templates.forEach(t => {
                    const card = document.createElement('div');
                    card.className = `bg-white p-6 rounded-lg shadow border-l-4 ${t.is_default ? 'border-green-500' : 'border-gray-300'}`;
                    card.innerHTML = `
                        <div class="flex justify-between items-start mb-4">
                            <div>
                                <h3 class="font-bold text-lg">${t.template_name}</h3>
                                <p class="text-sm text-gray-500">${t.company_name} ${t.apply_sst ? '<span class="text-indigo-600 font-bold ml-1">(SST Enabled)</span>' : ''}</p>
                            </div>
                            ${t.is_default ? '<span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">Default</span>' : ''}
                        </div>
                        <div class="space-y-2 text-sm text-gray-600 mb-4">
                            <p><i class="fas fa-map-marker-alt w-5"></i> ${t.company_address.substring(0, 50)}...</p>
                            <p><i class="fas fa-id-card w-5"></i> ${t.sst_registration_no}</p>
                            ${t.company_phone ? `<p><i class="fas fa-phone w-5"></i> ${t.company_phone}</p>` : ''}
                        </div>
                        <div class="flex justify-end space-x-2 border-t pt-4">
                            ${!t.is_default ? `
                                <button onclick="setDefault('${t.bubble_id}')" class="text-sm text-gray-600 hover:text-green-600 px-2 py-1">
                                    <i class="fas fa-check"></i> Set Default
                                </button>
                            ` : ''}
                            <button onclick='editTemplate(${JSON.stringify(t).replace(/'/g, "&#39;")})' class="text-sm text-blue-600 hover:text-blue-800 px-2 py-1">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                            <button onclick="deleteTemplate('${t.bubble_id}')" class="text-sm text-red-600 hover:text-red-800 px-2 py-1">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    `;
                    container.appendChild(card);
                });
            }

            function openModal(isEdit = false) {
                document.getElementById('modal').classList.remove('hidden');
                document.getElementById('modal').classList.add('flex');
                document.getElementById('modal-title').textContent = isEdit ? 'Edit Template' : 'New Template';
                if (!isEdit) {
                    document.getElementById('template-form').reset();
                    document.getElementById('bubble_id').value = '';
                }
            }

            function closeModal() {
                document.getElementById('modal').classList.add('hidden');
                document.getElementById('modal').classList.remove('flex');
            }

            function editTemplate(template) {
                openModal(true);
                document.getElementById('bubble_id').value = template.bubble_id;
                
                fields.forEach(f => {
                    const el = document.getElementById(f);
                    if (el) {
                        if (el.type === 'checkbox') {
                            el.checked = template[f];
                        } else {
                            el.value = template[f] || '';
                        }
                    }
                });
            }

            async function handleFormSubmit(e) {
                e.preventDefault();
                const bubbleId = document.getElementById('bubble_id').value;
                const isEdit = !!bubbleId;
                
                const payload = {};
                fields.forEach(f => {
                    const el = document.getElementById(f);
                    if (el.type === 'checkbox') {
                        payload[f] = el.checked;
                    } else if (el.value) {
                        payload[f] = el.value;
                    }
                });

                // Clean empty strings for optional fields
                ['logo_url', 'company_email', 'company_phone', 'bank_name', 'bank_account_no', 'bank_account_name', 'terms_and_conditions'].forEach(k => {
                    if (payload[k] === '') delete payload[k];
                });

                try {
                    const url = isEdit ? `${API_BASE}/templates/${bubbleId}` : `${API_BASE}/templates`;
                    const method = isEdit ? 'PUT' : 'POST';
                    
                    const response = await fetch(url, {
                        method: method,
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify(payload)
                    });

                    if (!response.ok) {
                        const err = await response.json();
                        throw new Error(err.detail || 'Failed to save');
                    }

                    closeModal();
                    fetchTemplates();
                } catch (err) {
                    alert(err.message);
                }
            }

            async function deleteTemplate(id) {
                if (!confirm('Are you sure you want to delete this template?')) return;
                
                try {
                    const response = await fetch(`${API_BASE}/templates/${id}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (!response.ok) throw new Error('Failed to delete');
                    fetchTemplates();
                } catch (err) {
                    alert(err.message);
                }
            }

            async function setDefault(id) {
                try {
                    const response = await fetch(`${API_BASE}/templates/${id}/set-default`, {
                        method: 'POST',
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (!response.ok) throw new Error('Failed to set default');
                    fetchTemplates();
                } catch (err) {
                    alert(err.message);
                }
            }

            function logout() {
                localStorage.removeItem('access_token');
                window.location.href = '/';
            }

            fetchTemplates();
        </script>
    </body>
    </html>
    """

@app.get("/admin/invoices", response_class=HTMLResponse)
async def admin_invoices():
    """Placeholder for Invoice Management"""
    return """
    <!DOCTYPE html>
    <html><head><title>Invoices</title><meta http-equiv="refresh" content="0; url=/admin/" /></head>
    <body><script>alert("Invoice management coming soon!"); window.location.href="/admin/";</script></body></html>
    """

@app.get("/admin/customers", response_class=HTMLResponse)
async def admin_customers():
    """Placeholder for Customer Management"""
    return """
    <!DOCTYPE html>
    <html><head><title>Customers</title><meta http-equiv="refresh" content="0; url=/admin/" /></head>
    <body><script>alert("Customer management coming soon!"); window.location.href="/admin/";</script></body></html>
    """

@app.get("/admin/migration", response_class=HTMLResponse)
async def admin_migration():
    """Placeholder for Migration Tool"""
    return """
    <!DOCTYPE html>
    <html><head><title>Migration</title><meta http-equiv="refresh" content="0; url=/admin/" /></head>
    <body><script>alert("Migration tool coming soon!"); window.location.href="/admin/";</script></body></html>
    """


@app.get("/admin/guides", response_class=HTMLResponse)
async def admin_guides():
    """Documentation and Guides Page"""
    import os
    
    # Read guide files
    guides = {}
    guide_files = {
        "sales_team_guide": "SALES_TEAM_INVOICE_LINK_GUIDE.md",
        "quick_reference": "INVOICE_LINK_QUICK_REFERENCE.md",
        "access_guide": "INVOICE_PAGE_ACCESS_GUIDE.md"
    }
    
    for key, filename in guide_files.items():
        filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    guides[key] = f.read()
                    except:
                guides[key] = f"Error reading {filename}"
        else:
            guides[key] = f"File {filename} not found"
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>EE Invoicing - Documentation & Guides</title>
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ font-family: 'Open Sans', ui-sans-serif, system-ui, -apple-system, sans-serif; }}
            .markdown-content {{
                line-height: 1.8;
            }}
            .markdown-content h1 {{
                font-size: 2rem;
                font-weight: 700;
                margin-top: 2rem;
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid #e5e7eb;
            }}
            .markdown-content h2 {{
                font-size: 1.5rem;
                font-weight: 600;
                margin-top: 1.5rem;
                margin-bottom: 0.75rem;
                color: #1f2937;
            }}
            .markdown-content h3 {{
                font-size: 1.25rem;
                font-weight: 600;
                margin-top: 1.25rem;
                margin-bottom: 0.5rem;
                color: #374151;
            }}
            .markdown-content p {{
                margin-bottom: 1rem;
                color: #4b5563;
            }}
            .markdown-content ul, .markdown-content ol {{
                margin-left: 1.5rem;
                margin-bottom: 1rem;
            }}
            .markdown-content li {{
                margin-bottom: 0.5rem;
                color: #4b5563;
            }}
            .markdown-content code {{
                background-color: #f3f4f6;
                padding: 0.125rem 0.375rem;
                border-radius: 0.25rem;
                font-family: 'Courier New', monospace;
                font-size: 0.875rem;
                color: #dc2626;
            }}
            .markdown-content pre {{
                background-color: #1f2937;
                color: #f9fafb;
                padding: 1rem;
                border-radius: 0.5rem;
                overflow-x: auto;
                margin-bottom: 1rem;
            }}
            .markdown-content pre code {{
                background-color: transparent;
                color: #f9fafb;
                padding: 0;
            }}
            .markdown-content table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 1rem;
            }}
            .markdown-content table th,
            .markdown-content table td {{
                border: 1px solid #e5e7eb;
                padding: 0.5rem;
                text-align: left;
            }}
            .markdown-content table th {{
                background-color: #f9fafb;
                font-weight: 600;
            }}
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <nav class="bg-blue-600 text-white p-4">
            <div class="container mx-auto flex justify-between items-center">
                <a href="/admin/" class="text-xl font-bold hover:text-blue-100">EE Invoicing System</a>
                <div>
                    <a href="/admin/" class="mr-4 hover:underline">Dashboard</a>
                    <button onclick="logout()" class="bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded">Logout</button>
                </div>
            </div>
        </nav>

        <div class="container mx-auto p-6">
            <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
                <h1 class="text-3xl font-bold text-gray-800 mb-4">📚 Documentation & Guides</h1>
                <p class="text-gray-600 mb-6">Complete guides for using the Invoice Creation system</p>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <a href="#sales-guide" class="bg-blue-50 hover:bg-blue-100 p-4 rounded-lg border-2 border-blue-200 transition">
                        <h3 class="font-semibold text-blue-900 mb-2">📖 Sales Team Guide</h3>
                        <p class="text-sm text-blue-700">Complete guide for generating invoice links</p>
                    </a>
                    <a href="#quick-ref" class="bg-green-50 hover:bg-green-100 p-4 rounded-lg border-2 border-green-200 transition">
                        <h3 class="font-semibold text-green-900 mb-2">⚡ Quick Reference</h3>
                        <p class="text-sm text-green-700">Fast lookup for AI agents and developers</p>
                    </a>
                    <a href="#access-guide" class="bg-purple-50 hover:bg-purple-100 p-4 rounded-lg border-2 border-purple-200 transition">
                        <h3 class="font-semibold text-purple-900 mb-2">🔗 Access Guide</h3>
                        <p class="text-sm text-purple-700">How to access the invoice creation page</p>
                    </a>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
                <div id="sales-guide" class="markdown-content">
                    <h1>Sales Team Invoice Creation Link Guide</h1>
                    <div style="white-space: pre-wrap; font-family: monospace; font-size: 0.9rem; max-height: 600px; overflow-y: auto; background: #f9fafb; padding: 1rem; border-radius: 0.5rem;">{guides.get('sales_team_guide', 'Guide not available')}</div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
                <div id="quick-ref" class="markdown-content">
                    <h1>Invoice Creation Link - Quick Reference</h1>
                    <div style="white-space: pre-wrap; font-family: monospace; font-size: 0.9rem; max-height: 600px; overflow-y: auto; background: #f9fafb; padding: 1rem; border-radius: 0.5rem;">{guides.get('quick_reference', 'Guide not available')}</div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
                <div id="access-guide" class="markdown-content">
                    <h1>Invoice Creation Page - Access Guide</h1>
                    <div style="white-space: pre-wrap; font-family: monospace; font-size: 0.9rem; max-height: 600px; overflow-y: auto; background: #f9fafb; padding: 1rem; border-radius: 0.5rem;">{guides.get('access_guide', 'Guide not available')}</div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-lg p-6">
                <div class="flex justify-between items-center">
                    <div>
                        <h2 class="text-xl font-bold text-gray-800 mb-2">Need Help?</h2>
                        <p class="text-gray-600">For technical support or questions, contact the development team.</p>
                    </div>
                    <a href="/admin/" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold">
                        Back to Dashboard
                    </a>
                </div>
            </div>
        </div>

        <script>
            function logout() {{
                localStorage.removeItem('access_token');
                window.location.href = '/';
            }}

            // Smooth scroll for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """


# Test route to verify server is working
@app.get("/test-create-invoice", response_class=HTMLResponse)
async def test_create_invoice():
    """Test route to verify /create-invoice route is accessible"""
    return HTMLResponse(content="<h1>Test Route Working!</h1><p>If you see this, the server is responding.</p><p><a href='/create-invoice'>Try /create-invoice</a></p>")


# Random Package Link Generator (For Testing)
@app.get("/demo/random-package-link", response_class=HTMLResponse)
async def random_package_link(db: Session = Depends(get_db)):
    """
    Pick a random package from DB and generate invoice creation link
    Sample use case: Test with RM500 discount + 10% off discount
    """
    from app.models.package import Package
    from sqlalchemy import func

    # 1. Fetch Random Package
    package_count = db.query(func.count(Package.id)).scalar() or 0
    if package_count == 0:
        return HTMLResponse(
            content="<h1 class='text-center mt-10 text-2xl text-red-600'>No packages found in database</h1>",
            status_code=404
        )

    random_offset = 0 if package_count == 1 else (package_count - 1)
    import random
    random_offset = random.randint(0, random_offset)
    package = db.query(Package).offset(random_offset).first()

    # 2. Generate Invoice Creation Link
    # Discounts: RM500 (fixed) + 10% (percentage)
    discount_fixed = 500
    discount_percent = 10
    invoice_link = f"/create-invoice?package_id={package.bubble_id}&discount_given={discount_fixed}%20{discount_percent}%25"

    # 3. Render HTML
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Random Package Link Generator</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen p-8">
        <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8">
            <h1 class="text-2xl font-bold mb-6 text-blue-600">🎲 Random Package Link Generator</h1>

            <div class="mb-6 p-4 bg-blue-50 rounded-lg">
                <h2 class="font-semibold text-blue-800 mb-2">Selected Package:</h2>
                <p class="text-xl font-bold text-gray-900">{package.name}</p>
                <p class="text-gray-600">Price: RM {package.price}</p>
                <p class="text-gray-500 text-sm">Package ID: {package.bubble_id}</p>
            </div>

            <div class="mb-6 p-4 bg-green-50 rounded-lg">
                <h2 class="font-semibold text-green-800 mb-2">Discount Applied:</h2>
                <p class="text-red-600 font-semibold">Fixed: RM {discount_fixed}</p>
                <p class="text-red-600 font-semibold">Percentage: {discount_percent}%</p>
                <p class="text-gray-600 text-sm mt-1">Total Discount: RM {discount_fixed + (package.price * discount_percent / 100)}</p>
            </div>

            <div class="mb-6 p-4 bg-yellow-50 rounded-lg">
                <h2 class="font-semibold text-yellow-800 mb-2">Expected Invoice Items:</h2>
                <ul class="list-disc list-inside text-gray-700 space-y-1">
                    <li><strong>Package:</strong> {package.name} (RM {package.price})</li>
                    <li><strong>Discount:</strong> RM {discount_fixed} (negative price)</li>
                    <li><strong>Discount:</strong> {discount_percent}% (negative price)</li>
                    <li><strong>SST:</strong> 8% (default)</li>
                    <li><strong>Total:</strong> RM {package.price - discount_fixed - (package.price * discount_percent / 100) + ((package.price - discount_fixed - (package.price * discount_percent / 100)) * 0.08)}</li>
                </ul>
            </div>

            <div class="mb-6">
                <h2 class="font-semibold text-gray-800 mb-2">Invoice Creation Link:</h2>
                <div class="bg-gray-100 p-3 rounded-lg border border-gray-300">
                    <code class="text-sm text-blue-600 break-all">{invoice_link}</code>
                </div>
            </div>

            <div class="flex gap-4">
                <a href="/admin/" class="flex-1 bg-gray-500 hover:bg-gray-600 text-white text-center py-3 rounded-lg font-semibold">
                    Back to Dashboard
                </a>
                <a href="{invoice_link}" class="flex-2 bg-green-500 hover:bg-green-600 text-white text-center py-3 px-6 rounded-lg font-semibold">
                    Open Invoice Form
                </a>
            </div>
        </div>
    </body>
    </html>
    """


# Catch-all route removed - routes should just work

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
