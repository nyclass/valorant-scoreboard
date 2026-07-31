from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "scoreboard.json"
)


OVERLAY_DIR = os.path.join(
    BASE_DIR,
    "overlay"
)


# Overlay anzeigen
@app.route("/")
def overlay():
    return send_from_directory(
        OVERLAY_DIR,
        "index.html"
    )


# Overlay Dateien laden
@app.route("/<path:filename>")
def overlay_files(filename):
    return send_from_directory(
        OVERLAY_DIR,
        filename
    )


# Scoreboard ausgeben
@app.route("/api/scoreboard")
def get_scoreboard():

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return jsonify(data)


# NEU: Controller sendet Updates hierhin
@app.route("/api/update", methods=["POST"])
def update_scoreboard():

    data = request.get_json()

    if not data or "players" not in data:
        return jsonify({
            "error": "Keine Spielerdaten erhalten"
        }), 400


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


    print("Neues Scoreboard erhalten:")
    print(data)


    return jsonify({
        "status": "ok"
    })


# Start
if __name__ == "__main__":

    print("[SERVER] Flask Server läuft")

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=False
    )