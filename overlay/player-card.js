const playerCard = document.querySelector("#player-card");
const playerName = document.querySelector("#player-name");
const playerLives = document.querySelector("#player-lives");
const pathParts = window.location.pathname.split("/").filter(Boolean);
const playerId = pathParts[0] === "overlay" && pathParts[1] === "player"
    ? decodeURIComponent(pathParts.slice(2).join("/"))
    : "";
let lastSignature = "";

function renderPlayer(player) {
    const signature = JSON.stringify({ name: player.name, lives: player.lives });
    if (signature === lastSignature) return;
    lastSignature = signature;

    playerName.textContent = player.name;
    playerLives.replaceChildren();
    playerLives.setAttribute("aria-label", `${player.lives} von 3 Leben`);

    for (let index = 0; index < 3; index += 1) {
        const heart = document.createElement("span");
        heart.textContent = "♥";
        heart.className = index < player.lives ? "is-full" : "is-empty";
        heart.setAttribute("aria-hidden", "true");
        playerLives.append(heart);
    }

    playerCard.hidden = false;
}

async function updatePlayerCard() {
    if (!playerId) return;

    try {
        const response = await fetch(`/api/players/${encodeURIComponent(playerId)}`, {
            cache: "no-store",
        });
        if (response.status === 404) {
            playerCard.hidden = true;
            return;
        }
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        renderPlayer(data.player);
    } catch (error) {
        console.error("Spielerkarte konnte nicht aktualisiert werden:", error);
    }
}

updatePlayerCard();
window.setInterval(updatePlayerCard, 500);
