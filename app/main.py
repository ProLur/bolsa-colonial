from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import httpx
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Bolsa Colonial - JSONBin",
    description="Mercado ficticio LUNA_CC con saldos y tenencias por jugador",
    version="0.1.1"
)

# ──────────────────────────────────────────────
# CONFIGURACIÓN JSONBIN
# ──────────────────────────────────────────────

MASTER_KEY = os.getenv("JSONBIN_MASTER_KEY")
if not MASTER_KEY:
    raise RuntimeError("Falta la variable JSONBIN_MASTER_KEY en .env o en variables de entorno")

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": MASTER_KEY
}

MARKET_BIN_ID = os.getenv("MARKET_BIN_ID")
USERS_BIN_ID = os.getenv("USERS_BIN_ID")

if not MARKET_BIN_ID or not USERS_BIN_ID:
    raise RuntimeError("Faltan MARKET_BIN_ID o USERS_BIN_ID en variables de entorno")

MARKET_URL = f"https://api.jsonbin.io/v3/b/{MARKET_BIN_ID}"
USERS_URL = f"https://api.jsonbin.io/v3/b/{USERS_BIN_ID}"

async def get_bin(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{url}/latest", headers=HEADERS, timeout=12.0)
            r.raise_for_status()
            return r.json()["record"]
        except Exception as e:
            raise HTTPException(503, f"No se pudo leer JSONBin: {str(e)}")

async def put_bin(url: str, data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.put(url, json=data, headers=HEADERS, timeout=12.0)
            r.raise_for_status()
        except Exception as e:
            raise HTTPException(503, f"No se pudo guardar en JSONBin: {str(e)}")

# ──────────────────────────────────────────────
# MODELOS
# ──────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class TradeRequest(BaseModel):
    username: str
    quantity: float = Field(..., gt=0)

# ──────────────────────────────────────────────
# SERVIR FRONTEND EN RAÍZ
# ──────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=FileResponse, include_in_schema=False)
@app.get("/index", response_class=FileResponse, include_in_schema=False)
async def serve_game():
    index_path = "static/index.html"
    if not os.path.exists(index_path):
        return FileResponse("static/index.html", status_code=404)  # fallback si no existe
    return FileResponse(index_path)

# Ruta de fallback para evitar 404 crudo en otras rutas no definidas
@app.get("/{path:path}", include_in_schema=False)
async def catch_all(path: str):
    return {"error": "Ruta no encontrada", "docs": "/docs", "market": "/api/market"}

# ──────────────────────────────────────────────
# RUTAS API
# ──────────────────────────────────────────────

@app.get("/api/market")
async def get_market():
    data = await get_bin(MARKET_URL)
    return {
        "symbol": data["symbol"],
        "name": data["name"],
        "current_price": round(data["current_price"], 6),
        "last_updated": data["last_updated"]
    }

@app.post("/api/register")
async def register(user: UserCreate):
    data = await get_bin(USERS_URL)
    users = data.get("users", [])

    if any(u["username"].lower() == user.username.lower() for u in users):
        raise HTTPException(400, "El nombre de usuario ya está en uso")

    next_id = data.get("next_user_id", 1)

    new_user = {
        "id": next_id,
        "username": user.username,
        "balance": 100.00,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "holdings": {"LUNA_CC": 0.0}
    }

    users.append(new_user)
    data["users"] = users
    data["next_user_id"] = next_id + 1

    await put_bin(USERS_URL, data)

    return {"message": "Jugador registrado exitosamente", "user": new_user}

@app.post("/api/buy")
async def buy(req: TradeRequest):
    market = await get_bin(MARKET_URL)
    data = await get_bin(USERS_URL)

    user = next((u for u in data["users"] if u["username"] == req.username), None)
    if not user:
        raise HTTPException(404, "Jugador no encontrado")

    price = Decimal(str(market["current_price"]))
    cost = Decimal(str(req.quantity)) * price

    if Decimal(str(user["balance"])) < cost:
        raise HTTPException(400, f"Saldo insuficiente (necesitas {float(cost):.2f})")

    user["balance"] = float(Decimal(str(user["balance"])) - cost)
    user["holdings"]["LUNA_CC"] = user["holdings"].get("LUNA_CC", 0.0) + req.quantity

    market["current_price"] = float((Decimal(str(market["current_price"])) + Decimal("0.0005")).quantize(Decimal("0.000001")))
    market["last_updated"] = datetime.utcnow().isoformat() + "Z"

    await put_bin(USERS_URL, data)
    await put_bin(MARKET_URL, market)

    return {
        "success": True,
        "action": "compra",
        "quantity": req.quantity,
        "new_price": market["current_price"],
        "new_balance": user["balance"]
    }

@app.post("/api/sell")
async def sell(req: TradeRequest):
    market = await get_bin(MARKET_URL)
    data = await get_bin(USERS_URL)

    user = next((u for u in data["users"] if u["username"] == req.username), None)
    if not user:
        raise HTTPException(404, "Jugador no encontrado")

    hold = user["holdings"].get("LUNA_CC", 0.0)
    if hold < req.quantity:
        raise HTTPException(400, f"No tienes suficientes LUNA_CC (tienes {hold:.2f})")

    price = Decimal(str(market["current_price"]))
    income = Decimal(str(req.quantity)) * price

    user["balance"] = float(Decimal(str(user["balance"])) + income)
    user["holdings"]["LUNA_CC"] = hold - req.quantity

    new_p = Decimal(str(market["current_price"])) - Decimal("0.0005")
    market["current_price"] = float(max(Decimal("0.01"), new_p).quantize(Decimal("0.000001")))
    market["last_updated"] = datetime.utcnow().isoformat() + "Z"

    await put_bin(USERS_URL, data)
    await put_bin(MARKET_URL, market)

    return {
        "success": True,
        "action": "venta",
        "quantity": req.quantity,
        "new_price": market["current_price"],
        "new_balance": user["balance"]
    }

@app.get("/api/portfolio")
async def portfolio(username: str = Query(...)):
    data = await get_bin(USERS_URL)
    market = await get_bin(MARKET_URL)

    user = next((u for u in data["users"] if u["username"] == username), None)
    if not user:
        raise HTTPException(404, "Jugador no encontrado")

    qty = user["holdings"].get("LUNA_CC", 0.0)
    value = qty * market["current_price"]

    return {
        "username": username,
        "balance": user["balance"],
        "holdings": {"LUNA_CC": {"quantity": qty, "value": round(value, 2)}},
        "total_assets": round(user["balance"] + value, 2),
        "current_price": round(market["current_price"], 6)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
