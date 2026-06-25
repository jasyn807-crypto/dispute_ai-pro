# Project: B2B Credit Repair SaaS Platform

## Architecture
A dual-portal web application with a FastAPI backend and a React frontend, using a SQLite database.

```
credit_repair_saas/
├── backend/
│   ├── app/
│   │   ├── core/           # Config, database, security
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── api/            # API routers (auth, agency, client, parser, dispute)
│   │   └── services/       # Parser, Dispute (LLM), Compliance, Mail simulation
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/          # Agency Dashboard, Client Portal, Login
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
└── tests_e2e/             # Independent opaque-box E2E test suite
    ├── run_e2e.py
    └── test_cases/
```

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| M1 | E2E Test Suite Development | Design E2E test runner, Tiers 1-4 test cases, publish TEST_READY.md | None | DONE (Conv: 4f488f34-7296-4960-bdde-551382135ef1) |
| M2 | Backend Core & Auth | Database, schemas, models, role-based auth (Agency vs Client) | None | DONE (Conv: 9c69ab36-75b3-4f8f-9886-e2ced3384c9c) |
| M3 | Report Parser Service | Upload and parse credit reports, extract negative items for Equifax, Experian, TransUnion | M2 | IN_PROGRESS (Conv: 9c69ab36-75b3-4f8f-9886-e2ced3384c9c) |
| M4 | Dispute & Compliance | LLM dispute draft generation, compliance helper (checks prohibited claims) | M2 | PLANNED |
| M5 | CRM & Mailing Simulator | Onboarding sequence, file upload, mailing simulator (USPS Lob API) with logs | M2 | PLANNED |
| M6 | Frontend & Integration | React dashboards for Agency/Client, connect with APIs | M3, M4, M5 | PLANNED |
| M7 | E2E Testing & Hardening | Pass E2E tests (Tiers 1-4), white-box Adversarial Coverage Hardening (Tier 5) | M1, M6 | PLANNED |

## Interface Contracts

### Auth API
- `POST /api/auth/register`: Register agency or client.
- `POST /api/auth/token`: OAuth2 password flow login, returns JWT token with role.
- `GET /api/auth/me`: Get current user info & role.

### Agency API
- `GET /api/agency/clients`: List clients.
- `GET /api/agency/metrics`: Get dispute success rates and simulated billing.

### Client API
- `GET /api/client/status`: Get tracking status.
- `POST /api/client/upload`: Upload address/identity verification documents.

### Parser API
- `POST /api/parser/upload`: Upload credit report (PDF/Text/JSON), returns negative items.
- `GET /api/parser/reports`: List uploaded reports.

### Dispute API
- `POST /api/dispute/generate`: Generate dispute letter for selected items.
- `POST /api/dispute/compliance`: Verify draft compliance.
- `POST /api/dispute/mail`: Simulate Lob certified mail dispatch.

## Code Layout
The codebase will reside entirely under `credit_repair_saas/`.
Metadata for coordinating subagents resides in `.agents/`.
Source code files must NOT be modified or created by the orchestrator directly.
