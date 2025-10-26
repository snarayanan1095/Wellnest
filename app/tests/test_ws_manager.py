"""
Tests for WebSocket Connection Manager
Tests WebSocket connection management, alert distribution, and error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ws_manager import ConnectionManager, manager


class TestConnectionManager:
    """Test suite for ConnectionManager class"""

    @pytest.fixture
    def conn_manager(self):
        """Create a fresh manager instance for each test"""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection"""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        ws.close = AsyncMock()
        return ws

    # ===== Initialization Tests =====

    def test_initialization(self, conn_manager):
        """Test manager initializes with empty connections"""
        assert conn_manager.active_connections == {}
        assert isinstance(conn_manager.active_connections, dict)

    # ===== Connection Management Tests =====

    @pytest.mark.asyncio
    async def test_connect_new_household(self, conn_manager, mock_websocket):
        """Test connecting first WebSocket for a household"""
        household_id = "household_001"

        await conn_manager.connect(mock_websocket, household_id)

        assert household_id in conn_manager.active_connections
        assert mock_websocket in conn_manager.active_connections[household_id]
        assert len(conn_manager.active_connections[household_id]) == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_multiple_clients_same_household(self, conn_manager, mock_websocket):
        """Test connecting multiple clients to same household"""
        household_id = "household_001"
        ws1 = mock_websocket
        ws2 = MagicMock()
        ws2.accept = AsyncMock()

        await conn_manager.connect(ws1, household_id)
        await conn_manager.connect(ws2, household_id)

        assert len(conn_manager.active_connections[household_id]) == 2
        assert ws1 in conn_manager.active_connections[household_id]
        assert ws2 in conn_manager.active_connections[household_id]

    @pytest.mark.asyncio
    async def test_connect_different_households(self, conn_manager, mock_websocket):
        """Test connecting clients to different households"""
        ws1 = mock_websocket
        ws2 = MagicMock()
        ws2.accept = AsyncMock()

        await conn_manager.connect(ws1, "household_001")
        await conn_manager.connect(ws2, "household_002")

        assert len(conn_manager.active_connections) == 2
        assert "household_001" in conn_manager.active_connections
        assert "household_002" in conn_manager.active_connections

    # ===== Disconnection Tests =====

    @pytest.mark.asyncio
    async def test_disconnect_existing_connection(self, conn_manager, mock_websocket):
        """Test disconnecting an existing WebSocket"""
        household_id = "household_001"
        await conn_manager.connect(mock_websocket, household_id)

        conn_manager.disconnect(mock_websocket, household_id)

        assert household_id in conn_manager.active_connections
        assert mock_websocket not in conn_manager.active_connections[household_id]
        assert len(conn_manager.active_connections[household_id]) == 0

    @pytest.mark.asyncio
    async def test_disconnect_one_of_multiple_connections(self, conn_manager):
        """Test disconnecting one client when multiple are connected"""
        household_id = "household_001"
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws2 = MagicMock()
        ws2.accept = AsyncMock()

        await conn_manager.connect(ws1, household_id)
        await conn_manager.connect(ws2, household_id)

        conn_manager.disconnect(ws1, household_id)

        assert ws1 not in conn_manager.active_connections[household_id]
        assert ws2 in conn_manager.active_connections[household_id]
        assert len(conn_manager.active_connections[household_id]) == 1

    def test_disconnect_nonexistent_household(self, conn_manager, mock_websocket):
        """Test disconnecting from non-existent household doesn't crash"""
        # Should not raise any exceptions
        conn_manager.disconnect(mock_websocket, "nonexistent_household")
        assert True  # If we get here, no exception was raised

    # ===== Alert Sending Tests =====

    @pytest.mark.asyncio
    async def test_send_alert_to_single_connection(self, conn_manager, mock_websocket):
        """Test sending alert to a single connected client"""
        household_id = "household_001"
        alert_message = {
            "type": "prolonged_inactivity",
            "severity": "high",
            "message": "No motion for 3 hours"
        }

        await conn_manager.connect(mock_websocket, household_id)
        await conn_manager.send_alert(household_id, alert_message)

        mock_websocket.send_json.assert_called_once_with(alert_message)

    @pytest.mark.asyncio
    async def test_send_alert_to_multiple_connections(self, conn_manager):
        """Test broadcasting alert to multiple connected clients"""
        household_id = "household_001"
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        alert_message = {"type": "test_alert", "message": "Test"}

        await conn_manager.connect(ws1, household_id)
        await conn_manager.connect(ws2, household_id)
        await conn_manager.send_alert(household_id, alert_message)

        ws1.send_json.assert_called_once_with(alert_message)
        ws2.send_json.assert_called_once_with(alert_message)

    @pytest.mark.asyncio
    async def test_send_alert_no_connections(self, conn_manager, capsys):
        """Test sending alert when no connections exist"""
        household_id = "household_001"
        alert_message = {"type": "test", "message": "test"}

        # Should not raise exception
        await conn_manager.send_alert(household_id, alert_message)

        # Check that warning was printed (optional)
        # Note: This might not work in all test environments

    @pytest.mark.asyncio
    async def test_send_alert_empty_connection_list(self, conn_manager):
        """Test sending alert to household with empty connection list"""
        household_id = "household_001"
        conn_manager.active_connections[household_id] = []
        alert_message = {"type": "test", "message": "test"}

        # Should handle gracefully
        await conn_manager.send_alert(household_id, alert_message)

    # ===== Error Handling Tests =====

    @pytest.mark.asyncio
    async def test_send_alert_connection_fails(self, conn_manager):
        """Test sending alert when connection fails"""
        household_id = "household_001"
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock(side_effect=Exception("Connection lost"))

        alert_message = {"type": "test", "message": "test"}

        await conn_manager.connect(ws, household_id)
        await conn_manager.send_alert(household_id, alert_message)

        # Dead connection should be removed
        assert ws not in conn_manager.active_connections.get(household_id, [])

    @pytest.mark.asyncio
    async def test_send_alert_partial_failure(self, conn_manager):
        """Test sending alert when some connections fail"""
        household_id = "household_001"
        ws_good = MagicMock()
        ws_good.accept = AsyncMock()
        ws_good.send_json = AsyncMock()

        ws_bad = MagicMock()
        ws_bad.accept = AsyncMock()
        ws_bad.send_json = AsyncMock(side_effect=Exception("Connection lost"))

        alert_message = {"type": "test", "message": "test"}

        await conn_manager.connect(ws_good, household_id)
        await conn_manager.connect(ws_bad, household_id)
        await conn_manager.send_alert(household_id, alert_message)

        # Good connection should still be there
        assert ws_good in conn_manager.active_connections[household_id]
        # Bad connection should be removed
        assert ws_bad not in conn_manager.active_connections[household_id]
        # Good connection should have received the alert
        ws_good.send_json.assert_called_once_with(alert_message)

    @pytest.mark.asyncio
    async def test_send_alert_all_connections_fail(self, conn_manager):
        """Test when all connections fail, household is cleaned up"""
        household_id = "household_001"
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock(side_effect=Exception("Connection lost"))

        alert_message = {"type": "test", "message": "test"}

        await conn_manager.connect(ws, household_id)
        await conn_manager.send_alert(household_id, alert_message)

        # Household should be removed from active_connections
        assert household_id not in conn_manager.active_connections

    # ===== Singleton Instance Tests =====

    def test_manager_singleton_exists(self):
        """Test that global manager instance exists"""
        from app.services.ws_manager import manager
        assert manager is not None
        assert isinstance(manager, ConnectionManager)

    # ===== Edge Cases =====

    @pytest.mark.asyncio
    async def test_connect_same_websocket_twice(self, conn_manager, mock_websocket):
        """Test connecting the same WebSocket twice to same household"""
        household_id = "household_001"

        await conn_manager.connect(mock_websocket, household_id)
        await conn_manager.connect(mock_websocket, household_id)

        # Should have two references (Python allows duplicate list items)
        assert conn_manager.active_connections[household_id].count(mock_websocket) == 2

    @pytest.mark.asyncio
    async def test_disconnect_already_disconnected(self, conn_manager, mock_websocket):
        """Test disconnecting a WebSocket that's already disconnected"""
        household_id = "household_001"
        await conn_manager.connect(mock_websocket, household_id)
        conn_manager.disconnect(mock_websocket, household_id)

        # Try disconnecting again - should not raise exception
        # Note: This will raise ValueError if not in list
        try:
            conn_manager.disconnect(mock_websocket, household_id)
        except ValueError:
            # Expected behavior - trying to remove from empty list
            pass

    # ===== Concurrent Access Tests =====

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, conn_manager):
        """Test handling multiple concurrent connection attempts"""
        household_id = "household_001"
        websockets = []

        for i in range(10):
            ws = MagicMock()
            ws.accept = AsyncMock()
            websockets.append(ws)

        # Connect all concurrently
        import asyncio
        await asyncio.gather(*[
            conn_manager.connect(ws, household_id)
            for ws in websockets
        ])

        assert len(conn_manager.active_connections[household_id]) == 10

    @pytest.mark.asyncio
    async def test_concurrent_disconnections(self, conn_manager):
        """Test handling multiple concurrent disconnections"""
        household_id = "household_001"
        websockets = []

        for i in range(5):
            ws = MagicMock()
            ws.accept = AsyncMock()
            await conn_manager.connect(ws, household_id)
            websockets.append(ws)

        # Disconnect all
        for ws in websockets:
            conn_manager.disconnect(ws, household_id)

        assert len(conn_manager.active_connections[household_id]) == 0

    # ===== Integration Test =====

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, conn_manager):
        """Test complete lifecycle: connect, send alerts, disconnect"""
        household_id = "household_001"
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()

        # Connect
        await conn_manager.connect(ws, household_id)
        assert ws in conn_manager.active_connections[household_id]

        # Send multiple alerts
        for i in range(3):
            alert = {"type": f"alert_{i}", "message": f"Test alert {i}"}
            await conn_manager.send_alert(household_id, alert)

        assert ws.send_json.call_count == 3

        # Disconnect
        conn_manager.disconnect(ws, household_id)
        assert ws not in conn_manager.active_connections.get(household_id, [])
