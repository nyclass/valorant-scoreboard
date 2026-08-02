const storageKey = "quizshow-player-id";
const page = document.body;
const connectPanel = document.querySelector("#connect-panel");
const connectForm = document.querySelector("#connect-form");
const nameInput = document.querySelector("#participant-name");
const buzzerApp = document.querySelector("#buzzer-app");
const buzzButton = document.querySelector("#buzz-button");
const disconnectButton = document.querySelector("#disconnect-button");
const statusLabel = document.querySelector("#participant-status-label");
const statusTitle = document.querySelector("#participant-status-title");
const statusHelp = document.querySelector("#participant-status-help");
const connectedName = document.querySelector("#connected-name");
const connectedScore = document.querySelector("#connected-score");
const connectedLives = document.querySelector("#connected-lives");
const message = document.querySelector("#participant-message");

let playerId = window.localStorage.getItem(storageKey);
let buzzPending = false;

async function api(path, options = {}) {
    const response = await fetch(path, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "Server nicht erreichbar.");
    return payload;
}

function showMessage(text, isError = false) {
    message.textContent = text;
    message.classList.toggle("is-error", isError);
}

function setConnected(connected) {
    connectPanel.hidden = connected;
    buzzerApp.hidden = !connected;
}

function disconnect(text = "") {
    playerId = null;
    window.localStorage.removeItem(storageKey);
    setConnected(false);
    page.dataset.participantState = "disconnected";
    if (text) showMessage(text, true);
}

function render(state) {
    if (!playerId) return;
    const player = state.players.find((item) => item.id === playerId);
    if (!player) {
        disconnect("Dieser Spieler wurde vom Moderator entfernt. Bitte erneut verbinden.");
        return;
    }

    setConnected(true);
    connectedName.textContent = player.name;
    connectedScore.textContent = String(player.score);
    connectedLives.textContent = `${player.lives} / 3`;

    const buzzer = state.buzzer;
    const isFirst = buzzer.first_player_id === playerId;
    const isWinner = buzzer.winner_player_id === playerId;

    if (isWinner) {
        page.dataset.participantState = "winner";
        statusLabel.textContent = "Gewinner";
        statusTitle.textContent = "Runde gewonnen";
        statusHelp.textContent = "Warte auf die nächste Frage.";
    } else if (isFirst) {
        page.dataset.participantState = "first";
        statusLabel.textContent = "Erster Buzzer";
        statusTitle.textContent = "Du warst zuerst";
        statusHelp.textContent = "Der Moderator entscheidet die Runde.";
    } else if (buzzer.first_player_id) {
        page.dataset.participantState = "other";
        statusLabel.textContent = "Buzzer belegt";
        statusTitle.textContent = "Jemand war schneller";
        statusHelp.textContent = "Warte auf die nächste Frage.";
    } else if (buzzer.enabled) {
        page.dataset.participantState = "ready";
        statusLabel.textContent = "Buzzer freigegeben";
        statusTitle.textContent = "Bereit";
        statusHelp.textContent = "Du kannst jetzt buzzern.";
    } else {
        page.dataset.participantState = "locked";
        statusLabel.textContent = "Buzzer gesperrt";
        statusTitle.textContent = "Warte auf den Moderator";
        statusHelp.textContent = "Der Buzzer wird für die nächste Frage freigegeben.";
    }

    buzzButton.disabled = buzzPending || !buzzer.enabled || Boolean(buzzer.first_player_id);
}

async function refresh() {
    if (!playerId) {
        setConnected(false);
        return;
    }
    try {
        render(await api("/api/state"));
        showMessage("");
    } catch (error) {
        showMessage(`Verbindung unterbrochen: ${error.message}`, true);
    }
}

connectForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const result = await api("/api/participants/connect", {
            method: "POST",
            body: JSON.stringify({ name: nameInput.value.trim() }),
        });
        playerId = result.player.id;
        window.localStorage.setItem(storageKey, playerId);
        nameInput.value = "";
        showMessage("Verbunden.");
        await refresh();
    } catch (error) {
        showMessage(error.message, true);
    }
});

buzzButton.addEventListener("click", async () => {
    if (!playerId || buzzPending) return;
    buzzPending = true;
    buzzButton.disabled = true;
    try {
        const result = await api("/api/buzzer/buzz", {
            method: "POST",
            body: JSON.stringify({ player_id: playerId }),
        });
        render(result.state);
    } catch (error) {
        showMessage(error.message, true);
    } finally {
        buzzPending = false;
        await refresh();
    }
});

disconnectButton.addEventListener("click", () => disconnect());

refresh();
window.setInterval(refresh, 350);
