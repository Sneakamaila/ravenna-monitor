# 🎄 Ravenna-Schlucht Ticket-Monitor mit Web-GUI

Ein leichtgewichtiger und robuster Monitor für den **Zweitmarkt / Rückläufer-Tickets** des Weihnachtsmarkts in der Ravennaschlucht auf **Reservix**. Sobald Besucher ihre Tickets auf den Zweitmarkt stellen, schlägt der Monitor sofort Alarm, meldet das Angebot in deinen Discord-Channel samt **Direkt-Kauflink** und zeigt alle Funde live in einer responsiven **Web-Oberfläche**.

---

## 🌟 Features

- **✨ Moderne Web-Oberfläche (Browser GUI):**
  - **Live Dashboard:** Status, Anzahl gefundener Tickets, Countdown bis zum nächsten Check, Gesamtzähler.
  - **Live-Ticket-Feed:** Zeigt alle aktuell verfügbaren Zweitmarkt-Karten mit Datumsbadge, Shuttlestation, Preiskategorien und direktem **"🛒 Jetzt bei Reservix kaufen"**-Button.
  - **🔔 Browser-Audio-Alarm:** Spielt über die Web-Audio-API einen dezenten Festtags-Klingelton ab, sobald neue Tickets gefunden werden (ideal, wenn der Tab nebenher offen ist).
  - **🚀 Automatischer Kauf-Tab:** Option, bei einem Ticketfund direkt automatisch die Kaufseite im Browser zu öffnen.
  - **📜 Live-Aktivitäts-Log:** Echtzeit-Terminal im Browser mit farbigen Event-Logs.
  - **⚡ Sofort-Prüf-Button & Pause-Modus:** Monitor jederzeit pausieren, fortsetzen oder eine Sofortprüfung per Knopfdruck anstoßen.
- **🧠 Clevere Einstellmöglichkeiten (direkt im GUI oder via `.env`):**
  - **👥 Paar- & Mengenkriterien:** Mindestanzahl an Tickets (z. B. mind. 2 für Paare) & Filter auf "Nur Erwachsene".
  - **💰 Maximalpreis-Deckel:** Teurere Spezialtarife oder Busse automatisch ignorieren (z. B. max. 20 €).
  - **📅 Wochentags-Filter:** Wähle per Schnellklick z. B. *"Nur Wochenende (Fr–So)"*, *"Nur Samstags"* oder beliebige Einzeltage.
  - **⏰ Zeitfenster-Filter:** Früheste und späteste Einlasszeit festlegen (z. B. nur Einlass zwischen 15:00 und 19:30 Uhr).
  - **🚫 Ausschluss-Tage:** Bestimmte Kalendertage sperren, an denen man keine Zeit hat (z. B. `2026-11-26, 2026-12-05`).
  - **🚌 Gezielte Anreise-Stationen:** Wähle flexibel aus, welche Shuttles infrage kommen (*Titisee, Hinterzarten, Himmelreich, Freiburg, PKW, Wanderer*).
- **🚀 Blitzschnell & Ressourcen-schonend:** Keine schweren Headless-Browser nötig. Fragt direkt die internen JSON-Endpunkte von Reservix ab.
- **🔔 Ausführliche Discord-Embeds:** Exakter Termin, Shuttlestation, Ticketanzahl, Preissumme und Direktlink.
- **🛡️ Anti-Spam & Deduplizierung:** Bereits gemeldete Angebote werden in `seen_offers.json` gespeichert, sodass man nicht mehrfach für dasselbe Ticket gepingt wird (inkl. "Cache leeren"-Knopf).
- **🐳 Docker & Docker-Compose:** Bereit für 24/7-Betrieb auf Heimserver, Raspberry Pi, VPS oder NAS mit Port `8080`.

---

## 🖥️ Web-GUI Vorschau

Öffne einfach **`http://localhost:8080`** im Browser deines Laptops, PCs oder Smartphones:

```text
+-----------------------------------------------------------------------------------+
|  🎄 Ravenna-Schlucht Monitor    [● Aktiv wird überwacht]  [⏸️ Pausieren] [⚡ Jetzt prüfen] |
+-----------------------------------------------------------------------------------+
|  [Aktive Slots: 3]   [Letzter Check: 14:35:10]   [Checks: 142]   [Discord-Alerts: 5] |
+-----------------------------------------------------------------------------------+
|  (🎟️ Verfügbare Tickets)   (⚙️ Clevere Einstellungen)   (📜 Live-Logs)               |
+-----------------------------------------------------------------------------------+
|  ┌──────────────────────────────────────────────────────────────┐                 |
|  │ [Shuttle ab Himmelreich]                     [2 Ticket(s)]  │                 |
|  │ 📅 Freitag, 11.12.2026 um 14:35 Uhr                          │                 |
|  │  • 1x Erwachsene (ab 16 Jahren)        9,35 €                │                 |
|  │  • 1x Kinder (6-15 Jahre)              5,50 €                │                 |
|  │ ------------------------------------------------------------ │                 |
|  │ Gesamt: 14,85 €                       [🛒 Jetzt kaufen ↗]     │                 |
|  └──────────────────────────────────────────────────────────────┘                 |
+-----------------------------------------------------------------------------------+
```

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

### 2. Discord Webhook anlegen & eintragen *(optional, aber empfohlen)*

1. Öffne Discord und gehe in die **Kanal-Einstellungen** des gewünschten Textkanals.
2. Wähle **Integrationen** ➡️ **Webhooks anzeigen** ➡️ **Neuer Webhook**.
3. Kopiere die Webhook-URL und trage sie in deiner `.env`-Datei (oder später direkt in der Web-GUI unter Einstellungen) ein:
   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/abcdefgh...
   ```
4. *(Optional)* Trage z. B. `@everyone` bei `DISCORD_MENTION` ein, falls du auf dem Smartphone laut benachrichtigt werden willst.

---

### Option A: Betrieb auf Unraid (Maßgeschneidert)

👉 Siehe die vollständige [Unraid Anleitung (UNRAID.md)](file:///home/hendrik/ravenna-monitor/UNRAID.md).

- **Host-Port:** `8088` (kollidiert **nicht** mit SABnzbd auf `8080`)
- **WebUI-Button:** Direkt im Unraid Docker-Tab integriert mit 🎄-Logo
- **Appdata:** `/mnt/user/appdata/ravenna-monitor`

---

### Option B: Betrieb mit Docker Compose (Allgemein)

```bash
# Monitor mit Web-UI im Hintergrund starten (Port 8088)
docker compose up -d

# Logs ansehen
docker compose logs -f

# Web-UI öffnen:
# http://localhost:8088 (oder IP deines Servers)
```

---

### Option C: Lokaler Betrieb mit Python

Voraussetzung: Python 3.10+

```bash
# Virtuelle Umgebung anlegen & aktivieren
python3 -m venv .venv
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Monitor samt Web-UI starten
python main.py

# 👉 Öffne jetzt im Browser: http://localhost:8080
```

---

## ⚙️ Clevere Konfigurationsoptionen

Alle Optionen können bequem über die **Web-Oberfläche** angepasst werden (werden automatisch in `.env` gespeichert) oder manuell in der `.env`-Datei konfiguriert werden:

| Variable | Standardwert | Beschreibung |
| :--- | :--- | :--- |
| `DISCORD_WEBHOOK_URL` | *keiner* | Webhook-URL für Discord-Benachrichtigungen |
| `DISCORD_MENTION` | *leer* | Erwähnung bei Alarm (z. B. `@everyone` oder `<@&RollenID>`) |
| `MIN_TICKETS` | `1` | Mindestanzahl verfügbarer Tickets im selben Zeitfenster (z. B. `2` für Paare) |
| `ONLY_ADULTS` | `false` | Falls `true`, werden Angebote ohne Erwachsenen-Tickets ignoriert |
| `MAX_PRICE_EUR` | *leer* | Höchstpreis pro Ticket in € (z. B. `20.00`) |
| `ALLOWED_WEEKDAYS` | `0,1,2,3,4,5,6` | Erlaubte Wochentage (z. B. `4,5,6` für Fr, Sa, So) |
| `EARLIEST_TIME` | *leer* | Früheste Einlasszeit im Format `HH:MM` (z. B. `14:00`) |
| `LATEST_TIME` | *leer* | Späteste Einlasszeit im Format `HH:MM` (z. B. `20:00`) |
| `EXCLUDED_DATES` | *leer* | Gesperrte Tage kommasepariert (z. B. `2026-11-26,2026-12-05`) |
| `MONITORED_GROUPS` | *alle 6* | Komma-separierte Reservix-Gruppen-IDs |
| `CHECK_INTERVAL_SECONDS`| `30` | Sekunden zwischen den Abfrage-Zyklen |
| `CHECK_INTERVAL_JITTER` | `5` | Zufällige Abweichung (+/- Sekunden) |
| `WEB_PORT` | `8080` | Port der Web-Oberfläche |
| `WEB_HOST` | `0.0.0.0` | Bind-Host für die Web-Oberfläche |
| `STATE_FILE_PATH` | `seen_offers.json` | Speicherort für bereits gemeldete Angebote |

---

## 💻 CLI-Optionen

`main.py` unterstützt weiterhin praktische Parameter:

```bash
# Web-UI auf einem anderen Port starten
python main.py --port 3000

# Rein im Terminal-Modus ohne Webserver laufen lassen
python main.py --no-web

# Einmalige Abfrage ausführen und beenden (z. B. für Cronjobs)
python main.py --once

# Discord Webhook mit einer Testnachricht prüfen
python main.py --test-discord

# Nur in der Konsole ausgeben, keine Discord-Nachrichten senden
python main.py --dry-run
```

---

## 🧪 Tests ausführen

```bash
source .venv/bin/activate
pytest
```
*(Alle 10 Tests decken Parser, Datenmodelle, Tracker, Discord-Embeds und FastAPI Web-Endpunkte ab).*
