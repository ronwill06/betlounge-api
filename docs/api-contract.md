# BetLounge API Contract (Stub)

This document is a frontend/backend handoff contract for the current FastAPI implementation.

Base URL (local): `http://localhost:8000`

## Conventions

- Content type: `application/json`
- All successful responses return HTTP `200`
- Query params marked required must be present
- Validation errors (missing/invalid params) return FastAPI `422`
- Internal server failures return `500` on `/v1/props/top` and `/v1/props/top_best`

## `GET /health`

### Response 200

```json
{
  "ok": true,
  "build": "option-b-grouping-v1",
  "main_file": "string"
}
```

## `GET /v1/props/markets`

Returns available market groups for a sport.

### Query params

- `sport` (string, required, min length 2)

### Response 200

```json
{
  "sport": "NBA",
  "markets": ["PRA", "Points"]
}
```

## `GET /v1/props/search`

Searches player names.

### Query params

- `query` (string, required, min length 2)
- `sport` (string, optional)

### Response 200

```json
{
  "players": ["LeBron James", "Other Player"]
}
```

## `GET /v1/props/top`

Returns scored picks, including multiple books per prop (`is_best_book` and `book_rank` indicate grouping/rank).

### Query params

- `sport` (string, required, min length 2)
- `market` (string, required, min length 2)
- `limit` (integer, optional, default `30`, min `1`, max `100`)

### Response 200

Array of `PropPickOut`:

```json
[
  {
    "prop_key": "NBA|PRA|LeBron James",
    "is_best_book": true,
    "book_rank": 1,
    "sport": "NBA",
    "market_group": "PRA",
    "player_name": "LeBron James",
    "book": "DK",
    "line": 44.5,
    "projection": 47.2,
    "confidence": 86,
    "has_edge": true,
    "recommended_side": "OVER",
    "edge": 2.7,
    "edge_abs": 2.7,
    "edge_pct": 0.060674,
    "score": 2.3229,
    "over_label": "OVER 44.5",
    "under_label": "UNDER 44.5"
  }
]
```

## `GET /v1/props/top_best`

Returns only best-book rows and only picks where `has_edge=true`.

### Query params

- `sport` (string, required, min length 2)
- `market` (string, required, min length 2)
- `limit` (integer, optional, default `30`, min `1`, max `100`)

### Response 200

Array of `PropPickOut` (same shape as `/v1/props/top`, filtered/deduped):

```json
[
  {
    "prop_key": "NBA|PRA|LeBron James",
    "is_best_book": true,
    "book_rank": 1,
    "sport": "NBA",
    "market_group": "PRA",
    "player_name": "LeBron James",
    "book": "DK",
    "line": 44.5,
    "projection": 47.2,
    "confidence": 86,
    "has_edge": true,
    "recommended_side": "OVER",
    "edge": 2.7,
    "edge_abs": 2.7,
    "edge_pct": 0.060674,
    "score": 2.3229,
    "over_label": "OVER 44.5",
    "under_label": "UNDER 44.5"
  }
]
```

## Shared schema: `PropPickOut`

- `prop_key`: string
- `is_best_book`: boolean
- `book_rank`: integer
- `sport`: string
- `market_group`: string
- `player_name`: string
- `book`: string
- `line`: number
- `projection`: number
- `confidence`: integer (`0..100`)
- `has_edge`: boolean
- `recommended_side`: `"OVER"` | `"UNDER"` | `null`
- `edge`: number
- `edge_abs`: number
- `edge_pct`: number
- `score`: number
- `over_label`: string
- `under_label`: string
