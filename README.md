# 🚀 DROPIFY — AI Job Matching Platform

**Platforma AI do automatycznego doboru zleceń | AI-powered job matching platform**

B2B marketplace connecting **e-commerce / dropshipping** clients with **freelancers & suppliers** automatically via AI. Bilingual **Polski + English**, global reach.

```
Client posts job ──▶ AI analyzes (Claude) ──▶ Semantic search (pgvector)
      ──▶ Top 3 matches scored ──▶ Auto-notify freelancers
      ──▶ Freelancer accepts ──▶ Contract + 8% fee ──▶ Complete ──▶ Rating
```

**Architecture:** Frontend → [Vercel](https://vercel.com) (Next.js) · Backend → your VPS (FastAPI + PostgreSQL + Redis + Celery) · AI → Claude API (+ OpenAI embeddings, with offline fallback)

---

## 📦 What's inside

```
├── src/                  ← Next.js frontend (Vercel)
│   ├── app/              ← pages: landing, auth, dashboard, jobs, matches, contracts, profile, admin
│   ├── components/       ← UI components
│   └── lib/              ← i18n (PL/EN), API client, auth context
│
├── backend/              ← FastAPI backend (VPS)
│   ├── app/
│   │   ├── main.py       ← app entry, CORS, seed
│   │   ├── models.py     ← User, Job, Match, Contract, Payment, Rating, …
│   │   ├── routes/       ← auth, users, jobs, matches, ratings, analytics, contracts, admin, plans
│   │   ├── tasks/        ← Celery: AI matching pipeline, daily reports, auto-complete
│   │   └── utils/        ← AI engine, scoring formula, embeddings, security, email
│   ├── scripts/seed.py   ← demo data + AI matching
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml    ← db (pgvector) + redis + api + worker + beat + n8n + nginx
├── nginx.conf            ← reverse proxy + SSL
├── n8n-workflows/        ← gotowe szablony automatyzacji (Telegram, Slack, inbound)
└── .env.example          ← frontend env
```

### 🤖 n8n automatyzacje (self-hosted, 0 zł)

Platforma wysyła **podpisane eventy** na webhooki n8n (nowe zlecenie, match, kontrakt, płatność, prowizja referral, dzienny raport AI), a n8n może też **tworzyć zlecenia** przez `POST /api/n8n/trigger`. 5 gotowych szablonów w `n8n-workflows/` (Telegram, Slack, formularze → zlecenia). Konfiguracja i instrukcje: `doku/N8N_AUTOMACJE.md`.

### Backend API (FastAPI — `/api/*`)

| Endpoint | Description |
|---|---|
| `POST /api/auth/register` · `POST /api/auth/login` · `GET /api/auth/me` | Auth (JWT) |
| `GET/PUT /api/users/me`, `GET /api/users` | Profiles, freelancer search |
| `POST /api/jobs`, `GET /api/jobs`, `GET /api/jobs/{id}`, `POST /api/jobs/{id}/complete` | Jobs + auto AI matching trigger |
| `GET /api/jobs/recommended` | AI recommendations for freelancers |
| `GET /api/matches/job/{job_id}`, `GET /api/matches/mine`, `POST /api/matches/{id}/accept\|reject` | AI matches |
| `POST /api/ratings` | Reviews |
| `GET /api/analytics/dashboard` | Stats |
| `GET /api/admin/stats` | Admin panel |
| `GET /api/contracts/mine`, `POST /api/contracts/{id}/milestones/{mid}/submit\|release` | Milestone escrow |
| `POST /api/payments/checkout/{contract_id}/{milestone_id}`, `GET /api/payments/config` | Real Stripe Checkout (falls back to instant demo release if Stripe isn't configured) |
| `GET /api/plans`, `POST /api/plans/subscribe` | Subscriptions |
| `POST /api/factory/listing`, `POST /api/factory/video-script` | AI Listing Factory + video script generator |
| `GET /api/fx/rates`, `GET /api/fx/tax-hint/{country}` | Global currency conversion + cross-border tax hint |
| `GET /api/contracts/{id}/agreement` | AI-generated plain-language contract agreement |
| `GET /api/users/{id}/risk-score` | Smart Supplier Risk Score |
| `POST /api/copilot/ask`, `GET /api/copilot/history/{job_id}` | AI Co-Pilot (in-job assistant) |
| `GET /api/matches/{id}/schedule` | Time-zone overlap / async scheduling suggestion |
| `POST/GET/DELETE /api/developer/keys`, `POST /api/v1/external/jobs` | White-label / reseller API |

Interactive docs: `https://your-backend/docs` (Swagger).

Full bilingual (PL/EN) platform blueprint — business model, architecture, audit findings, and all 8 new features in detail: [`doku/MEGA_PLATFORM_BLUEPRINT.md`](doku/MEGA_PLATFORM_BLUEPRINT.md).

### 🤖 AI Matching Engine (self-working)

1. **Job analysis** — Claude API extracts category, skills, urgency, fair price (`app/utils/ai.py`). Rule-based fallback when no API key → platform works out of the box.
2. **Embeddings** — OpenAI `text-embedding-3-small` (1536 dims) with a deterministic local hashing vectorizer fallback. Zero-cost offline mode.
3. **Search** — pgvector cosine similarity (`pgvector/pgvector:pg16` image), automatic Python fallback.
4. **Scoring** — `SCORE = Semantic(0.40) + Rating(0.25) + Price_Fit(0.20) + Availability(0.15)`.
5. **Top 3 matches** → auto email + in-app notifications → freelancer accepts → contract.

### ⚙️ Automation (Celery — runs 24/7)

- `matching.trigger_ai_matching` — full matching pipeline per job (also runs inline if Celery is down)
- `matching.recommend_jobs_to_freelancers` — nightly re-matching
- `reports.daily_summary` — 07:00 daily revenue/activity email to admins
- `reports.auto_complete_overdue` — auto-closes stale contracts
- Flower dashboard on `:5555` to monitor tasks

---

## 🚀 Deploy

### 1. Backend → VPS (30 min)

```bash
# Hetzner CAX11 (2 vCPU / 4 GB / 40 GB) ≈ 20 PLN/mies.
ssh root@YOUR_VPS_IP

apt update && apt install -y docker.io docker-compose-v2
git clone <your-repo> /opt/dropify && cd /opt/dropify

cp backend/.env.example backend/.env
nano backend/.env        # SECRET_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, SMTP, N8N_*
docker compose up -d --build

# Verify
curl http://localhost:8000/api/health
# Docs: http://YOUR_VPS_IP:8000/docs

# n8n UI (localhost only) — przez SSH tunnel:
#   ssh -L 5678:127.0.0.1:5678 root@YOUR_VPS_IP  →  http://localhost:5678
```

### 2. Domain + SSL

```bash
# Point DNS A record → VPS IP, then:
apt install -y certbot
certbot certonly --standalone -d api.dropify.app
# Edit nginx.conf: replace dropify.app with your domain
docker compose restart nginx
```

### 3. Frontend → Vercel

1. Push repo to GitHub.
2. Import in [vercel.com/new](https://vercel.com/new).
3. Add env var: `NEXT_PUBLIC_API_URL=https://api.dropify.app/api`
4. Deploy. Language switcher (PL/EN) is built in.

### 4. Seed demo data (optional)

```bash
docker compose exec api python scripts/seed.py
# Demo login:  demo@dropify.app / demo1234
# Freelancers: foto@, studio@, dev@, design@, copy@dropify.app / demo1234
# Admin:       admin@dropify.app / admin123
```

### Local development

```bash
# Backend (needs PostgreSQL+Redis or use docker for infra):
cd backend && python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Celery (optional): celery -A app.tasks.celery_app.celery_app worker -l info

# Frontend:
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm install && npm run dev   # http://localhost:3000
```

---

## 💰 Business model (from docs)

| Stream | M6 | M12 |
|---|---|---|
| Transaction fees (8%) | 1,500 PLN | 8,000 PLN |
| Subscriptions (Starter/Pro/Enterprise) | 400 PLN | 2,000 PLN |
| API / integrations | 200 PLN | 1,500 PLN |
| **TOTAL** | **2,100 PLN** | **11,500 PLN** |

Costs: ~190 PLN/mies. (VPS + AI APIs). **Breakeven: 3–4 jobs/miesiąc.**

## 🛡️ Security notes

- JWT auth, bcrypt password hashing, role-based access (client/freelancer/admin).
- Rate limiting in nginx; CORS allow-list via `CORS_ORIGINS`.
- Change `SECRET_KEY` and `ADMIN_PASSWORD` in production.
- Automated DB backups: `backend/scripts/backup.sh` (cron `0 3 * * *`).

## License

MIT — use freely for personal or commercial projects.
