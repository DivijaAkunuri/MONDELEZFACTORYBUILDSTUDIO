# Construction Cost Estimator — PRD

## Original Problem Statement
Build an AI-powered Construction Cost Estimator (same UI as reference screenshot) accessible from the app's navbar. All contents in the interface must work: estimation calculation, confidence score, graphs, charts, currency conversion. Static rate data from MDLZ xlsx; framework rules from the docx. Requires an AI tool.

## User Choices (confirmed)
- LLM: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) via Emergent Universal Key
- FX: Live rates (open.er-api.com) with 1h cache + static fallback
- Scope: Full 6-step wizard + rich output dashboard
- Deployment: Standalone `/estimator` page with left sidebar
- Rate DB: MDLZ activity rates seeded (`rate_data.py`)

## Architecture
- **Backend (FastAPI + Motor/Mongo + emergentintegrations)**
  - `GET /api/estimator/reference` – dropdown/reference lists
  - `GET /api/estimator/fx-rates` – live USD-based FX rates
  - `POST /api/estimator/calculate` – full estimate + AI insights
  - `POST /api/estimator/calculate-fast` – calc only (for live UI updates)
  - `POST /api/estimator/save` / `GET /api/estimator/list` / `GET /api/estimator/{id}` – persistence
  - `rate_data.py` – Civil activities, Utility systems, Region multipliers (0.55–1.35), Location tier, Complexity factors, Industry presets, Currency symbols

- **Frontend (React 19 + Recharts + Shadcn UI + Tailwind)**
  - `/estimator` route with left navy sidebar, top header (unit/currency/user), sub-header actions (Save, Recalculate, Compare, Export), 6-step stepper, right toolbar
  - 6 KPI cards (Total Cost, Cost/m², Duration, Confidence, Contingency, Region Benchmark)
  - 9 tabs (Summary / Breakdown / BOQ / Utilities / Process / Infra / Cash Flow / Sensitivity / Assumptions)
  - Donut + Line charts (Recharts), Top-12 BOQ table, Utilities summary, Project overview, AI Assumptions/Risks/Optimizations, 7 utility demand cards
  - 6-step Wizard (Project Details → Geometry → Structural → Utilities → Infra → Output)
  - Client-side currency conversion using FX rates

## Confidence Score Logic
Base 92 → penalties for brownfield (-6), remote tier (-4), remote_site (-2), explosion_risk (-3), zero capacity (-8) → clamped [45, 96] → labeled High/Medium/Low.

## Implemented (2026-07-20)
- Full backend estimator (compute_estimate, AI insights, FX cache, MongoDB persistence)
- Full frontend Estimator page with wizard, KPIs, charts, BOQ, utility cards, tabs
- Testing agent: 100% pass on backend and frontend (iteration_1.json)

## Backlog / Next Tasks
- P1: PDF export of estimate + BOQ
- P1: Compare Options — save two scenarios side-by-side
- P2: Drawing Upload with AI take-off (Sora/vision on architectural drawings)
- P2: Rate Database CRUD screen to edit unit rates per region
- P2: User auth & multi-project workspace
