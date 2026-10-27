import pytest
import httpx
from pathlib import Path
from src.config import Config
from src.monitor import TicketMonitor
from src.reservix_client import ReservixClient
from src.tracker import OfferTracker
from src.discord_notifier import DiscordNotifier
from src.web.app import create_app


@pytest.fixture
def test_app(tmp_path: Path):
    config = Config(
        discord_webhook_url="https://discord.com/api/webhooks/dummy",
        state_file_path=tmp_path / "seen.json",
    )
    tracker = OfferTracker(config.state_file_path)
    client = ReservixClient()
    notifier = DiscordNotifier(webhook_url=config.discord_webhook_url)
    monitor = TicketMonitor(config=config, client=client, tracker=tracker, notifier=notifier)
    return create_app(monitor)


@pytest.mark.anyio
async def test_web_index(test_app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.status_code == 200
        assert "Ravenna-Schlucht Ticket-Monitor" in resp.text


@pytest.mark.anyio
async def test_web_status(test_app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as ac:
        resp = await ac.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "is_running" in data
        assert "paused" in data
        assert "active_slots_count" in data


@pytest.mark.anyio
async def test_web_config_update(test_app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as ac:
        # Get config
        resp = await ac.get("/api/config")
        assert resp.status_code == 200
        cfg = resp.json()
        assert cfg["min_tickets"] == 1

        # Update config
        update_resp = await ac.post("/api/config", json={
            "min_tickets": 2,
            "only_adults": True,
            "allowed_weekdays": [4, 5, 6],
            "earliest_time": "15:00",
            "max_price_eur": 25.5,
        })
        assert update_resp.status_code == 200
        updated = update_resp.json()["config"]
        assert updated["min_tickets"] == 2
        assert updated["only_adults"] is True
        assert updated["allowed_weekdays"] == [4, 5, 6]
        assert updated["earliest_time"] == "15:00"
        assert updated["max_price_eur"] == 25.5


@pytest.mark.anyio
async def test_web_toggle_pause(test_app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as ac:
        resp1 = await ac.post("/api/toggle-pause")
        assert resp1.status_code == 200
        assert resp1.json()["paused"] is True

        resp2 = await ac.post("/api/toggle-pause")
        assert resp2.status_code == 200
        assert resp2.json()["paused"] is False
