import asyncio
import logging
from collections import Counter
from datetime import datetime, timezone
from typing import List, Optional
import httpx

from src.models import EventSlot, TicketOffer

logger = logging.getLogger(__name__)

# Dark Holiday Red matching Ravenna-Schlucht theme
EMBED_COLOR_ALERT = 0xA21311
# Festive Emerald Green for test messages
EMBED_COLOR_TEST = 0x10B981


class DiscordNotifier:
    def __init__(self, webhook_url: Optional[str] = None, mention: Optional[str] = None):
        self.webhook_url = webhook_url
        self.mention = mention

    async def send_notification(
        self,
        slot: EventSlot,
        offers: List[TicketOffer],
        client: Optional[httpx.AsyncClient] = None,
    ) -> bool:
        """Send a rich Discord embed notification for newly found tickets."""
        if not self.webhook_url:
            logger.info(
                f"[DRY-RUN] Neue Tickets gefunden für {slot.name} ({slot.formatted_start}) - "
                f"{len(offers)} Angebot(e). Kein Webhook konfiguriert."
            )
            for o in offers:
                logger.info(f"   -> Angebot #{o.id}: {o.price_category} ({o.formatted_price})")
            return True

        embed = self._build_offer_embed(slot, offers)
        payload = {
            "content": self.mention if self.mention else None,
            "embeds": [embed],
        }

        return await self._post_webhook(payload, client=client)

    async def send_test_message(self, client: Optional[httpx.AsyncClient] = None) -> bool:
        """Send a test message to verify Discord webhook configuration."""
        if not self.webhook_url:
            logger.error("Keine DISCORD_WEBHOOK_URL konfiguriert. Testnachricht kann nicht gesendet werden.")
            return False

        embed = {
            "title": "✅ Ravenna-Monitor: Testnachricht erfolgreich!",
            "description": "Die Verbindung zu Discord funktioniert einwandfrei. Der Monitor ist bereit zur Überwachung des Zweitmarkts.",
            "color": EMBED_COLOR_TEST,
            "fields": [
                {
                    "name": "⚙️ Status",
                    "value": "Monitor aktiv & betriebsbereit",
                    "inline": True,
                },
                {
                    "name": "🔔 Benachrichtigung",
                    "value": "Du wirst sofort gepingt, sobald Tickets eingestellt werden.",
                    "inline": True,
                },
            ],
            "footer": {
                "text": "Ravenna-Monitor • Ticket-Überwachung",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        payload = {
            "content": f"Test-Alarm: {self.mention}" if self.mention else None,
            "embeds": [embed],
        }

        success = await self._post_webhook(payload, client=client)
        if success:
            logger.info("Testnachricht erfolgreich an Discord gesendet!")
        return success

    def _build_offer_embed(self, slot: EventSlot, offers: List[TicketOffer]) -> dict:
        total_tickets = len(offers)
        total_cents = sum(o.price_cents for o in offers)
        total_eur = total_cents / 100.0

        # Group categories with counts and prices
        # e.g. "2x Erwachsene (ab 16 Jahren) à 9,35 €"
        category_counts = Counter(o.price_category for o in offers)
        category_prices = {}
        for o in offers:
            if o.price_category not in category_prices:
                category_prices[o.price_category] = o.formatted_price

        ticket_lines = []
        for cat, count in category_counts.items():
            price_str = category_prices.get(cat, "")
            ticket_lines.append(f"• **{count}x** {cat} (à {price_str})")
        tickets_text = "\n".join(ticket_lines)

        fields = [
            {
                "name": "📅 Termin / Einlass",
                "value": f"**{slot.formatted_start}**",
                "inline": False,
            },
            {
                "name": "📍 Anreise / Art",
                "value": slot.group_name or "Ravennaschlucht",
                "inline": True,
            },
            {
                "name": "🔢 Verfügbare Tickets",
                "value": f"**{total_tickets} Ticket(s)** gesamt",
                "inline": True,
            },
            {
                "name": "🏷️ Preiskategorien",
                "value": tickets_text,
                "inline": False,
            },
            {
                "name": "💰 Gesamtsumme",
                "value": f"**{total_eur:.2f} €**".replace(".", ","),
                "inline": True,
            },
            {
                "name": "🛒 Direktlink zum Kauf",
                "value": f"[👉 **Hier Tickets direkt bei Reservix buchen!**]({slot.buy_url})",
                "inline": False,
            },
        ]

        title = f"🎟️ {total_tickets} Zweitmarkt-Ticket(s) verfügbar!"

        return {
            "title": title,
            "url": slot.buy_url,
            "color": EMBED_COLOR_ALERT,
            "description": (
                f"Es sind soeben Tickets auf dem Zweitmarkt für den Weihnachtsmarkt in der Ravennaschlucht freigeworden!\n"
                f"**Veranstaltung:** [{slot.name}]({slot.buy_url})"
            ),
            "fields": fields,
            "footer": {
                "text": "Ravenna-Monitor • Zweitmarkt-Alert • Schnell buchen!",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _post_webhook(self, payload: dict, client: Optional[httpx.AsyncClient] = None) -> bool:
        if not self.webhook_url:
            return False

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=10.0)
            should_close = True

        try:
            for attempt in range(3):
                resp = await client.post(self.webhook_url, json=payload)
                if resp.status_code == 429:
                    # Discord Rate Limit
                    retry_after = resp.json().get("retry_after", 1.5)
                    logger.warning(f"Discord Rate Limit erreicht. Warte {retry_after}s...")
                    await asyncio.sleep(float(retry_after))
                    continue
                resp.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Fehler beim Senden des Discord-Webhooks: {e}")
            return False
        finally:
            if should_close:
                await client.aclose()
        return False
