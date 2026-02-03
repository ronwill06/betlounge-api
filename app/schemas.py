from pydantic import BaseModel, Field

class PropPickOut(BaseModel):
    prop_key: str
    is_best_book: bool
    book_rank: int

    sport: str
    market_group: str
    player_name: str
    book: str

    line: float
    projection: float
    confidence: int = Field(ge=0, le=100)

    has_edge: bool
    recommended_side: str | None  # "OVER" / "UNDER" / null
    edge: float
    edge_abs: float
    edge_pct: float
    score: float

    # bettor-friendly UI: show both pills + which is highlighted
    over_label: str
    under_label: str

class MarketsOut(BaseModel):
    sport: str
    markets: list[str]

class SearchOut(BaseModel):
    players: list[str]
