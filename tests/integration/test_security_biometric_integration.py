"""
Integration tests against a real MongoDB (and Redis for auth cache).

Set CBT_INTEGRATION_MONGO_URL before pytest (e.g. mongodb://localhost:27017).
DATABASE_URL is derived from that in tests/conftest.py before the app is imported.
"""

from __future__ import annotations

import os
import uuid

import pytest
from starlette.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def require_integration_mongo():
    if not os.environ.get("CBT_INTEGRATION_MONGO_URL"):
        pytest.skip("Set CBT_INTEGRATION_MONGO_URL to run integration tests")


@pytest.fixture(scope="module")
def integration_client(require_integration_mongo):
    from src.cbt.main import app

    with TestClient(app) as client:
        yield client


def _register_admin(integration_client: TestClient) -> tuple[str, str]:
    """Create an ADMINISTRATOR user via open registration + user-create API."""
    suffix = uuid.uuid4().hex[:8]
    gate_username = f"gate_{suffix}"
    gate_password = "GatePass1!"
    gate_email = f"gate_{suffix}@test.local"

    resp = integration_client.post(
        "/api/v1/auth/register",
        json={
            "username": gate_username,
            "email": gate_email,
            "password": gate_password,
            "confirm_password": gate_password,
            "first_name": "Gate",
            "last_name": "User",
        },
    )
    assert resp.status_code == 200, resp.text

    login = integration_client.post(
        "/api/v1/auth/login",
        json={
            "username": gate_username,
            "password": gate_password,
            "require_biometric": False,
        },
    )
    assert login.status_code == 200, login.text
    gate_token = login.json()["access_token"]

    admin_username = f"adm_{suffix}"
    admin_password = "AdminPass1!"
    admin_email = f"adm_{suffix}@test.local"
    cr = integration_client.post(
        "/api/v1/users/",
        json={
            "username": admin_username,
            "email": admin_email,
            "password": admin_password,
            "first_name": "Int",
            "last_name": "Admin",
            "role": "ADMINISTRATOR",
        },
        headers={"Authorization": f"Bearer {gate_token}"},
    )
    assert cr.status_code == 201, cr.text

    return admin_username, admin_password


def _login(integration_client: TestClient, username: str, password: str) -> str:
    r = integration_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password, "require_biometric": False},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_sast_scan_persists_and_security_endpoints(
    require_integration_mongo, integration_client: TestClient
):
    username, password = _register_admin(integration_client)
    token = _login(integration_client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    r = integration_client.post(
        "/api/v1/security/sast/scan",
        json={"scan_type": "quick"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("scan_id")
    assert body["scan_id"] != "pending"
    scan_id = body["scan_id"]
    assert body.get("vulnerabilities_found", 0) >= 1

    r2 = integration_client.get("/api/v1/security/scans", headers=headers)
    assert r2.status_code == 200, r2.text
    payload = r2.json()
    scans = payload.get("scans", [])
    assert isinstance(scans, list)
    assert any(s.get("id") == scan_id for s in scans)

    r3 = integration_client.get(f"/api/v1/security/scan/{scan_id}", headers=headers)
    assert r3.status_code == 200, r3.text
    detail = r3.json()
    assert detail.get("scan", {}).get("id") == scan_id
    assert len(detail.get("vulnerabilities", [])) >= 1

    r4 = integration_client.get("/api/v1/security/dashboard", headers=headers)
    assert r4.status_code == 200, r4.text


def test_biometric_template_register_returns_template(require_integration_mongo, integration_client: TestClient):
    username, password = _register_admin(integration_client)
    token = _login(integration_client, username, password)
    headers = {"Authorization": f"Bearer {token}"}

    r = integration_client.post(
        "/api/v1/biometric/templates/register",
        json={
            "biometric_type": "fingerprint",
            "template_data": "dGVzdA==",
            "quality_score": 0.5,
            "metadata": {},
        },
        headers=headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("template_id")
    assert body.get("biometric_type") == "fingerprint"

    listed = integration_client.get("/api/v1/biometric/templates", headers=headers)
    assert listed.status_code == 200, listed.text
    tpl_payload = listed.json()
    items = tpl_payload.get("templates", [])
    ids = {item.get("template_id") for item in items}
    assert body["template_id"] in ids


def test_metrics_endpoint_when_enabled(require_integration_mongo, integration_client: TestClient):
    r = integration_client.get("/metrics")
    assert r.status_code == 200
    text = r.text
    assert "#" in text or "HELP" in text
