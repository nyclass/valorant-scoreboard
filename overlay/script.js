async function updateScoreboard(){

    const response = await fetch(
        "http://127.0.0.1:5000/api/scoreboard"
    );


    const players = await response.json();


    const container = document.getElementById(
        "players"
    );


    container.innerHTML = "";


    players.forEach(player => {


        const div = document.createElement(
            "div"
        );


        div.className = "player";


        div.innerHTML = `
            <span>${player.name}</span>
            <span>${player.score}</span>
        `;


        container.appendChild(div);


    });


}



updateScoreboard();


setInterval(
    updateScoreboard,
    1000
);