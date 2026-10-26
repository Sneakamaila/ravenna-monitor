from datetime import datetime
from pathlib import Path
from src.models import EventSlot, TicketOffer
from src.tracker import OfferTracker


def test_tracker_lifecycle(tmp_path: Path):
    state_file = tmp_path / "test_seen.json"
    tracker = OfferTracker(state_file)

    dt = datetime(2026, 12, 11, 14, 35)
    slot = EventSlot(id=1, sync_id="2601", name="Test", start_date_time=dt, end_date_time=dt, url_path="test", is_bookable=True)
    o1 = TicketOffer(id=101, price_cents=950, currency="EUR", price_category="Erwachsene", status="BOOKABLE")
    o2 = TicketOffer(id=102, price_cents=950, currency="EUR", price_category="Erwachsene", status="BOOKABLE")

    # Both should be new initially
    new_offers = tracker.filter_new_offers(slot, [o1, o2])
    assert len(new_offers) == 2

    # Mark o1 as alerted
    tracker.mark_alerted(slot, [o1])
    assert tracker.is_known(101) is True
    assert tracker.is_known(102) is False

    # Second check: only o2 should be new
    new_offers_2 = tracker.filter_new_offers(slot, [o1, o2])
    assert len(new_offers_2) == 1
    assert new_offers_2[0].id == 102

    # Reload tracker from file
    tracker_reloaded = OfferTracker(state_file)
    assert tracker_reloaded.is_known(101) is True
    assert tracker_reloaded.is_known(102) is False
