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

@app.post("/buy")
def buy(amount: float):
    """
    Compra ficticia.
    A mayor cantidad, mayor impacto en el precio.
    """
    if amount <= 0:
        return {"error": "La cantidad debe ser positiva"}

    # Impacto simple y controlado
    impact = amount * 0.001
    market["price"] = round(market["price"] + impact, 4)
    market["last_update"] = datetime.utcnow().isoformat()

    return {
        "action": "buy",
        "amount": amount,
        "new_price": market["price"],
        "timestamp": market["last_update"]
    }

@app.post("/sell")
def sell(amount: float):
    """
    Venta ficticia.
    Reduce el precio global.
    """
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
