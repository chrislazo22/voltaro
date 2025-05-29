"""
Test script to verify MeterValues are properly stored in database.
Run this after sending MeterValues requests from the mock client.
"""

import asyncio
from app.database import AsyncSessionLocal, close_db
from app.models import MeterValue, Session, ChargePoint
from sqlalchemy import select, func
from loguru import logger


async def check_meter_values():
    """Check if MeterValues were stored correctly."""
    try:
        async with AsyncSessionLocal() as session:
            # Query for all meter values
            result = await session.execute(
                select(MeterValue).order_by(MeterValue.created_at.desc())
            )
            meter_values = result.scalars().all()

            if meter_values:
                print("✅ Meter values found in database:")
                print("=" * 80)

                for mv in meter_values:
                    # Get related session if exists
                    related_session = None
                    if mv.session_id:
                        related_session = await session.get(Session, mv.session_id)

                    print(f"Meter Value ID: {mv.id}")
                    print(f"  Timestamp: {mv.timestamp}")
                    print(f"  Value: {mv.value} {mv.unit}")
                    print(f"  Measurand: {mv.measurand}")
                    print(f"  Context: {mv.context}")
                    print(f"  Location: {mv.location}")
                    if mv.phase:
                        print(f"  Phase: {mv.phase}")
                    print(f"  Format: {mv.format}")
                    if related_session:
                        print(f"  Session: Transaction {related_session.transaction_id}")
                    else:
                        print(f"  Session: None (standalone meter value)")
                    print(f"  Created At: {mv.created_at}")
                    print("-" * 40)

                return True
            else:
                print("❌ No meter values found in database")
                return False

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return False
    finally:
        await close_db()


async def get_meter_value_stats():
    """Get statistics about stored meter values."""
    try:
        async with AsyncSessionLocal() as session:
            # Count by measurand
            result = await session.execute(
                select(MeterValue.measurand, func.count(MeterValue.id))
                .group_by(MeterValue.measurand)
            )
            measurand_counts = result.fetchall()

            # Count by unit
            result = await session.execute(
                select(MeterValue.unit, func.count(MeterValue.id))
                .group_by(MeterValue.unit)
            )
            unit_counts = result.fetchall()

            # Count by context
            result = await session.execute(
                select(MeterValue.context, func.count(MeterValue.id))
                .group_by(MeterValue.context)
            )
            context_counts = result.fetchall()

            # Count with/without sessions
            result = await session.execute(
                select(func.count(MeterValue.id)).where(MeterValue.session_id.is_not(None))
            )
            with_session_count = result.scalar()

            result = await session.execute(
                select(func.count(MeterValue.id)).where(MeterValue.session_id.is_(None))
            )
            without_session_count = result.scalar()

            print(f"\n📊 Meter Value Statistics:")
            print("=" * 50)
            
            print(f"\n📏 By Measurand:")
            for measurand, count in measurand_counts:
                print(f"  {measurand}: {count}")

            print(f"\n📐 By Unit:")
            for unit, count in unit_counts:
                print(f"  {unit}: {count}")

            print(f"\n📋 By Context:")
            for context, count in context_counts:
                print(f"  {context}: {count}")

            print(f"\n🔗 Session Association:")
            print(f"  With Session: {with_session_count}")
            print(f"  Without Session: {without_session_count}")

            return {
                'measurand_counts': measurand_counts,
                'unit_counts': unit_counts,
                'context_counts': context_counts,
                'with_session': with_session_count,
                'without_session': without_session_count
            }

    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        return {}
    finally:
        await close_db()


async def check_recent_meter_values():
    """Check the most recent meter values."""
    try:
        async with AsyncSessionLocal() as session:
            # Get the 5 most recent meter values
            result = await session.execute(
                select(MeterValue)
                .order_by(MeterValue.timestamp.desc())
                .limit(5)
            )
            recent_values = result.scalars().all()

            if recent_values:
                print(f"\n🕒 5 Most Recent Meter Values:")
                print("=" * 50)

                for mv in recent_values:
                    print(f"{mv.timestamp}: {mv.value} {mv.unit} ({mv.measurand})")

            return len(recent_values)

    except Exception as e:
        logger.error(f"Recent values query failed: {e}")
        return 0
    finally:
        await close_db()


if __name__ == "__main__":
    print("🔍 Checking MeterValues database storage...\n")

    success = asyncio.run(check_meter_values())
    stats = asyncio.run(get_meter_value_stats())
    recent_count = asyncio.run(check_recent_meter_values())

    if success:
        print(f"\n✅ MeterValues database storage is working correctly!")
        print(f"💡 Found meter values with various measurands and contexts")
    else:
        print(f"\n❌ MeterValues database storage test failed.")
        print(f"💡 Try running the mock client first to send MeterValues") 