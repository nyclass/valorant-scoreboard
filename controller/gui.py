import tkinter as tk

from logic import (
    get_players,
    change_name,
    add_score,
    remove_score,
    reset_scores
)


BACKGROUND = "#111111"
CARD = "#1c1c1c"
TEXT = "#ffffff"
ACCENT = "#00ff88"


class ScoreboardGUI:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title(
            "NYCLASS VALORANT CONTROLLER"
        )

        self.root.geometry(
            "700x550"
        )

        self.root.configure(
            bg=BACKGROUND
        )

        self.root.resizable(
            False,
            False
        )


        title = tk.Label(
            self.root,
            text="NYCLASS VALORANT CONTROLLER",
            font=(
                "Arial",
                20,
                "bold"
            ),
            fg=ACCENT,
            bg=BACKGROUND
        )

        title.pack(
            pady=20
        )


        subtitle = tk.Label(
            self.root,
            text="OBS SCOREBOARD CONTROL PANEL",
            font=(
                "Arial",
                10
            ),
            fg="gray",
            bg=BACKGROUND
        )

        subtitle.pack()


        self.entries = []
        self.score_labels = []


        self.create_players()


        reset = tk.Button(
            self.root,
            text="RESET SCORE",
            font=(
                "Arial",
                12,
                "bold"
            ),
            bg="#aa2222",
            fg=TEXT,
            width=20,
            height=2,
            command=self.reset
        )

        reset.pack(
            pady=25
        )


    def create_players(self):

        players = get_players()


        for index, player in enumerate(players):

            frame = tk.Frame(
                self.root,
                bg=CARD,
                width=600,
                height=60
            )

            frame.pack(
                pady=5,
                padx=40,
                fill="x"
            )


            name = tk.Entry(
                frame,
                font=(
                    "Arial",
                    13
                ),
                width=20,
                bg="#333333",
                fg=TEXT,
                insertbackground=TEXT
            )


            name.insert(
                0,
                player["name"]
            )


            name.pack(
                side="left",
                padx=20,
                pady=10
            )


            name.bind(
                "<KeyRelease>",
                lambda e,
                i=index,
                entry=name:
                change_name(
                    i,
                    entry.get()
                )
            )


            self.entries.append(
                name
            )


            score = tk.Label(
                frame,
                text=str(player["score"]),
                font=(
                    "Arial",
                    18,
                    "bold"
                ),
                fg=ACCENT,
                bg=CARD,
                width=5
            )


            score.pack(
                side="left",
                padx=20
            )


            self.score_labels.append(
                score
            )


            plus = tk.Button(
                frame,
                text="+",
                font=(
                    "Arial",
                    14,
                    "bold"
                ),
                width=4,
                command=lambda i=index:
                self.add(i)
            )


            plus.pack(
                side="right",
                padx=10
            )


            minus = tk.Button(
                frame,
                text="-",
                font=(
                    "Arial",
                    14,
                    "bold"
                ),
                width=4,
                command=lambda i=index:
                self.remove(i)
            )


            minus.pack(
                side="right"
            )


    def add(self, index):

        add_score(index)

        self.update()


    def remove(self, index):

        remove_score(index)

        self.update()


    def reset(self):

        reset_scores()

        self.update()


    def update(self):

        players = get_players()

        for i, player in enumerate(players):

            self.score_labels[i].config(
                text=str(player["score"])
            )


    def run(self):

        self.root.mainloop()



if __name__ == "__main__":

    app = ScoreboardGUI()

    app.run()