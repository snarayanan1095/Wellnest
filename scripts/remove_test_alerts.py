#!/usr/bin/env python3
"""
Script to remove test alerts from MongoDB
"""
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.mongo import MongoDB

async def remove_test_alerts():
    """Remove all test alerts from the database"""
    try:
        # Connect to MongoDB
        await MongoDB.connect()

        # Delete all test alerts
        db = MongoDB.client[MongoDB._db_name]
        collection = db["alerts"]

        # Find test alerts before deleting (for logging)
        test_alerts = await collection.find({"type": "test_alert"}).to_list(None)

        if test_alerts:
            print(f"Found {len(test_alerts)} test alert(s) to remove:")
            for alert in test_alerts:
                print(f"  - {alert.get('_id')} from {alert.get('household_id')}")

            # Delete all test alerts
            result = await collection.delete_many({"type": "test_alert"})
            print(f"✓ Deleted {result.deleted_count} test alert(s)")
        else:
            print("No test alerts found in database")

        # Also check for alerts with "test" in the message
        test_message_alerts = await collection.find(
            {"message": {"$regex": "test", "$options": "i"}}
        ).to_list(None)

        if test_message_alerts:
            print(f"\nFound {len(test_message_alerts)} alert(s) with 'test' in message:")
            for alert in test_message_alerts:
                print(f"  - {alert.get('_id')}: {alert.get('message')[:50]}")

            # Ask for confirmation before deleting these
            result = await collection.delete_many(
                {"message": {"$regex": "test alert", "$options": "i"}}
            )
            print(f"✓ Deleted {result.deleted_count} alert(s) with 'test alert' in message")

        print("\n✓ Cleanup complete")

    except Exception as e:
        print(f"Error removing test alerts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(remove_test_alerts())