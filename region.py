"""Карта мира: сетка 20×20, у каждого региона владелец и ценность."""
from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from bot.models.base import Base

MAP_SIZE = 20  # мир 20×20 = 400 регионов


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # = y * MAP_SIZE + x
    x: Mapped[int] = mapped_column(Integer)
    y: Mapped[int] = mapped_column(Integer)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.telegram_id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    terrain: Mapped[str] = mapped_column(String(32), default="plains")  # plains/forest/mountain/water
    resource: Mapped[str | None] = mapped_column(String(32), nullable=True)  # iron/oil/food
    population: Mapped[int] = mapped_column(BigInteger, default=500)
    value: Mapped[int] = mapped_column(Integer, default=100)  # оборона нейтралов / ценность
    is_capital: Mapped[bool] = mapped_column(Boolean, default=False)
    is_water: Mapped[bool] = mapped_column(Boolean, default=False)
