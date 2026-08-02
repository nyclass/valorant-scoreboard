# Der Dümmste fliegt – lokales Quizshow-System

Das Projekt stellt drei Arten lokaler Browseransichten bereit:

- **Moderator-Dashboard:** Spieler, Punkte und jeweils drei Leben verwalten,
  Buzzer freigeben oder zurücksetzen, ersten Buzz sehen und Gewinner auswählen.
- **Teilnehmer-Buzzer:** Mit einem Namen verbinden und nach Freigabe buzzern.
- **OBS-Spielerkarten:** Pro Spieler eine eigene kompakte, transparente
  Browserquelle mit Name und verbleibenden Leben. Die Karten werden in OBS frei
  unter den jeweiligen Kameras positioniert.

## Schnellstart unter Windows

1. `start_scoreboard.bat` doppelt anklicken.
2. Beim ersten Start kurz warten. Die Startdatei erstellt automatisch eine lokale
   Python-Umgebung und installiert die benötigten Pakete.
3. Das Moderator-Dashboard öffnet sich automatisch im Standardbrowser.
4. Das Startfenster geöffnet lassen. Mit **Enter** im Startfenster werden Server
   und alle lokalen Ansichten sauber beendet.

Voraussetzung ist Python 3. Für die automatische Paketinstallation wird beim
ersten Start eine Internetverbindung benötigt. Fehler bleiben im Startfenster
sichtbar und enthalten einen Lösungshinweis.

## Adressen

Auf dem Spiel-PC:

- Moderator: `http://127.0.0.1:8080/moderator`
- Teilnehmer-Buzzer: `http://127.0.0.1:8080/buzzer`
- OBS-Spielerkarten: Die individuellen Adressen stehen direkt bei jedem Spieler
  im Moderator-Dashboard bereit.

Teilnehmer im gleichen WLAN öffnen den Buzzer über die lokale IP-Adresse des
Spiel-PCs, zum Beispiel `http://192.168.1.50:8080/buzzer`. Die lokale IPv4-Adresse
ist unter Windows mit `ipconfig` zu finden. Falls Windows beim ersten Start nach
einer Firewall-Freigabe fragt, muss der Zugriff im privaten Netzwerk erlaubt
werden.

Für jeden Spieler wird in OBS eine eigene Browserquelle angelegt:

1. Im Moderator-Dashboard beim gewünschten Spieler **Link kopieren** wählen.
2. Den kopierten Link als URL einer OBS-Browserquelle eintragen.
3. Als Ausgangsgröße eignen sich etwa 400 × 100 Pixel.
4. Die Karte in OBS frei unter der passenden Kamera positionieren.

Die Adressen haben das Schema
`http://127.0.0.1:8080/overlay/player/<spieler-id>`. Jede Karte aktualisiert Name
und Leben automatisch. Punkte werden dort bewusst nicht angezeigt. Der Bereich
außerhalb der einzelnen Karte bleibt transparent.

## Technische Hinweise

Die Spielstände werden in `data/scoreboard.json` gespeichert. Der Server verwendet
standardmäßig Port 8080; über die Umgebungsvariable `PORT` kann ein anderer Port
gesetzt werden. Eine reine Startprüfung ohne Browser ist mit
`start_scoreboard.bat --check` möglich.

Der Server kann weiterhin einzeln mit `python server/server.py` gestartet werden.
