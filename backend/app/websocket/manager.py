import json
from typing import List, Dict, Any
from fastapi import WebSocket

class WebSocketManager:
    """
    WEBSOCKET MANAGER
    Broadcasts real-time metrics, health states, active alerts, incidents,
    and egress verification events to all connected operator dashboards.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message_type: str, data: Any):
        payload = json.dumps({"type": message_type, "data": data})
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)

        for dead_conn in disconnected:
            self.disconnect(dead_conn)

ws_manager = WebSocketManager()

