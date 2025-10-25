# app/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ws_manager import manager

router = APIRouter()

@router.websocket("/ws/alerts/{household_id}")
async def websocket_alerts(websocket: WebSocket, household_id: str):
    await manager.connect(websocket, household_id)
    print(f"✓ WebSocket client connected for household {household_id}")
    try:
        while True:
            # Keep connection alive by receiving heartbeat/ping messages
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, household_id)
        print(f"✓ WebSocket client disconnected from household {household_id}")
    except Exception as e:
        print(f"❌ WebSocket error for household {household_id}: {e}")
        manager.disconnect(websocket, household_id)
