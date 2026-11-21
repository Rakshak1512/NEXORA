from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.websocket.manager import ws_manager
from auth_helpers import login_as_platform_admin


def test_websocket_rejects_missing_authentication(client):
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "AUTH", "token": "not-a-valid-token"})
        try:
            websocket.receive_json()
            assert False, "Unauthenticated websocket should be closed"
        except WebSocketDisconnect as exc:
            assert exc.code in (4401, 4403)


def test_websocket_accepts_valid_user_token_and_registers_tenant_scope(client):
    token = login_as_platform_admin(client)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "AUTH", "token": token})
        assert websocket.receive_json() == {"type": "AUTHENTICATED"}
        scopes = list(ws_manager.active_connections.values())
        assert scopes
        assert scopes[-1]["tenant_id"]
