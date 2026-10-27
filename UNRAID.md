# 🎄 Vollständige Unraid-Installation für Ravenna-Monitor

Diese Anleitung ist exakt auf deinen Unraid-Server (`192.168.178.47`) zugeschnitten.

---

## ⚡ Der schnellste Weg (in 30 Sekunden fertig)

### Schritt 1: Unraid Terminal öffnen
Klicke in der Unraid Web-Oberfläche oben rechts in der Menüleiste auf das Terminal-Symbol **`>_`**.

### Schritt 2: Befehle reinkopieren & Enter drücken
Kopiere diesen Dreizeiler in das Terminal-Fenster und drücke Enter:

```bash
git clone https://github.com/Sneakamaila/ravenna-monitor.git /mnt/user/appdata/ravenna-monitor
cd /mnt/user/appdata/ravenna-monitor
docker compose up -d --build
```

*(Docker lädt die Basis-Dateien herunter, baut den Container in ca. 15 Sekunden und startet ihn im Hintergrund.)*

### Schritt 3: Fertig! WebUI über Unraid öffnen
1. Gehe in Unraid auf den Reiter **Docker**.
2. Dort siehst du jetzt den neuen Container **`ravenna-monitor`** mit dem 🎄-Logo.
3. Klicke auf das Icon und wähle im Menü **WebUI**.
4. Dein Browser öffnet sofort:
   👉 **`http://192.168.178.47:8088`**

---

## 🛡️ Warum kein Port doppelt belegt wird

Auf deinem Unraid-Server belegt **SABnzbd** bereits den Standardport **`8080`**.
- Der Ravenna-Monitor nutzt auf deinem Host stattdessen den Port **`8088`**.
- Port `8088` ist auf deinem Server **vollständig frei**.
- Keine Kollisionen mit SABnzbd (`8080`), cruise-monitor (`8000`), zigbee2mqtt (`8090`) oder Open-WebUI (`9339`).

---

## ⚙️ Wie du den Monitor danach bedienst

* **WebUI öffnen:** Einfach im Unraid Docker-Tab auf das 🎄-Icon ➡️ **WebUI** klicken.
* **Einstellungen:** Trage im Web-Dashboard unter *Einstellungen* deinen Discord-Webhook ein, stelle den Paar-Modus (mind. 2 Tickets) und eure Wunschtermine ein. Klicke auf *Speichern*.
* **Pause / Start:** Kannst du direkt im Web-Dashboard oder über das Unraid-Menü steuern.
* **Updates:** Falls es neue Updates gibt, im Terminal einfach:
  ```bash
  cd /mnt/user/appdata/ravenna-monitor && git pull && docker compose up -d --build
  ```
