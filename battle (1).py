from datetime import datetime
from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from bot.models.base import Base


class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attacker_id: Mapped[int | None] = mapped_column(ForeignKey("users.telegram_id"), nullable=True)
    defender_id: Mapped[int | None] = mapped_column(ForeignKey("users.telegram_id"), nullable=True)
    is_npc: Mapped[bool] = mapped_column(Boolean, default=True)
    npc_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="in_progress")  # in_progress/attacker_win/defender_win
    turns: Mapped[int] = mapped_column(Integer, default=0)
    log: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
