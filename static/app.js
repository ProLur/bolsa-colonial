async function loadMarket() {
  try {
    const res = await fetch("/market", { cache: "no-store" });
    const data = await res.json();

    document.getElementById("price").innerText =
      data.price.toFixed(2) + " €";
    document.getElementById("trend").innerText = "OK";
  } catch (e) {
    document.getElementById("trend").innerText = "ERROR";
  }
}

async function buy(amount) {
  await fetch(`/buy?amount=${amount}`, { cache: "no-store" });
  loadMarket();
}

async function sell(amount) {
  await fetch(`/sell?amount=${amount}`, { cache: "no-store" });
  loadMarket();
}

document.addEventListener("DOMContentLoaded", () => {
  loadMarket();
  setInterval(loadMarket, 4000);
});
