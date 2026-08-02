from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
from uuid import uuid4

from flask import Flask, jsonify, redirect, request, send_from_directory, url_for
from flask_cors import CORS


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = Path(os.environ.get("SCOREBOARD_DATA_FILE", BASE_DIR / "data" / "scoreboard.json"))
OVERLAY_DIR = BASE_DIR / "overlay"
WEB_DIR = BASE_DIR / "web"


class StateStore:
    """Thread-safe, file-backed game state for the local event."""

    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file
        self._lock = threading.RLock()
        self._state = self._load()

    @staticmethod
    def _new_player(
        name: str,
        score: int = 0,
        player_id: str | None = None,
        lives: int = 3,
    ) -> dict:
        return {
            "id": player_id or uuid4().hex,
            "name": name,
            "score": score,
            "lives": lives,
        }

    def _load(self) -> dict:
        try:
            with self.data_file.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            raw = {}

        players = []
        seen_ids = set()

        for index, item in enumerate(raw.get("players", [])):
            if not isinstance(item, dict):
                continue

            name = str(item.get("name", f"Spieler {index + 1}")).strip()
            if not name:
                name = f"Spieler {index + 1}"

            try:
                score = int(item.get("score", 0))
            except (TypeError, ValueError):
                score = 0

            try:
                lives = int(item.get("lives", 3))
            except (TypeError, ValueError):
                lives = 3
            lives = min(3, max(0, lives))

            player_id = str(item.get("id", "")).strip()
            if not player_id or player_id in seen_ids:
                player_id = uuid4().hex
            seen_ids.add(player_id)
            players.append(self._new_player(name[:40], score, player_id, lives))

        raw_buzzer = raw.get("buzzer", {}) if isinstance(raw.get("buzzer"), dict) else {}
        valid_ids = {player["id"] for player in players}
        first_player_id = raw_buzzer.get("first_player_id")
        winner_player_id = raw_buzzer.get("winner_player_id")

        return {
            "players": players,
            "buzzer": {
                "enabled": bool(raw_buzzer.get("enabled", False)),
                "first_player_id": first_player_id if first_player_id in valid_ids else None,
                "winner_player_id": winner_player_id if winner_player_id in valid_ids else None,
                "round": max(0, int(raw_buzzer.get("round", 0) or 0)),
            },
            "updated_at": raw.get("updated_at") or self._timestamp(),
        }

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _save_locked(self) -> None:
        self._state["updated_at"] = self._timestamp()
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = self.data_file.with_suffix(self.data_file.suffix + ".tmp")
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(self._state, file, indent=4, ensure_ascii=False)
        os.replace(temporary_file, self.data_file)

    def snapshot(self) -> dict:
        with self._lock:
            return deepcopy(self._state)

    def _player_locked(self, player_id: str) -> dict | None:
        return next(
            (player for player in self._state["players"] if player["id"] == player_id),
            None,
        )

    def connect_player(self, name: str) -> tuple[dict, bool]:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Bitte einen Namen eingeben.")
        if len(clean_name) > 40:
            raise ValueError("Der Name darf hoechstens 40 Zeichen lang sein.")

        with self._lock:
            existing = next(
                (
                    player
                    for player in self._state["players"]
                    if player["name"].casefold() == clean_name.casefold()
                ),
                None,
            )
            if existing:
                return deepcopy(existing), False

            player = self._new_player(clean_name)
            self._state["players"].append(player)
            self._save_locked()
            return deepcopy(player), True

    def remove_player(self, player_id: str) -> bool:
        with self._lock:
            player = self._player_locked(player_id)
            if not player:
                return False

            self._state["players"].remove(player)
            buzzer = self._state["buzzer"]
            if buzzer["first_player_id"] == player_id:
                buzzer["first_player_id"] = None
            if buzzer["winner_player_id"] == player_id:
                buzzer["winner_player_id"] = None
            self._save_locked()
            return True

    def change_score(self, player_id: str, delta: int) -> dict | None:
        with self._lock:
            player = self._player_locked(player_id)
            if not player:
                return None
            player["score"] += delta
            self._save_locked()
            return deepcopy(player)

    def change_lives(
        self,
        player_id: str,
        *,
        delta: int | None = None,
        lives: int | None = None,
    ) -> dict | None:
        with self._lock:
            player = self._player_locked(player_id)
            if not player:
                return None

            target = lives if lives is not None else player["lives"] + int(delta or 0)
            if not 0 <= target <= 3:
                raise ValueError("Leben muessen zwischen 0 und 3 liegen.")

            player["lives"] = target
            self._save_locked()
            return deepcopy(player)

    def release_buzzer(self) -> dict:
        with self._lock:
            buzzer = self._state["buzzer"]
            buzzer.update(
                {
                    "enabled": True,
                    "first_player_id": None,
                    "winner_player_id": None,
                    "round": buzzer["round"] + 1,
                }
            )
            self._save_locked()
            return deepcopy(self._state)

    def reset_buzzer(self) -> dict:
        with self._lock:
            self._state["buzzer"].update(
                {
                    "enabled": False,
                    "first_player_id": None,
                    "winner_player_id": None,
                }
            )
            self._save_locked()
            return deepcopy(self._state)

    def buzz(self, player_id: str) -> tuple[dict, bool, str]:
        with self._lock:
            player = self._player_locked(player_id)
            if not player:
                raise KeyError(player_id)

            buzzer = self._state["buzzer"]
            if buzzer["first_player_id"]:
                return deepcopy(self._state), False, "already_taken"
            if not buzzer["enabled"]:
                return deepcopy(self._state), False, "locked"

            buzzer["first_player_id"] = player_id
            buzzer["enabled"] = False
            self._save_locked()
            return deepcopy(self._state), True, "accepted"

    def choose_winner(self, player_id: str) -> dict | None:
        with self._lock:
            if not self._player_locked(player_id):
                return None
            self._state["buzzer"]["winner_player_id"] = player_id
            self._state["buzzer"]["enabled"] = False
            self._save_locked()
            return deepcopy(self._state)


app = Flask(__name__)
CORS(app)
store = StateStore(DATA_FILE)


def request_json() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def player_name(state: dict, player_id: str | None) -> str | None:
    if not player_id:
        return None
    player = next((item for item in state["players"] if item["id"] == player_id), None)
    return player["name"] if player else None


def public_state(state: dict | None = None) -> dict:
    state = state or store.snapshot()
    result = deepcopy(state)
    result["buzzer"]["first_player_name"] = player_name(
        state, state["buzzer"]["first_player_id"]
    )
    result["buzzer"]["winner_player_name"] = player_name(
        state, state["buzzer"]["winner_player_id"]
    )
    return result


@app.get("/")
def home():
    return redirect(url_for("moderator"))


@app.get("/overlay")
def overlay_directory():
    return redirect(f"{url_for('moderator')}#players-heading")


@app.get("/moderator")
def moderator():
    return send_from_directory(WEB_DIR, "moderator.html")


@app.get("/buzzer")
def buzzer_page():
    return send_from_directory(WEB_DIR, "buzzer.html")


@app.get("/overlay/player/<player_id>")
def player_overlay(player_id: str):
    state = store.snapshot()
    if not any(player["id"] == player_id for player in state["players"]):
        return "Spieler wurde nicht gefunden.", 404
    return send_from_directory(OVERLAY_DIR, "player.html")


@app.get("/ui/<path:filename>")
def ui_files(filename: str):
    return send_from_directory(WEB_DIR, filename)


@app.get("/overlay/<path:filename>")
def overlay_files(filename: str):
    return send_from_directory(OVERLAY_DIR, filename)


@app.get("/api/state")
def get_state():
    return jsonify(public_state())


@app.get("/api/scoreboard")
def get_scoreboard():
    return jsonify({"players": store.snapshot()["players"]})


@app.get("/api/players/<player_id>")
def get_player(player_id: str):
    state = store.snapshot()
    player = next(
        (item for item in state["players"] if item["id"] == player_id),
        None,
    )
    if not player:
        return jsonify({"error": "Spieler wurde nicht gefunden."}), 404
    return jsonify({"player": player})


@app.post("/api/participants/connect")
@app.post("/api/players")
def connect_player():
    try:
        player, created = store.connect_player(str(request_json().get("name", "")))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"player": player, "created": created}), 201 if created else 200


@app.delete("/api/players/<player_id>")
def remove_player(player_id: str):
    if not store.remove_player(player_id):
        return jsonify({"error": "Spieler wurde nicht gefunden."}), 404
    return jsonify({"status": "ok"})


@app.post("/api/players/<player_id>/score")
def change_score(player_id: str):
    raw_delta = request_json().get("delta")
    if isinstance(raw_delta, bool):
        return jsonify({"error": "Punkteaenderung muss eine Zahl sein."}), 400
    try:
        delta = int(raw_delta)
    except (TypeError, ValueError):
        return jsonify({"error": "Punkteaenderung muss eine Zahl sein."}), 400
    if not -100 <= delta <= 100 or delta == 0:
        return jsonify({"error": "Punkteaenderung muss zwischen -100 und 100 liegen."}), 400

    player = store.change_score(player_id, delta)
    if not player:
        return jsonify({"error": "Spieler wurde nicht gefunden."}), 404
    return jsonify({"player": player})


@app.post("/api/players/<player_id>/lives")
def change_lives(player_id: str):
    data = request_json()
    has_delta = "delta" in data
    has_lives = "lives" in data
    if has_delta == has_lives:
        return jsonify({"error": "Bitte entweder delta oder lives angeben."}), 400

    try:
        if has_delta:
            if isinstance(data["delta"], bool):
                raise ValueError
            delta = int(data["delta"])
            if delta not in (-1, 1):
                raise ValueError
            player = store.change_lives(player_id, delta=delta)
        else:
            if isinstance(data["lives"], bool):
                raise ValueError
            lives = int(data["lives"])
            if not 0 <= lives <= 3:
                raise ValueError
            player = store.change_lives(player_id, lives=lives)
    except (TypeError, ValueError):
        return jsonify({"error": "Leben muessen als ganze Zahl zwischen 0 und 3 angegeben werden."}), 400

    if not player:
        return jsonify({"error": "Spieler wurde nicht gefunden."}), 404
    return jsonify({"player": player})


@app.post("/api/buzzer/release")
def release_buzzer():
    return jsonify(public_state(store.release_buzzer()))


@app.post("/api/buzzer/reset")
def reset_buzzer():
    return jsonify(public_state(store.reset_buzzer()))


@app.post("/api/buzzer/buzz")
def buzz():
    player_id = str(request_json().get("player_id", ""))
    try:
        state, accepted, reason = store.buzz(player_id)
    except KeyError:
        return jsonify({"error": "Spieler wurde nicht gefunden."}), 404

    return jsonify(
        {
            "accepted": accepted,
            "reason": reason,
            "state": public_state(state),
        }
    )


@app.post("/api/buzzer/winner")
def choose_winner():
    player_id = str(request_json().get("player_id", ""))
    state = store.choose_winner(player_id)
    if not state:
        return jsonify({"error": "Spieler wurde nicht gefunden."}), 404
    return jsonify(public_state(state))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"[SERVER] Quizshow-Server laeuft auf http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
