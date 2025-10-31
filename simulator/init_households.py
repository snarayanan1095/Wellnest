"""
One-time script to initialize households collection from households.json
Run this once to populate the households collection in MongoDB
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.mongo import MongoDB


async def init_households():
    """Initialize households collection from households.json"""

    # Read households.json
    households_file = Path(__file__).parent / "households.json"
    with open(households_file, 'r') as f:
        households_data = json.load(f)

    print(f"📋 Found {len(households_data)} households in households.json")

    # Connect to MongoDB
    await MongoDB.connect()

    # Insert households using MongoDB.write
    inserted_count = 0
    for household_id, data in households_data.items():
        # Extract unique residents from events
        residents = []
        seen_residents = set()

        for event in data.get("events", []):
            resident_name = event.get("resident")
            if resident_name and resident_name not in seen_residents:
                residents.append({
                    "id": f"{household_id}_{resident_name}",
                    "name": resident_name.capitalize(),
                    "age": 75  # Default age, can be updated later
                })
                seen_residents.add(resident_name)

        # If no residents found, create a generic one
        if not residents:
            residents.append({
                "id": f"{household_id}_resident",
                "name": "Resident",
                "age": 75
            })

        household_doc = {
            "_id": household_id,
            "name": data["name"],
            "residents": residents,
            "sensors": data.get("events", []),  # Store sensor configuration
            "status": "active",  # Will be updated to 'inactive' by anomaly detector if no activity
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        try:
            await MongoDB.write("households", household_doc)
            print(f"   ✓ {household_id}: {data['name']} ({len(residents)} residents)")
            inserted_count += 1
        except Exception as e:
            print(f"   ✗ Failed to insert {household_id}: {e}")

    print(f"\n✅ Inserted {inserted_count} households successfully!")

    print("\n📊 Households collection initialized successfully!")
    print(f"   Collection: households")
    print(f"   Documents: {inserted_count}")

    # Close connection
    await MongoDB.close()


if __name__ == "__main__":
    print("="*60)
    print("🏠 Wellnest Household Initialization")
    print("="*60)
    print("This script will create a 'households' collection in MongoDB")
    print("from the households.json configuration file.")
    print("="*60 + "\n")

    asyncio.run(init_households())

    print("\n" + "="*60)
    print("✨ Done! You can now use the households collection in your API.")
    print("="*60)
