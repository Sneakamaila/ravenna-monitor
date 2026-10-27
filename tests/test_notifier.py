from datetime import datetime
import pytest
from src.discord_notifier import DiscordNotifier
from src.models import EventSlot, TicketOffer


def test_build_offer_embed():
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/dummy/dummy", mention="@everyone")
    dt = datetime(2026, 12, 11, 14, 35)
    slot = EventSlot(
        id=1,
        sync_id="2601831",
        name="Weihnachtsmarkt Ravenna - Shuttle ab Himmelreich",
        start_date_time=dt,
        end_date_time=dt,
        url_path="tickets-weihnachtsmarkt/e2601831",
        is_bookable=True,
        group_name="Shuttle ab Himmelreich",
    )
    o1 = TicketOffer(id=1, price_cents=935, currency="EUR", price_category="Erwachsene (ab 16 Jahren)", status="BOOKABLE")
    o2 = TicketOffer(id=2, price_cents=550, currency="EUR", price_category="Kinder (6-15 Jahre)", status="BOOKABLE")

    embed = notifier._build_offer_embed(slot, [o1, o2])

    assert "2 Zweitmarkt-Ticket(s) verfügbar!" in embed["title"]
    assert slot.buy_url in embed["url"]

    # Verify fields
    fields = {f["name"]: f["value"] for f in embed["fields"]}
    assert any("Termin / Einlass" in k for k in fields)
    assert "Freitag, 11.12.2026 um 14:35 Uhr" in fields["📅 Termin / Einlass"]
    assert "Shuttle ab Himmelreich" in fields["📍 Anreise / Art"]
    assert "2 Ticket(s)" in fields["🔢 Verfügbare Tickets"]
    assert "1x" in fields["🏷️ Preiskategorien"]
    assert "14,85 €" in fields["💰 Gesamtsumme"]
    assert slot.buy_url in fields["🛒 Direktlink zum Kauf"]


@pytest.mark.anyio
async def test_send_notification_no_webhook_returns_false():
    notifier = DiscordNotifier(webhook_url=None)
    dt = datetime(2026, 12, 11, 14, 35)
    slot = EventSlot(
        id=1,
        sync_id="2601831",
        name="Weihnachtsmarkt Ravenna",
        start_date_time=dt,
        end_date_time=dt,
        url_path="p",
        is_bookable=True,
    )
    offer = TicketOffer(id=1, price_cents=935, currency="EUR", price_category="Erwachsene", status="BOOKABLE")

    result = await notifier.send_notification(slot, [offer])
    # Must return False so that dry-run does not falsely increment alert counter
    assert result is False

