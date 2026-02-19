from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import httpx
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Bolsa Colonial - JSONBin")

MASTER_KEY = os.getenv("JSONBIN_MASTER_KEY")
if not MASTER_KEY:
    raise ValueError("Falta JSONBIN_MASTER_KEY en .env")

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": MASTER_KEY
}

MARKET_URL = f"https://api.jsonbin.io/v3/b/{os.getenv('MARKET_BIN_ID')}"
USERS_URL = f"https://api.jsonbin.io/v3/b/{os.getenv('USERS_BIN_ID')}"

async def get_bin_data(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{url}/latest", headers=HEADERS, timeout=10.0)
        resp.raise_for_status()  # Lanza excepción si no es 200
        return resp.json()["record"]

async def update_bin(url: str, data: Dict[str, Any]):
    async with httpx.AsyncClient() as client:
        resp = await client.put(url, json=data, headers=HEADERS, timeout=10.0)
        resp.raise_for_status()

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nombre de usuario único")

class TradeRequest(BaseModel):
    username: str
    quantity: float = Field(..., gt=0, description="Cantidad de LUNA_CC")

@app.post("/api/register", summary="Registrar nuevo jugador")
async def register(user_data: UserCreate):
    try:
        data = await get_bin_data(USERS_URL)
    except Exception as e:
        raise HTTPException(500, f"Error al conectar con JSONBin: {str(e)}")

    users = data.get("users", [])
    
    if any(u["username"].lower() == user_data.username.lower() for u in users):
        raise HTTPException(400, "El nombre de usuario ya está en uso")

    next_id = data.get("next_user_id", 1)
    
    new_user = {
        "id": next_id,
        "username": user_data.username,
        "balance": 100.00,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "holdings": {"LUNA_CC": 0.0}
    }
    
    users.append(new_user)
    data["users"] = users
    data["next_user_id"] = next_id + 1
    
    await update_bin(USERS_URL, data)
    
    return {"message": "Jugador registrado exitosamente", "user": new_user}

@app.get("/api/market", summary="Ver precio actual de LUNA_CC")
async def get_market():
    data = await get_bin_data(MARKET_URL)
    return {
        "symbol": data["symbol"],
        "name": data["name"],
        "current_price": round(data["current_price"], 6),
        "last_updated": data["last_updated"]
    }

@app.post("/api/buy", summary="Comprar LUNA_CC")
async def buy(request: TradeRequest):
    market = await get_bin_data(MARKET_URL)
    users_data = await get_bin_data(USERS_URL)
    
    user = next((u for u in users_data["users"] if u["username"] == request.username), None)
    if not user:
        raise HTTPException(404, "Jugador no encontrado")
    
    price = Decimal(str(market["current_price"]))
    cost = Decimal(str(request.quantity)) * price
    
    if Decimal(str(user["balance"])) < cost:
        raise HTTPException(400, f"Saldo insuficiente (necesitas {float(cost):.2f})")
    
    user["balance"] = float(Decimal(str(user["balance"])) - cost)
    user["holdings"]["LUNA_CC"] += request.quantity
    
    # Sube un poco el precio por demanda
    new_price = Decimal(str(market["current_price"])) + Decimal("0.0005")
    market["current_price"] = float(new_price.quantize(Decimal("0.000001")))
    market["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    await update_bin(USERS_URL, users_data)
    await update_bin(MARKET_URL, market)
    
    return {
        "success": True,
        "action": "compra",
        "quantity": request.quantity,
        "price_per_unit": float(price),
        "total_cost": float(cost),
        "new_balance": user["balance"],
        "new_price": market["current_price"]
    }

@app.post("/api/sell", summary="Vender LUNA_CC")
async def sell(request: TradeRequest):
    market = await get_bin_data(MARKET_URL)
    users_data = await get_bin_data(USERS_URL)
    
    user = next((u for u in users_data["users"] if u["username"] == request.username), None)
    if not user:
        raise HTTPException(404, "Jugador no encontrado")
    
    current_hold = user["holdings"].get("LUNA_CC", 0.0)
    if current_hold < request.quantity:
        raise HTTPException(400, f"No tienes suficientes LUNA_CC (tienes {current_hold})")
    
    price = Decimal(str(market["current_price"]))
    income = Decimal(str(request.quantity)) * price
    
    user["balance"] = float(Decimal(str(user["balance"])) + income)
    user["holdings"]["LUNA_CC"] -= request.quantity
    
    # Baja un poco el precio por oferta
    new_price = Decimal(str(market["current_price"])) - Decimal("0.0005")
    market["current_price"] = float(max(Decimal("0.01"), new_price).quantize(Decimal("0.000001")))
    market["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    await update_bin(USERS_URL, users_data)
    await update_bin(MARKET_URL, market)
    
    return {
        "success": True,
        "action": "venta",
        "quantity": request.quantity,
        "price_per_unit": float(price),
        "total_income": float(income),
        "new_balance": user["balance"],
        "new_price": market["current_price"]
    }

@app.get("/api/portfolio", summary="Ver portafolio de un jugador")
async def portfolio(username: str = Query(..., description="Nombre de usuario")):
    users_data = await get_bin_data(USERS_URL)
    market = await get_bin_data(MARKET_URL)
    
    user = next((u for u in users_data["users"] if u["username"] == username), None)
    if not user:
        raise HTTPException(404, "Jugador no encontrado")
    
    holdings_qty = user["holdings"].get("LUNA_CC", 0.0)
    holdings_value = holdings_qty * market["current_price"]
    
    return {
        "username": user["username"],
        "balance": user["balance"],
        "holdings": {
            "LUNA_CC": {
                "quantity": holdings_qty,
                "current_value": round(holdings_value, 2)
            }
        },
        "total_assets": round(user["balance"] + holdings_value, 2),
        "current_price": market["current_price"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
