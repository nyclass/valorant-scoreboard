const elements = {
    body: document.body,
    status: document.querySelector("#buzzer-heading"),
    help: document.querySelector("#buzzer-help"),
    firstPlayer: document.querySelector("#first-player"),
    quickWinner: document.querySelector("#quick-winner"),
    release: document.querySelector("#release-buzzer"),
    reset: document.querySelector("#reset-buzzer"),
    message: document.querySelector("#message"),
    addForm: document.querySelector("#add-player-form"),
    nameInput: document.querySelector("#player-name"),
    playerList: document.querySelector("#player-list"),
    emptyPlayers: document.querySelector("#empty-players"),
};

let currentState = null;
let lastPlayersSignature = "";

async function api(path, options = {}) {
    const response = await fetch(path, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(payload.error || "Die Aktion konnte nicht ausgeführt werden.");
    }
    return payload;
}

function showMessage(text, isError = false) {
    elements.message.textContent = text;
    elements.message.classList.toggle("is-error", isError);
}

function button(label, className, title, action) {
    const control = document.createElement("button");
    control.type = "button";
    control.className = className;
    control.textContent = label;
    control.title = title;
    control.setAttribute("aria-label", title);
    control.addEventListener("click", action);
    return control;
}

async function copyOverlayLink(player) {
    const overlayUrl = `${window.location.origin}/overlay/player/${encodeURIComponent(player.id)}`;
    try {
        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(overlayUrl);
        } else {
            const textarea = document.createElement("textarea");
            textarea.value = overlayUrl;
            textarea.setAttribute("readonly", "");
            textarea.style.position = "fixed";
            textarea.style.opacity = "0";
            document.body.append(textarea);
            textarea.select();
            const copied = document.execCommand("copy");
            textarea.remove();
            if (!copied) throw new Error("Kopieren wurde vom Browser abgelehnt.");
        }
        showMessage(`Overlay-Link für ${player.name} kopiert.`);
    } catch (error) {
        showMessage(`Link konnte nicht kopiert werden: ${error.message}`, true);
    }
}

function renderPlayers(state) {
    const signature = JSON.stringify({
        players: state.players,
        first: state.buzzer.first_player_id,
        winner: state.buzzer.winner_player_id,
    });
    if (signature === lastPlayersSignature) return;
    lastPlayersSignature = signature;

    elements.playerList.replaceChildren();
    elements.emptyPlayers.hidden = state.players.length > 0;

    state.players.forEach((player) => {
        const row = document.createElement("article");
        row.className = "player-row";
        row.classList.toggle("is-first", player.id === state.buzzer.first_player_id);
        row.classList.toggle("is-winner", player.id === state.buzzer.winner_player_id);
        row.dataset.playerId = player.id;

        const name = document.createElement("span");
        name.className = "player-name";
        name.textContent = player.name;

        const identity = document.createElement("div");
        identity.className = "player-identity";

        const overlayShortcuts = document.createElement("div");
        overlayShortcuts.className = "overlay-shortcuts";

        const overlayPath = `/overlay/player/${encodeURIComponent(player.id)}`;
        const openOverlay = document.createElement("a");
        openOverlay.className = "overlay-shortcut";
        openOverlay.href = overlayPath;
        openOverlay.target = "_blank";
        openOverlay.rel = "noopener";
        openOverlay.textContent = "Karte öffnen";
        openOverlay.setAttribute("aria-label", `Overlay-Karte für ${player.name} öffnen`);

        const copyOverlay = button(
            "Link kopieren",
            "overlay-shortcut overlay-copy-button",
            `Overlay-Link für ${player.name} kopieren`,
            () => copyOverlayLink(player),
        );
        overlayShortcuts.append(openOverlay, copyOverlay);
        identity.append(name, overlayShortcuts);

        const score = document.createElement("strong");
        score.className = "player-score";
        score.textContent = String(player.score);
        score.setAttribute("aria-label", `${player.score} Punkte`);

        const lives = document.createElement("div");
        lives.className = "lives-control";
        lives.setAttribute("aria-label", `${player.lives} von 3 Leben verbleibend`);

        const hearts = document.createElement("span");
        hearts.className = "life-hearts";
        hearts.setAttribute("aria-hidden", "true");
        for (let index = 0; index < 3; index += 1) {
            const heart = document.createElement("span");
            heart.textContent = "♥";
            heart.className = index < player.lives ? "is-full" : "is-empty";
            hearts.append(heart);
        }

        lives.append(
            button("−", "life-button", `${player.name} ein Leben abziehen`, () => changeLives(player.id, -1)),
            hearts,
            button("+", "life-button", `${player.name} ein Leben wiederherstellen`, () => changeLives(player.id, 1)),
        );

        const actions = document.createElement("div");
        actions.className = "player-actions";
        actions.append(
            button("−", "score-button", `Einen Punkt von ${player.name} abziehen`, () => changeScore(player.id, -1)),
            button("+", "score-button", `${player.name} einen Punkt geben`, () => changeScore(player.id, 1)),
            button("Gewinner", "winner-button", `${player.name} als Gewinner wählen`, () => chooseWinner(player.id)),
            button("×", "remove-button", `${player.name} entfernen`, () => removePlayer(player)),
        );

        row.append(identity, score, lives, actions);
        elements.playerList.append(row);
    });
}

function render(state) {
    currentState = state;
    const buzzer = state.buzzer;
    const firstPlayer = buzzer.first_player_name;
    const winner = buzzer.winner_player_name;

    if (winner) {
        elements.body.dataset.buzzerState = "winner";
        elements.status.textContent = "Runde entschieden";
        elements.help.textContent = `${winner} ist als Gewinner ausgewählt.`;
    } else if (firstPlayer) {
        elements.body.dataset.buzzerState = "buzzed";
        elements.status.textContent = "Buzzer gedrückt";
        elements.help.textContent = "Der erste Buzzer ist eindeutig erfasst.";
    } else if (buzzer.enabled) {
        elements.body.dataset.buzzerState = "ready";
        elements.status.textContent = "Bereit";
        elements.help.textContent = "Der Buzzer ist freigegeben.";
    } else {
        elements.body.dataset.buzzerState = "locked";
        elements.status.textContent = "Gesperrt";
        elements.help.textContent = "Buzzer für die nächste Frage freigeben.";
    }

    elements.firstPlayer.textContent = firstPlayer || "Noch niemand";
    elements.quickWinner.disabled = !buzzer.first_player_id || Boolean(winner);
    elements.release.disabled = buzzer.enabled && !firstPlayer;
    renderPlayers(state);
}

async function refresh() {
    try {
        render(await api("/api/state"));
    } catch (error) {
        showMessage(`Verbindung zum Server unterbrochen: ${error.message}`, true);
    }
}

async function perform(path, options, successMessage) {
    try {
        const result = await api(path, options);
        if (result.players && result.buzzer) render(result);
        showMessage(successMessage);
        await refresh();
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function changeScore(playerId, delta) {
    await perform(
        `/api/players/${playerId}/score`,
        { method: "POST", body: JSON.stringify({ delta }) },
        delta > 0 ? "Punkt vergeben." : "Punkt abgezogen.",
    );
}

async function changeLives(playerId, delta) {
    await perform(
        `/api/players/${playerId}/lives`,
        { method: "POST", body: JSON.stringify({ delta }) },
        delta > 0 ? "Leben wiederhergestellt." : "Leben abgezogen.",
    );
}

async function chooseWinner(playerId) {
    await perform(
        "/api/buzzer/winner",
        { method: "POST", body: JSON.stringify({ player_id: playerId }) },
        "Gewinner ausgewählt.",
    );
}

async function removePlayer(player) {
    if (!window.confirm(`${player.name} wirklich aus dem Spiel entfernen?`)) return;
    await perform(`/api/players/${player.id}`, { method: "DELETE" }, "Spieler entfernt.");
}

elements.addForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = elements.nameInput.value.trim();
    if (!name) return;

    try {
        const result = await api("/api/players", {
            method: "POST",
            body: JSON.stringify({ name }),
        });
        elements.nameInput.value = "";
        showMessage(result.created ? "Spieler hinzugefügt." : "Spieler war bereits vorhanden.");
        await refresh();
        elements.nameInput.focus();
    } catch (error) {
        showMessage(error.message, true);
    }
});

elements.release.addEventListener("click", () => perform(
    "/api/buzzer/release",
    { method: "POST", body: "{}" },
    "Buzzer ist freigegeben.",
));

elements.reset.addEventListener("click", () => perform(
    "/api/buzzer/reset",
    { method: "POST", body: "{}" },
    "Buzzer wurde zurückgesetzt.",
));

elements.quickWinner.addEventListener("click", () => {
    if (currentState?.buzzer.first_player_id) {
        chooseWinner(currentState.buzzer.first_player_id);
    }
});

refresh();
window.setInterval(refresh, 500);
