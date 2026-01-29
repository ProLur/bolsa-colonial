const API = "";

async function loadMarket() {
    const res = await fetch("/market");
    const data = await res.json();
    document.getElementById("price").innerText =
        data.price.toFixed(2) + " €";
}

async function buy(amount) {
    await fetch(`/buy?amount=${amount}`);
    loadMarket();
}

async function sell(amount) {
    await fetch(`/sell?amount=${amount}`);
    loadMarket();
}

loadMarket();
setInterval(loadMarket, 5000);
