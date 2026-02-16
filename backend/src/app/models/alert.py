from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AlertLog(Base):
    __tablename__ = "alert_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, index=True)
    event_type: Mapped[str] = mapped_column(String(50))  # halt, resume, trade_rejected, etc.
    severity: Mapped[str] = mapped_column(String(20))  # info, warning, critical
    message: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String(20), default="log")  # log, telegram, webhook
    delivered: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
