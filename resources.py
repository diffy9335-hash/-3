from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from bot.models.base import Base


class Resources(Base):
    __tablename__ = "resources"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), primary_key=True)
    money: Mapped[int] = mapped_column(BigInteger, default=500)
    food: Mapped[int] = mapped_column(BigInteger, default=300)
    iron: Mapped[int] = mapped_column(BigInteger, default=100)
    oil: Mapped[int] = mapped_column(BigInteger, default=50)
    science: Mapped[int] = mapped_column(BigInteger, default=0)
    population: Mapped[int] = mapped_column(BigInteger, default=1000)
    energy: Mapped[int] = mapped_column(BigInteger, default=200)
    industry: Mapped[int] = mapped_column(BigInteger, default=100)
