from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="Bolsa Colonial",
    description="Mercado ficticio compartido ambientado en ciencia ficción",
    version="0.1.0"
)

# Estado global del mercado (MVP)
market = {
    "symbol": "LUNA_CC",
    "name": "Luna CC",
    "price": 1.00,
    "last_update": datetime.utcnow().isoformat()
}

@app.get("/")
def root():
    return {
        "status": "Bolsa Colonial activa",
        "market": market["symbol"]
    }

@app.get("/market")
def get_market():
    return market


@app.api_route("/buy", methods=["GET", "POST"])
@app.api_route("/buy/", methods=["GET", "POST"])
def buy(amount: float):
    if amount <= 0:
        return {"error": "La cantidad debe ser positiva"}

    impact = amount * 0.001
    market["price"] = round(market["price"] + impact, 4)
    market["last_update"] = datetime.utcnow().isoformat()

    return {
        "action": "buy",
        "amount": amount,
        "new_price": market["price"],
        "timestamp": market["last_update"]
    }


@app.api_route("/sell", methods=["GET", "POST"])
@app.api_route("/sell/", methods=["GET", "POST"])
def sell(amount: float):
    if amount <= 0:
        return {"error": "La cantidad debe ser positiva"}

    impact = amount * 0.001
    market["price"] = round(max(0.01, market["price"] - impact), 4)
    market["last_update"] = datetime.utcnow().isoformat()

    return {
        "action": "sell",
        "amount": amount,
        "new_price": market["price"],
        "timestamp": market["last_update"]
    }
