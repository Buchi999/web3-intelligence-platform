from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready():
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "demo_mode" in body


def test_wallet_stub_not_implemented():
    response = client.get("/api/v1/wallet/0x0000000000000000000000000000000000000000")
    assert response.status_code == 200
    assert response.json()["status"] == "not_implemented"
