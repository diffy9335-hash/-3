from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from bot.models.base import Base


class Nation(Base):
    __tablename__ = "nations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    code: Mapped[str] = mapped_column(String(8), unique=True)
    flag: Mapped[str] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(Text, default="")
    bonus_economy: Mapped[int] = mapped_column(Integer, default=0)
    bonus_army: Mapped[int] = mapped_column(Integer, default=0)
    bonus_science: Mapped[int] = mapped_column(Integer, default=0)
    bonus_stability: Mapped[int] = mapped_column(Integer, default=0)
