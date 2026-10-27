import pytest
import httpx
from datetime import datetime
from pathlib import Path
from src.config import Config
from src.models import EventSlot, TicketOffer, SlotAvailability
from src.monitor import TicketMonitor
from src.reservix_client import ReservixClient
from src.tracker import OfferTracker
from src.discord_notifier import DiscordNotifier
from src.web.app import create_app


@pytest.fixture
def monitor_instance(tmp_path: Path):
    config = Config(
        discord_webhook_url="https://discord.com/api/webhooks/dummy",
        state_file_path=tmp_path / "seen.json",
        env_file_path=tmp_path / ".env",
    )
    tracker = OfferTracker(config.state_file_path)
    client = ReservixClient()
    notifier = DiscordNotifier(webhook_url=config.discord_webhook_url)
    return TicketMonitor(config=config, client=client, tracker=tracker, notifier=notifier)


@pytest.fixture
def test_app(monitor_instance):
    return create_app(monitor_instance)


@pytest.mark.anyio
async def test_web_index(test_app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.status_code == 200
        assert "Ravenna-Schlucht Ticket-Monitor" in resp.text
        assert "dateFrom" in resp.text
        assert "sortSelect" in resp.text


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

        # Update config with date range
        update_resp = await ac.post("/api/config", json={
            "min_tickets": 2,
            "only_adults": True,
            "date_from": "2026-12-01",
            "date_to": "2026-12-15",
            "allowed_weekdays": [4, 5, 6],
            "earliest_time": "15:00",
            "max_price_eur": 25.5,
        })
        assert update_resp.status_code == 200
        updated = update_resp.json()["config"]
        assert updated["min_tickets"] == 2
        assert updated["only_adults"] is True
        assert updated["date_from"] == "2026-12-01"
        assert updated["date_to"] == "2026-12-15"
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


@pytest.mark.anyio
async def test_dynamic_filter_applied_to_active_slots(monitor_instance, test_app):
    # Populate monitor with existing search results
    slot1 = EventSlot(
        id=1,
        sync_id="1001",
        name="Slot in November",
        start_date_time=datetime(2026, 11, 27, 16, 0),  # Friday
        end_date_time=datetime(2026, 11, 27, 18, 0),
        url_path="path1",
        is_bookable=True,
        group_id=545832,
    )
    # Slot 1 has 1 adult ticket
    avail1 = SlotAvailability(slot=slot1, offers=[
        TicketOffer(id=1, price_cents=950, currency="EUR", price_category="Erwachsene", status="BOOKABLE")
    ])

    slot2 = EventSlot(
        id=2,
        sync_id="1002",
        name="Slot in December",
        start_date_time=datetime(2026, 12, 11, 16, 0),  # Friday
        end_date_time=datetime(2026, 12, 11, 18, 0),
        url_path="path2",
        is_bookable=True,
        group_id=545832,
    )
    # Slot 2 has 2 adult tickets
    avail2 = SlotAvailability(slot=slot2, offers=[
        TicketOffer(id=2, price_cents=950, currency="EUR", price_category="Erwachsene", status="BOOKABLE"),
        TicketOffer(id=3, price_cents=950, currency="EUR", price_category="Erwachsene", status="BOOKABLE")
    ])

    monitor_instance.raw_active_slots = [avail1, avail2]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as ac:
        # 1. Default config: both slots should appear
        res1 = await ac.get("/api/active-slots")
        assert len(res1.json()) == 2

        # 2. Update config to require MIN_TICKETS = 2
        # Slot 1 only has 1 ticket -> should be filtered out immediately!
        await ac.post("/api/config", json={"min_tickets": 2})
        res2 = await ac.get("/api/active-slots")
        slots2 = res2.json()
        assert len(slots2) == 1
        assert slots2[0]["sync_id"] == "1002"

        # 3. Update date range to November only (2026-11-01 to 2026-11-30) and min_tickets = 1
        # Slot 2 is in December -> filtered out! Only Slot 1 should appear!
        await ac.post("/api/config", json={
            "min_tickets": 1,
            "date_from": "2026-11-01",
            "date_to": "2026-11-30"
        })
        res3 = await ac.get("/api/active-slots")
        slots3 = res3.json()
        assert len(slots3) == 1
        assert slots3[0]["sync_id"] == "1001"


@pytest.mark.anyio
async def test_active_slots_sorting(monitor_instance, test_app):
    slot_early = EventSlot(
        id=1,
        sync_id="101",
        name="Slot A - Titisee",
        start_date_time=datetime(2026, 12, 4, 15, 0),
        end_date_time=datetime(2026, 12, 4, 17, 0),
        url_path="p1",
        is_bookable=True,
        group_id=545832,
        group_name="Titisee Shuttle",
    )
    # 1 ticket at 20.00 EUR
    avail_early = SlotAvailability(slot=slot_early, offers=[
        TicketOffer(id=1, price_cents=2000, currency="EUR", price_category="Erwachsene", status="BOOKABLE")
    ])

    slot_late = EventSlot(
        id=2,
        sync_id="102",
        name="Slot B - Freiburg",
        start_date_time=datetime(2026, 12, 11, 17, 0),
        end_date_time=datetime(2026, 12, 11, 19, 0),
        url_path="p2",
        is_bookable=True,
        group_id=546305,
        group_name="Freiburg Shuttle",
    )
    # 3 tickets at 10.00 EUR each
    avail_late = SlotAvailability(slot=slot_late, offers=[
        TicketOffer(id=2, price_cents=1000, currency="EUR", price_category="Erwachsene", status="BOOKABLE"),
        TicketOffer(id=3, price_cents=1000, currency="EUR", price_category="Erwachsene", status="BOOKABLE"),
        TicketOffer(id=4, price_cents=1000, currency="EUR", price_category="Erwachsene", status="BOOKABLE"),
    ])

    monitor_instance.raw_active_slots = [avail_early, avail_late]

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as ac:
        # Default sort (date-asc)
        res = await ac.get("/api/active-slots?sort=date-asc")
        data = res.json()
        assert [s["sync_id"] for s in data] == ["101", "102"]

        # Date descending
        res = await ac.get("/api/active-slots?sort=date-desc")
        data = res.json()
        assert [s["sync_id"] for s in data] == ["102", "101"]

        # Tickets descending (102 has 3 tickets, 101 has 1)
        res = await ac.get("/api/active-slots?sort=tickets-desc")
        data = res.json()
        assert [s["sync_id"] for s in data] == ["102", "101"]

        # Tickets ascending
        res = await ac.get("/api/active-slots?sort=tickets-asc")
        data = res.json()
        assert [s["sync_id"] for s in data] == ["101", "102"]

        # Price ascending (102 is 10 EUR, 101 is 20 EUR)
        res = await ac.get("/api/active-slots?sort=price-asc")
        data = res.json()
        assert [s["sync_id"] for s in data] == ["102", "101"]

        # Price descending (101 is 20 EUR, 102 is 10 EUR)
        res = await ac.get("/api/active-slots?sort=price-desc")
        data = res.json()
        assert [s["sync_id"] for s in data] == ["101", "102"]

        # Group name ascending ("Freiburg" before "Titisee")
        res = await ac.get("/api/active-slots?sort=group-asc")
        data = res.json()
        assert [s["sync_id"] for s in data] == ["102", "101"]


@pytest.mark.anyio
async def test_config_handles_none_values(test_app, monitor_instance):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as ac:
        resp = await ac.post("/api/config", json={
            "earliest_time": None,
            "latest_time": None,
            "date_from": None,
            "date_to": None,
        })
        assert resp.status_code == 200
        assert monitor_instance.config.earliest_time is None
        assert monitor_instance.config.latest_time is None
        assert monitor_instance.config.date_from is None
        assert monitor_instance.config.date_to is None


@pytest.mark.anyio
async def test_active_slots_show_all(test_app, monitor_instance):
    slot = EventSlot(
        id=99,
        sync_id="999",
        name="Out of filter slot",
        start_date_time=datetime(2026, 11, 26, 16, 0),
        end_date_time=datetime(2026, 11, 26, 18, 0),
        url_path="p",
        is_bookable=True,
    )
    avail = SlotAvailability(slot=slot, offers=[
        TicketOffer(id=1, price_cents=500, currency="EUR", price_category="Kinder", status="BOOKABLE")
    ])
    monitor_instance.raw_active_slots = [avail]
    # Set config to only adults (so avail is filtered out)
    monitor_instance.config.only_adults = True

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test") as ac:
        # Filtered should be empty
        res1 = await ac.get("/api/active-slots?show_all=false")
        assert len(res1.json()) == 0

        # show_all=true should return the raw slot
        res2 = await ac.get("/api/active-slots?show_all=true")
        assert len(res2.json()) == 1
        assert res2.json()[0]["sync_id"] == "999"


