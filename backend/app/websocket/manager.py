import json
from typing import Dict, Any, Optional
from fastapi import WebSocket


class WebSocketManager:
    """Tenant- and organization-scoped real-time event broadcaster."""

    def __init__(self):
        self.active_connections: Dict[WebSocket, Dict[str, Optional[str]]] = {}

    async def register(self, websocket: WebSocket, tenant_id: str, organization_id: Optional[str] = None):
        self.active_connections[websocket] = {
            "tenant_id": str(tenant_id),
            "organization_id": str(organization_id) if organization_id else None,
        }

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

    def _matching_connections(self, tenant_id=None, organization_id=None):
        if tenant_id is None and organization_id is None:
            # Fail closed: unscoped events must never be broadcast to all tenants.
            return []
        targets = []
        for connection, scope in list(self.active_connections.items()):
            matches = True
            if tenant_id is not None:
                matches = matches and scope["tenant_id"] == str(tenant_id)
            if organization_id is not None:
                matches = matches and scope["organization_id"] == str(organization_id)
            if matches:
                targets.append(connection)
        return targets

    async def _send(self, payload: str, tenant_id=None, organization_id=None):
        disconnected = []
        for connection in self._matching_connections(tenant_id, organization_id):
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast(self, message_type, data=None, tenant_id=None, organization_id=None):
        if isinstance(message_type, dict) and data is None:
            event = message_type
            tenant_id = tenant_id or event.get("tenant_id") or event.get("data", {}).get("tenant_id")
            organization_id = organization_id or event.get("organization_id") or event.get("data", {}).get("organization_id")
        else:
            event = {"type": message_type, "data": data}
        await self._send(json.dumps(event), tenant_id, organization_id)

    async def broadcast_json(self, data: Dict[str, Any], tenant_id=None, organization_id=None):
        tenant_id = tenant_id or data.get("tenant_id")
        organization_id = organization_id or data.get("organization_id")
        await self._send(json.dumps(data), tenant_id, organization_id)


ws_manager = WebSocketManager()
