import pytest
from unittest.mock import AsyncMock, MagicMock
from app.websocket import ConnectionManager


def test_connection_manager_connect_disconnect():
    manager = ConnectionManager()
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()

    import asyncio
    asyncio.get_event_loop().run_until_complete(manager.connect(mock_ws))
    assert len(manager.active_connections) == 1

    manager.disconnect(mock_ws)
    assert len(manager.active_connections) == 0
