# Web3 Wallet & NFT Intelligence Platform

A read-only analytics platform that turns a wallet or NFT collection address into a
structured intelligence report: portfolio breakdown, transaction behavior, NFT holdings,
holder concentration, heuristic behavior classification, and a transparent risk score —
summarized into plain English by an LLM that only sees pre-computed structured data, never
raw chain data.

**This product never requests, stores, or transmits private keys or seed phrases.** It only
reads publicly available blockchain data.

## Status: Phase 3 — BlockchainProvider + Etherscan Integration

The `BlockchainProvider` abstraction is implemented and tested (`app/providers/`):
`EtherscanProvider` (real Ethereum mainnet data via Etherscan API v2) and `DemoProvider`
(deterministic synthetic data, used automatically when no `ETHERSCAN_API_KEY` is set). A
factory (`app/providers/factory.py`) is the only place that decides which one to use — nothing
else in the app imports a concrete provider directly.

API routes (`/api/v1/wallet/...`, `/api/v1/collection/...`) are **not yet wired** to the
provider — that's Phase 4. They still return `{"status": "not_implemented"}` stubs.

**Known free-tier limitation, by design, not an oversight:** Etherscan's free tier has no
endpoint that lists all current ERC-20 balances for a wallet, or all holders of an NFT
collection. `get_token_balances` approximates holdings from transfer history (marked
`ESTIMATED`); `get_collection_holders` raises `ProviderCapabilityError` rather than fabricating
a holder list — that capability lands in Phase 8 via a specialized indexer (Alchemy/Reservoir).

## Features (planned, see roadmap)

- Wallet analyzer: balances, tokens, NFTs, transaction summary
- Transaction analysis: frequency, largest transactions, active/dormant periods
- Token portfolio analysis with concentration metrics
- NFT holder intelligence: holder counts, concentration, distribution
- Transparent heuristic wallet behavior classification (with visible confidence + factors)
- Transparent risk indicator score (with visible factors, never accusatory)
- AI-generated narrative report (Groq API) from structured data only — never invents facts
- PDF report export
- Demo mode with clearly labeled synthetic data when no provider key is configured

## Architecture

See [`phase1-architecture.md`](./phase1-architecture.md) (or your copy of it) for the full
system architecture, database schema, API design, and provider abstraction strategy.

Short version: the API layer never talks to a blockchain provider or LLM directly. It always
goes through a `BlockchainProvider` / `LLMProvider` abstraction, and expensive work happens in
a background worker, not in the request/response cycle.

```
Frontend (React) → FastAPI → Background workers → BlockchainProvider (Etherscan)
                                                  → LLMProvider (Groq)
                            → PostgreSQL / Redis
```

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, PostgreSQL, Redis, Celery
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Blockchain data:** Etherscan API (Ethereum mainnet, MVP chain)
- **AI summarization:** Groq API (OpenAI-compatible chat completions, e.g. Llama 3.3 70B)
- **Containerization:** Docker Compose (Postgres, Redis, backend, frontend)

## Getting Started

### 1. Environment variables

```bash
cp .env.example .env
# then fill in ETHERSCAN_API_KEY and GROQ_API_KEY
```

Without `ETHERSCAN_API_KEY` set, the app runs in `DEMO_MODE` and never fabricates real-looking
chain data — this is checked automatically at startup (see `app/core/config.py`).

### 2. Run with Docker Compose (recommended)

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:5173

### 3. Run locally without Docker

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

You'll also need Postgres and Redis running locally, or point `DATABASE_URL`/`REDIS_URL` in
`.env` at existing instances.

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
cd backend
source .venv/bin/activate
pytest app/tests/ -v
```

Currently covers: health/readiness endpoints and the wallet stub contract. Analysis-logic
tests land alongside each phase that implements real logic (transaction analysis, risk
scoring, etc.) per the roadmap.

## API Documentation

Once the backend is running, interactive OpenAPI docs are at `http://localhost:8000/docs`.

Core routes (see architecture doc §6 for full list):

- `GET /api/v1/wallet/{address}` — wallet overview
- `GET /api/v1/wallet/{address}/transactions|tokens|nfts|analysis`
- `GET /api/v1/collection/{address}` — collection overview
- `GET /api/v1/collection/{address}/holders|analysis`
- `POST /api/v1/reports` — generate a report
- `GET /api/v1/health`, `GET /api/v1/ready`

## Security

- No private keys or seed phrases are ever requested or handled — this is a read-only
  analytics product on public data only.
- Secrets live only in `.env` (git-ignored); `.env.example` never contains real values.
- Input validation on all addresses before any provider call.
- SQLAlchemy ORM (no raw SQL string interpolation).
- JWT auth with hashed passwords (Phase 14).
- Rate limiting per user/IP (Phase 15).

## Data Limitations

Blockchain data has inherent limitations that every report will surface explicitly:
wallet ownership isn't always attributable to one person, prices can be volatile or
unavailable historically, and heuristic classifications can produce false positives. The
platform labels estimated values, unavailable data, and demo data clearly rather than
presenting them as verified fact.

## Roadmap

See architecture doc for the full 19-phase build sequence. Next up: **Phase 3 —
BlockchainProvider abstraction + Etherscan integration.**

## License

MIT — see [LICENSE](./LICENSE).
