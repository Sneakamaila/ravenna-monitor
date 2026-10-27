import asyncio
from collections import deque
from datetime import datetime, timezone
import logging
import random
from typing import Deque, Dict, List, Optional
import httpx

from src.config import Config, DEFAULT_KNOWN_GROUPS
from src.discord_notifier import DiscordNotifier
from src.models import EventSlot, TicketOffer, SlotAvailability
from src.reservix_client import ReservixClient
from src.tracker import OfferTracker

logger = logging.getLogger(__name__)


class TicketMonitor:
    def __init__(
        self,
        config: Config,
        client: Optional[ReservixClient] = None,
        tracker: Optional[OfferTracker] = None,
        notifier: Optional[DiscordNotifier] = None,
    ):
        self.config = config
        self.client = client or ReservixClient()
        self.tracker = tracker or OfferTracker(config.state_file_path)
        self.notifier = notifier or DiscordNotifier(
            webhook_url=config.discord_webhook_url,
            mention=config.discord_mention,
        )
        self._is_running = False
        self._check_trigger_event = asyncio.Event()

        # Real-time state for UI
        self.is_checking: bool = False
        self.last_check_time: Optional[datetime] = None
        self.next_check_time: Optional[datetime] = None
        self.total_checks: int = 0
        self.total_alerts_sent: int = 0
        self.active_slots: List[SlotAvailability] = []
        self.recent_logs: Deque[dict] = deque(maxlen=200)

    def log_event(self, level: str, message: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        self.recent_logs.append({
            "time": now_str,
            "level": level,
            "message": message,
        })

    def trigger_check_now(self):
        """Immediately wake up the monitor loop for an instant check."""
        self._check_trigger_event.set()

    def slot_matches_filter(self, slot: EventSlot) -> bool:
        """Check if slot matches weekday, time range, and excluded dates filters."""
        # 1. Weekday filter
        if slot.start_date_time.weekday() not in self.config.allowed_weekdays:
            return False

        # 2. Excluded dates filter ("YYYY-MM-DD")
        date_str = slot.start_date_time.strftime("%Y-%m-%d")
        if date_str in self.config.excluded_dates:
            return False

        # 3. Time filter (HH:MM)
        time_str = slot.start_date_time.strftime("%H:%M")
        if self.config.earliest_time and time_str < self.config.earliest_time:
            return False
        if self.config.latest_time and time_str > self.config.latest_time:
            return False

        return True

    def filter_offers(self, offers: List[TicketOffer]) -> List[TicketOffer]:
        """Apply offer-level filters: adult-only and max price."""
        filtered = offers
        if self.config.only_adults:
            filtered = [o for o in filtered if o.is_adult]

        if self.config.max_price_eur is not None:
            filtered = [o for o in filtered if o.price_eur <= self.config.max_price_eur]

        return filtered

    async def check_all_groups(self) -> int:
        """Runs a complete check cycle across all monitored groups.
        Returns the number of new offers alerted."""
        if self.is_checking:
            return 0

        self.is_checking = True
        new_alerts_count = 0
        current_active_slots: List[SlotAvailability] = []
        groups_to_check: Dict[int, str] = {}

        for gid in self.config.monitored_groups:
            name = DEFAULT_KNOWN_GROUPS.get(gid, f"Gruppe {gid}")
            groups_to_check[gid] = name

        msg = f"Starte Prüfzyklus über {len(groups_to_check)} Gruppen..."
        logger.info(msg)
        self.log_event("INFO", msg)

        try:
            for gid, gname in groups_to_check.items():
                try:
                    alerts, group_availabilities = await self.check_group(gid, gname)
                    new_alerts_count += alerts
                    current_active_slots.extend(group_availabilities)
                except Exception as e:
                    err_msg = f"Fehler bei Gruppe {gid} ({gname}): {e}"
                    logger.error(err_msg, exc_info=True)
                    self.log_event("ERROR", err_msg)
                await asyncio.sleep(0.5)

            self.active_slots = current_active_slots
            self.total_checks += 1
            self.total_alerts_sent += new_alerts_count
            self.last_check_time = datetime.now()

            finish_msg = (
                f"Prüfzyklus #{self.total_checks} fertig: "
                f"{len(self.active_slots)} buchbare Slots aktiv, {new_alerts_count} neue Alerts."
            )
            logger.info(finish_msg)
            self.log_event("SUCCESS" if new_alerts_count > 0 else "INFO", finish_msg)

        finally:
            self.is_checking = False

        return new_alerts_count

    async def check_group(self, group_id: int, group_name: str) -> tuple[int, List[SlotAvailability]]:
        """Check all slots in a single group."""
        events = await self.client.fetch_calendar_events(group_id, group_name)
        if not events:
            return 0, []

        bookable_events = [e for e in events if e.is_bookable]
        logger.debug(f"Gruppe {group_id} ({group_name}): {len(bookable_events)}/{len(events)} Slots buchbar.")

        if not bookable_events:
            return 0, []

        group_alerts = 0
        group_availabilities: List[SlotAvailability] = []

        for slot in bookable_events:
            alerts, availability = await self.check_slot_offers(slot)
            group_alerts += alerts
            if availability:
                group_availabilities.append(availability)
            await asyncio.sleep(0.3)

        return group_alerts, group_availabilities

    async def check_slot_offers(self, slot: EventSlot) -> tuple[int, Optional[SlotAvailability]]:
        """Check for active resale marketplace offers for a specific slot."""
        offers = await self.client.fetch_marketplace_offers(slot.sync_id, slot.url_path)
        if not offers:
            return 0, None

        # Build raw availability object for UI viewing
        availability = SlotAvailability(slot=slot, offers=offers)

        # Apply slot filters (weekday, time, excluded dates)
        if not self.slot_matches_filter(slot):
            logger.debug(f"Slot {slot.sync_id} ({slot.formatted_start}) entspricht nicht den Zeit-/Datums-Filtern.")
            return 0, availability

        # Apply offer filters (adults, max price)
        matching_offers = self.filter_offers(offers)
        if not matching_offers:
            logger.debug(f"Slot {slot.sync_id}: Angebote vorhanden, aber keines erfüllt die Kriterien.")
            return 0, availability

        # Minimum tickets requirement
        if len(matching_offers) < self.config.min_tickets:
            logger.debug(
                f"Slot {slot.sync_id}: {len(matching_offers)} passende Tickets < min_tickets ({self.config.min_tickets})."
            )
            return 0, availability

        # Check for new unalerted offers
        new_offers = self.tracker.filter_new_offers(slot, matching_offers)
        if not new_offers:
            return 0, availability

        found_msg = (
            f"🎉 NEUE TICKETS: {slot.group_name} am {slot.formatted_start} "
            f"({len(new_offers)} Angebot(e))!"
        )
        logger.info(found_msg)
        self.log_event("ALERT", found_msg)

        # Send alert
        # Update notifier webhook in case config was edited via GUI
        self.notifier.webhook_url = self.config.discord_webhook_url
        self.notifier.mention = self.config.discord_mention

        success = await self.notifier.send_notification(slot, new_offers)
        if success:
            self.tracker.mark_alerted(slot, new_offers)
            return len(new_offers), availability
        else:
            return 0, availability

    async def run(self):
        """Continuously monitor in a loop until cancelled."""
        self._is_running = True
        logger.info("=== Ravenna-Schlucht Ticket-Monitor Loop gestartet ===")

        while self._is_running:
            if not self.config.paused:
                try:
                    await self.check_all_groups()
                except Exception as e:
                    err_msg = f"Fehler im Hauptzyklus: {e}"
                    logger.error(err_msg, exc_info=True)
                    self.log_event("ERROR", err_msg)
            else:
                logger.debug("Monitor ist pausiert.")

            jitter = random.uniform(-self.config.check_interval_jitter, self.config.check_interval_jitter)
            sleep_time = max(5.0, self.config.check_interval_seconds + jitter)
            self.next_check_time = datetime.now() + asyncio.to_timedelta(seconds=sleep_time) if hasattr(asyncio, 'to_timedelta') else None

            # Reset trigger event
            self._check_trigger_event.clear()

            try:
                # Wait for timeout OR manual trigger
                await asyncio.wait_for(self._check_trigger_event.wait(), timeout=sleep_time)
                logger.info("Sofort-Prüfung manuell ausgelöst!")
                self.log_event("INFO", "Sofort-Prüfung durch Benutzer ausgelöst.")
            except asyncio.TimeoutError:
                # Normal sleep elapsed
                pass
            except asyncio.CancelledError:
                logger.info("Monitor-Task abgebrochen.")
                break

    def stop(self):
        self._is_running = False
        self._check_trigger_event.set()
