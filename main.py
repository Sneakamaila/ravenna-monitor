import argparse
import asyncio
import logging
import signal
import sys
import uvicorn
from src.config import Config
from src.discord_notifier import DiscordNotifier
from src.monitor import TicketMonitor
from src.reservix_client import ReservixClient
from src.tracker import OfferTracker
from src.web.app import create_app


def setup_logging(log_level: str):
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def async_main():
    parser = argparse.ArgumentParser(
        description="Überwacht den Reservix-Zweitmarkt für den Weihnachtsmarkt in der Ravennaschlucht samt schöner Web-GUI."
    )
    parser.add_argument("--once", action="store_true", help="Führt nur einen einzigen Prüfzyklus durch und beendet sich.")
    parser.add_argument("--test-discord", action="store_true", help="Sendet eine Test-Nachricht an den konfigurierten Discord Webhook.")
    parser.add_argument("--no-web", "--cli", action="store_true", help="Deaktiviert das Web-UI und läuft rein in der Konsole.")
    parser.add_argument("--port", type=int, default=None, help="Port für die Web-Oberfläche (Standard: 8080).")
    parser.add_argument("--host", type=str, default=None, help="Host für die Web-Oberfläche (Standard: 0.0.0.0).")
    parser.add_argument("--interval", type=int, default=None, help="Prüfintervall in Sekunden.")
    parser.add_argument("--min-tickets", type=int, default=None, help="Mindestanzahl verfügbarer Tickets.")
    parser.add_argument("--only-adults", action="store_true", help="Nur Tickets für Erwachsene berücksichtigen.")
    parser.add_argument("--dry-run", action="store_true", help="Deaktiviert Discord-Alerts und loggt nur in die Konsole.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Aktiviert ausführliches Debug-Logging.")

    args = parser.parse_args()

    config = Config.from_env()

    if args.verbose:
        config.log_level = "DEBUG"
    if args.interval is not None:
        config.check_interval_seconds = max(5, args.interval)
    if args.min_tickets is not None:
        config.min_tickets = max(1, args.min_tickets)
    if args.only_adults:
        config.only_adults = True
    if args.dry_run:
        config.discord_webhook_url = None
    if args.port is not None:
        config.web_port = args.port
    if args.host is not None:
        config.web_host = args.host

    setup_logging(config.log_level)
    logger = logging.getLogger("main")

    # Handle Discord test
    if args.test_discord:
        if not config.discord_webhook_url:
            logger.error("Fehler: Keine DISCORD_WEBHOOK_URL in .env oder Umgebung konfiguriert!")
            sys.exit(1)
        notifier = DiscordNotifier(webhook_url=config.discord_webhook_url, mention=config.discord_mention)
        logger.info("Sende Testnachricht an Discord...")
        success = await notifier.send_test_message()
        if success:
            logger.info("Testnachricht wurde erfolgreich gesendet! ✅")
            sys.exit(0)
        else:
            logger.error("Fehler beim Senden der Testnachricht. Bitte Webhook-URL prüfen. ❌")
            sys.exit(1)

    client = ReservixClient()
    tracker = OfferTracker(config.state_file_path)
    notifier = DiscordNotifier(webhook_url=config.discord_webhook_url, mention=config.discord_mention)

    monitor = TicketMonitor(config=config, client=client, tracker=tracker, notifier=notifier)

    if args.once:
        try:
            alerts = await monitor.check_all_groups()
            logger.info(f"Einmaliger Durchlauf abgeschlossen. {alerts} neue Angebote gefunden.")
        finally:
            await client.close()
        return

    # Setup graceful shutdown handlers
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown-Signal empfangen, beende Monitor...")
        monitor.stop()
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass

    # Start background monitor loop
    monitor_task = asyncio.create_task(monitor.run())

    if not args.no_web:
        # Start Web UI via Uvicorn server in same asyncio loop
        app = create_app(monitor)
        uvi_config = uvicorn.Config(
            app=app,
            host=config.web_host,
            port=config.web_port,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(uvi_config)

        logger.info("===============================================================")
        logger.info(f"🎄 Ravenna-Schlucht Ticket-Monitor Web-UI gestartet!")
        logger.info(f"👉 Öffne im Browser: http://localhost:{config.web_port}")
        logger.info("===============================================================")

        async def run_server():
            await server.serve()
            stop_event.set()

        server_task = asyncio.create_task(run_server())

        await stop_event.wait()
        server.should_exit = True
        await server_task
    else:
        logger.info("Monitor läuft im reinen CLI-Modus (ohne Web-UI).")
        await stop_event.wait()

    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    await client.close()
    logger.info("Monitor sauber beendet.")


def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
