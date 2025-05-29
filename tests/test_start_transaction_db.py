#!/usr/bin/env python3
"""
Test script to verify StartTransaction sessions are properly stored in database.
Run this after sending StartTransaction requests from the mock client.
"""

import sys
import os
# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from app.database import AsyncSessionLocal, close_db
from app.models import Session, ChargePoint, IdTag
from sqlalchemy import select, desc
from loguru import logger


async def check_sessions():
    """Check if StartTransaction sessions were created correctly."""
    try:
        async with AsyncSessionLocal() as session:
            # Query for all sessions
            result = await session.execute(
                select(Session)
                .join(ChargePoint)
                .join(IdTag)
                .order_by(Session.created_at.desc())
            )
            sessions = result.scalars().all()

            if sessions:
                print("✅ Sessions found in database:")
                print("=" * 80)

                for sess in sessions:
                    # Get related charge point and ID tag
                    charge_point = await session.get(ChargePoint, sess.charge_point_id)
                    id_tag = await session.get(IdTag, sess.id_tag_id)

                    print(f"Session ID: {sess.id}")
                    print(f"  Transaction ID: {sess.transaction_id}")
                    print(
                        f"  Charge Point: {charge_point.id if charge_point else 'Unknown'}"
                    )
                    print(f"  ID Tag: {id_tag.tag if id_tag else 'Unknown'}")
                    print(f"  Connector: {sess.connector_id}")
                    print(f"  Meter Start: {sess.meter_start} Wh")
                    print(f"  Start Time: {sess.start_timestamp}")
                    print(f"  Status: {sess.status}")
                    if sess.reservation_id:
                        print(f"  Reservation ID: {sess.reservation_id}")
                    print(f"  Created At: {sess.created_at}")
                    print("-" * 40)

                return True
            else:
                print("❌ No sessions found in database")
                return False

    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return False
    finally:
        await close_db()


async def check_active_sessions():
    """Check for currently active sessions."""
    try:
        async with AsyncSessionLocal() as session:
            # Query for active sessions only
            result = await session.execute(
                select(Session)
                .join(ChargePoint)
                .join(IdTag)
                .where(Session.status == "Active")
                .order_by(Session.start_timestamp.desc())
            )
            active_sessions = result.scalars().all()

            if active_sessions:
                print(f"\n🔋 {len(active_sessions)} Active Sessions:")
                print("=" * 50)

                for sess in active_sessions:
                    charge_point = await session.get(ChargePoint, sess.charge_point_id)
                    id_tag = await session.get(IdTag, sess.id_tag_id)

                    print(
                        f"Transaction {sess.transaction_id}: {charge_point.id} connector {sess.connector_id}"
                    )
                    print(f"  Tag: {id_tag.tag} | Started: {sess.start_timestamp}")
                    print(f"  Meter Start: {sess.meter_start} Wh")

                return len(active_sessions)
            else:
                print("\n📴 No active sessions found")
                return 0

    except Exception as e:
        logger.error(f"Active sessions query failed: {e}")
        return 0
    finally:
        await close_db()


async def get_session_stats():
    """Get session statistics."""
    try:
        async with AsyncSessionLocal() as session:
            # Count sessions by status
            result = await session.execute(
                select(Session.status, Session.id).group_by(Session.status, Session.id)
            )
            all_sessions = result.fetchall()

            stats = {}
            for sess_status, sess_id in all_sessions:
                stats[sess_status] = stats.get(sess_status, 0) + 1

            if stats:
                print(f"\n📊 Session Statistics:")
                print("=" * 30)
                for status, count in stats.items():
                    print(f"  {status}: {count}")

            return stats

    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        return {}
    finally:
        await close_db()


if __name__ == "__main__":
    print("🔍 Checking StartTransaction database storage...\n")

    success = asyncio.run(check_sessions())
    active_count = asyncio.run(check_active_sessions())
    stats = asyncio.run(get_session_stats())

    if success:
        print(f"\n✅ StartTransaction database storage is working correctly!")
        if active_count > 0:
            print(f"💡 You have {active_count} active charging sessions")
    else:
        print(f"\n❌ StartTransaction database storage test failed.")

