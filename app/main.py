import os
import traceback

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import PropOffer, PropProjection
from .schemas import MarketsOut, PropPickOut, SearchOut
from .scoring import score_pick


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*").strip()
    if not raw:
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()] or ["*"]


app = FastAPI(title="BetLounge API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _round2(value: float) -> float:
    return round(float(value), 2)


def _round6(value: float) -> float:
    return round(float(value), 6)


def _build_scored_props_raw(*, sport: str, market: str, db: Session) -> list[dict]:
    offers = db.execute(
        select(PropOffer).where(
            PropOffer.sport == sport,
            PropOffer.market_group == market,
        )
    ).scalars().all()

    projections = db.execute(
        select(PropProjection).where(
            PropProjection.sport == sport,
            PropProjection.market_group == market,
        )
    ).scalars().all()

    proj_by_player = {p.player_name: p for p in projections}

    raw: list[dict] = []
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
            confidence=p.confidence,
        )

        prop_key = f"{s.sport}|{s.market_group}|{s.player_name}"
        line_r2 = _round2(s.line)

        raw.append(
            {
                "prop_key": prop_key,
                "sport": s.sport,
                "market_group": s.market_group,
                "player_name": s.player_name,
                "book": s.book,
                "line": line_r2,
                "projection": _round2(s.projection),
                "confidence": s.confidence,
                "has_edge": s.has_edge,
                "recommended_side": s.recommended_side,
                "edge": _round2(s.edge),
                "edge_abs": _round2(s.edge_abs),
                "edge_pct": _round6(s.edge_pct),
                "score": _round6(s.score),
                "over_label": f"OVER {line_r2:.1f}",
                "under_label": f"UNDER {line_r2:.1f}",
            }
        )

    return raw


def _group_rank_and_sort(raw: list[dict]) -> list[PropPickOut]:
    """Option B: group multiple books per prop and mark best book + rank within group."""
    grouped: dict[str, list[dict]] = {}
    for item in raw:
        grouped.setdefault(item["prop_key"], []).append(item)

    out: list[PropPickOut] = []
    best_score_by_key: dict[str, float] = {}

    for key, items in grouped.items():
        # Sort within group by score desc, then confidence, then abs edge
        items.sort(key=lambda x: (x["score"], x["confidence"], x["edge_abs"]), reverse=True)
        best_score_by_key[key] = items[0]["score"] if items else 0.0

        for idx, item in enumerate(items, start=1):
            out.append(
                PropPickOut(
                    prop_key=item["prop_key"],
                    is_best_book=(idx == 1),
                    book_rank=idx,
                    sport=item["sport"],
                    market_group=item["market_group"],
                    player_name=item["player_name"],
                    book=item["book"],
                    line=item["line"],
                    projection=item["projection"],
                    confidence=item["confidence"],
                    has_edge=item["has_edge"],
                    recommended_side=item["recommended_side"],
                    edge=item["edge"],
                    edge_abs=item["edge_abs"],
                    edge_pct=item["edge_pct"],
                    score=item["score"],
                    over_label=item["over_label"],
                    under_label=item["under_label"],
                )
            )

    # Sort overall by best-book score per prop_key so one prop doesn't dominate the feed.
    # Then keep best-book rows above alternates inside the same group.
    out.sort(
        key=lambda x: (
            best_score_by_key.get(x.prop_key, 0.0),
            1 if x.is_best_book else 0,
            x.score,
        ),
        reverse=True,
    )

    return out


@app.get("/health")
def health():
    # Backward-compatible endpoint used by existing docs/tooling.
    return {
        "ok": True,
        "build": "option-b-grouping-v1",
        "main_file": __file__,
    }


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/readyz")
def readyz(db: Session = Depends(get_db)):
    try:
        db.execute(select(1)).scalar_one()
        return {"ok": True}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"database not ready: {exc}") from exc


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
    """Option B (multiple books, grouped in UI)."""
    try:
        raw = _build_scored_props_raw(sport=sport, market=market, db=db)
        scored = _group_rank_and_sort(raw)

        # Optional: drop "no edge" picks from the feed
        # scored = [x for x in scored if x.has_edge]

        return scored[:limit]
    except Exception as e:
        # Print full traceback to the uvicorn console.
        print("/v1/props/top failed:")
        print(traceback.format_exc())
        # Also return a short detail string to the client for faster debugging.
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/props/top_best", response_model=list[PropPickOut])
def top_best_props(
    sport: str = Query(..., min_length=2),
    market: str = Query(..., min_length=2),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Best-of behavior: one row per prop group (best book only)."""
    try:
        raw = _build_scored_props_raw(sport=sport, market=market, db=db)
        scored = _group_rank_and_sort(raw)

        # Only include picks with an edge.
        scored = [x for x in scored if x.has_edge]

        # Keep only best-book row per prop group.
        best_only = [x for x in scored if x.is_best_book]

        # Sort by score desc (ties: confidence, edge_abs)
        best_only.sort(key=lambda x: (x.score, x.confidence, x.edge_abs), reverse=True)

        return best_only[:limit]
    except Exception as e:
        print("/v1/props/top_best failed:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
