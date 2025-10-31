# app/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from app.services.ws_manager import manager

router = APIRouter()

@router.websocket("/ws/alerts/{household_id}")
async def websocket_alerts(websocket: WebSocket, household_id: str):
    # Accept the WebSocket connection without Origin validation
    await websocket.accept()
    manager.add_connection(websocket, household_id)
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

@router.websocket("/ws/events/{household_id}")
async def websocket_events(websocket: WebSocket, household_id: str):
    """WebSocket endpoint for real-time event streaming per household"""
    print(f"🔌 WebSocket connection request for household {household_id}")

    # Accept the WebSocket connection without Origin validation
    await websocket.accept()
    print(f"✅ WebSocket accepted for household {household_id}")

    # Add connection and send initial state
    print(f"📨 Calling add_connection_with_state for {household_id}...")
    await manager.add_connection_with_state(websocket, household_id)
    print(f"✓ WebSocket events client connected for household {household_id}")

    try:
        while True:
            # Keep connection alive by receiving heartbeat/ping messages
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, household_id)
        print(f"✓ WebSocket events client disconnected from household {household_id}")
    except Exception as e:
        print(f"❌ WebSocket events error for household {household_id}: {e}")
        manager.disconnect(websocket, household_id)
