# 🎄 Ravenna-Schlucht Ticket-Monitor

Ein leichtgewichtiger und robuster Monitor für den **Zweitmarkt / Rückläufer-Tickets** des Weihnachtsmarkts in der Ravennaschlucht auf **Reservix**. Sobald Besucher ihre Tickets auf den Zweitmarkt stellen, schlägt der Monitor sofort Alarm und sendet eine detaillierte Benachrichtigung samt **Direkt-Kauflink** in deinen Discord-Channel.

---

## 🌟 Features

- **🚀 Blitzschnell & Ressourcen-schonend:** Keine schweren Headless-Browser (wie Puppeteer/Playwright) nötig. Fragt direkt die internen JSON-Endpunkte von Reservix ab.
- **📍 Überwachung aller relevanten Anreise-Optionen:**
  - 🚌 Shuttle ab Titisee (Gruppe `545832`)
  - 🚌 Shuttle ab Hinterzarten (Gruppe `545884`)
  - 🚌 Shuttle ab Himmelreich (Gruppe `545886`)
  - 🚌 Shuttle ab Freiburg (Gruppe `546305`)
  - 🚗 Parken & Eintritt (PKW) (Gruppe `545934`)
  - 🥾 Nur Eintritt / Wander-Ticket (Gruppe `545947`)
- **🔔 Ausführliche Discord-Embeds:**
  - Exakter Termin & Einlasszeit (z. B. *Freitag, 11.12.2026 um 14:35 Uhr*)
  - Anreiseart / Shuttlestation
  - Preiskategorien & Ticketanzahl (z. B. *1x Erwachsene à 9,35 €*, *2x Kinder à 5,50 €*)
  - Gesamtsumme
  - **Direkter Kauflink** zum Timeslot für schnellstes Bestellen
- **🛡️ Anti-Spam & Deduplizierung:** Bereits gemeldete Angebote werden in `seen_offers.json` gespeichert, sodass man nicht mehrfach für dasselbe Angebot gepingt wird.
- **⚙️ Flexible Filter:**
  - Mindestanzahl an Tickets pro Zeitfenster (z. B. mindestens 2 Tickets für Paare)
  - Nur Erwachsenen-Tickets (optional Kinder-/Behindertentarife ignorieren)
- **🐳 Docker & Docker-Compose:** Bereit für 24/7-Betrieb auf Heimserver, Raspberry Pi, VPS oder NAS.

---

## 📱 Vorschau der Discord-Benachrichtigung

```text
🎟️ 2 Zweitmarkt-Ticket(s) verfügbar!
Es sind soeben Tickets auf dem Zweitmarkt für den Weihnachtsmarkt in der Ravennaschlucht freigeworden!
Veranstaltung: Weihnachtsmarkt in der Ravennaschlucht – Shuttle & Eintritt ab Himmelreich

📅 Termin / Einlass: Freitag, 11.12.2026 um 14:35 Uhr
📍 Anreise / Art:    Shuttle ab Himmelreich
🔢 Verfügbare Tickets: 2 Ticket(s) gesamt
🏷️ Preiskategorien:  • 1x Erwachsene (ab 16 Jahren) (à 9,35 €)
                     • 1x Kinder (6-15 Jahre) (à 5,50 €)
💰 Gesamtsumme:      14,85 €
🛒 Direktlink:       [👉 Hier Tickets direkt bei Reservix buchen!]
```

---

## 🚀 Schnellstart

### 1. Repository klonen & vorbereiten

```bash
git clone https://github.com/Sneakamaila/ravenna-monitor.git
cd ravenna-monitor
cp .env.example .env
```

### 2. Discord Webhook anlegen & eintragen

1. Öffne Discord und gehe in die **Kanal-Einstellungen** des gewünschten Textkanals.
2. Wähle **Integrationen** ➡️ **Webhooks anzeigen** ➡️ **Neuer Webhook**.
3. Kopiere die Webhook-URL und trage sie in deiner `.env`-Datei ein:
   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefgh...
   ```
4. *(Optional)* Falls du gepingt werden möchtest, trage z. B. `@everyone` oder deine Nutzer-/Rollen-ID bei `DISCORD_MENTION` ein.

---

### Option A: Betrieb mit Docker (Empfohlen für 24/7-Betrieb)

Der Monitor kann dauerhaft im Hintergrund via Docker betrieben werden:

```bash
# 1. Testnachricht an Discord senden zur Verifikation
docker compose run --rm ravenna-monitor python main.py --test-discord

# 2. Monitor im Hintergrund starten
docker compose up -d

# Logs ansehen
docker compose logs -f

# Monitor stoppen
docker compose down
```

---

### Option B: Lokaler Betrieb mit Python

Voraussetzung: Python 3.10+

```bash
# Virtuelle Umgebung anlegen & aktivieren
python3 -m venv .venv
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# 1. Discord-Verbindung testen
python main.py --test-discord

# 2. Einmaligen Testlauf starten (Dry-Run ohne Alarm)
python main.py --once --dry-run

# 3. Monitor dauerhaft starten
python main.py
```

---

## ⚙️ Konfigurationsoptionen (`.env`)

| Variable | Standardwert | Beschreibung |
| :--- | :--- | :--- |
| `DISCORD_WEBHOOK_URL` | *keiner* | Webhook-URL für Discord-Benachrichtigungen |
| `DISCORD_MENTION` | *leer* | Erwähnung bei Alarm (z. B. `@everyone` oder `<@&RollenID>`) |
| `CHECK_INTERVAL_SECONDS` | `30` | Sekunden zwischen den Abfrage-Zyklen |
| `CHECK_INTERVAL_JITTER` | `5` | Zufällige Abweichung (+/- Sekunden), um Traffic organisch zu halten |
| `MIN_TICKETS` | `1` | Mindestanzahl verfügbarer Tickets im selben Zeitfenster |
| `ONLY_ADULTS` | `false` | Falls `true`, werden Angebote ohne Erwachsenen-Tickets ignoriert |
| `MONITORED_GROUPS` | *alle 6* | Komma-separierte Reservix-Gruppen-IDs |
| `STATE_FILE_PATH` | `seen_offers.json` | Pfad zur Cache-Datei für bereits gemeldete Angebote |
| `LOG_LEVEL` | `INFO` | Loglevel (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 💻 CLI-Optionen

`main.py` unterstützt verschiedene praktische Parameter:

```bash
# Einmalige Abfrage ausführen und beenden (z. B. für Cronjobs)
python main.py --once

# Discord Webhook mit einer Testnachricht prüfen
python main.py --test-discord

# Nur in der Konsole ausgeben, keine Discord-Nachrichten senden
python main.py --dry-run

# Nur Zeitfenster mit mindestens 2 Tickets melden
python main.py --min-tickets 2

# Nur Erwachsenen-Tickets melden
python main.py --only-adults

# Abfrageintervall überschreiben (z. B. 20 Sekunden)
python main.py --interval 20

# Ausführliches Debug-Logging einschalten
python main.py -v
```

---

## 🧪 Tests ausführen

Tests können jederzeit mit `pytest` ausgeführt werden:

```bash
source .venv/bin/activate
pytest
```

---

## 🔍 Funktionsweise im Detail

Reservix lädt für jeden Veranstaltungskalender (`/tickets/kalender/reihe/weihnachtsmarkt/{groupId}`) ein initiales JSON-Objekt mit sämtlichen ~250–350 Zeitslots der gesamten Saison. In diesem JSON ist das Flag `isBookable` enthalten.
- Sobald ein Besucher ein Ticket auf den Zweitmarkt stellt oder eine Reservierung verfällt, springt `isBookable` für den jeweiligen Timeslot serverseitig auf `true`.
- Der Monitor erkennt diesen Statuswechsel sofort und ruft den gezielten API-Endpunkt `/ajax/resale-marketplace/{syncId}/offers` ab.
- Dieser Endpunkt liefert alle Details (Preiskategorie, Preis in Cent, Status `BOOKABLE` und Angebots-ID).
- Über die Angebots-ID stellt der Monitor sicher, dass derselbe Fund nicht doppelt alarmiert wird.
