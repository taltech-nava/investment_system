# Schema & Design Decisions

This document records non-obvious design decisions made during development — the reasoning behind them, the alternatives considered, and what was explicitly deferred. Intended for all team members.

---

## 1. forecasts table — field-level decisions

### `predicted_price` is nullable

**Decision:** `predicted_price` is nullable (`NULL` until verified).

**Why:** LLM extraction runs 3 times per source. A row is saved for each run (see extraction logic below). If all 3 extracted values agree AND the LLM confirms they are equal → `extraction_status = 'llm_verified'` and `predicted_price` is set automatically. If they disagree → `extraction_status = 'llm_verification_failed'` and a human must inspect the row and set `predicted_price` manually. Until that happens, `predicted_price = NULL`.

**Consequence:** the aggregate pipeline (`ForecastAggregateRepository.get_source_forecasts`) always filters `predicted_price IS NOT NULL` to prevent unverified rows from entering aggregates.

**Alternative considered (Option B):** unverified rows live in a separate staging table and are only promoted to `forecasts` after human verification — keeping `predicted_price NOT NULL` always. Rejected as too much infrastructure for current stage. Will revisit when the LLM extraction pipeline is built.

---

### `extracted_raw_price` is nullable

**Decision:** `extracted_raw_price` is nullable.

**Why:** this field only has meaning for LLM-extracted rows. yfinance rows and manually entered rows never go through LLM extraction — for them `extracted_raw_price = NULL`. A NULL here means "did not go through extraction", not "extraction failed".

---

### `extracted_raw_price_run` — one row per LLM run

**Decision:** the LLM extraction pipeline saves one `forecasts` row per run, not one row per source. For 3 runs on one source: 3 rows, same `publisher_id`, same `prediction_date`, with `extracted_raw_price_run = 1 / 2 / 3`.

**Why:** preserves the full audit trail of all extraction attempts. `predicted_price` is set identically on all rows (once verified) or remains NULL on all rows (pending).

---

### `estimate_type` CHECK constraint — full value set

**Decision:** allowed values for `estimate_type`:
- `source_point_estimate` — single price directly from external source (yfinance T object)
- `llm_point_estimate` — single price extracted by LLM from a snippet
- `llm_scenario_estimate` — bear/base/bull price extracted by LLM (rare but supported)
- `manual_point_estimate` — single price entered manually by user
- `manual_scenario_estimate` — bear/base/bull entered manually by user

**Why manual types are separate from source types:** allows clean filtering at analysis time without cross-referencing `entry_mode`. The full taxonomy covers every combination of origin × shape with no ambiguity.

---

### `conviction` lives on `forecasts`, not only on `forecast_aggregates`

**Decision:** `conviction tinyint` and `conviction_source varchar(10)` exist on both tables.

- On `forecasts`: user-entered personal confidence in a specific prediction. `conviction_source = 'manual'`. Only relevant for manual entries.
- On `forecast_aggregates`: calculated from coefficient of variation of input forecasts. `conviction_source = 'calculated'`.

**Why:** these are epistemologically different — one is subjective confidence, one is statistical dispersion. Same scale (1–5), different meaning, distinguished by `conviction_source`.

---

## 2. forecast_aggregates — pipeline logic

### yfinance data is treated as individual point estimates

**Decision:** each yfinance T object entry (one per institution) is stored as a `source_point_estimate` / `scenario = 'single'` row in `forecasts`. yfinance's pre-aggregated low/mean/high targets are **not used**.

**Why:** the pre-aggregated values have unknown N, STD, and methodology. Using them would corrupt conviction calculation (which requires knowing individual values to compute dispersion) and contaminate the aggregate calculation (averaging an opaque aggregate).

---

### Manual entries do not feed `forecast_aggregates`

**Decision:** manual entries (`entry_mode = 'manual'`) are excluded from the aggregate pipeline entirely. They are queried directly from `forecasts` and displayed separately as "user's own view".

**Why:** manual entries are personal opinion, not external analyst consensus. Mixing them into `averaged_point_estimate` aggregates would corrupt the consensus signal.

---

### Tercile splitting for bear/base/bull from point estimates

**Decision:** when ≥ 3 `source_point_estimate` rows exist for an instrument, they are sorted by `predicted_price`, split into equal thirds, and averaged per third → `source_scenario_estimate` bear/base/bull aggregates. Remainder rows go to bull (`n // 3` split).

---

## 3. Deferred decisions

| Topic | Decision | Reason deferred |
|---|---|---|
| Extraction staging (Option B) | Use nullable `predicted_price` instead (Option A) | Too much infrastructure now; revisit when LLM pipeline is built |
| Manual entries in aggregates | Excluded for now | Epistemologically different from market consensus; revisit if multiple analysts use the tool |
| `extracted_raw_price` / `predicted_price` separation | Kept on same row | Sufficient for MVP; separate table only needed if full run history per source is required |
