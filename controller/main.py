import os
import sys


# Projekt-Hauptordner finden
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Projektordner für Imports hinzufügen
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)


def start_controller():
    print("[SYSTEM] Controller wird gestartet...")

    try:
        from controller import manager

        manager.start()

    except ImportError as e:
        print(f"[INFO] Noch kein Controller-Modul gefunden: {e}")

    except Exception as e:
        print(f"[FEHLER] Controller: {e}")

def start_overlay():
    print("[SYSTEM] Overlay wird gestartet...")

    try:
        from overlay import overlay

        overlay.start()

    except ImportError:
        print("[INFO] Noch kein Overlay-Modul gefunden.")

    except Exception as e:
        print(f"[FEHLER] Overlay: {e}")


def start_server():
    print("[SYSTEM] Server wird gestartet...")

    try:
        from server import server

        server.start()

    except ImportError:
        print("[INFO] Noch kein Server-Modul gefunden.")

    except Exception as e:
        print(f"[FEHLER] Server: {e}")


def main():
    print("==============================")
    print("   VALORANT SCOREBOARD")
    print("        NYCLASS SYSTEM")
    print("==============================")

    start_controller()
    start_overlay()
    start_server()

    print("[SYSTEM] Alle Module geladen.")


if __name__ == "__main__":
    main()