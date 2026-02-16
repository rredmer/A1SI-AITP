"""
Tests for kill switch (halt/resume) endpoints.
"""

import pytest


class TestHaltEndpoint:
    @pytest.mark.asyncio
    async def test_halt_trading(self, client):
        resp = await client.post(
            "/api/risk/1/halt",
            json={"reason": "manual test halt"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_halted"] is True
        assert data["halt_reason"] == "manual test halt"
        assert "halted" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_resume_trading(self, client):
        # First halt
        await client.post("/api/risk/1/halt", json={"reason": "test"})
        # Then resume
        resp = await client.post("/api/risk/1/resume")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_halted"] is False
        assert data["halt_reason"] == ""
        assert "resumed" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_halted_trade_rejected(self, client):
        # Halt trading
        await client.post("/api/risk/1/halt", json={"reason": "emergency"})
        # Attempt a trade
        resp = await client.post(
            "/api/risk/1/check-trade",
            json={
                "symbol": "BTC/USDT",
                "side": "buy",
                "size": 0.01,
                "entry_price": 97000,
                "stop_loss_price": 92150,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approved"] is False
        assert "halted" in data["reason"].lower()

    @pytest.mark.asyncio
    async def test_resume_then_trade_approved(self, client):
        # Halt then resume
        await client.post("/api/risk/1/halt", json={"reason": "test"})
        await client.post("/api/risk/1/resume")
        # Trade should be approved now
        resp = await client.post(
            "/api/risk/1/check-trade",
            json={
                "symbol": "BTC/USDT",
                "side": "buy",
                "size": 0.01,
                "entry_price": 50000,
                "stop_loss_price": 48500,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["approved"] is True

    @pytest.mark.asyncio
    async def test_halt_status_visible(self, client):
        await client.post("/api/risk/1/halt", json={"reason": "visible check"})
        resp = await client.get("/api/risk/1/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_halted"] is True
        assert data["halt_reason"] == "visible check"
