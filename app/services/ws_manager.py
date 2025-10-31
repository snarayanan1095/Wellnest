# app/services/ws_manager.py
from typing import Dict, List, Optional
import json
from datetime import datetime
import asyncio
from app.db.mongo import MongoDB

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List] = {}
        # MongoDB will be used for persistent cache instead of in-memory

    async def connect(self, websocket, household_id: str):
        await websocket.accept()
        if household_id not in self.active_connections:
            self.active_connections[household_id] = []
        self.active_connections[household_id].append(websocket)

    async def add_connection_with_state(self, websocket, household_id: str):
        """Add an already-accepted WebSocket connection and send initial state"""
        print(f"📤 Starting add_connection_with_state for {household_id}")

        if household_id not in self.active_connections:
            self.active_connections[household_id] = []
        self.active_connections[household_id].append(websocket)
        print(f"📝 Added connection to list for {household_id}, total: {len(self.active_connections[household_id])}")

        # Fetch cached resident locations from MongoDB
        residents_data = {}
        timestamps = {}

        try:
            # Get all resident locations for this household from MongoDB
            locations = await MongoDB.read(
                "resident_locations",
                query={"household_id": household_id},
                sort=[("last_active", -1)]  # Most recent first
            )

            # Group by resident (in case of duplicates, use most recent)
            seen_residents = set()
            for loc in locations:
                resident = loc.get("resident")
                if resident and resident not in seen_residents:
                    residents_data[resident] = loc.get("location", "Unknown")
                    timestamps[resident] = loc.get("last_active")
                    seen_residents.add(resident)

            print(f"🔍 MongoDB cache check for {household_id}: {len(residents_data)} residents")

        except Exception as e:
            print(f"⚠️ Error fetching cached locations from MongoDB: {e}")
            # Fall back to empty state if MongoDB query fails
            pass

        initial_state = {
            "type": "initial_state",
            "residents": residents_data,
            "timestamps": timestamps
        }

        try:
            print(f"📨 Attempting to send initial state to {household_id}...")
            await websocket.send_json(initial_state)
            if residents_data:
                print(f"✓ Sent initial state to household {household_id}: {len(residents_data)} residents with timestamps")
                # Debug: Show what we're actually sending
                for resident, location in residents_data.items():
                    ts = timestamps.get(resident, "no timestamp")
                    print(f"  - {resident}: {location} (ts: {ts})")
            else:
                print(f"✓ Sent empty initial state to household {household_id} (no cached data yet)")
        except Exception as e:
            print(f"❌ Failed to send initial state for {household_id}: {e}")
            import traceback
            traceback.print_exc()

    def add_connection(self, websocket, household_id: str):
        """Add an already-accepted WebSocket connection"""
        if household_id not in self.active_connections:
            self.active_connections[household_id] = []
        self.active_connections[household_id].append(websocket)

    async def update_resident_location(self, household_id: str, resident: str, location: str):
        """Update the cached location and timestamp for a resident in MongoDB"""
        try:
            timestamp = datetime.utcnow()

            # Upsert the resident location document
            document = {
                "_id": f"{household_id}_{resident}",  # Unique ID per household-resident combo
                "household_id": household_id,
                "resident": resident,
                "location": location,
                "last_active": timestamp.isoformat(),
                "updated_at": timestamp.isoformat()
            }

            # First try to update, if no document exists, insert it
            result = await MongoDB.update(
                "resident_locations",
                {"_id": document["_id"]},
                {"$set": document}
            )

            # If no document was modified, insert a new one
            if result == 0:
                await MongoDB.write("resident_locations", document)

            print(f"📍 MongoDB cache updated: {household_id}/{resident} -> {location} at {timestamp.strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"❌ Failed to update MongoDB cache: {e}")

    def disconnect(self, websocket, household_id: str):
        if household_id in self.active_connections:
            try:
                self.active_connections[household_id].remove(websocket)
                # Clean up empty connection lists immediately
                if not self.active_connections[household_id]:
                    del self.active_connections[household_id]
                    print(f"🧹 Cleaned up connection list for household {household_id}")
            except ValueError:
                # Connection wasn't in the list
                pass

    async def send_alert(self, household_id: str, message: dict):
        # Check if there are any active connections for this household
        if household_id not in self.active_connections or not self.active_connections[household_id]:
            # Only print warning occasionally to avoid log spam
            if not hasattr(self, '_warning_count'):
                self._warning_count = {}
            if household_id not in self._warning_count:
                self._warning_count[household_id] = 0
            self._warning_count[household_id] += 1

            # Only warn every 10th attempt to reduce log noise
            if self._warning_count[household_id] % 10 == 1:
                print(f"⚠️ No active WebSocket connections for household {household_id} (suppressing further warnings)")
            return

        dead_connections = []
        for connection in self.active_connections[household_id]:
            try:
                await connection.send_json(message)
                print(f"✓ Alert sent via WebSocket to household {household_id}")
            except Exception as e:
                print(f"❌ Failed to send alert via WebSocket to household {household_id}: {e}")
                dead_connections.append(connection)

        # Clean up dead connections
        for conn in dead_connections:
            try:
                self.active_connections[household_id].remove(conn)
                print(f"🧹 Removed dead WebSocket connection for household {household_id}")
            except ValueError:
                # Connection already removed
                pass

        # Clean up empty connection lists
        if household_id in self.active_connections and not self.active_connections[household_id]:
            del self.active_connections[household_id]
            print(f"🧹 Cleaned up empty connection list for household {household_id}")

manager = ConnectionManager()
