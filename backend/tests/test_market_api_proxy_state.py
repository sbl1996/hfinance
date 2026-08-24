import sys
import types

from fastapi.testclient import TestClient

fake_jose = types.ModuleType("jose")
fake_jose.JWTError = Exception
fake_jose.jwt = types.SimpleNamespace(
    decode=lambda token, secret, algorithms=None: {"sub": "admin"},
    encode=lambda payload, secret, algorithm=None: "token",
)
sys.modules.setdefault("jose", fake_jose)

from app.main import app
from app.services.network_proxy_state import get_route_policies


async def _noop_async():
    return None


def _auth_headers(role: str) -> dict[str, str]:
    token = "guest" if role == "guest" else "admin"
    return {"Authorization": f"Bearer {token}"}


def test_get_route_policies_requires_login_and_returns_default(monkeypatch):
        monkeypatch.setattr("app.main.init_database", _noop_async)
        monkeypatch.setattr("app.main.start_scheduler", _noop_async)
        monkeypatch.setattr("app.main.close_db", _noop_async)
        monkeypatch.setattr("app.core.auth.verify_token", lambda token: True)
        monkeypatch.setattr(
            "app.core.auth.jwt.decode",
            lambda token, _secret, algorithms=None: {"sub": "admin" if token == "admin" else "guest"},
        )

        with TestClient(app) as client:
            response = client.get("/api/market/route-policies", headers=_auth_headers("admin"))

        assert response.status_code == 200
        assert response.status_code == 200
        assert response.json()["policies"]["YAHOO"] == "VPN"


def test_guest_cannot_update_route_policies(monkeypatch):
        monkeypatch.setattr("app.main.init_database", _noop_async)
        monkeypatch.setattr("app.main.start_scheduler", _noop_async)
        monkeypatch.setattr("app.main.close_db", _noop_async)
        monkeypatch.setattr("app.core.auth.verify_token", lambda token: True)
        monkeypatch.setattr(
            "app.core.auth.jwt.decode",
            lambda token, _secret, algorithms=None: {"sub": "guest"},
        )

        with TestClient(app) as client:
            response = client.put(
                "/api/market/route-policies",
                json={"policies": {"YAHOO": "DIRECT"}},
                headers=_auth_headers("guest"),
            )

        assert response.status_code == 403
        assert response.status_code == 403


def test_admin_can_update_route_policies(monkeypatch):
        monkeypatch.setattr("app.main.init_database", _noop_async)
        monkeypatch.setattr("app.main.start_scheduler", _noop_async)
        monkeypatch.setattr("app.main.close_db", _noop_async)
        monkeypatch.setattr("app.core.auth.verify_token", lambda token: True)
        monkeypatch.setattr(
            "app.core.auth.jwt.decode",
            lambda token, _secret, algorithms=None: {"sub": "admin"},
        )

        with TestClient(app) as client:
            response = client.put(
                "/api/market/route-policies",
                json={"policies": {"YAHOO": "DIRECT"}},
                headers=_auth_headers("admin"),
            )

        assert response.status_code == 200
        assert response.json()["policies"]["YAHOO"] == "DIRECT"
