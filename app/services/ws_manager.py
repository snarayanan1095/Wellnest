# app/services/ws_manager.py
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List] = {}

    async def connect(self, websocket, household_id: str):
        await websocket.accept()
        if household_id not in self.active_connections:
            self.active_connections[household_id] = []
        self.active_connections[household_id].append(websocket)

    def disconnect(self, websocket, household_id: str):
        if household_id in self.active_connections:
            self.active_connections[household_id].remove(websocket)

    async def send_alert(self, household_id: str, message: dict):
        if household_id not in self.active_connections:
            print(f"⚠️ No active WebSocket connections for household {household_id}")
            return

        if not self.active_connections[household_id]:
            print(f"⚠️ Empty connection list for household {household_id}")
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
