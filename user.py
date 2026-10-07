from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, false, func
from sqlalchemy.orm import Mapped, mapped_column
from bot.models.base import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str] = mapped_column(String(64), default="Командир")
    nation_id: Mapped[int | None] = mapped_column(ForeignKey("nations.id"), nullable=True)
    government: Mapped[str] = mapped_column(String(32), default="republic")
    level: Mapped[int] = mapped_column(Integer, default=1)
    exp: Mapped[int] = mapped_column(Integer, default=0)
    reputation: Mapped[int] = mapped_column(Integer, default=0)
    stability: Mapped[int] = mapped_column(Integer, default=70)
    motto: Mapped[str] = mapped_column(String(128), default="")
    last_daily: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notifications_enabled: Mapped[bool] = mapped_column(default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    ban_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def display_name(self) -> str:
        return self.nickname or (self.username or str(self.telegram_id))
