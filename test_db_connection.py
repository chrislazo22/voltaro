"""
Simple test to verify database connection.
Run this after setting up PostgreSQL.
"""
import asyncio
from app.database import engine, init_db, close_db
from loguru import logger
from sqlalchemy import text

async def test_connection():
    """Test database connection."""
    try:
        # Test basic connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            logger.info(f"Database connection successful! Test query result: {row}")
        
        # Test table creation
        await init_db()
        logger.exception("Database initialization successful!")
        
    except Exception as e:
        logger.exception("Database connection failed")
        return False
    finally:
        await close_db()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    if success:
        print("✅ Database setup is working correctly!")
    else:
        print("❌ Database setup failed. Check your PostgreSQL configuration.") 
