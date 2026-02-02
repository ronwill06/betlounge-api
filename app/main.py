from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from .db import get_db
from .models import PropOffer, PropProjection
from .scoring import score_pick
from .schemas import PropPickOut, MarketsOut, SearchOut

app = FastAPI(title="BetLounge API", version="0.1.0")

def _build_scored_props(
    *,
    sport: str,
    market: str,
    db: Session,
) -> list[PropPickOut]:
    offers = db.execute(
        select(PropOffer).where(
            PropOffer.sport == sport,
            PropOffer.market_group == market
        )
    ).scalars().all()

    projections = db.execute(
        select(PropProjection).where(
            PropProjection.sport == sport,
            PropProjection.market_group == market
        )
    ).scalars().all()

    proj_by_player = {p.player_name: p for p in projections}

    scored: list[PropPickOut] = []
    for o in offers:
        p = proj_by_player.get(o.player_name)
        if not p:
            continue

        s = score_pick(
            sport=o.sport,
            market_group=o.market_group,
            player_name=o.player_name,
            book=o.book,
            line=o.line,
            projection=p.projection,
            confidence=p.confidence
        )

        scored.append(PropPickOut(
            sport=s.sport,
            market_group=s.market_group,
            player_name=s.player_name,
            book=s.book,
            line=s.line,
            projection=s.projection,
            confidence=s.confidence,
            has_edge=s.has_edge,
            recommended_side=s.recommended_side,
            edge=s.edge,
            edge_abs=s.edge_abs,
            edge_pct=s.edge_pct,
            score=s.score,
            over_label=f"OVER {s.line:.1f}",
            under_label=f"UNDER {s.line:.1f}",
        ))

    return scored

def _sort_scored_props(scored: list[PropPickOut]) -> list[PropPickOut]:
    # Sort by blended score desc; if tie, higher confidence, then higher edge_abs
    return sorted(scored, key=lambda x: (x.score, x.confidence, x.edge_abs), reverse=True)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/v1/props/markets", response_model=MarketsOut)
def markets(
    sport: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(PropOffer.market_group).where(PropOffer.sport == sport).distinct()
    ).scalars().all()
    markets = sorted(set(rows))
    return MarketsOut(sport=sport, markets=markets)

@app.get("/v1/props/search", response_model=SearchOut)
def search_players(
    query: str = Query(..., min_length=2),
    sport: str | None = None,
    db: Session = Depends(get_db),
):
    q = select(PropOffer.player_name).where(PropOffer.player_name.ilike(f"%{query}%"))
    if sport:
        q = q.where(PropOffer.sport == sport)
    rows = db.execute(q.distinct()).scalars().all()
    return SearchOut(players=sorted(rows)[:25])

@app.get("/v1/props/top", response_model=list[PropPickOut])
def top_props(
    sport: str = Query(..., min_length=2),
    market: str = Query(..., min_length=2),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    MVP behavior:
    - For the requested sport+market, join offer lines with projections by (sport, market_group, player_name).
    - Compute score (edgePct * confidence).
    - Sort descending by score.
    - Return top N.
    """
    scored = _build_scored_props(sport=sport, market=market, db=db)
    scored = _sort_scored_props(scored)

    # Optional: for MVP you may want to drop "no edge" picks from Top Props Today.
    # If you want that behavior, uncomment:
    # scored = [x for x in scored if x.has_edge]

    return scored[:limit]

@app.get("/v1/props/top_best", response_model=list[PropPickOut])
def top_best_props(
    sport: str = Query(..., min_length=2),
    market: str = Query(..., min_length=2),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Best-of behavior:
    - Only include picks with an edge.
    - For each player, keep the single best-scoring book.
    - Return top N by score.
    """
    scored = _build_scored_props(sport=sport, market=market, db=db)
    scored = [x for x in scored if x.has_edge]
    scored = _sort_scored_props(scored)

    best_by_player: list[PropPickOut] = []
    seen_players: set[str] = set()
    for pick in scored:
        if pick.player_name in seen_players:
            continue
        seen_players.add(pick.player_name)
        best_by_player.append(pick)

    return best_by_player[:limit]
