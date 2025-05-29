#!/usr/bin/env python3
"""
Test script to verify database models.
"""

import sys
import os
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from app.database import init_db, close_db, AsyncSessionLocal
from app.models import ChargePoint, IdTag, Session, MeterValue
from loguru import logger

async def test_models():
    """Test creating and querying database models."""
    try:
        # Initialize database (create tables)
        await init_db()
        
        # Test creating some sample data
        async with AsyncSessionLocal() as session:
            # Create a charge point
            charge_point = ChargePoint(
                id="CP001",
                vendor="MockVendor",
                model="MockModel",
                status="Available",
                is_online=True,
                last_seen=datetime.utcnow()
            )
            session.add(charge_point)
            
            # Create an ID tag
            id_tag = IdTag(
                tag="RFID123456",
                status="Accepted",
                user_name="Test User"
            )
            session.add(id_tag)
            
            # Commit the changes
            await session.commit()
            
            logger.info("Sample data created successfully!")
            
            # Query the data back
            result = await session.get(ChargePoint, "CP001")
            if result:
                logger.info(f"Found charge point: {result.id} - {result.vendor} {result.model}")
            
            logger.info("✅ Models test completed successfully!")
            
    except Exception as e:
        logger.error(f"Models test failed: {e}")
        return False
    finally:
        await close_db()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_models())
    if success:
        print("✅ Database models are working correctly!")
    else:
        print("❌ Database models test failed.") 