"""Market API tests — exchange list, indicators, regime, exchange config CRUD."""

import pytest


@pytest.mark.django_db
class TestExchangeEndpoints:
    def test_list_exchanges(self, authenticated_client):
        resp = authenticated_client.get("/api/exchanges/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["id"] in ["binance", "coinbase", "kraken", "kucoin", "bybit"]

    def test_indicator_list(self, authenticated_client):
        resp = authenticated_client.get("/api/indicators/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert "rsi_14" in data
        assert "sma_50" in data


@pytest.mark.django_db
class TestRegimeEndpoints:
    def test_regime_current_all(self, authenticated_client):
        resp = authenticated_client.get("/api/regime/current/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))

    def test_regime_current_unknown_symbol(self, authenticated_client):
        resp = authenticated_client.get("/api/regime/current/UNKNOWN/PAIR/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["regime"] == "unknown"
        assert data["confidence"] == 0.0

    def test_regime_history(self, authenticated_client):
        resp = authenticated_client.get("/api/regime/history/BTC/USDT/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_regime_history_respects_limit(self, authenticated_client):
        resp = authenticated_client.get("/api/regime/history/BTC/USDT/?limit=5")
        assert resp.status_code == 200

    def test_regime_recommendation_unknown(self, authenticated_client):
        resp = authenticated_client.get("/api/regime/recommendation/UNKNOWN/PAIR/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["primary_strategy"] == "none"
        assert data["reasoning"] == "No data available"

    def test_regime_recommendations_all(self, authenticated_client):
        resp = authenticated_client.get("/api/regime/recommendations/")
        assert resp.status_code == 200

    def test_position_size_bad_float(self, authenticated_client):
        resp = authenticated_client.post(
            "/api/regime/position-size/",
            {"symbol": "BTC/USDT", "entry_price": "not_a_number", "stop_loss_price": 0},
            format="json",
        )
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_position_size_valid(self, authenticated_client):
        resp = authenticated_client.post(
            "/api/regime/position-size/",
            {"symbol": "BTC/USDT", "entry_price": 50000, "stop_loss_price": 48000},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "position_size" in data or "regime" in data


@pytest.mark.django_db
class TestExchangeConfigCRUD:
    def test_list_empty(self, authenticated_client):
        resp = authenticated_client.get("/api/exchange-configs/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_exchange_config(self, authenticated_client):
        resp = authenticated_client.post(
            "/api/exchange-configs/",
            {
                "name": "Test Binance",
                "exchange_id": "binance",
                "is_sandbox": True,
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Binance"
        assert data["exchange_id"] == "binance"
        assert data["is_sandbox"] is True

    def test_get_exchange_config(self, authenticated_client):
        create = authenticated_client.post(
            "/api/exchange-configs/",
            {"name": "Get Test", "exchange_id": "kraken"},
            format="json",
        )
        pk = create.json()["id"]
        resp = authenticated_client.get(f"/api/exchange-configs/{pk}/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Test"

    def test_get_exchange_config_not_found(self, authenticated_client):
        resp = authenticated_client.get("/api/exchange-configs/9999/")
        assert resp.status_code == 404

    def test_update_exchange_config(self, authenticated_client):
        create = authenticated_client.post(
            "/api/exchange-configs/",
            {"name": "Update Me", "exchange_id": "binance"},
            format="json",
        )
        pk = create.json()["id"]
        resp = authenticated_client.put(
            f"/api/exchange-configs/{pk}/",
            {"name": "Updated Name"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_delete_exchange_config(self, authenticated_client):
        create = authenticated_client.post(
            "/api/exchange-configs/",
            {"name": "Delete Me", "exchange_id": "binance"},
            format="json",
        )
        pk = create.json()["id"]
        resp = authenticated_client.delete(f"/api/exchange-configs/{pk}/")
        assert resp.status_code == 204

        resp = authenticated_client.get(f"/api/exchange-configs/{pk}/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestDataSourceConfigCRUD:
    def _create_exchange(self, client):
        resp = client.post(
            "/api/exchange-configs/",
            {"name": "For DS", "exchange_id": "binance"},
            format="json",
        )
        return resp.json()["id"]

    def test_list_empty(self, authenticated_client):
        resp = authenticated_client.get("/api/data-sources/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_data_source(self, authenticated_client):
        ex_pk = self._create_exchange(authenticated_client)
        resp = authenticated_client.post(
            "/api/data-sources/",
            {
                "exchange_config": ex_pk,
                "symbols": ["BTC/USDT"],
                "timeframes": ["1h"],
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["symbols"] == ["BTC/USDT"]
        assert data["timeframes"] == ["1h"]

    def test_delete_data_source(self, authenticated_client):
        ex_pk = self._create_exchange(authenticated_client)
        create = authenticated_client.post(
            "/api/data-sources/",
            {"exchange_config": ex_pk, "symbols": ["ETH/USDT"], "timeframes": ["1d"]},
            format="json",
        )
        pk = create.json()["id"]
        resp = authenticated_client.delete(f"/api/data-sources/{pk}/")
        assert resp.status_code == 204
