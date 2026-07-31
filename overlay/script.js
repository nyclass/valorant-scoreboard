
console.log("Scoreboard Script geladen");

async function updateScoreboard() {

    try {

        const response = await fetch(
            "http://127.0.0.1:5000/api/scoreboard"
        );

        const data = await response.json();

        console.log("Daten vom Server:", data);

        const players = data.players || data;

        console.log("Spieler:", players);


        const container = document.getElementById("players");


        if (!container) {
            console.error("Kein #players Element gefunden");
            return;
        }


        container.innerHTML = "";


        players.forEach(player => {

            const div = document.createElement("div");

            div.className = "player";


            div.innerHTML = `
                <span class="player-name">
                    ${player.name}
                </span>

                <span class="player-score">
                    ${player.score}
                </span>
            `;


            container.appendChild(div);

        });


    } catch (error) {

        console.error(
            "Scoreboard Fehler:",
            error
        );

    }

}


// sofort laden
updateScoreboard();


// jede Sekunde aktualisieren
setInterval(
    updateScoreboard,
    1000
);

