from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


BASE_URL = "https://weihnachtsmarkt-ravennaschlucht.reservix.de"


@dataclass
class GroupConfig:
    id: int
    name: str


@dataclass
class EventSlot:
    id: int
    sync_id: str
    name: str
    start_date_time: datetime
    end_date_time: datetime
    url_path: str
    is_bookable: bool
    bookable_info: str = ""
    group_id: int = 0
    group_name: str = ""

    @property
    def buy_url(self) -> str:
        clean_path = self.url_path.lstrip("/")
        return f"{BASE_URL}/{clean_path}"

    @property
    def formatted_start(self) -> str:
        # German day name and format: z.B. Samstag, 12.12.2026 um 14:30 Uhr
        weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        weekday = weekdays[self.start_date_time.weekday()]
        return f"{weekday}, {self.start_date_time.strftime('%d.%m.%Y um %H:%M Uhr')}"


@dataclass
class TicketOffer:
    id: int
    price_cents: int
    currency: str
    price_category: str
    status: str
    customer_uuid: str = ""
    category_name: str = ""

    @property
    def price_eur(self) -> float:
        return self.price_cents / 100.0

    @property
    def is_adult(self) -> bool:
        lower = self.price_category.lower()
        # "Erwachsene" or general "Preis pro Person"
        return "erwachsen" in lower or "pro person" in lower or "vollzahler" in lower

    @property
    def formatted_price(self) -> str:
        return f"{self.price_eur:.2f} €".replace(".", ",")


@dataclass
class SlotAvailability:
    slot: EventSlot
    offers: List[TicketOffer] = field(default_factory=list)

    @property
    def total_tickets(self) -> int:
        return len(self.offers)

    @property
    def adult_tickets(self) -> int:
        return sum(1 for o in self.offers if o.is_adult)

    @property
    def min_price_eur(self) -> Optional[float]:
        if not self.offers:
            return None
        return min(o.price_eur for o in self.offers)

    @property
    def max_price_eur(self) -> Optional[float]:
        if not self.offers:
            return None
        return max(o.price_eur for o in self.offers)
