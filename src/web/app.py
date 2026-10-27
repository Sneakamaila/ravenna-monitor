import asyncio
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from src.config import Config, DEFAULT_KNOWN_GROUPS, WEEKDAY_NAMES
from src.models import SlotAvailability
from src.monitor import TicketMonitor

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"


class ConfigUpdateRequest(BaseModel):
    discord_webhook_url: Optional[str] = None
    discord_mention: Optional[str] = None
    check_interval_seconds: Optional[int] = None
    check_interval_jitter: Optional[int] = None
    min_tickets: Optional[int] = None
    only_adults: Optional[bool] = None
    monitored_groups: Optional[List[int]] = None
    allowed_weekdays: Optional[List[int]] = None
    earliest_time: Optional[str] = None
    latest_time: Optional[str] = None
    max_price_eur: Optional[float] = None
    excluded_dates: Optional[List[str]] = None
    paused: Optional[bool] = None


def create_app(monitor: TicketMonitor) -> FastAPI:
    app = FastAPI(title="Ravenna Ticket Monitor", version="1.0.0")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        html_file = TEMPLATES_DIR / "index.html"
        if not html_file.exists():
            return HTMLResponse("<h1>Template index.html not found</h1>", status_code=500)
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content)

    @app.get("/api/status")
    async def get_status():
        last_check_str = monitor.last_check_time.strftime("%H:%M:%S") if monitor.last_check_time else None
        return {
            "is_running": monitor._is_running,
            "paused": monitor.config.paused,
            "is_checking": monitor.is_checking,
            "last_check_time": last_check_str,
            "total_checks": monitor.total_checks,
            "total_alerts_sent": monitor.total_alerts_sent,
            "active_slots_count": len(monitor.active_slots),
            "known_groups": DEFAULT_KNOWN_GROUPS,
            "weekday_names": WEEKDAY_NAMES,
        }

    @app.get("/api/active-slots")
    async def get_active_slots():
        slots_data = []
        for avail in monitor.active_slots:
            slot = avail.slot
            offers_data = [
                {
                    "id": o.id,
                    "price_cents": o.price_cents,
                    "price_eur": o.price_eur,
                    "formatted_price": o.formatted_price,
                    "price_category": o.price_category,
                    "is_adult": o.is_adult,
                    "status": o.status,
                }
                for o in avail.offers
            ]
            slots_data.append({
                "slot_id": slot.id,
                "sync_id": slot.sync_id,
                "name": slot.name,
                "formatted_start": slot.formatted_start,
                "start_iso": slot.start_date_time.isoformat(),
                "group_name": slot.group_name,
                "group_id": slot.group_id,
                "buy_url": slot.buy_url,
                "total_tickets": avail.total_tickets,
                "adult_tickets": avail.adult_tickets,
                "min_price_eur": avail.min_price_eur,
                "max_price_eur": avail.max_price_eur,
                "offers": offers_data,
            })
        return slots_data

    @app.get("/api/config")
    async def get_config():
        return monitor.config.to_dict()

    @app.post("/api/config")
    async def update_config(req: ConfigUpdateRequest):
        data = req.model_dump(exclude_unset=True)
        monitor.config.update_from_dict(data)
        # Update notifier immediately
        monitor.notifier.webhook_url = monitor.config.discord_webhook_url
        monitor.notifier.mention = monitor.config.discord_mention
        # Save to .env
        monitor.config.save_to_env_file()
        logger.info("Konfiguration über Web-UI aktualisiert und in .env gespeichert.")
        return {"status": "ok", "config": monitor.config.to_dict()}

    @app.post("/api/check-now")
    async def trigger_check():
        if monitor.is_checking:
            return {"status": "already_checking"}
        monitor.trigger_check_now()
        return {"status": "triggered"}

    @app.post("/api/toggle-pause")
    async def toggle_pause():
        monitor.config.paused = not monitor.config.paused
        monitor.config.save_to_env_file()
        action = "pausiert" if monitor.config.paused else "fortgesetzt"
        monitor.log_event("INFO", f"Monitor wurde über Web-UI {action}.")
        return {"status": "ok", "paused": monitor.config.paused}

    @app.post("/api/reset-cache")
    async def reset_cache():
        monitor.tracker.clear()
        monitor.log_event("WARNING", "Cache bereits gesehener Angebote wurde geleert.")
        return {"status": "ok"}

    @app.post("/api/test-discord")
    async def test_discord():
        if not monitor.config.discord_webhook_url:
            raise HTTPException(status_code=400, detail="Keine DISCORD_WEBHOOK_URL konfiguriert.")
        success = await monitor.notifier.send_test_message()
        if not success:
            raise HTTPException(status_code=500, detail="Discord Webhook Test fehlgeschlagen. Bitte URL prüfen.")
        return {"status": "ok"}

    @app.get("/api/logs")
    async def get_logs():
        return list(monitor.recent_logs)

    return app
