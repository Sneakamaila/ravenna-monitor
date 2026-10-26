from datetime import datetime
from src.models import EventSlot, TicketOffer, SlotAvailability


def test_event_slot_properties():
    dt_start = datetime(2026, 12, 11, 14, 35)
    dt_end = datetime(2026, 12, 11, 16, 35)
    slot = EventSlot(
        id=24001,
        sync_id="2601831",
        name="Weihnachtsmarkt in der Ravennaschlucht – Shuttle & Eintritt ab Himmelreich",
        start_date_time=dt_start,
        end_date_time=dt_end,
        url_path="tickets-weihnachtsmarkt/e2601831",
        is_bookable=True,
        group_id=545886,
        group_name="Shuttle ab Himmelreich",
    )

    assert slot.buy_url == "https://weihnachtsmarkt-ravennaschlucht.reservix.de/tickets-weihnachtsmarkt/e2601831"
    assert "Freitag" in slot.formatted_start
    assert "11.12.2026" in slot.formatted_start
    assert "14:35" in slot.formatted_start


def test_ticket_offer_properties():
    offer_adult = TicketOffer(
        id=536046,
        price_cents=935,
        currency="EUR",
        price_category="Erwachsene (ab 16 Jahren)",
        status="BOOKABLE",
    )
    assert offer_adult.price_eur == 9.35
    assert offer_adult.is_adult is True
    assert "9,35" in offer_adult.formatted_price

    offer_child = TicketOffer(
        id=534420,
        price_cents=550,
        currency="EUR",
        price_category="Kinder (6-15 Jahre)",
        status="BOOKABLE",
    )
    assert offer_child.price_eur == 5.50
    assert offer_child.is_adult is False
    assert "5,50" in offer_child.formatted_price


def test_slot_availability_calculations():
    dt = datetime(2026, 12, 11, 14, 35)
    slot = EventSlot(
        id=1,
        sync_id="123",
        name="Test Slot",
        start_date_time=dt,
        end_date_time=dt,
        url_path="test/123",
        is_bookable=True,
    )
    o1 = TicketOffer(id=1, price_cents=950, currency="EUR", price_category="Erwachsene", status="BOOKABLE")
    o2 = TicketOffer(id=2, price_cents=500, currency="EUR", price_category="Kinder", status="BOOKABLE")

    avail = SlotAvailability(slot=slot, offers=[o1, o2])
    assert avail.total_tickets == 2
    assert avail.adult_tickets == 1
    assert avail.min_price_eur == 5.0
    assert avail.max_price_eur == 9.5
