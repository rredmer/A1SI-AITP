from datetime import datetime

from sqlalchemy import JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RiskState(Base):
    __tablename__ = "risk_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(index=True, unique=True)
    total_equity: Mapped[float] = mapped_column(default=10000.0)
    peak_equity: Mapped[float] = mapped_column(default=10000.0)
    daily_start_equity: Mapped[float] = mapped_column(default=10000.0)
    daily_pnl: Mapped[float] = mapped_column(default=0.0)
    total_pnl: Mapped[float] = mapped_column(default=0.0)
    open_positions: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    is_halted: Mapped[bool] = mapped_column(default=False)
    halt_reason: Mapped[str] = mapped_column(String(200), default="")
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


class RiskLimitsConfig(Base):
    __tablename__ = "risk_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(index=True, unique=True)
    max_portfolio_drawdown: Mapped[float] = mapped_column(default=0.15)
    max_single_trade_risk: Mapped[float] = mapped_column(default=0.02)
    max_daily_loss: Mapped[float] = mapped_column(default=0.05)
    max_open_positions: Mapped[int] = mapped_column(default=10)
    max_position_size_pct: Mapped[float] = mapped_column(default=0.20)
    max_correlation: Mapped[float] = mapped_column(default=0.70)
    min_risk_reward: Mapped[float] = mapped_column(default=1.5)
    max_leverage: Mapped[float] = mapped_column(default=1.0)
