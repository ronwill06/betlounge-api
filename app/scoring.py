from dataclasses import dataclass
from math import fabs

NO_EDGE_THRESHOLD = 0.5

@dataclass(frozen=True)
class ScoredPick:
    sport: str
    market_group: str
    player_name: str
    book: str
    line: float
    projection: float
    confidence: int

    has_edge: bool
    recommended_side: str | None  # "OVER" / "UNDER" / None
    edge: float                   # signed: projection - line
    edge_abs: float
    edge_pct: float               # abs(edge)/line
    score: float                  # edge_pct * (confidence/100)

def score_pick(
    *,
    sport: str,
    market_group: str,
    player_name: str,
    book: str,
    line: float,
    projection: float,
    confidence: int
) -> ScoredPick:
    edge = projection - line
    edge_abs = fabs(edge)
    has_edge = edge_abs >= NO_EDGE_THRESHOLD

    if not has_edge:
        recommended = None
    else:
        recommended = "OVER" if edge > 0 else "UNDER"

    edge_pct = (edge_abs / line) if line and line > 0 else 0.0
    score = edge_pct * (max(0, min(confidence, 100)) / 100.0)

    return ScoredPick(
        sport=sport,
        market_group=market_group,
        player_name=player_name,
        book=book,
        line=line,
        projection=projection,
        confidence=confidence,
        has_edge=has_edge,
        recommended_side=recommended,
        edge=edge,
        edge_abs=edge_abs,
        edge_pct=edge_pct,
        score=score
    )