from flask import Flask, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

# Pfad zur JSON-Datei
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "scoreboard.json"
)


@app.route("/")
def home():
    return "Valorant Scoreboard Server läuft!"


@app.route("/api/scoreboard")
def get_scoreboard():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    print(data)   # <-- diese Zeile hinzufügen

    return jsonify(data["players"])

def start():

    print("[SERVER] Flask Server läuft auf Port 5000")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )


if __name__ == "__main__":
    start()