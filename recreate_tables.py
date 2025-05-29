"""
Script to drop and recreate database tables with updated schema.
Use this when you've made changes to the model structure.
"""

import asyncio
from app.database import engine, Base, close_db
from app.models import ChargePoint, IdTag, Session, MeterValue
from loguru import logger


async def recreate_tables():
    """Drop all tables and recreate them with the current schema."""
    try:
        async with engine.begin() as conn:
            # Drop all tables
            logger.info("Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Tables dropped successfully")

            # Create all tables with new schema
            logger.info("Creating tables with updated schema...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables created successfully")

        logger.info("✅ Database schema updated successfully!")
        return True

    except Exception as e:
        logger.error(f"Failed to recreate tables: {e}")
        return False
    finally:
        await close_db()


if __name__ == "__main__":
    print("⚠️  WARNING: This will delete all existing data in the database!")
    response = input("Are you sure you want to continue? (y/N): ")

    if response.lower() == "y":
        success = asyncio.run(recreate_tables())
        if success:
            print("✅ Database tables recreated successfully!")
        else:
            print("❌ Failed to recreate database tables.")
    else:
        print("Operation cancelled.")

