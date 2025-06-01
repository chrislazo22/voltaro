#!/usr/bin/env python3
"""
Start the Voltaro API server with both REST API and OCPP WebSocket functionality.
"""

import uvicorn
from loguru import logger

if __name__ == "__main__":
    logger.info("Starting Voltaro API server...")
    logger.info("REST API will be available at: http://localhost:8000")
    logger.info("OCPP WebSocket server will run on: ws://localhost:9000")
    logger.info("API documentation: http://localhost:8000/docs")

    uvicorn.run(
        "app.api_server:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )

