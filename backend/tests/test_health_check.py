"""Health check endpoint tests."""
import pytest


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_simple_unchanged(self, client):
        """Simple health check returns just status ok (no auth required)."""
        resp = client.get("/api/health/")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {"status": "ok"}
        assert "checks" not in data

    def test_health_detailed_includes_checks(self, client):
        """Detailed health check includes checks dict."""
        resp = client.get("/api/health/?detailed=true")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "disk" in data["checks"]
        assert "memory" in data["checks"]

    def test_health_detailed_database_ok(self, client):
        """Database check returns ok when DB is accessible."""
        resp = client.get("/api/health/?detailed=true")
        data = resp.json()
        assert data["checks"]["database"]["status"] == "ok"

    def test_health_detailed_disk_ok(self, client):
        """Disk check returns ok with usage info."""
        resp = client.get("/api/health/?detailed=true")
        data = resp.json()
        disk = data["checks"]["disk"]
        assert disk["status"] == "ok"
        assert "total_gb" in disk
        assert "free_gb" in disk
        assert "used_pct" in disk
        assert disk["writable"] is True

    def test_health_detailed_memory_ok(self, client):
        """Memory check returns ok with RSS info."""
        resp = client.get("/api/health/?detailed=true")
        data = resp.json()
        mem = data["checks"]["memory"]
        assert mem["status"] == "ok"
        assert "rss_mb" in mem
        assert mem["rss_mb"] > 0

    def test_health_detailed_no_auth_required(self, client):
        """Detailed health check works without authentication."""
        resp = client.get("/api/health/?detailed=true")
        assert resp.status_code == 200
        assert resp.json()["status"] in ("ok", "degraded")
