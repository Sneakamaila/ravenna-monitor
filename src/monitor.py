import asyncio
import logging
import random
from typing import Dict, List, Optional
import httpx

from src.config import Config, DEFAULT_KNOWN_GROUPS
from src.discord_notifier import DiscordNotifier
from src.models import EventSlot, TicketOffer
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

    async def check_all_groups(self) -> int:
        """Runs a complete check cycle across all monitored groups.
        Returns the number of new offers alerted."""
        new_alerts_count = 0
        groups_to_check: Dict[int, str] = {}

        for gid in self.config.monitored_groups:
            name = DEFAULT_KNOWN_GROUPS.get(gid, f"Gruppe {gid}")
            groups_to_check[gid] = name

        logger.info(f"Starte Prüfzyklus über {len(groups_to_check)} Gruppen...")

        for gid, gname in groups_to_check.items():
            try:
                alerts = await self.check_group(gid, gname)
                new_alerts_count += alerts
            except Exception as e:
                logger.error(f"Unerwarteter Fehler bei Prüfung von Gruppe {gid} ({gname}): {e}", exc_info=True)
            # Small delay between groups to be gentle on Reservix servers
            await asyncio.sleep(0.5)

        logger.info(f"Prüfzyklus abgeschlossen. {new_alerts_count} neue Angebote gemeldet.")
        return new_alerts_count

    async def check_group(self, group_id: int, group_name: str) -> int:
        """Check all slots in a single group."""
        events = await self.client.fetch_calendar_events(group_id, group_name)
        if not events:
            return 0

        bookable_events = [e for e in events if e.is_bookable]
        logger.debug(f"Gruppe {group_id} ({group_name}): {len(bookable_events)}/{len(events)} Slots als buchbar markiert.")

        if not bookable_events:
            return 0

        group_alerts = 0
        for slot in bookable_events:
            alerts = await self.check_slot_offers(slot)
            group_alerts += alerts
            await asyncio.sleep(0.3)

        return group_alerts

    async def check_slot_offers(self, slot: EventSlot) -> int:
        """Check for active resale marketplace offers for a specific slot."""
        offers = await self.client.fetch_marketplace_offers(slot.sync_id, slot.url_path)
        if not offers:
            logger.debug(f"Slot {slot.sync_id} ({slot.formatted_start}) war buchbar, aber keine aktiven Angebote im Zweitmarkt.")
            return 0

        # Optional filters
        if self.config.only_adults:
            offers = [o for o in offers if o.is_adult]
            if not offers:
                logger.debug(f"Slot {slot.sync_id}: Angebote vorhanden, aber keines erfüllt den Erwachsenen-Filter.")
                return 0

        if len(offers) < self.config.min_tickets:
            logger.debug(
                f"Slot {slot.sync_id}: {len(offers)} Angebote gefunden, unterschreitet min_tickets={self.config.min_tickets}."
            )
            return 0

        # Filter out already alerted offers
        new_offers = self.tracker.filter_new_offers(slot, offers)
        if not new_offers:
            logger.debug(f"Slot {slot.sync_id}: {len(offers)} Angebot(e) aktiv, aber bereits bekannt/gemeldet.")
            return 0

        logger.info(
            f"🎉 NEUE TICKETS GEFUNDEN! {slot.group_name} am {slot.formatted_start} - {len(new_offers)} neue(s) Angebot(e)!"
        )

        # Send alert
        success = await self.notifier.send_notification(slot, new_offers)
        if success:
            self.tracker.mark_alerted(slot, new_offers)
            return len(new_offers)
        else:
            logger.warning(f"Konnte Benachrichtigung für Slot {slot.sync_id} nicht senden.")
            return 0

    async def run(self):
        """Continuously monitor in a loop until cancelled."""
        self._is_running = True
        logger.info("=== Ravenna-Schlucht Weihnachtsmarkt Ticket Monitor gestartet ===")
        logger.info(f"Überwachte Gruppen: {self.config.monitored_groups}")
        logger.info(f"Basis-Intervall: {self.config.check_interval_seconds}s (Jitter: +/- {self.config.check_interval_jitter}s)")
        logger.info(f"Discord Webhook: {'Konfiguriert' if self.config.discord_webhook_url else 'Nicht konfiguriert (DRY-RUN)'}")

        while self._is_running:
            try:
                await self.check_all_groups()
            except Exception as e:
                logger.error(f"Fehler im Hauptzyklus: {e}", exc_info=True)

            jitter = random.uniform(-self.config.check_interval_jitter, self.config.check_interval_jitter)
            sleep_time = max(5.0, self.config.check_interval_seconds + jitter)
            logger.debug(f"Warte {sleep_time:.1f}s bis zum nächsten Prüfzyklus...")
            try:
                await asyncio.sleep(sleep_time)
            except asyncio.CancelledError:
                logger.info("Monitor wird beendet...")
                break

    def stop(self):
        self._is_running = False
