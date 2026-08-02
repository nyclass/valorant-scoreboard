"""Start the local quiz server and browser-based moderator dashboard together."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket
import sys
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8080
START_TIMEOUT_SECONDS = 10


class StartupError(RuntimeError):
    """An expected startup problem with a user-friendly description."""


def configured_port() -> int:
    raw_port = os.environ.get("PORT", str(DEFAULT_PORT))

    try:
        port = int(raw_port)
    except ValueError as exc:
        raise StartupError(
            f'Der konfigurierte Port "{raw_port}" ist keine gueltige Zahl.'
        ) from exc

    if not 1 <= port <= 65535:
        raise StartupError(f"Der konfigurierte Port {port} liegt ausserhalb 1-65535.")

    return port


def ensure_port_is_available(port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("0.0.0.0", port))
        except OSError as exc:
            raise StartupError(
                f"Port {port} wird bereits verwendet. Bitte ein eventuell noch "
                "laufendes Scoreboard oder ein anderes Programm auf diesem Port beenden."
            ) from exc


def local_network_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 80))
            address = probe.getsockname()[0]
        return address if not address.startswith("127.") else None
    except OSError:
        return None


class ScoreboardServer:
    def __init__(self, port: int) -> None:
        from server.server import app
        from werkzeug.serving import make_server

        self._server = make_server("0.0.0.0", port, app, threaded=True)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="scoreboard-server",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._thread.join(timeout=5)
        self._server.server_close()


def wait_until_ready(port: int) -> None:
    health_url = f"http://127.0.0.1:{port}/api/scoreboard"
    deadline = time.monotonic() + START_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        try:
            with urlopen(health_url, timeout=1) as response:
                payload = response.read()
            if response.status == 200 and b'"players"' in payload:
                return
        except (OSError, URLError):
            time.sleep(0.2)

    raise StartupError(
        f"Der Server war nach {START_TIMEOUT_SECONDS} Sekunden nicht erreichbar."
    )


def run(check_only: bool = False) -> None:
    port = configured_port()
    ensure_port_is_available(port)

    server = ScoreboardServer(port)
    print(f"[START] Server wird auf http://127.0.0.1:{port} gestartet ...")
    server.start()

    try:
        wait_until_ready(port)
        print("[OK] Server ist erreichbar.")

        if check_only:
            print("[OK] Startpruefung erfolgreich.")
            return

        moderator_url = f"http://127.0.0.1:{port}/moderator"
        buzzer_url = f"http://127.0.0.1:{port}/buzzer"
        print(f"[START] Moderator-Dashboard: {moderator_url}")
        print(f"[INFO] Teilnehmer-Buzzer:     {buzzer_url}")
        print(f"[INFO] OBS-Spielerkarten:     {moderator_url}#players-heading")
        network_ip = local_network_ip()
        if network_ip:
            print(f"[INFO] Buzzer im lokalen Netz: http://{network_ip}:{port}/buzzer")

        if not webbrowser.open(moderator_url):
            print("[INFO] Browser konnte nicht automatisch geoeffnet werden.")
            print("       Bitte die Moderator-Adresse manuell oeffnen.")

        input("[LAEUFT] Zum Beenden von Server und Dashboard ENTER druecken ... ")
    finally:
        print("[STOP] Server wird beendet ...")
        server.stop()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Serverstart pruefen und ohne Browser wieder beenden",
    )
    args = parser.parse_args()

    try:
        run(check_only=args.check)
    except StartupError as exc:
        print(f"[FEHLER] {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[STOP] Start wurde abgebrochen.")
        return 0
    except Exception as exc:
        print(f"[FEHLER] Unerwarteter Startfehler: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
