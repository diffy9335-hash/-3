from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from bot.models.base import Base


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.telegram_id"), index=True)
    type: Mapped[str] = mapped_column(String(32), index=True)
    level: Mapped[int] = mapped_column(Integer, default=0)  # 0 = строится с нуля
    finishes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
