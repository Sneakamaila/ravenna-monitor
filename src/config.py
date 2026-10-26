import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

DEFAULT_KNOWN_GROUPS: Dict[int, str] = {
    545832: "Shuttle ab Titisee",
    545884: "Shuttle ab Hinterzarten",
    545886: "Shuttle ab Himmelreich",
    546305: "Shuttle ab Freiburg",
    545934: "Parken & Eintritt (PKW)",
    545947: "Nur Eintritt (Wander-Ticket)",
}


@dataclass
class Config:
    discord_webhook_url: Optional[str] = None
    discord_mention: Optional[str] = None
    check_interval_seconds: int = 30
    check_interval_jitter: int = 5
    min_tickets: int = 1
    only_adults: bool = False
    monitored_groups: List[int] = field(default_factory=lambda: list(DEFAULT_KNOWN_GROUPS.keys()))
    state_file_path: Path = field(default_factory=lambda: Path("seen_offers.json"))
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip() or None
        mention = os.getenv("DISCORD_MENTION", "").strip() or None

        interval_raw = os.getenv("CHECK_INTERVAL_SECONDS", "30").strip()
        try:
            interval = max(5, int(interval_raw))
        except ValueError:
            interval = 30

        jitter_raw = os.getenv("CHECK_INTERVAL_JITTER", "5").strip()
        try:
            jitter = max(0, int(jitter_raw))
        except ValueError:
            jitter = 5

        min_tickets_raw = os.getenv("MIN_TICKETS", "1").strip()
        try:
            min_tickets = max(1, int(min_tickets_raw))
        except ValueError:
            min_tickets = 1

        only_adults_raw = os.getenv("ONLY_ADULTS", "false").strip().lower()
        only_adults = only_adults_raw in ("true", "1", "yes", "y")

        groups_raw = os.getenv("MONITORED_GROUPS", "").strip()
        if groups_raw:
            groups = []
            for part in groups_raw.split(","):
                part = part.strip()
                if part.isdigit():
                    groups.append(int(part))
            if not groups:
                groups = list(DEFAULT_KNOWN_GROUPS.keys())
        else:
            groups = list(DEFAULT_KNOWN_GROUPS.keys())

        state_file = Path(os.getenv("STATE_FILE_PATH", "seen_offers.json").strip())
        log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper()

        return cls(
            discord_webhook_url=webhook,
            discord_mention=mention,
            check_interval_seconds=interval,
            check_interval_jitter=jitter,
            min_tickets=min_tickets,
            only_adults=only_adults,
            monitored_groups=groups,
            state_file_path=state_file,
            log_level=log_level,
        )
