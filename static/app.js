let lastPrice = null;
let history = [];

async function loadMarket() {
    const res = await fetch("/market");
    const data = await res.json();

    const priceEl = document.getElementById("price");
    const trendEl = document.getElementById("trend");

    const price = data.price;
    priceEl.innerText = price.toFixed(2) + " €";

    if (lastPrice !== null) {
        if (price > lastPrice) {
            priceEl.className = "price up";
            trendEl.innerText = "▲ Subiendo";
        } else if (price < lastPrice) {
            priceEl.className = "price down";
            trendEl.innerText = "▼ Bajando";
        } else {
            priceEl.className = "price";
            trendEl.innerText = "— Sin cambios";
        }
    }

    lastPrice = price;

    history.push(price);
    if (history.length > 20) history.shift();

    drawChart();
}

function drawChart() {
    const canvas = document.getElementById("chart");
    const ctx = canvas.getContext("2d");

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (history.length < 2) return;

    const max = Math.max(...history);
    const min = Math.min(...history);
    const range = max - min || 1;

    ctx.beginPath();
    ctx.strokeStyle = "#4fc3f7";
    ctx.lineWidth = 2;

    history.forEach((value, index) => {
        const x = (index / (history.length - 1)) * canvas.width;
        const y = canvas.height - ((value - min) / range) * canvas.height;

        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.stroke();
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
setInterval(loadMarket, 4000);
