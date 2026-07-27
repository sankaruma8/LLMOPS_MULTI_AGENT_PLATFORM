import sys
import os
import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)


def test_home_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_health_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_metrics_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True


def test_system_status_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.get("/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "data" in data
    assert "environment" in data["data"]
    assert "features" in data["data"]


def test_rate_limit_stats_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.get("/rate-limit/stats")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "data" in data


def test_cache_stats_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.get("/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "data" in data
    assert "embedding_cache_size" in data["data"]


def test_clear_cache_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.post("/cache/clear")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_docs_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200


def test_metrics_reset():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.post("/metrics/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_audit_log_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.get("/system/audit")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "data" in data


def test_audit_log_with_params():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.get("/system/audit?limit=10")
    assert response.status_code == 200


@pytest.mark.skip(reason="Requires Groq API call - test in integration")
def test_chat_no_auth():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/chat",
        json={
            "session_id": "test-session",
            "message": "Hello",
            "stream": False
        }
    )
    assert response.status_code in [200, 429]


@pytest.mark.skip(reason="Requires Groq API call - test in integration")
def test_chat_stream_endpoint():
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app)
    response = client.post(
        "/chat/stream",
        json={
            "session_id": "test-session",
            "message": "Hello",
            "stream": True
        }
    )
    assert response.status_code in [200, 429]
