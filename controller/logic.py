import json
import os


# Speicherort der Scoreboard-Daten
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "scoreboard.json"
)


# Standard-Spieler
players = [
    {
        "name": "Spieler 1",
        "score": 0
    },
    {
        "name": "Spieler 2",
        "score": 0
    },
    {
        "name": "Spieler 3",
        "score": 0
    },
    {
        "name": "Spieler 4",
        "score": 0
    },
    {
        "name": "Spieler 5",
        "score": 0
    }
]


def save_data():
    """
    Speichert aktuellen Stand für Overlay
    """

    data = {
        "players": players
    }

    os.makedirs(
        os.path.dirname(DATA_FILE),
        exist_ok=True
    )

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def get_players():
    """
    Gibt alle Spieler zurück
    """

    return players



def change_name(index, name):
    """
    Ändert einen Spielernamen
    """

    if 0 <= index < len(players):
        players[index]["name"] = name

    save_data()



def add_score(index):
    """
    Erhöht Punktzahl
    """

    if 0 <= index < len(players):
        players[index]["score"] += 1

    save_data()



def remove_score(index):
    """
    Verringert Punktzahl
    """

    if 0 <= index < len(players):
        players[index]["score"] -= 1

    save_data()



def reset_scores():
    """
    Setzt alle Punkte zurück
    """

    for player in players:
        player["score"] = 0

    save_data()