# Web3 Wallet & NFT Intelligence Platform

A read-only analytics platform that turns an Ethereum wallet or NFT collection address into a structured intelligence report: portfolio breakdown, transaction behavior, NFT holdings, holder concentration, heuristic behavior classification and a transparent risk score. Reports can be exported as PDF and optionally summarized in plain English by an LLM that only ever sees pre-computed structured data, never raw chain data.

> **This product never requests, stores or transmits private keys or seed phrases.** It only reads publicly available blockchain data.

## Features

- **Transaction analysis**: frequency, active days, incoming/outgoing split, largest transaction, dormant periods
- **Token portfolio analysis**: balances, USD valuation (CoinGecko) and concentration metrics, with unpriced tokens clearly flagged and excluded
- **NFT holdings**: collection counts and concentration by NFT count
- **Collection holder intelligence**: holder counts, holder distribution buckets, top-holder share of supply
- **Wallet behavior classification**: transparent heuristics (e.g. whale, NFT collector, diversified, long-term holder, bot-like) with a visible confidence and the factors behind each label
- **Risk indicator**: additive 0–100 score with every contributing factor listed, and a built-in disclaimer. It flags patterns worth investigating and never makes accusations.
- **AI narrative (optional)**: Groq-hosted LLM summary written only from structured, pre-computed data
- **PDF report export** for both wallets and collections
- **Demo mode**: with no Etherscan key configured, the app runs on clearly labeled synthetic data and never fabricates real-looking chain data
- **Confidence labels** (`real` / `estimated` / `synthetic`) on data throughout

## Architecture

Application code never talks to a blockchain, pricing or LLM vendor directly. It goes through provider abstractions, and a factory decides which concrete provider to use.

```
Frontend (React)  →  FastAPI  →  Analysis engine  →  BlockchainProvider (Etherscan | Demo)
                                                  →  HolderProvider     (Alchemy NFT API)
                                                  →  PriceProvider      (CoinGecko)
                                                  →  LLMProvider        (Groq | Null)
                              →  Report builder  →  PDF export (ReportLab)
```

| Layer | Location |
|---|---|
| Providers (Etherscan, Alchemy, CoinGecko, Demo) | `backend/app/providers/` |
| Analysis (transactions, tokens, NFTs, holders, behavior, risk) | `backend/app/analysis/` |
| LLM abstraction + wallet narrative | `backend/app/llm/` |
| Report assembly + PDF export | `backend/app/reports/` |
| API routes | `backend/app/api/v1/` |
| Config, address validation, errors, logging | `backend/app/core/` |
| React app | `frontend/src/` |

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Redis, Celery, httpx, ReportLab
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Data sources:** Etherscan (chain data), Alchemy NFT API (holders), CoinGecko (token prices)
- **AI summarization:** Groq API (OpenAI-compatible, default model `llama-3.3-70b-versatile`)
- **Infrastructure:** Docker Compose (Postgres, Redis, backend, frontend)

## Getting Started

### 1. Environment variables

```bash
cp .env.example .env
# then fill in ETHERSCAN_API_KEY and, optionally, GROQ_API_KEY
```

When running the backend locally without Docker, the settings are read from `backend/.env`.

Without `ETHERSCAN_API_KEY`, the app starts in `DEMO_MODE` automatically. Without `GROQ_API_KEY`, reports use a rule-based summary instead of an AI-generated one.

### 2. Run with Docker Compose (recommended)

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (interactive docs at `/docs`)
- Frontend: http://localhost:5173

### 3. Run locally without Docker

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Postgres and Redis must be running locally, or point `DATABASE_URL` and `REDIS_URL` at existing instances.

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
# Backend
cd backend
pytest app/tests/ -v

# Frontend
cd frontend
npm test
```

## API

Interactive OpenAPI docs are served at `http://localhost:8000/docs` once the backend is running.

- `GET /api/v1/wallet/{address}` and `/transactions`, `/tokens`, `/nfts`, `/analysis`
- `GET /api/v1/collection/{address}` and `/holders`, `/analysis`
- `POST /api/v1/reports`
- `GET /api/v1/health`, `GET /api/v1/ready`

## Sample Output

Example generated reports are in `backend/`: `wallet-report-v4.pdf` (latest wallet report) and `collection-report.pdf` (NFT collection holder report).

## Security

- No private keys or seed phrases are ever requested or handled
- Secrets live only in `.env` (git-ignored); `.env.example` contains no real values
- Ethereum addresses are validated before any provider call
- SQLAlchemy ORM only, with no raw SQL string interpolation
- Planned: JWT auth with hashed passwords and per-user/IP rate limiting

## Data Limitations

Every report surfaces these explicitly:

- Wallet ownership isn't always attributable to one person
- Token and NFT prices are volatile and reflect a single point in time
- Heuristic classifications are pattern-based observations and can produce false positives
- NFT concentration is measured by **count**, not floor-price value
- Estimated values, unavailable data and demo data are labeled rather than presented as verified fact

## License

MIT. See [LICENSE](./LICENSE).
