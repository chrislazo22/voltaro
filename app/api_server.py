"""
FastAPI REST API server for Voltaro dashboard.
This serves HTTP API endpoints alongside the OCPP WebSocket server.
"""

import asyncio
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import router
from app.main import main as start_ocpp_server


# Create FastAPI app
app = FastAPI(
    title="Voltaro API",
    description="REST API for EV charging management",
    version="1.0.0",
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Voltaro API is running", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check for monitoring."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


# Background task to run OCPP WebSocket server
ocpp_server_task = None


async def start_background_ocpp_server():
    """Start the OCPP WebSocket server in the background."""
    global ocpp_server_task
    try:
        logger.info("Starting OCPP WebSocket server in background...")
        ocpp_server_task = asyncio.create_task(start_ocpp_server())
        await ocpp_server_task
    except Exception as e:
        logger.error(f"OCPP server error: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Voltaro API server...")

    # Start OCPP WebSocket server in background
    asyncio.create_task(start_background_ocpp_server())

    logger.info("API server startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Voltaro API server...")

    # Cancel OCPP server task
    global ocpp_server_task
    if ocpp_server_task and not ocpp_server_task.done():
        ocpp_server_task.cancel()
        try:
            await ocpp_server_task
        except asyncio.CancelledError:
            logger.info("OCPP server task cancelled")

    logger.info("API server shutdown complete")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Voltaro API server with uvicorn...")
    uvicorn.run(
        "app.api_server:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )

