"""
Script to add test ID tags to the database for authorization testing.
"""

import sys
import os
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta
from app.database import AsyncSessionLocal, close_db
from app.models import IdTag
from loguru import logger
from sqlalchemy import select


async def setup_test_tags():
    """Add various test ID tags with different statuses."""
    try:
        async with AsyncSessionLocal() as session:
            # Test tags to create
            test_tags = [
                {
                    "tag": "VALID001",
                    "status": "Accepted",
                    "user_name": "John Doe",
                    "user_email": "john@example.com",
                    "expiry_date": datetime.utcnow()
                    + timedelta(days=365),  # Valid for 1 year
                },
                {
                    "tag": "VALID002",
                    "status": "Accepted",
                    "user_name": "Jane Smith",
                    "user_email": "jane@example.com",
                    "expiry_date": None,  # No expiry
                },
                {
                    "tag": "BLOCKED001",
                    "status": "Blocked",
                    "user_name": "Blocked User",
                    "user_email": "blocked@example.com",
                },
                {
                    "tag": "EXPIRED001",
                    "status": "Accepted",
                    "user_name": "Expired User",
                    "user_email": "expired@example.com",
                    "expiry_date": datetime.utcnow()
                    - timedelta(days=30),  # Expired 30 days ago
                },
                {
                    "tag": "PARENT001",
                    "status": "Accepted",
                    "user_name": "Parent Tag",
                    "user_email": "parent@example.com",
                },
                {
                    "tag": "CHILD001",
                    "status": "Accepted",
                    "user_name": "Child Tag",
                    "user_email": "child@example.com",
                    "parent_id_tag": "PARENT001",
                },
            ]

            # Add each test tag
            for tag_data in test_tags:
                # Check if tag already exists
                stmt = select(IdTag).where(IdTag.tag == tag_data["tag"])
                result = await session.execute(stmt)
                existing_tag = result.scalar_one_or_none()
                # existing_tag = await session.get(IdTag, tag_data["tag"])
                if existing_tag:
                    logger.info(f"Tag {tag_data['tag']} already exists, skipping")
                    continue

                # Create new tag
                new_tag = IdTag(
                    tag=tag_data["tag"],
                    status=tag_data["status"],
                    user_name=tag_data["user_name"],
                    user_email=tag_data["user_email"],
                    expiry_date=tag_data.get("expiry_date"),
                    parent_id_tag=tag_data.get("parent_id_tag"),
                )
                session.add(new_tag)
                logger.info(f"Added test tag: {tag_data['tag']} ({tag_data['status']})")

            await session.commit()
            logger.info("✅ Test ID tags created successfully!")

            # Display summary
            print("\n📋 Test ID Tags Created:")
            print("=" * 50)
            for tag_data in test_tags:
                expiry_str = ""
                if tag_data.get("expiry_date"):
                    if tag_data["expiry_date"] < datetime.utcnow():
                        expiry_str = " (EXPIRED)"
                    else:
                        expiry_str = f" (expires: {tag_data['expiry_date'].strftime('%Y-%m-%d')})"

                parent_str = ""
                if tag_data.get("parent_id_tag"):
                    parent_str = f" (parent: {tag_data['parent_id_tag']})"

                print(
                    f"  {tag_data['tag']}: {tag_data['status']}{expiry_str}{parent_str}"
                )

            return True

    except Exception as e:
        logger.error(f"Failed to create test tags: {e}")
        return False
    finally:
        await close_db()


if __name__ == "__main__":
    success = asyncio.run(setup_test_tags())
    if success:
        print("\n✅ Test ID tags setup completed!")
        print("\nYou can now test authorization with these tags:")
        print("  - VALID001, VALID002: Should be accepted")
        print("  - BLOCKED001: Should be blocked")
        print("  - EXPIRED001: Should be expired")
        print("  - CHILD001: Should be accepted with parent tag")
        print("  - UNKNOWN123: Should be invalid (not in database)")
    else:
        print("\n❌ Failed to setup test ID tags.")
