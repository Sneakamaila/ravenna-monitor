import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from src.models import EventSlot, TicketOffer

logger = logging.getLogger(__name__)


class OfferTracker:
    def __init__(self, state_file: Path):
        self.state_file = Path(state_file)
        self.seen_offers: Dict[str, dict] = {}
        self.load()

    def load(self):
        if not self.state_file.exists():
            self.seen_offers = {}
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.seen_offers = data.get("offers", {})
                logger.info(f"{len(self.seen_offers)} bereits bekannte Angebote aus {self.state_file} geladen.")
        except Exception as e:
            logger.warning(f"Konnte {self.state_file} nicht laden: {e}. Starte mit leerem Cache.")
            self.seen_offers = {}

    def save(self):
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = self.state_file.with_suffix(".tmp")
            data = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "offers": self.seen_offers,
            }
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_file, self.state_file)
        except Exception as e:
            logger.error(f"Fehler beim Speichern von {self.state_file}: {e}")

    def filter_new_offers(self, slot: EventSlot, offers: List[TicketOffer]) -> List[TicketOffer]:
        """Returns only offers that haven't been alerted yet."""
        new_offers: List[TicketOffer] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for offer in offers:
            key = str(offer.id)
            if key not in self.seen_offers or not self.seen_offers[key].get("alerted", False):
                new_offers.append(offer)
            else:
                # Update last_seen timestamp
                self.seen_offers[key]["last_seen"] = now_iso

        return new_offers

    def mark_alerted(self, slot: EventSlot, offers: List[TicketOffer]):
        """Mark offers as alerted and persist to state."""
        now_iso = datetime.now(timezone.utc).isoformat()
        for offer in offers:
            key = str(offer.id)
            self.seen_offers[key] = {
                "offer_id": offer.id,
                "event_sync_id": slot.sync_id,
                "category": offer.price_category,
                "price_cents": offer.price_cents,
                "first_seen": self.seen_offers.get(key, {}).get("first_seen", now_iso),
                "last_seen": now_iso,
                "alerted": True,
            }
        self.save()

    def is_known(self, offer_id: int) -> bool:
        return str(offer_id) in self.seen_offers

    def clear(self):
        """Reset the seen offers cache."""
        self.seen_offers = {}
        self.save()
        logger.info("Cache für bereits gesehene Angebote wurde geleert.")
