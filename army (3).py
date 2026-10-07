from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from bot.models.base import Base


class ArmyUnit(Base):
    __tablename__ = "army_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), index=True)
    unit_type: Mapped[str] = mapped_column(String(32))
    count: Mapped[int] = mapped_column(BigInteger, default=0)
