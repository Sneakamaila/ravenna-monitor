import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
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

WEEKDAY_NAMES = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
]


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

    # Clever additional filters
    allowed_weekdays: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])
    date_from: Optional[str] = None      # Format "YYYY-MM-DD", e.g. "2026-11-27"
    date_to: Optional[str] = None        # Format "YYYY-MM-DD", e.g. "2026-12-20"
    earliest_time: Optional[str] = None  # Format "HH:MM", e.g. "14:00"
    latest_time: Optional[str] = None    # Format "HH:MM", e.g. "20:00"
    max_price_eur: Optional[float] = None  # e.g. 20.00
    excluded_dates: List[str] = field(default_factory=list)  # ["2026-11-26"]

    # Web UI settings
    web_host: str = "0.0.0.0"
    web_port: int = 8080
    paused: bool = False

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

        # Clever filters from env
        weekdays_raw = os.getenv("ALLOWED_WEEKDAYS", "").strip()
        if weekdays_raw:
            try:
                allowed_weekdays = [int(x.strip()) for x in weekdays_raw.split(",") if x.strip().isdigit()]
                if not allowed_weekdays:
                    allowed_weekdays = [0, 1, 2, 3, 4, 5, 6]
            except Exception:
                allowed_weekdays = [0, 1, 2, 3, 4, 5, 6]
        else:
            allowed_weekdays = [0, 1, 2, 3, 4, 5, 6]

        earliest = os.getenv("EARLIEST_TIME", "").strip() or None
        latest = os.getenv("LATEST_TIME", "").strip() or None
        date_from = os.getenv("DATE_FROM", "").strip() or None
        date_to = os.getenv("DATE_TO", "").strip() or None

        max_price_raw = os.getenv("MAX_PRICE_EUR", "").strip()
        max_price: Optional[float] = None
        if max_price_raw:
            try:
                max_price = float(max_price_raw.replace(",", "."))
            except ValueError:
                max_price = None

        excluded_raw = os.getenv("EXCLUDED_DATES", "").strip()
        excluded_dates = [d.strip() for d in excluded_raw.split(",") if d.strip()] if excluded_raw else []

        web_host = os.getenv("WEB_HOST", "0.0.0.0").strip()
        try:
            web_port = int(os.getenv("WEB_PORT", os.getenv("PORT", "8080")).strip())
        except ValueError:
            web_port = 8080

        paused = os.getenv("MONITOR_PAUSED", "false").strip().lower() in ("true", "1", "yes")

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
            allowed_weekdays=allowed_weekdays,
            date_from=date_from,
            date_to=date_to,
            earliest_time=earliest,
            latest_time=latest,
            max_price_eur=max_price,
            excluded_dates=excluded_dates,
            web_host=web_host,
            web_port=web_port,
            paused=paused,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "discord_webhook_url": self.discord_webhook_url or "",
            "discord_mention": self.discord_mention or "",
            "check_interval_seconds": self.check_interval_seconds,
            "check_interval_jitter": self.check_interval_jitter,
            "min_tickets": self.min_tickets,
            "only_adults": self.only_adults,
            "monitored_groups": self.monitored_groups,
            "allowed_weekdays": self.allowed_weekdays,
            "date_from": self.date_from or "",
            "date_to": self.date_to or "",
            "earliest_time": self.earliest_time or "",
            "latest_time": self.latest_time or "",
            "max_price_eur": self.max_price_eur,
            "excluded_dates": self.excluded_dates,
            "web_host": self.web_host,
            "web_port": self.web_port,
            "paused": self.paused,
            "log_level": self.log_level,
        }

    def update_from_dict(self, data: Dict[str, Any]):
        if "discord_webhook_url" in data:
            val = str(data["discord_webhook_url"]).strip()
            self.discord_webhook_url = val or None
        if "discord_mention" in data:
            val = str(data["discord_mention"]).strip()
            self.discord_mention = val or None
        if "check_interval_seconds" in data:
            try:
                self.check_interval_seconds = max(5, int(data["check_interval_seconds"]))
            except (ValueError, TypeError):
                pass
        if "check_interval_jitter" in data:
            try:
                self.check_interval_jitter = max(0, int(data["check_interval_jitter"]))
            except (ValueError, TypeError):
                pass
        if "min_tickets" in data:
            try:
                self.min_tickets = max(1, int(data["min_tickets"]))
            except (ValueError, TypeError):
                pass
        if "only_adults" in data:
            self.only_adults = bool(data["only_adults"])
        if "monitored_groups" in data and isinstance(data["monitored_groups"], list):
            self.monitored_groups = [int(g) for g in data["monitored_groups"] if str(g).isdigit()]
        if "allowed_weekdays" in data and isinstance(data["allowed_weekdays"], list):
            self.allowed_weekdays = [int(w) for w in data["allowed_weekdays"] if 0 <= int(w) <= 6]
        if "date_from" in data:
            val = str(data["date_from"]).strip()
            self.date_from = val or None
        if "date_to" in data:
            val = str(data["date_to"]).strip()
            self.date_to = val or None
        if "earliest_time" in data:
            val = str(data["earliest_time"]).strip()
            self.earliest_time = val or None
        if "latest_time" in data:
            val = str(data["latest_time"]).strip()
            self.latest_time = val or None
        if "max_price_eur" in data:
            try:
                val = float(data["max_price_eur"]) if data["max_price_eur"] not in (None, "", 0) else None
                self.max_price_eur = val
            except (ValueError, TypeError):
                self.max_price_eur = None
        if "excluded_dates" in data and isinstance(data["excluded_dates"], list):
            self.excluded_dates = [str(d).strip() for d in data["excluded_dates"] if str(d).strip()]
        if "paused" in data:
            self.paused = bool(data["paused"])

    def save_to_env_file(self, env_path: Path = Path(".env")):
        """Persist current configuration to .env file."""
        lines = [
            f"DISCORD_WEBHOOK_URL={self.discord_webhook_url or ''}\n",
            f"DISCORD_MENTION={self.discord_mention or ''}\n",
            f"CHECK_INTERVAL_SECONDS={self.check_interval_seconds}\n",
            f"CHECK_INTERVAL_JITTER={self.check_interval_jitter}\n",
            f"MIN_TICKETS={self.min_tickets}\n",
            f"ONLY_ADULTS={'true' if self.only_adults else 'false'}\n",
            f"MONITORED_GROUPS={','.join(str(g) for g in self.monitored_groups)}\n",
            f"ALLOWED_WEEKDAYS={','.join(str(w) for w in self.allowed_weekdays)}\n",
            f"DATE_FROM={self.date_from or ''}\n",
            f"DATE_TO={self.date_to or ''}\n",
            f"EARLIEST_TIME={self.earliest_time or ''}\n",
            f"LATEST_TIME={self.latest_time or ''}\n",
            f"MAX_PRICE_EUR={self.max_price_eur if self.max_price_eur is not None else ''}\n",
            f"EXCLUDED_DATES={','.join(self.excluded_dates)}\n",
            f"WEB_PORT={self.web_port}\n",
            f"WEB_HOST={self.web_host}\n",
            f"MONITOR_PAUSED={'true' if self.paused else 'false'}\n",
            f"LOG_LEVEL={self.log_level}\n",
        ]
        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            pass
