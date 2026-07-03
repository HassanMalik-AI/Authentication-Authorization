from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import engine, Base
from app.core.config import settings
from app.middleware.security import SecurityHeadersMiddleware
from app.routes import auth, users, roles, admin
import logging

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    Base.metadata.create_all(bind=engine)
    logging.info("Database tables created/verified")
    yield
    # Shutdown
    logging.info("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Secure Authentication System",
    description="Production-ready auth with JWT, RBAC, MFA, and PostgreSQL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security Middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Register routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {
        "message": "Secure Auth API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}