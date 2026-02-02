from sqlalchemy import String, Integer, Float, DateTime, Enum, Index, func
from sqlalchemy.orm import Mapped, mapped_column
import enum

from .db import Base

class BetSide(str, enum.Enum):
    OVER = "OVER"
    UNDER = "UNDER"

class PropOffer(Base):
    """
    Sportsbook line for a specific player+market.
    Example: LeBron PRA 49.5 at DraftKings.
    """
    __tablename__ = "prop_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    sport: Mapped[str] = mapped_column(String(16), index=True)            # NBA, NFL, etc
    market_group: Mapped[str] = mapped_column(String(32), index=True)     # PRA, Points, Rec Yds...
    player_name: Mapped[str] = mapped_column(String(64), index=True)

    book: Mapped[str] = mapped_column(String(32), index=True)             # DK, FD, MGM...
    line: Mapped[float] = mapped_column(Float)

    # optional metadata
    game_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    start_time: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

Index("ix_offer_lookup", PropOffer.sport, PropOffer.market_group, PropOffer.player_name)

class PropProjection(Base):
    """
    Your model’s projection for player+market.
    Example: LeBron PRA projection 53.2 confidence 78.
    """
    __tablename__ = "prop_projections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    sport: Mapped[str] = mapped_column(String(16), index=True)
    market_group: Mapped[str] = mapped_column(String(32), index=True)
    player_name: Mapped[str] = mapped_column(String(64), index=True)

    projection: Mapped[float] = mapped_column(Float)
    confidence: Mapped[int] = mapped_column(Integer)  # 0..100

    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

Index("ix_proj_lookup", PropProjection.sport, PropProjection.market_group, PropProjection.player_name)