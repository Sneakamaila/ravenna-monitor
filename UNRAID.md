# 🎄 Unraid Installationsanleitung für Ravenna-Monitor

Diese Anleitung ist exakt auf deinen Unraid-Server (`192.168.178.47`) zugeschnitten.

---

## 🔍 Port-Prüfung & Konfliktvermeidung

Auf deinem Unraid-Server sind laut Docker-Übersicht u. a. folgende Ports bereits belegt:
- **`8080`** ➡️ **SABnzbd** *(sowie Open-WebUI intern & SearXNG intern)*
- **`8000` & `8444`** ➡️ **cruise-monitor**
- **`8090`** ➡️ **zigbee2mqtt**
- **`8443`** ➡️ **finsight**
- **`4420`** ➡️ **FiestaBoard**
- **`7878`** ➡️ **Radarr**
- **`8989`** ➡️ **Sonarr**
- **`9696`** ➡️ **Prowlarr**
- **`9339`** ➡️ **Open-WebUI**
- **`9595`** ➡️ **SearXNG**

✅ **Gewählter Port für Ravenna-Monitor:** **`8088`**
- Port `8088` ist auf deinem Server **vollständig frei**.
- Keine Port-Kollision mit SABnzbd oder anderen Diensten!
- Das Web-Dashboard ist nach dem Start sofort unter **`http://192.168.178.47:8088`** erreichbar.

---

## 📂 Appdata-Speicherpfad

Wie bei deinen anderen Containern (`/mnt/user/appdata/cruise-monitor-app`, `/mnt/user/appdata/fiestaboard`, etc.) nutzt der Monitor den Standard-Pfad:
- **Host-Pfad:** `/mnt/user/appdata/ravenna-monitor`
- **Container-Pfad:** `/app/data`

Hier werden die Konfiguration (`.env`) und der Cache (`seen_offers.json`) dauerhaft gesichert.

---

## 🚀 Installation auf Unraid

Du kannst zwischen zwei bequemen Wegen wählen:

---

### Option 1: Über Unraid Docker Compose Manager (Empfohlen)

*Da du bereits Compose-Container wie `finsight` nutzt, ist dies der schnellste Weg:*

1. Öffne dein Unraid WebGUI und gehe auf den Reiter **Docker**.
2. Scrolle zu deinem **Compose**-Bereich und klicke auf **Add New Stack** (z. B. Name: `ravenna-monitor`).
3. Klicke auf **Edit Stack** und füge den folgenden Inhalt ein:

```yaml
version: "3.8"

services:
  ravenna-monitor:
    image: ghcr.io/sneakamaila/ravenna-monitor:latest
    container_name: ravenna-monitor
    restart: unless-stopped
    ports:
      - "8088:8080"
    environment:
      - DISCORD_WEBHOOK_URL=
      - DISCORD_MENTION=
      - CHECK_INTERVAL_SECONDS=30
      - CHECK_INTERVAL_JITTER=5
      - MIN_TICKETS=1
      - ONLY_ADULTS=false
      - STATE_FILE_PATH=/app/data/seen_offers.json
      - WEB_PORT=8080
      - WEB_HOST=0.0.0.0
    volumes:
      - /mnt/user/appdata/ravenna-monitor:/app/data
    labels:
      net.unraid.docker.managed: "dockerman"
      net.unraid.docker.webui: "http://[IP]:[PORT:8088]"
      net.unraid.docker.icon: "https://raw.githubusercontent.com/Sneakamaila/ravenna-monitor/main/assets/icon.png"
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

4. Klicke auf **Save Changes** und danach auf **Compose Up**.
5. **Fertig!** Im Unraid Docker-Tab erscheint der Container mit dem Weihnachts-Icon 🎄. Ein Klick auf das Icon öffnet das Menü mit dem **WebUI**-Button, der direkt dein Dashboard öffnet.

---

### Option 2: Über Unraid Container Template (Add Container)

*Falls du den Container lieber als nativen Unraid-Container verwalten möchtest:*

1. Lade das fertige XML-Template auf deinen Unraid-Server in das Template-Verzeichnis herunter:
   *(Im Unraid Web-Terminal oder via SSH ausführen)*:
   ```bash
   mkdir -p /boot/config/plugins/dockerMan/templates-user
   curl -sSL https://raw.githubusercontent.com/Sneakamaila/ravenna-monitor/main/unraid/ravenna-monitor.xml -o /boot/config/plugins/dockerMan/templates-user/my-ravenna-monitor.xml
   ```
2. Gehe in Unraid auf den Reiter **Docker** und klicke ganz unten auf **Add Container**.
3. Wähle oben im Dropdown bei **Template** `ravenna-monitor` aus.
4. Alle Einstellungen sind sofort perfekt vorausgefüllt:
   - **Name:** `ravenna-monitor`
   - **Repository:** `ghcr.io/sneakamaila/ravenna-monitor:latest`
   - **Icon:** Automatisch das 🎄-Logo
   - **WebUI:** `http://[IP]:[PORT:8088]`
   - **WebUI Port:** `8088` (Host) ➡️ `8080` (Container)
   - **Appdata Pfad:** `/mnt/user/appdata/ravenna-monitor`
5. *(Optional)* Trage direkt deine `DISCORD_WEBHOOK_URL` ein (oder mache das später im Web-Dashboard).
6. Klicke unten auf **Apply**.

---

## 🖱️ WebUI starten

Sobald der Container läuft:
1. Klicke im Unraid Docker-Tab einfach auf das **🎄 ravenna-monitor** Icon.
2. Klicke im Kontextmenü auf **WebUI** (genau wie bei deinen anderen Containern).
3. Dein Browser öffnet sofort:
   👉 **`http://192.168.178.47:8088`**
