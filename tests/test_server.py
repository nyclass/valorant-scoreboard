import json
from pathlib import Path
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from server import server as server_module


class QuizshowServerTest(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_directory.name) / "scoreboard.json"
        self.data_file.write_text('{"players": []}', encoding="utf-8")
        self.original_store = server_module.store
        server_module.store = server_module.StateStore(self.data_file)
        self.client = server_module.app.test_client()

    def tearDown(self):
        server_module.store = self.original_store
        self.temp_directory.cleanup()

    def connect(self, name):
        response = self.client.post("/api/participants/connect", json={"name": name})
        self.assertIn(response.status_code, (200, 201))
        return response.get_json()["player"]

    def test_browser_pages_and_assets_are_available(self):
        player = self.connect("Overlay Test")
        for path in (
            "/moderator",
            "/buzzer",
            "/ui/styles.css",
            f"/overlay/player/{player['id']}",
            "/overlay/player-card.css",
            "/overlay/player-card.js",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                try:
                    self.assertEqual(response.status_code, 200)
                finally:
                    response.close()

        for path in ("/", "/overlay"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/moderator", response.headers["Location"])

        self.assertEqual(self.client.get("/overlay/player/missing").status_code, 404)

    def test_complete_moderator_and_buzzer_flow(self):
        anna = self.connect("Anna")
        ben = self.connect("Ben")

        release = self.client.post("/api/buzzer/release", json={})
        self.assertTrue(release.get_json()["buzzer"]["enabled"])

        first = self.client.post("/api/buzzer/buzz", json={"player_id": anna["id"]})
        second = self.client.post("/api/buzzer/buzz", json={"player_id": ben["id"]})
        self.assertTrue(first.get_json()["accepted"])
        self.assertFalse(second.get_json()["accepted"])
        self.assertEqual(second.get_json()["reason"], "already_taken")

        winner = self.client.post("/api/buzzer/winner", json={"player_id": anna["id"]})
        self.assertEqual(winner.get_json()["buzzer"]["winner_player_name"], "Anna")

        score = self.client.post(f"/api/players/{anna['id']}/score", json={"delta": 1})
        self.assertEqual(score.get_json()["player"]["score"], 1)

        self.assertEqual(anna["lives"], 3)
        lost_life = self.client.post(
            f"/api/players/{anna['id']}/lives", json={"delta": -1}
        )
        self.assertEqual(lost_life.get_json()["player"]["lives"], 2)
        restored = self.client.post(
            f"/api/players/{anna['id']}/lives", json={"lives": 3}
        )
        self.assertEqual(restored.get_json()["player"]["lives"], 3)

        scoreboard = self.client.get("/api/scoreboard").get_json()
        self.assertEqual([player["name"] for player in scoreboard["players"]], ["Anna", "Ben"])
        single_player = self.client.get(f"/api/players/{anna['id']}").get_json()
        self.assertEqual(single_player["player"]["name"], "Anna")
        self.assertEqual(single_player["player"]["lives"], 3)

        self.assertEqual(self.client.delete(f"/api/players/{ben['id']}").status_code, 200)
        state = self.client.get("/api/state").get_json()
        self.assertEqual(len(state["players"]), 1)

    def test_first_buzz_is_atomic(self):
        player_one = server_module.store.connect_player("Spieler A")[0]
        player_two = server_module.store.connect_player("Spieler B")[0]
        server_module.store.release_buzzer()
        barrier = threading.Barrier(2)

        def buzz(player_id):
            barrier.wait()
            return server_module.store.buzz(player_id)[1]

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(buzz, [player_one["id"], player_two["id"]]))

        self.assertEqual(sum(results), 1)
        persisted = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertIn(
            persisted["buzzer"]["first_player_id"],
            {player_one["id"], player_two["id"]},
        )

    def test_validation_errors_are_clear(self):
        self.assertEqual(
            self.client.post("/api/players", json={"name": "  "}).status_code,
            400,
        )
        player = self.connect("Clara")
        self.assertEqual(
            self.client.post(
                f"/api/players/{player['id']}/score", json={"delta": 0}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/buzzer/buzz", json={"player_id": "missing"}
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                f"/api/players/{player['id']}/lives", json={"lives": 4}
            ).status_code,
            400,
        )


if __name__ == "__main__":
    unittest.main()
