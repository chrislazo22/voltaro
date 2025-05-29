"""
Test ChangeAvailability OCPP 1.6 functionality.

Tests the implementation of OCPP 1.6 Section 5.2 Change Availability
with MVP constraints (single ChargePoint with single Connector).
"""

import asyncio
import pytest
from tests.mock_client import MockClient
from app.central_system import CentralSystem
from app.database import AsyncSessionLocal
from app.models import ChargePoint, Session, ConnectorStatus
from sqlalchemy import select
from app.utils import utc_now_naive


async def test_change_availability_basic():
    """Test basic ChangeAvailability functionality."""
    print("\n🧪 Testing ChangeAvailability - Basic Functionality")
    print("=" * 60)

    # Start mock client
    mock_client = MockClient("TEST_CP_001")
    print("📱 Starting mock charge point...")

    try:
        # Connect charge point
        await mock_client.start()
        await asyncio.sleep(2)  # Let boot complete

        print("✅ Mock charge point connected and booted")

        # Test 1: Change connector 1 to Inoperative
        print("\n📋 Test 1: Change connector 1 to Inoperative")
        central_system = CentralSystem()
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_001",
            connector_id=1,
            availability_type="Inoperative"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Accepted", f"Expected Accepted, got {result['status']}"
        print("   ✅ Connector 1 set to Inoperative")

        # Wait for StatusNotification
        await asyncio.sleep(2)

        # Test 2: Change connector 1 to Operative
        print("\n📋 Test 2: Change connector 1 to Operative")
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_001", 
            connector_id=1,
            availability_type="Operative"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Accepted", f"Expected Accepted, got {result['status']}"
        print("   ✅ Connector 1 set to Operative")

        # Wait for StatusNotification
        await asyncio.sleep(2)

        # Test 3: Change entire ChargePoint (connector_id = 0) to Inoperative
        print("\n📋 Test 3: Change ChargePoint (connector_id=0) to Inoperative")
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_001",
            connector_id=0,
            availability_type="Inoperative"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Accepted", f"Expected Accepted, got {result['status']}"
        print("   ✅ ChargePoint set to Inoperative (affects all connectors)")

        await asyncio.sleep(2)

        print("\n🎉 Basic ChangeAvailability tests passed!")

    finally:
        await mock_client.stop()
        print("🔌 Mock charge point disconnected")


async def test_change_availability_with_transaction():
    """Test ChangeAvailability when transaction is in progress."""
    print("\n🧪 Testing ChangeAvailability - With Active Transaction")
    print("=" * 60)

    mock_client = MockClient("TEST_CP_002")
    print("📱 Starting mock charge point...")

    try:
        # Connect and boot
        await mock_client.start()
        await asyncio.sleep(2)

        print("✅ Mock charge point connected")

        # Start a transaction
        print("\n📋 Step 1: Start a transaction")
        start_result = await CentralSystem.remote_start_transaction(
            charge_point_id="TEST_CP_002",
            id_tag="VALID001",
            connector_id=1
        )

        print(f"   RemoteStartTransaction: {start_result['status']}")
        assert start_result["success"], "Failed to start transaction"

        # Wait for transaction to establish
        await asyncio.sleep(3)

        # Try to change availability while transaction is active
        print("\n📋 Step 2: Try to change availability during transaction")
        central_system = CentralSystem()
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_002",
            connector_id=1,
            availability_type="Inoperative"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Scheduled", f"Expected Scheduled, got {result['status']}"
        print("   ✅ ChangeAvailability correctly scheduled (transaction in progress)")

        # Try changing the entire ChargePoint (connector_id = 0) during transaction
        print("\n📋 Step 3: Try to change ChargePoint availability during transaction")
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_002",
            connector_id=0,
            availability_type="Inoperative"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Scheduled", f"Expected Scheduled, got {result['status']}"
        print("   ✅ ChargePoint ChangeAvailability correctly scheduled")

        print("\n🎉 Transaction-based ChangeAvailability tests passed!")

    finally:
        await mock_client.stop()
        print("🔌 Mock charge point disconnected")


async def test_change_availability_invalid_inputs():
    """Test ChangeAvailability with invalid inputs."""
    print("\n🧪 Testing ChangeAvailability - Invalid Inputs")
    print("=" * 60)

    mock_client = MockClient("TEST_CP_003")
    print("📱 Starting mock charge point...")

    try:
        await mock_client.start()
        await asyncio.sleep(2)

        print("✅ Mock charge point connected")

        # Test 1: Invalid connector_id (MVP only supports 0 and 1)
        print("\n📋 Test 1: Invalid connector_id")
        central_system = CentralSystem()
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_003",
            connector_id=2,  # Invalid for MVP
            availability_type="Operative"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Rejected", f"Expected Rejected, got {result['status']}"
        print("   ✅ Invalid connector_id correctly rejected")

        # Test 2: Invalid availability type
        print("\n📋 Test 2: Invalid availability type")
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_003",
            connector_id=1,
            availability_type="InvalidType"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Rejected", f"Expected Rejected, got {result['status']}"
        print("   ✅ Invalid availability type correctly rejected")

        # Test 3: Negative connector_id
        print("\n📋 Test 3: Negative connector_id")
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_003",
            connector_id=-1,
            availability_type="Operative"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Rejected", f"Expected Rejected, got {result['status']}"
        print("   ✅ Negative connector_id correctly rejected")

        print("\n🎉 Invalid input tests passed!")

    finally:
        await mock_client.stop()
        print("🔌 Mock charge point disconnected")


async def test_change_availability_already_in_state():
    """Test ChangeAvailability when already in requested state."""
    print("\n🧪 Testing ChangeAvailability - Already in State")
    print("=" * 60)

    mock_client = MockClient("TEST_CP_004")
    print("📱 Starting mock charge point...")

    try:
        await mock_client.start()
        await asyncio.sleep(2)

        print("✅ Mock charge point connected")

        # First, set to Inoperative
        print("\n📋 Step 1: Set connector to Inoperative")
        central_system = CentralSystem()
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_004",
            connector_id=1,
            availability_type="Inoperative"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Accepted"
        await asyncio.sleep(2)

        # Try to set to Inoperative again (already in this state)
        print("\n📋 Step 2: Try to set to Inoperative again")
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_004",
            connector_id=1,
            availability_type="Inoperative"
        )

        print(f"   Response: {result}")
        assert result["status"] == "Accepted", f"Expected Accepted, got {result['status']}"
        print("   ✅ Already in state correctly returned Accepted")

        print("\n🎉 Already-in-state tests passed!")

    finally:
        await mock_client.stop()
        print("🔌 Mock charge point disconnected")


async def test_change_availability_database_persistence():
    """Test that availability changes persist in database."""
    print("\n🧪 Testing ChangeAvailability - Database Persistence")
    print("=" * 60)

    mock_client = MockClient("TEST_CP_005")
    print("📱 Starting mock charge point...")

    try:
        await mock_client.start()
        await asyncio.sleep(2)

        print("✅ Mock charge point connected")

        # Change to Inoperative
        print("\n📋 Step 1: Change connector to Inoperative")
        central_system = CentralSystem()
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_005",
            connector_id=1,
            availability_type="Inoperative"
        )

        assert result["status"] == "Accepted"
        await asyncio.sleep(1)

        # Check database
        print("\n📋 Step 2: Verify database persistence")
        async with AsyncSessionLocal() as session:
            # Get latest ConnectorStatus for this connector
            status_result = await session.execute(
                select(ConnectorStatus)
                .where(ConnectorStatus.charge_point_id == "TEST_CP_005")
                .where(ConnectorStatus.connector_id == 1)
                .order_by(ConnectorStatus.created_at.desc())
                .limit(1)
            )
            latest_status = status_result.scalar_one_or_none()

            assert latest_status is not None, "No ConnectorStatus record found"
            assert latest_status.availability == "Inoperative", f"Expected Inoperative, got {latest_status.availability}"
            print(f"   ✅ Database shows availability: {latest_status.availability}")

        # Change back to Operative and verify
        print("\n📋 Step 3: Change back to Operative")
        result = await central_system.change_availability(
            charge_point_id="TEST_CP_005",
            connector_id=1,
            availability_type="Operative"
        )

        assert result["status"] == "Accepted"
        await asyncio.sleep(1)

        async with AsyncSessionLocal() as session:
            status_result = await session.execute(
                select(ConnectorStatus)
                .where(ConnectorStatus.charge_point_id == "TEST_CP_005")
                .where(ConnectorStatus.connector_id == 1)
                .order_by(ConnectorStatus.created_at.desc())
                .limit(1)
            )
            latest_status = status_result.scalar_one_or_none()

            assert latest_status.availability == "Operative", f"Expected Operative, got {latest_status.availability}"
            print(f"   ✅ Database shows availability: {latest_status.availability}")

        print("\n🎉 Database persistence tests passed!")

    finally:
        await mock_client.stop()
        print("🔌 Mock charge point disconnected")


async def run_all_tests():
    """Run all ChangeAvailability tests."""
    print("🚀 Starting ChangeAvailability Test Suite")
    print("=" * 80)

    tests = [
        test_change_availability_basic,
        test_change_availability_with_transaction,
        test_change_availability_invalid_inputs,
        test_change_availability_already_in_state,
        test_change_availability_database_persistence,
    ]

    for i, test in enumerate(tests, 1):
        print(f"\n📋 Running test {i}/{len(tests)}: {test.__name__}")
        try:
            await test()
            print(f"✅ Test {i} passed: {test.__name__}")
        except Exception as e:
            print(f"❌ Test {i} failed: {test.__name__}")
            print(f"   Error: {e}")
            raise

    print("\n🎉 All ChangeAvailability tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests()) 