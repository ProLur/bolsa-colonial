from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime
from sqlalchemy.orm import Session

from .database import engine, SessionLocal
from .models import Base, Market

app = FastAPI(
    title="Bolsa Colonial",
    description="Mercado ficticio compartido ambientado en ciencia ficción",
    version="0.3.0"
)

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# ==========================
# STATIC FILES (FRONTEND)
# ==========================
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/index")
def index():
    return FileResponse("static/index.html")


# ==========================
# UTILIDADES
# ==========================
def get_market(db: Session) -> Market:
    market = db.query(Market).filter(Market.symbol == "LUNA_CC").first()

    if not market:
        market = Market(
            symbol="LUNA_CC",
            name="Luna CC",
            price=1.00
        )
        db.add(market)
        db.commit()
        db.refresh(market)

    return market


# ==========================
# API ENDPOINTS
# ==========================
@app.get("/")
def root():
    return {"status": "Bolsa Colonial activa"}


@app.get("/market")
def market():
    db = SessionLocal()
    market = get_market(db)

    return {
        "symbol": market.symbol,
        "name": market.name,
        "price": market.price,
        "last_update": datetime.utcnow().isoformat()
    }


@app.api_route("/buy", methods=["GET", "POST"])
@app.api_route("/buy/", methods=["GET", "POST"])
def buy(amount: float):
    if amount <= 0:
        return {"error": "Cantidad inválida"}

    db = SessionLocal()
    market = get_market(db)

    market.price = round(market.price + (amount * 0.001), 4)
    db.commit()

    return {"new_price": market.price}


@app.api_route("/sell", methods=["GET", "POST"])
@app.api_route("/sell/", methods=["GET", "POST"])
def sell(amount: float):
    if amount <= 0:
        return {"error": "Cantidad inválida"}

    db = SessionLocal()
    market = get_market(db)

    market.price = round(max(0.01, market.price - (amount * 0.001)), 4)
    db.commit()

    return {"new_price": market.price}
