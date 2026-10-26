import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
import httpx

from src.models import BASE_URL, EventSlot, TicketOffer
from src.config import DEFAULT_KNOWN_GROUPS

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": f"{BASE_URL}/",
}

AJAX_HEADERS = {
    **DEFAULT_HEADERS,
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/plain, */*",
}


class ReservixClient:
    def __init__(self, client: Optional[httpx.AsyncClient] = None, timeout: float = 15.0):
        self._external_client = client is not None
        self._client = client or httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True)

    async def close(self):
        if not self._external_client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def discover_groups(self) -> Dict[int, str]:
        """Scrape the homepage to discover all active event group calendars."""
        try:
            resp = await self._client.get(f"{BASE_URL}/")
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.warning(f"Konnte Startseite nicht abrufen für Auto-Discovery: {e}. Verwende Fallback-Gruppen.")
            return DEFAULT_KNOWN_GROUPS.copy()

        # Find all calendar group links
        pattern = re.compile(r"href=[\"'](?:https?://[^\"']+)?/tickets/kalender/reihe/weihnachtsmarkt/(\d+)[\"']", re.IGNORECASE)
        found_ids = set()
        for match in pattern.finditer(html):
            found_ids.add(int(match.group(1)))

        discovered: Dict[int, str] = {}
        for gid in found_ids:
            # Skip bus groups (535283)
            if gid == 535283:
                continue
            name = DEFAULT_KNOWN_GROUPS.get(gid, f"Kategorie #{gid}")
            discovered[gid] = name

        if not discovered:
            return DEFAULT_KNOWN_GROUPS.copy()

        return discovered

    async def fetch_calendar_events(self, group_id: int, group_name: str = "") -> List[EventSlot]:
        """Fetch the calendar view for a group and parse all available time slots."""
        url = f"{BASE_URL}/tickets/kalender/reihe/weihnachtsmarkt/{group_id}"
        try:
            resp = await self._client.get(url)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            logger.error(f"Fehler beim Laden von Kalender für Gruppe {group_id} ({group_name}): {e}")
            return []

        events = self._parse_calendar_script(html, group_id, group_name)
        return events

    def _parse_calendar_script(self, html: str, group_id: int, group_name: str) -> List[EventSlot]:
        match = re.search(r"rx\.ReactApps\.calendar\(\s*(\{.*?\})\s*\);", html, re.DOTALL)
        if not match:
            logger.debug(f"Kein rx.ReactApps.calendar in Gruppe {group_id} gefunden.")
            return []

        data_str = match.group(1)
        ev_start = data_str.find("events:")
        if ev_start == -1:
            return []

        ev_json_str = data_str[ev_start + len("events:"):].strip()
        last_bracket = ev_json_str.rfind("]")
        if last_bracket == -1:
            return []

        raw_json = ev_json_str[:last_bracket + 1]
        try:
            raw_events = json.loads(raw_json)
        except Exception as e:
            logger.error(f"Konnte Event-JSON für Gruppe {group_id} nicht parsen: {e}")
            return []

        slots: List[EventSlot] = []
        for raw in raw_events:
            try:
                start_dt = datetime.fromtimestamp(raw["startDateTime"] / 1000.0)
                end_dt = datetime.fromtimestamp(raw.get("endDateTime", raw["startDateTime"]) / 1000.0)
                slot = EventSlot(
                    id=raw["id"],
                    sync_id=str(raw["syncId"]),
                    name=raw.get("name", ""),
                    start_date_time=start_dt,
                    end_date_time=end_dt,
                    url_path=raw.get("urlPath", ""),
                    is_bookable=bool(raw.get("isBookable", False)),
                    bookable_info=raw.get("bookableInfo", ""),
                    group_id=group_id,
                    group_name=group_name or DEFAULT_KNOWN_GROUPS.get(group_id, f"Gruppe {group_id}"),
                )
                slots.append(slot)
            except Exception as e:
                logger.warning(f"Fehler beim Parsen eines Slots in Gruppe {group_id}: {e}")

        return slots

    async def fetch_marketplace_offers(self, event_sync_id: str, url_path: str = "") -> List[TicketOffer]:
        """Query the resale marketplace endpoint for active offers for a specific time slot."""
        url = f"{BASE_URL}/ajax/resale-marketplace/{event_sync_id}/offers"
        headers = dict(AJAX_HEADERS)
        if url_path:
            headers["Referer"] = f"{BASE_URL}/{url_path.lstrip('/')}"

        try:
            resp = await self._client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Zweitmarkt-Angebote für Event {event_sync_id}: {e}")
            return []

        if not isinstance(data, list):
            logger.warning(f"Unerwartete Antwort für Event {event_sync_id}: {data}")
            return []

        offers: List[TicketOffer] = []
        for item in data:
            status = item.get("status", "")
            if status != "BOOKABLE":
                continue

            price_info = item.get("price") or {}
            price_val = price_info.get("value", 0)
            currency = price_info.get("currency", "EUR")

            offer = TicketOffer(
                id=item["id"],
                price_cents=price_val,
                currency=currency,
                price_category=item.get("priceCategory", ""),
                status=status,
                customer_uuid=item.get("customerUuid", ""),
                category_name=item.get("categoryName", ""),
            )
            offers.append(offer)

        return offers
