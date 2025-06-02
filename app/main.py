from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .api.routes import events
from .core.logging import setup_logging
from .services.initialization import initialize_services

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    logger.info("Starting up Event Tagging System...")
    try:
        await initialize_services()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.warning("App starting with limited functionality")
        # Don't raise - let the app start anyway
    
    yield
    
    # Shutdown
    logger.info("Shutting down Event Tagging System...")

# Create FastAPI app
app = FastAPI(
    title="IDA Event Tagging System",
    description="An AI-powered system for categorizing international development events",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router, prefix="/api/v1", tags=["events"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IDA Event Tagging System",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )