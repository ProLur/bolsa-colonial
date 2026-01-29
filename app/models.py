from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Market(Base):
    __tablename__ = "market"

    id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, index=True)
    name = Column(String)
    price = Column(Float)
