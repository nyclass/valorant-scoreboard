```css
body {
    background: transparent;
    font-family: "Arial", sans-serif;
}


.scoreboard {

    width: 500px;

    background: rgba(10, 10, 15, 0.85);

    color: white;

    padding: 30px;

    border-radius: 18px;

    border: 2px solid rgba(255,255,255,0.15);

    box-shadow:
        0 0 25px rgba(0,0,0,0.6);

}


h1 {

    text-align: center;

    margin-top: 0;
    margin-bottom: 25px;

    font-size: 42px;

    letter-spacing: 4px;

    text-transform: uppercase;

}


#players {

    display: flex;

    flex-direction: column;

    gap: 12px;

}



.player {

    display: flex;

    justify-content: space-between;

    align-items: center;

    padding: 14px 20px;

    font-size: 32px;

    font-weight: bold;

    background: rgba(255,255,255,0.08);

    border-radius: 12px;

    transition: 0.2s;

}



.player:hover {

    background: rgba(255,255,255,0.18);

}



.player-name {

    text-align: left;

}



.player-score {

    font-size: 36px;

    color: #ff4655;

}
```
