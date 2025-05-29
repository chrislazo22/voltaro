#!/usr/bin/env python3
"""
Quick test for ID tag validation.
"""
import sys
import os
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.central_system import CentralSystem


async def test_id_validation():
    """Test ID tag validation."""
    print("🏷️  Testing ID Tag Validation")
    print("=" * 30)

    test_tags = ["VALID001", "VALID002", "BLOCKED001", "EXPIRED001", "INVALID999"]

    for tag in test_tags:
        result = await CentralSystem.validate_id_tag(tag)
        status = result.get("status", "Unknown")
        reason = result.get("reason", "")
        print(f"  {tag}: {status} - {reason}")


if __name__ == "__main__":
    asyncio.run(test_id_validation())

