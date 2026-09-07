# DROPIFY — Dokumentacja projektu

**Ostatnia aktualizacja:** 2026-08-23 · **Wersja:** 2.1 · **Język:** PL/EN

> Niniejszy plik jest jedynym kompletnym źródłem informacji o projekcie.
> Starsze pliki w `doku/` nieaktualne — patrz sekcja "Historia dokumentacji".

---

## Spis treści

1. [Przegląd projektu i architektura](#1-przegląd-projektu-i-architektura)
2. [Instalacja i konfiguracja środowiska](#2-instalacja-i-konfiguracja-środowiska)
3. [Struktura katalogów i moduły](#3-struktura-katalogów-i-moduły)
4. [Komendy deweloperskie](#4-komendy-deweloperskie)
5. [Backend API — pełna referencja](#5-backend-api--pełna-referencja)
6. [Silnik AI Matching — jak działa](#6-silnik-ai-matching--jak-działa)
7. [Automatyzacje (Celery + n8n)](#7-automatyzacje-celery--n8n)
8. [Model biznesowy i prowizje](#8-model-biznesowy-i-prowizje)
9. [Konfiguracja bazy danych / integracje zewnętrzne](#9-konfiguracja-bazy-danych--integracje-zewnętrzne)
10. [Bezpieczeństwo](#10-bezpieczeństwo)
11. [Znane problemy, ograniczenia, TODO](#11-znane-problemy-ograniczenia-todo)
12. [Historia ważnych decyzji architektonicznych](#12-historia-ważnych-decyzji-architektonicznych)
13. [Historia dokumentacji](#13-historia-dokumentacji)
14. [Aspekty prawne i regulacyjne](#14-aspekty-prawne-i-regulacyjne)
15. [Pełny wykaz funkcji (20 + F1–F8)](#15-pełny-wykaz-funkcji-20--f1f8)
16. [Pełna roadmapa (chronologiczna)](#16-pełna-roadmapa-chronologiczna)
17. [Rozszerzony model biznesowy — konkurencja i segmenty](#17-rozszerzony-model-biznesowy--konkurencja-i-segmenty)
18. [Inwentarz braków prawnych i biznesowych](#18-inwentarz-braków-prawnych-i-biznesowych)
19. [Pakiet inwestorski / Pitch Deck](#19-pakiet-inwestorski--pitch-deck)

---

## 1. Przegląd projektu i architektura

DROPIFY to globalna platforma B2B typu marketplace, która **automatycznie** dopasowuje zlecenia (e-commerce, dropshipping, usługi cyfrowe) do freelancerów i dostawców za pomocą AI (Claude + embeddingi wektorowe), a następnie **samodzielnie** prowadzi transakcję od dopasowania aż po wypłatę — analiza zlecenia, matching, kontrakt, escrow z etapami płatności, kontrola jakości (AI QA), rozliczenie i program poleceń.

Platforma jest dwujęzyczna (PL/EN, przełącznik jednym kliknięciem) i zaprojektowana do globalnej ekspansji.

### Architektura high-level

```
┌─────────────────────────────────────┐
│   FRONTEND — Next.js 16             │
│   Hosting: Vercel (globalny CDN)    │
│   PL/EN i18n, brak DB po stronie    │
│   frontu                            │
└───────────────┬─────────────────────┘
                │ HTTPS / REST (/api/*)
                ▼
┌─────────────────────────────────────┐
│   BACKEND — FastAPI (Python 3.11+)  │
│   Hosting: własny VPS (Docker)      │
│   JWT auth, 20 routerów             │
└───┬─────────┬─────────┬─────────────┘
    │         │         │
┌───▼───┐ ┌──▼───┐ ┌───▼───────────┐
│Postgres│ │Redis │ │ Claude API    │
│+pgvector│ │+Celery│ │+ OpenAI emb. │
│(dane + │ │(kolejka│ │(fallback:    │
│embeddings)│ │zadań) │ │reguły lokal) │
└────────┘ └──┬───┘ └───────────────┘
              │
        ┌─────▼─────┐
        │    n8n     │ → Telegram / Slack
        │ (localhost)│   / Sheets / webhooks
        └────────────┘
```

**Kluczowa cecha:** każda funkcja AI ma **lokalny fallback bez kluczy API** (reguły/heurystyki), a każde zadanie Celery ma **wykonanie inline**, gdy broker Redis nie działa. Platforma działa od pierwszego dnia nawet bez płatnych kluczy API.

### Stack technologiczny

| Warstwa | Technologia | Koszt |
|---------|-------------|-------|
| Frontend | Next.js 16, React 19, TypeScript | 0 (Vercel free tier) |
| Backend | FastAPI, SQLAlchemy, Pydantic | 0 (open source) |
| Baza danych | PostgreSQL 16 + pgvector | 0 (open source) |
| Cache/Kolejka | Redis 7 + Celery | 0 (open source) |
| AI | Claude API (Anthropic) + OpenAI embeddings | ~150 PLN/mies. |
| Płatności | Stripe (opcjonalnie — bez niego tryb demo) | 2.9% per transakcja |
| Hosting | VPS Hetzner CAX11 (2 vCPU / 4 GB / 40 GB) | 20 PLN/mies. |
| Frontend CDN | Vercel | 0 (free tier) |
| Automatyzacje | n8n (self-hosted) | 0 |
| SSL | Let's Encrypt | 0 |
| **RAZEM** | | **~190 PLN/mies.** |

---

## 2. Instalacja i konfiguracja środowiska

### Wymagania wstępne

- Git
- Docker + Docker Compose v2
- Python 3.11+ (dev lokalny)
- Node.js 18+ (dev frontendu)
- Konto Anthropic (dla Claude API) — opcjonalnie, platforma działa bez niego
- Konto Stripe (dla płatności) — opcjonalnie, bez niego tryb demo

### Szybki start (lokalnie)

```bash
# 1. Klonuj repo
git clone <your-repo>
cd dropify

# 2. Skonfiguruj zmienne środowiskowe
cp backend/.env.example backend/.env
cp .env.example .env.local

# 3. Edytuj backend/.env — uzupełnij:
#    SECRET_KEY (min. 32 znaki)
#    ANTHROPIC_API_KEY (opcjonalnie)
#    STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET (opcjonalnie)

# 4. Uruchom cały stack
docker compose up -d --build

# 5. Poczekaj ~30s na inicjalizację bazy, potwierdź:
curl http://localhost:8000/api/health
# → {"status":"ok","message":"DROPIFY is running","version":"1.0.0"}

# 6. Frontend
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm install && npm run dev    # http://localhost:3000
```

### Logowanie demo

| Rola | Email | Hasło |
|------|-------|-------|
| Admin | `admin@dropify.app` | `admin123` |
| Klient | `demo@dropify.app` | `demo1234` |
| Freelancer | `foto@dropify.app` | `demo1234` |
| Freelancer | `studio@dropify.app` | `demo1234` |
| Freelancer | `dev@dropify.app` | `demo1234` |
| Freelancer | `design@dropify.app` | `demo1234` |

Aby załadować dane demo: `SEED_DEMO_DATA=True` w `backend/.env`, potem zrestartuj API.

### Wdrożenie na VPS (produkcja)

```bash
# 1. Kup VPS (Hetzner CAX11: 20 PLN/mies.)
ssh root@YOUR_VPS_IP

# 2. Zainstaluj Docker
apt update && apt install -y docker.io docker-compose-v2

# 3. Klonuj i skonfiguruj
git clone <your-repo> /opt/dropify && cd /opt/dropify
cp backend/.env.example backend/.env
nano backend/.env   # uzupełnij sekrety

# 4. Uruchom
docker compose up -d --build

# 5. Weryfikacja
curl http://localhost:8000/api/health

# 6. Frontend → Vercel
#    - Push repo na GitHub
#    - Import na vercel.com/new
#    - Env: NEXT_PUBLIC_API_URL=https://api.dropify.app/api
#    - Deploy

# 7. SSL (Let's Encrypt)
apt install -y certbot
certbot certonly --standalone -d api.dropify.app
# Edytuj nginx.conf — zamień domeny
docker compose restart nginx
```

### Zmienne środowiskowe (backend/.env)

| Zmienna | Opis | Wymagana? |
|---------|------|-----------|
| `SECRET_KEY` | Klucz JWT (min. 32 znaki) | **TAK** |
| `DATABASE_URL` | URL PostgreSQL | Tak (domyślny: `postgresql://dropify:dropify_pass@db:5432/dropify`) |
| `REDIS_URL` | URL Redis | Tak (domyślny: `redis://redis:6379/0`) |
| `ANTHROPIC_API_KEY` | Klucz Claude API | Nie (fallback na reguły) |
| `OPENAI_API_KEY` | Klucz OpenAI (embeddingi) | Nie (fallback na lokalny hashowanie) |
| `STRIPE_SECRET_KEY` | Klucz Stripe | Nie (tryb demo) |
| `STRIPE_WEBHOOK_SECRET` | Sekret webhooka Stripe | Nie (tryb demo) |
| `STRIPE_PUBLISHABLE_KEY` | Klucz publiczny Stripe | Nie |
| `FRONTEND_URL` | URL frontendu (dla Stripe redirect) | Nie (domyślny: `http://localhost:3000`) |
| `N8N_WEBHOOK_URL` | URL webhooka n8n | Nie |
| `N8N_WEBHOOK_SECRET` | HMAC secret dla n8n | Nie |
| `N8N_INBOUND_KEY` | API key dla n8n → DROPIFY | Nie |
| `CORS_ORIGINS` | Dozwolone origins (JSON array) | Nie (domyślny: localhost) |
| `PLATFORM_FEE_RATE` | Podstawowa prowizja (0.08 = 8%) | Nie (domyślny: 0.08) |
| `ADMIN_EMAIL` | Email admina | Nie (domyślny: `admin@dropify.app`) |
| `ADMIN_PASSWORD` | Hasło admina | Nie (domyślny: `admin123`) |
| `SEED_DEMO_DATA` | Automatyczne tworzenie danych demo | Nie (domyślny: False) |

---

## 3. Struktura katalogów i moduły

### Struktura główna

```
dropify/
├── src/                        ← Next.js 16 frontend (Vercel)
│   ├── app/                    ← App Router (Next.js 16)
│   │   ├── layout.tsx          ← Root layout (fonty, AuthProvider, LangProvider)
│   │   ├── page.tsx            ← Landing page
│   │   ├── login/              ← Logowanie
│   │   ├── register/           ← Rejestracja
│   │   ├── forgot-password/    ← Reset hasła (krok 1)
│   │   ├── reset-password/     ← Reset hasła (krok 2)
│   │   ├── verify-email/       ← Weryfikacja email
│   │   ├── fees/               ← Kalkulator prowizji (#20)
│   │   ├── terms/              ← Regulamin (Terms of Service) — WDROZONE 23.08.2026
│   │   ├── privacy/            ← Polityka Prywatnosci (Privacy Policy) — WDROZONE 23.08.2026
│   │   ├── not-found.tsx       ← Custom 404 — WDROZONE 23.08.2026
│   │   ├── error.tsx           ← Error boundary — WDROZONE 23.08.2026
│   │   ├── dashboard/
│   │   │   ├── page.tsx        ← Dashboard główny
│   │   │   ├── jobs/           ← Zlecenia (lista, nowe, [id])
│   │   │   ├── matches/        ← Matchy
│   │   │   ├── contracts/      ← Kontrakty + escrow
│   │   │   ├── factory/        ← AI Listing Factory (#F1/#F6)
│   │   │   ├── developer/      ← White-label API (#F8)
│   │   │   ├── freelancers/    ← Lista specjalistów
│   │   │   ├── integrations/   ← Shopify, BaseLinker (#9-#11)
│   │   │   ├── briefing/       ← AI briefing
│   │   │   └── profile/        ← Profil użytkownika
│   │   └── admin/              ← Panel admina
│   ├── components/             ← UI components
│   │   ├── DashShell.tsx       ← Layout dashboardu
│   │   ├── Footer.tsx
│   │   ├── JobCard.tsx
│   │   ├── LangSwitch.tsx      ← Przełącznik PL/EN
│   │   ├── PortalNav.tsx       ← Nawigacja dashboardu
│   │   └── ui.tsx              ← Shadcn/ui components
│   └── lib/                    ← Warstwa wspólna
│       ├── api.ts              ← API client (fetch + JWT)
│       ├── auth.tsx            ← AuthContext + useAuth
│       ├── categories.ts       ← Kategorie (single source of truth)
│       ├── i18n.tsx            ← Tłumaczenia PL/EN (600+ kluczy)
│       └── types.ts            ← Typy TypeScript
│
├── backend/                    ← FastAPI backend (VPS)
│   ├── app/
│   │   ├── main.py             ← Entry point, CORS, lifespan, seed
│   │   ├── config.py           ← Settings (pydantic-settings)
│   │   ├── database.py         ← SQLAlchemy engine + session
│   │   ├── models.py           ← 15 modeli ORM
│   │   ├── schemas.py          ← Schemas Pydantic
│   │   ├── deps.py             ← Dependencies FastAPI
│   │   ├── routes/             ← 20 routerów API
│   │   │   ├── auth.py         ← /api/auth/* (register, login, me, forgot/reset, verify)
│   │   │   ├── users.py        ← /api/users/* (profile, search, risk-score)
│   │   │   ├── jobs.py         ← /api/jobs/* (CRUD, generate, deliverables, fair-price)
│   │   │   ├── matches.py      ← /api/matches/* (accept/reject, interview, price, schedule)
│   │   │   ├── contracts.py    ← /api/contracts/* (milestones, escrow, refund, dispute, agreement)
│   │   │   ├── payments.py     ← /api/payments/* (Stripe Checkout, config)
│   │   │   ├── ratings.py      ← /api/ratings/*
│   │   │   ├── analytics.py    ← /api/analytics/*
│   │   │   ├── admin.py        ← /api/admin/* (stats, users, disputes)
│   │   │   ├── plans.py        ← /api/plans/* (subscriptions)
│   │   │   ├── notifications.py← /api/notifications/*
│   │   │   ├── referrals.py    ← /api/referrals/*
│   │   │   ├── webhooks.py     ← /api/webhooks/* (Stripe webhook)
│   │   │   ├── n8n.py          ← /api/n8n/* (trigger wejściowy)
│   │   │   ├── factory.py      ← /api/factory/* (AI listings, video scripts, source finder)
│   │   │   ├── copilot.py      ← /api/copilot/* (AI Co-Pilot)
│   │   │   ├── developer.py    ← /api/developer/* (API keys, white-label)
│   │   │   ├── fx.py           ← /api/fx/* (waluty, podatki)
│   │   │   ├── integrations.py ← /api/integrations/* (Shopify, BaseLinker)
│   │   │   ├── invoices.py     ← /api/invoices/* (#5 fakturowanie VAT)
│   │   │   ├── badges.py       ← /api/badges/* (#17 skill badges)
│   │   │   └── radar.py        ← /api/radar/* (Portal Radar — skan portali)
│   │   ├── connectors/          ← Portal Radar: 1 plik = 1 portal (oficjalne API/RSS)
│   │   │   ├── base.py         ← Connector, NormalizedListing/Talent
│   │   │   ├── _http.py        ← wspólny httpx + parser RSS/Atom (stdlib)
│   │   │   ├── registry.py     ← ALL_CONNECTORS
│   │   │   └── *.py            ← remotive, remoteok, arbeitnow, useme, justjoinit, github, ...
│   │   ├── tasks/
│   │   │   ├── celery_app.py   ← Konfiguracja Celery
│   │   │   ├── matching.py     ← AI matching pipeline
│   │   │   ├── reports.py      ← Daily summary, auto-complete
│   │   │   ├── radar.py        ← Portal Radar: scan_all_sources (beat co 6 h)
│   │   │   └── n8n_sync.py     ← Synchronizacja z n8n
│   │   └── utils/
│   │       ├── ai.py           ← Claude API (analiza, listing, copilot, umowy)
│   │       ├── scoring.py      ← Scoring formula
│   │       ├── security.py     ← JWT, bcrypt, referral codes
│   │       ├── emailer.py      ← Email (SMTP/SendGrid)
│   │       ├── fees.py         ← Dynamic fee calculation
│   │       ├── currency.py     ← Przeliczenia walutowe
│   │       ├── risk.py         ← Supplier risk score
│   │       ├── timezone_util.py← Strefy czasowe
│   │       ├── jobs.py         ← Helpery zleceń
│   │       ├── notifications.py← Helpery powiadomień
│   │       ├── n8n.py          ← HMAC signing, webhook dispatch
│   │       ├── invoicing.py    ← #5 Invoice generation, VAT calculation
│   │       └── badges.py       ← #17 Badge awarding, portfolio stats
│   ├── scripts/
│   │   ├── seed.py             ← Dane demo + AI matching
│   │   └── backup.sh           ← Backup bazy (cron: 0 3 * * *)
│   ├── tests/                  ← 47 testów pytest
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_jobs_and_matching.py
│   │   ├── test_contracts_escrow.py
│   │   ├── test_payments_security.py
│   │   ├── test_new_features.py
│   │   ├── test_password_reset_and_disputes.py
│   │   ├── test_sprint4_integrations.py
│   │   └── test_categories.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   ├── pytest.ini
│   └── .env.example
│
├── docker-compose.yml          ← db + redis + api + worker + beat + flower + n8n + nginx
├── nginx.conf                  ← Reverse proxy + SSL
├── .env.example                ← Frontend env
├── n8n-workflows/              ← 5 szablonów automatyzacji
│   ├── dropify-01-job-created-telegram.json
│   ├── dropify-02-match-created-slack.json
│   ├── dropify-03-contract-completed-telegram.json
│   ├── dropify-04-daily-report-telegram.json
│   └── dropify-05-inbound-job-create.json
├── integrations/
│   └── woocommerce/
│       ├── dropify-fulfillment-ai.php   ← Wtyczka WordPress
│       └── README.md
├── package.json                ← Next.js deps
├── tsconfig.json
├── next.config.ts
└── eslint.config.mjs
```

### Modele bazy danych (21 tabel)

| Model | Tabela | Opis |
|-------|--------|------|
| `User` | `users` | Klienci, freelancerzy, admini |
| `Job` | `jobs` | Zlecenia |
| `Match` | `matches` | Dopasowania AI |
| `Contract` | `contracts` | Kontrakty (z escrow, sporami) |
| `Milestone` | `milestones` | Etapy płatności (#5) |
| `Payment` | `payments` | Płatności (Stripe/refund/wypłaty) |
| `Rating` | `ratings` | Oceny i recenzje |
| `Notification` | `notifications` | Powiadomienia in-app |
| `Referral` | `referrals` | Program poleceń |
| `Commission` | `commissions` | Prowizje referral 2.0 (#15) |
| `DailyReport` | `daily_reports` | Codzienne raporty AI |
| `Subscription` | `subscriptions` | Subskrypcje (Free/Starter/Pro/Enterprise) |
| `ApiKey` | `api_keys` | Klucze API (#F8 White-label) |
| `Listing` | `listings` | Wygenerowane oferty (#F1) |
| `StoreConnection` | `store_connections` | Połączenia sklepowe (Shopify/BaseLinker) |
| `CopilotMessage` | `copilot_messages` | Wiadomości AI Co-Pilot (#F5) |
| `Invoice` | `invoices` | Faktury za prowizję platformy (#5) |
| `Badge` | `badges` | Skill badge'e (#17) |
| `ExternalListing` | `external_listings` | Portal Radar: leady zleceń z zewn. portali |
| `ExternalTalent` | `external_talent` | Portal Radar: profile wykonawców z zewn. platform |
| `RadarScanLog` | `radar_scan_logs` | Portal Radar: log skanów (per źródło) |

---

## 4. Komendy deweloperskie

### Uruchamianie

```bash
# Cały stack (backend + baza + redis + celery + n8n + nginx)
docker compose up -d --build

# Tylko backend (lokalnie, bez Dockera)
cd backend && python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Tylko frontend
cp .env.example .env.local        # NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm install && npm run dev        # http://localhost:3000

# Celery worker (opcjonalnie, uruchamia się też w Dockerze)
celery -A app.tasks.celery_app.celery_app worker --loglevel=info

# Celery beat (schedulery)
celery -A app.tasks.celery_app.celery_app beat --loglevel=info
```

### Testy

```bash
# Wszystkie testy (47 testów, zero infrastruktury — SQLite)
cd backend && pytest

# Tylko jeden plik
cd backend && pytest test_auth.py -v

# Z coverage
cd backend && pytest --cov=app
```

### Lint i typecheck

```bash
# Backend — kompilacja
cd backend && python -m py_compile app/main.py

# Frontend — TypeScript
npx tsc --noEmit

# Frontend — ESLint
npx eslint .
```

### Backup bazy

```bash
# Ręczny
docker compose exec db pg_dump -U dropify dropify > backup_$(date +%Y%m%d).sql

# Automatyczny (cron: 0 3 * * *)
bash backend/scripts/backup.sh
```

### Seed danych demo

```bash
docker compose exec api python scripts/seed.py
```

### Logs

```bash
docker compose logs -f api        # Backend
docker compose logs -f worker     # Celery worker
docker compose logs -f db         # PostgreSQL
docker compose logs -f n8n        # n8n

# Flower (monitoring Celery) — http://localhost:5555
```

---

## 5. Backend API — pełna referencja

### Auth

| Endpoint | Method | Auth | Opis |
|----------|--------|------|------|
| `/api/auth/register` | POST | Nie | Rejestracja (client/freelancer) |
| `/api/auth/login` | POST | Nie | Logowanie → JWT |
| `/api/auth/me` | GET | Tak | Aktualny użytkownik |
| `/api/auth/forgot-password` | POST | Nie | Wyślij link resetujący |
| `/api/auth/reset-password` | POST | Nie | Reset hasła tokenem |
| `/api/auth/send-verification` | POST | Tak | Wyślij email weryfikacyjny |
| `/api/auth/verify-email` | POST | Nie | Weryfikacja email |

### Jobs

| Endpoint | Method | Auth | Opis |
|----------|--------|------|------|
| `/api/jobs` | POST | Tak (client) | Utwórz zlecenie → auto AI matching |
| `/api/jobs` | GET | Nie | Lista zleceń (paginacja, filtr kategorii) |
| `/api/jobs/mine` | GET | Tak | Moje zlecenia |
| `/api/jobs/recommended` | GET | Tak (freelancer) | Polecane zlecenia AI |
| `/api/jobs/{id}` | GET | Nie | Szczegóły zlecenia |
| `/api/jobs/{id}` | PUT | Tak (owner) | Aktualizuj zlecenie |
| `/api/jobs/{id}` | DELETE | Tak (owner) | Usuń zlecenie |
| `/api/jobs/{id}/complete` | POST | Tak (client) | Zakończ zlecenie |
| `/api/jobs/generate` | POST | Tak | AI generuje draft z 1 zdania (#14) |
| `/api/jobs/{id}/deliverables` | POST | Tak (freelancer) | Wrzuć deliverables → AI QA (#2) |
| `/api/jobs/{id}/fair-price` | GET | Nie | Uczciwa cena wg AI (#3) |

### Matches

| Endpoint | Method | Auth | Opis |
|----------|--------|------|------|
| `/api/matches/job/{job_id}` | GET | Tak | Matche dla zlecenia |
| `/api/matches/mine` | GET | Tak | Moje matche |
| `/api/matches/{id}/accept` | POST | Tak (freelancer) | Akceptuj match → kontrakt |
| `/api/matches/{id}/reject` | POST | Tak (freelancer) | Odrzuć match (#4 fallback chain) |
| `/api/matches/{id}/interview` | POST | Tak (freelancer) | Odpowiedzi na AI interview (#1) |
| `/api/matches/{id}/propose-price` | POST | Tak (freelancer) | Propozycja ceny (#3) |
| `/api/matches/{id}/confirm-price` | POST | Tak (client) | Akceptuj cenę (#3) |
| `/api/matches/{id}/decline-price` | POST | Tak (client) | Odrzuć cenę (#3) |
| `/api/matches/{id}/schedule` | GET | Nie | Strefa czasowa client↔freelancer (#F7) |

### Contracts

| Endpoint | Method | Auth | Opis |
|----------|--------|------|------|
| `/api/contracts/mine` | GET | Tak | Moje kontrakty |
| `/api/contracts/{id}` | GET | Tak | Szczegóły kontraktu |
| `/api/contracts/{id}/milestones/{mid}/submit` | POST | Tak (freelancer) | Oddaj etap → in_review |
| `/api/contracts/{id}/milestones/{mid}/release` | POST | Tak (client) | Zwolnij płatność |
| `/api/contracts/{id}/request-refund` | POST | Tak (client) | Gwarancja zwrotu (#7) |
| `/api/contracts/{id}/dispute` | POST | Tak | Zgłoś spór |
| `/api/contracts/{id}/resolve-dispute` | POST | Tak (admin) | Rozstrzygnij spór |
| `/api/contracts/{id}/agreement` | GET | Nie | Pobierz umowę AI (#F3) |

### Payments

| Endpoint | Method | Auth | Opis |
|----------|--------|------|------|
| `/api/payments/config` | GET | Nie | Czy Stripe aktywny? |
| `/api/payments/checkout/{cid}/{mid}` | POST | Tak | Stripe Checkout Session |

### Inne

| Endpoint | Method | Auth | Opis |
|----------|--------|------|------|
| `/api/ratings` | POST | Tak | Dodaj ocenę |
| `/api/ratings/user/{id}` | GET | Nie | Oceny użytkownika |
| `/api/analytics/dashboard` | GET | Tak | Statystyki |
| `/api/admin/stats` | GET | Tak (admin) | Statystyki admina |
| `/api/admin/users` | GET | Tak (admin) | Lista użytkowników |
| `/api/admin/disputes` | GET | Tak (admin) | Aktywne spory |
| `/api/plans` | GET | Nie | Plany subskrypcji |
| `/api/plans/subscribe` | POST | Tak | Subskrypcja |
| `/api/notifications` | GET | Tak | Powiadomienia |
| `/api/notifications/read-all` | POST | Tak | Oznacz wszystkie jako przeczytane |
| `/api/referrals/me` | GET | Tak | Moje prowizje referral |
| `/api/factory/listing` | POST | Tak | Generuj ofertę AI (#F1) |
| `/api/factory/video-script` | POST | Tak | Generuj scenariusz wideo (#F6) |
| `/api/factory/history` | GET | Tak | Historia ofert |
| `/api/factory/source-finder` | POST | Tak | Product Source Finder (#12) |
| `/api/factory/source-finder/create-jobs` | POST | Tak | Utwórz zlecenia z planu |
| `/api/copilot/ask` | POST | Tak | Zapytaj AI Co-Pilot (#F5) |
| `/api/copilot/history/{job_id}` | GET | Tak | Historia czatu |
| `/api/developer/keys` | GET/POST | Tak | Zarządzanie kluczami API (#F8) |
| `/api/developer/keys/{id}` | DELETE | Tak | Unieważnij klucz |
| `/api/v1/external/jobs` | POST | Tak (API key) | Partner endpoint (#F8) |
| `/api/fx/rates` | GET | Nie | Kursy walut (#F2) |
| `/api/fx/tax-hint/{country}` | GET | Nie | Notatka VAT (#F2) |
| `/api/integrations/mine` | GET | Tak | Moje sklepy |
| `/api/integrations/shopify/connect` | POST | Tak | Połącz Shopify (#10) |
| `/api/integrations/baselinker/connect` | POST | Tak | Połącz BaseLinker (#11) |
| `/api/integrations/baselinker/{id}/sync` | POST | Tak | Sync BaseLinker |
| `/api/integrations/{id}` | DELETE | Tak | Odłącz sklep |
| `/api/n8n/trigger` | POST | Tak (API key) | Trigger wejściowy z n8n |
| `/api/users/me` | GET/PUT | Tak | Profil |
| `/api/users` | GET | Nie | Lista freelancerów |
| `/api/users/{id}` | GET | Nie | Profil użytkownika |
| `/api/users/{id}/risk-score` | GET | Nie | Risk Score (#F4) |
| `/api/users/me/profile` | GET | Tak | Profil (alternatywny endpoint) |
| `/api/matches/{match_id}/generate` | POST | Tak | Ponowne uruchomienie matchingu dla zlecenia |
| `/api/webhooks/health` | GET | Nie | Health check webhookow |
| `/api/integrations/shopify/webhook/{connection_id}` | POST | Tak (HMAC) | Inbound webhook ze Shopify |
| `/api/integrations/shopify/{connection_id}/push-listing` | POST | Tak | Wyslij oferte AI do Shopify |

### Invoices (#5)

| Endpoint | Method | Auth | Opis |
|----------|--------|------|------|
| `/api/invoices/generate/{contract_id}` | POST | Tak (admin) | Generuj fakturę za prowizję z kontraktu |
| `/api/invoices` | GET | Tak | Lista faktur (admin: wszystkie, klient: swoje) |
| `/api/invoices/summary` | GET | Tak (admin) | Podsumowanie przychodów z VAT |
| `/api/invoices/{id}` | GET | Tak | Szczegóły faktury |

### Skill Badges (#17)

| Endpoint | Method | Auth | Opis |
|----------|--------|------|------|
| `/api/badges` | GET | Nie | Lista dostępnych kategorii badge'ów |
| `/api/badges/mine` | GET | Tak | Moje badge'e |
| `/api/badges/user/{user_id}` | GET | Nie | Badge'e użytkownika (portfolio) |
| `/api/badges/stats` | GET | Tak | Statystyki mojego portfolio |
| `/api/badges/stats/{user_id}` | GET | Nie | Statystyki portfolio użytkownika |

### Portal Radar — skan portali globalnych (popyt + podaż)

Skan zewnętrznych portali **wyłącznie przez oficjalne API / RSS** (`app/connectors/`),
upsert z deduplikacją po `(source, external_id)`, task Celery `app.tasks.radar.scan_all_sources`
(beat co `RADAR_SCAN_INTERVAL_HOURS`, domyślnie 6 h). Import leada tworzy realny `Job`
przez `create_job_and_match` (właściciel: bot `RADAR_BOT_EMAIL`) → uruchamia AI matching.
Konektory startowe: Remotive, RemoteOK, Arbeitnow, Jobicy, We Work Remotely,
HN „Who is hiring", Useme (PL), Just Join IT (PL), Adzuna*, USAJOBS*, GitHub, Stack Overflow, dev.to
(`*` = wymaga klucza). Konfiguracja: `doku/INTEGRACJE_ROZSZERZENIA.md`.

| Endpoint | Method | Auth | Opis |
|----------|--------|------|------|
| `/api/radar/sources` | GET | Tak | Lista konektorów + ostatni skan + liczniki |
| `/api/radar/scan` | POST | Admin | Uruchom skan (`?source=` lub wszystkie) |
| `/api/radar/listings` | GET | Tak | Leady zleceń (filtry: source, category, remote, q, status) |
| `/api/radar/talent` | GET | Tak | Profile wykonawców (filtry: source, skill, q, status) |
| `/api/radar/listings/{id}/import` | POST | Client/Admin | Import leada → nowy Job + AI matching |
| `/api/radar/listings/{id}/dismiss` | POST | Client/Admin | Odrzuć lead |
| `/api/radar/talent/{id}/status` | POST | Client/Admin | `contacted` / `invited` / `dismissed` |
| `/api/radar/stats` | GET | Tak | Liczniki wg statusu + stan źródeł |

Interactive docs: `https://your-backend/docs` (Swagger UI).

---

## 6. Silnik AI Matching — jak działa

### Pipeline (30 sekund end-to-end)

```
1. Klient tworzy zlecenie
   ↓
2. Claude API analizuje → kategoria, umiejętności, urgency, uczciwa cena
   (fallback: reguły regex gdy brak klucza API)
   ↓
3. Generowanie embeddingu (1536 wymiarów)
   (OpenAI text-embedding-3-small, fallback: deterministyczne hashowanie lokalne)
   ↓
4. pgvector cosine similarity → top 20 kandydatów
   (fallback: Python fallback gdy brak pgvector)
   ↓
5. Scoring: Semantic(0.40) + Rating(0.25) + Price_Fit(0.20) + Availability(0.15)
   ↓
6. Top 3 matche → auto-powiadomienia → freelancer akceptuje → kontrakt
```

### Formuła scoringu

```
SCORE = (Semantic × 0.40) + (Rating × 0.25) + (Price_Fit × 0.20) + (Availability × 0.15)
```

| Czynnik | Waga | Obliczanie |
|---------|------|------------|
| Semantic Similarity | 40% | `cosine_similarity(job_vector, freelancer_vector)` — zakres 0-1 |
| Rating | 25% | `user.rating / 5.0` — brak oceny = 0.70 (neutralny) |
| Price Fit | 20% | Budget ≥ fair_price×0.8 → 1.0; ≥ fair_price×0.5 → 0.5; inaczej 0.2 |
| Availability | 15% | ≥7 dni → 1.0; ≥3 dni → 0.7; <3 dni → 0.3 |

**Cel (niezweryfikowany):**文档y twierdzą o 92% acceptance rate — nie jest to zweryfikowane w kodzie, to cel/założenie.

### Fallbacki (działają bez kluczy API)

| Komponent | Gdy brak API | Implementacja |
|-----------|-------------|---------------|
| Claude analysis | Reguły regex + słowniki kategorii | `app/utils/ai.py` → `analyze_job_fallback()` |
| Embeddings | Deterministyczne hashowanie tekstu → wektor 1536D | `app/utils/ai.py` → `local_hash_embedding()` |
| pgvector search | Python fallback (pętla po wszystkich freelancerach) | `app/utils/ai.py` → `fallback_similarity_search()` |
| Copilot | Rule-based FAQ | `app/utils/ai.py` → `answer_copilot_fallback()` |
| Contract agreement | Szablon tekstowy | `app/utils/ai.py` → `generate_contract_agreement_fallback()` |

---

## 7. Automatyzacje (Celery + n8n)

### Zadania Celery (runs 24/7)

| Zadanie | Cron/Trigger | Opis |
|---------|-------------|------|
| `matching.trigger_ai_matching` | Po utworzeniu zlecenia (lub inline gdy Redis down) | Pełny pipeline AI matching |
| `matching.recommend_jobs_to_freelancers` | Nocnie | Ponowne dopasowanie zleceń do freelancerów |
| `reports.daily_summary` | 07:00 codziennie | Dzienny raport (przychody, anomalie, AI insights) |
| `reports.auto_complete_overdue` | Co 30 min | Auto-zamykanie przeterminowanych kontraktów |
| `matching.auto_release_milestones` | Co 30 min | Auto-zwolnienie escrow po 48h ciszy klienta |
| `matching.process_referral_commissions` | 03:15 codziennie | Obliczanie prowizji referral |
| `matching.process_payouts` | 04:00 codziennie | Automatyczne wypłaty (bank/stablecoin) |

Flower dashboard: `http://localhost:5555`

### Eventy n8n (DROPIFY → n8n)

Platforma wysyła HMAC-podpisane eventy na webhooki n8n:

| Event | Kiedy |
|-------|-------|
| `dropify-job-created` | Nowe zlecenie |
| `dropify-match-created` | AI znalazł wykonawcę |
| `dropify-contract-created` | Akceptacja matcha |
| `dropify-job-completed` | Zakończenie zlecenia |
| `dropify-payment-created` | Płatność kontraktu |
| `dropify-referral-commission` | Prowizja referral |
| `dropify-daily-report` | Codziennie 07:00 |

### Szablony n8n (5 gotowych)

| Plik | Co robi |
|------|---------|
| `dropify-01-job-created-telegram.json` | Nowe zlecenie → Telegram |
| `dropify-02-match-created-slack.json` | Nowy match → Slack |
| `dropify-03-contract-completed-telegram.json` | Zakończone zlecenie → Telegram |
| `dropify-04-daily-report-telegram.json` | Dzienny raport → Telegram |
| `dropify-05-inbound-job-create.json` | n8n → DROPIFY (tworzenie zleceń) |

Import: n8n UI → Workflows → Import from File → Activate.

### Endpoint wejściowy (n8n → DROPIFY)

```
POST /api/n8n/trigger
Header: X-Dropify-Api-Key: <N8N_INBOUND_KEY>

Akcje:
- { "action": "notify", "email": "...", "title": "...", "body": "...", "type": "info" }
- { "action": "job.create", "client_email": "...", "title": "...", ... }
```

---

## 8. Model biznesowy i prowizje

### 5 strumieni przychodu

| Strumień | Stawka | Cel M6 | Cel M12 |
|----------|--------|--------|---------|
| Prowizja transakcyjna | 8% (dynamicznie 5-12%) | 1 500 PLN | 8 000 PLN |
| Subskrypcje (Free/Starter 49/Pro 149/Enterprise 499+) | — | 400 PLN | 2 000 PLN |
| Wtyczka WooCommerce | 49 PLN jednorazowo | — | częściowo |
| Aplikacja Shopify | 29 PLN/mies. | — | częściowo |
| API / White-label (#F8) | 500–2000 PLN/mies. | 200 PLN | 1 500 PLN |
| **RAZEM** | | **~2 100 PLN** | **~11 500 PLN** |

> **Uwaga:** Starsze dokumenty w `doku/` zawierały rozbieżne prognozy M12 (92 000–200 000 PLN). Wyższe liczby zakładały nierealistyczne wskaźniki konwersji. Powyższe wartości są zwymiarowane (itemized) i spójne z unit economics.

### Prowizja dynamiczna (#8)

| Typ freelancera | Prowizja |
|-----------------|----------|
| Top-rated (rating ≥4.8, ≥20 ocen) | 5% |
| Nowi (≤3 oceny) | 12% |
| Reszta | 8% (default) |

### Unit economics (zlecenie 800 PLN)

```
Prowizja 8%:           +64 PLN
- Płatność (2.5%):     -1.60 PLN
- AI (Claude):         -2 PLN
- Wsparcie:            -3 PLN
= NETTO:                57.4 PLN (≈71% marży)
```

**Breakeven:** 190 PLN koszty stałe ÷ 57 PLN = **3–4 zlecenia/miesiąc**.

### Koszty stałe (MVP)

| Pozycja | Koszt |
|---------|-------|
| VPS (Hetzner CAX11) | 20 PLN/mies. |
| Claude API (est.) | ~150 PLN/mies. |
| Domena | ~5 PLN/mies. |
| **RAZEM** | **~175–190 PLN/mies.** |

> **Uwaga:** Prognozy przychodów (M3: 3 200 PLN, M6: 21 000 PLN, M12: 92 000 PLN) to **cele/założenia**, nie zweryfikowane dane. Rzeczywiste wyniki zależą od adopcji i konwersji.

---

## 9. Konfiguracja bazy danych / integracje zewnętrzne

### Docker Compose — usługi

| Serwis | Obraz | Port | Opis |
|--------|-------|------|------|
| `db` | `pgvector/pgvector:pg16` | 5432 | PostgreSQL + pgvector |
| `redis` | `redis:7-alpine` | 6379 | Cache + Celery broker |
| `api` | `./backend` | 8000 | FastAPI |
| `worker` | `./backend` | — | Celery worker |
| `beat` | `./backend` | — | Celery beat (schedulery) |
| `flower` | `mher/flower:2.0` | 5555 | Monitoring Celery |
| `n8n` | `n8nio/n8n:latest` | 5678 (localhost) | Automatyzacje |
| `nginx` | `nginx:alpine` | 80, 443 | Reverse proxy + SSL |

### Wolumeny

- `postgres_data` — dane PostgreSQL
- `redis_data` — dane Redis
- `n8n_data` — dane n8n

### Integracje zewnętrzne

| Usługa | Do czego | Wymagana? |
|--------|----------|-----------|
| Stripe | Płatności kartą, escrow, wypłaty | Nie (tryb demo) |
| Anthropic (Claude) | AI matching, analiza, copilot, umowy | Nie (fallback regułowy) |
| OpenAI | Embeddingi wektorowe | Nie (fallback lokalny) |
| SendGrid / SMTP | Email (powiadomienia, reset hasła) | Nie (tryb cichy) |
| Telegram | Powiadomienia n8n | Nie |
| Slack | Powiadomienia n8n | Nie |
| Shopify | Integracja sklepowa (#10) | Nie |
| BaseLinker | Integracja Allegro/WooCommerce (#11) | Nie |

### WooCommerce Plugin

Wtyczka WordPress w `integrations/woocommerce/`:
- Kopiuj `dropify-fulfillment-ai.php` do `wp-content/plugins/`
- Aktywuj w WordPress → Plugins
- W DROPIFY dashboard → Developer / API → utwórz klucz partnerski
- W WordPress → Settings → DROPIFY Fulfillment AI → wklej URL API + klucz
- Opcja: auto-create on publish

Wykorzystuje istniejące endpointy API (White-label #F8), nie wymaga dodatkowego backendu.

---

## 10. Bezpieczeństwo

- JWT auth, bcrypt password hashing, role-based access (client/freelancer/admin)
- Rate limiting w nginx (30 req/s z burst 50)
- CORS allow-list via `CORS_ORIGINS`, metody ograniczone do GET/POST/PUT/DELETE/OPTIONS
- `SECRET_KEY` i `ADMIN_PASSWORD` — **WARNING przy starcie** jesli sa domyslne (config.py:67-71)
- `DEBUG=False` domyslnie (config.py:9) — bezpieczne dla produkcji
- Automatyczne backupy DB: `backend/scripts/backup.sh` (cron `0 3 * * *`)
- Stripe webhook signature verification (abezpieczenie przed fałszerstwem płatności)
- Tokeny JWT z `purpose` claim (nie da się ich użyć jako sesji)
- n8n dostępny tylko na `127.0.0.1:5678` (SSH tunnel)

### Znane luki bezpieczenstwa (do zamkniecia przed launchem)

| Priorytet | Luka | Status |
|-----------|------|--------|
| ~~WYSOKI~~ | ~~Redis bez autoryzacji (docker-compose)~~ | **WDROZONE** (23.08.2026) — `--requirepass` + REDIS_URL z haslem |
| ~~WYSOKI~~ | ~~Flower monitoring publicznie dostepny (port 5555)~~ | **WDROZONE** (23.08.2026) — basic auth + port 127.0.0.1 tylko |
| ~~WYSOKI~~ | ~~Nginx udostepnia `/docs` i `/openapi.json` publicznie~~ | **WDROZONE** (23.08.2026) — return 404 w nginx |
| ~~SREDNI~~ | ~~Health endpoint ujawnia status kluczy API (Anthropic/OpenAI/Stripe)~~ | **WDROZONE** (23.08.2026) — API keys check tylko dla adminow (Bearer token + role=admin) |
| ~~SREDNI~~ | ~~Domyslny Postgres password `dropify_pass` w docker-compose~~ | **CZESC_CIOWO** — nadal w compose jako fallback, ale REDIS juz z haslem |

---

## 11. Znane problemy, ograniczenia, TODO

### Brakujące / do dokończenia

1. **CI/CD** — ~~brak `.github/workflows`~~ → **WDROZONE** (`.github/workflows/ci.yml`: testy pytest, lint, typecheck, build — uruchamia sie na push/PR do main/master)
2. **F2 extension** — ~~podłączenie żywego API kursów walut zamiast statycznej migawki~~ **WDROZONE** — Frankfurter API (free, no key) z cache 1h + static fallback
3. **F5 extension** — ~~historia czatu widoczna też dla drugiej strony kontraktu~~ → **WDROZONE** (endpoint `copilot/history` zwraca wiadomości wszystkich uczestników kontraktu, test `test_f5_ai_copilot_history_visible_to_contract_parties`)
4. **Aktywacja n8n** — ~~domyślne włączenie 5 gotowych workflow przy starcie kontenera~~ **CZESC_CIOWO WDROZONE** — mount `/workflows` + setup script `setup.sh` do auto-importu; wymaga uruchomienia po starcie n8n
5. ~~**Fakturowanie/VAT**~~ dla własnej prowizji platformy — **WDROZONE** (23.08.2026) — model Invoice, utils/invoicing.py, routes/invoices.py, config NIP/VAT/ADDRESS, auto-generacja faktur z platnosci
6. ~~**Rozstrzyganie sporow**~~ → **WDROZONE** (23.08.2026) — proporcjonalny podzial (freelancer_pct 0-100%) + release_to_freelancer + refund_client
7. ~~**Regulamin + Polityka Prywatnosci**~~ → **WDROZONE** (23.08.2026) — strony `/terms` i `/privacy`
8. ~~**Security: DEBUG=True, brak warningow**~~ → **WDROZONE** (23.08.2026) — DEBUG=False, warnings dla default SECRET_KEY/ADMIN_PASSWORD
9. ~~**CORS zbyt szeroki**~~ → **WDROZONE** (23.08.2026) — metody ograniczone do GET/POST/PUT/DELETE/OPTIONS
10. ~~**Brakujace i18n keys**~~ → **WDROZONE** (23.08.2026) — contracts.status.cancelled/disputed
11. ~~**Custom 404 + Error boundary**~~ → **WDROZONE** (23.08.2026) — not-found.tsx, error.tsx
12. ~~**Security: /docs, Flower, Redis**~~ → **WDROZONE** (23.08.2026) — nginx 404, Flower basic auth, Redis --requirepass
13. ~~**i18n: brakujace tlumaczenia dashboard**~~ → **WDROZONE** (23.08.2026) — ~25 nowych kluczy (matches, contracts, freelancers, profile, admin)
14. ~~**RODO: brak zgody w formularzach**~~ → **WDROZONE** (23.08.2026) — checkbox + backend validation + timestamp

### Ograniczenia techniczne

- Frontend na Vercel (Next.js), backend na VPS — dwa osobne hostingi
- n8n słucha tylko na localhost (wymaga SSH tunnelingu do UI)
- Płatności Stripe w trybie demo gdy brak kluczy (celowo zaprojektowane)
- Stablecoin payouts — preferencje w profilu, ale automatyczne wypłaty wymagają skonfigurowanego Stripe
- **Security gaps przed launchem:** ~~Redis bez hasla~~ WDROZONE, ~~Flower publiczny~~ WDROZONE, ~~/docs publiczne~~ WDROZONE (patrz §10)

---

## 12. Historia ważnych decyzji architektonicznych

### Frontend: React → Next.js 16

Dokumenty w `doku/` (w tym `dropify_starter_kit.md`, `Technical_Blueprint_DROPIFY.docx`) opisują frontend jako React+Vite. **Faktycznie frontend to Next.js 16 z App Router** — zmiana została dokonana przed niniejszą konsolidacją. Next.js wybrano ze względu na:
- Vercel deployment (zero-config)
- App Router (lepsza struktura dla dashboardu)
- SSR/SSG dla landing page
- i18n through custom provider (nie next-intl)

### Backend: monolit FastAPI zamiast mikroserwisów

Wybrano monolit zamiast mikroserwisów ze względu na:
- Mały zespół (1 osoba)
- Prostszy deployment (1 kontener Docker)
- Wystarczający na MVP i etap M1-M6
- Możliwość podziału na mikroserwisy później (M12+)

### Fallbacki AI (każda funkcja działa bez kluczy API)

Kluczowa decyzja: każda funkcja AI ma lokalny fallback (reguły/heurystyki). Dzięki temu:
- Platforma działa od pierwszego dnia (zero kosztów API)
- Niezawodność (API outage nie blokuje platformy)
- Łatwiejszy development (nie wymaga kluczy API do testowania)

### Stripe Checkout zamiast PaymentIntents

Wybrano Stripe Checkout (redirect) zamiast PaymentIntents (embedded) ze względu na:
- Prostsza integracja
- Lepsze UX dla klientów (strona Stripe)
- Automatyczne obsługiwanie 3D Secure
- Fallback na tryb demo gdy brak Stripe

### Prowizja dynamiczna (#8)

Zamiast stałej prowizji 8% wprowadzono dynamiczną (5-12%) opartą o reputację freelancera:
- Top-rated (4.8+, 20+ ocen): 5% — nagradza jakość
- Nowi (≤3 oceny): 12% — compensation za wyższe ryzyko
- Reszta: 8% — default
- Stawka zapisywana na kontrakcie, nie zmienia się w trakcie

---

## 13. Historia dokumentacji

### Pliki w `doku/` — status

| Plik | Status | Uwagi |
|------|--------|-------|
| `MEGA_PLATFORM_BLUEPRINT.md` | **AKTUALNY** (21.08.2026) | Najnowszy i najpełniejszy — nadpisuje starsze |
| `README_START_HERE.md` | NIEAKTUALNY | Nadbiór z 00_CZYTAJ_NAJPIERW + README.md |
| `00_CZYTAJ_NAJPIERW.txt` | NIEAKTUALNY | Duplikat SUMMARY + README |
| `SUMMARY_EVERYTHING.txt` | NIEAKTUALNY | Duplikat 00_CZYTAJ_NAJPIERW |
| `COMPLETE_GUIDE_CZYTAJ_TO.txt` | NIEAKTUALNY | Nadbiór z dropify_starter_kit.md |
| `dropify_starter_kit.md` | NIEAKTUALNY | Kod opisuje React+Vite, a nie Next.js |
| `Biznes_Plan_DROPIFY_Zero_Budget.docx` | CZĘŚCIOWO AKTUALNY | Biznes plan OK, techniczne nieaktualne |
| `Technical_Blueprint_DROPIFY.docx` | NIEAKTUALNY | Architektura opisuje stary stack |
| `30_DNI_LAUNCH_CHECKLIST.txt` | NIEAKTUALNY | Plan na FastAPI+React, nie Next.js |
| `AI_MATCHING_ENGINE_DEEP_DIVE.txt` | CZĘŚCIOWO AKTUALNY | Scoring OK, embellishe'owane statystyki |
| `FULL_AUTOMATION_PASSIVE_INCOME.txt` | CZĘŚCIOWO AKTUALNY | Wizja OK, nierealistyczne prognozy |
| `PLAN_20_FUNKCJI_PONAD_KONKURENCJA.md` | AKTUALNY | Sprinty 1-3 wdrożone, Sprint 4 częściowo |
| `N8N_AUTOMACJE.md` | AKTUALNY | Instrukcja n8n aktualna |

### Rozbieżności文档owe vs kod

| Kwestia | Dokumenty mówią | Kod mówi | Rozstrzygnięcie |
|---------|-----------------|----------|-----------------|
| Frontend framework | React + Vite (`dropify_starter_kit.md`) | Next.js 16 App Router (`package.json`, `src/app/`) | **Kod: Next.js 16** |
| Frontend hosting | Docker (`dropify_starter_kit.md`) | Vercel (`nginx.conf`: redirect do `dropify.vercel.app`) | **Kod: Vercel** |
| Prowizja | 8% flat (starsze dokumenty) | Dynamiczna 5-12% (`config.py`, `fees.py`) | **Kod: dynamiczna** |
| Struktura backendu | Osobne pliki models/ routes/ (`dropify_starter_kit.md`) | `models.py` (monolit), `routes/` (folder) | **Kod: monolit models.py** |
| 92% acceptance rate | `AI_MATCHING_ENGINE_DEEP_DIVE.txt` | Brak weryfikacji w kodzie | **Założenie/cel** |
| Revenue projections M12 | 92 000–200 000 PLN (SUMMARY/COMPLETE_GUIDE) | 11 500 PLN (itemized, zwymiarowane) | **11 500 PLN (bezpieczniejsza prognoza)** |

### Plik glówny

`README.md` w katalogu głównym (19.08.2026) jest aktualnym opisem technicznym i zastępuje `README_START_HERE.md` oraz większość treści z `doku/`.


---

## 14. Aspekty prawne i regulacyjne

### Dane prawne platformy

| Element | Dane |
|---------|------|
| **Wlasciciel platformy** | **HardbanRecords Lab** |
| **Siedziba** | Wiercień, Polska |
| **Email kontaktowy / prawny** | dropify@hardbanrecordslab.online |
| **Logo (zrodlowe)** | `G:\Dropify Service\public\logo Dropify Service.png` |
| **Logo (design)** | `G:\Trening\Forma60\designe\logo.png` |
| **Trademark** | DROPIFY — all rights reserved, HardbanRecords Lab |
| **Prawa autorskie** | © 2026 DROPIFY / HardbanRecords Lab. Wszelkie prawa zastrzeżone. |

> ~~`Footer.tsx` zawiera linki do Regulaminu i Polityki Prywatnosci, ktore nie prowadza do zadnych realnych stron~~ **ZROBIONE** — strony `/terms` i `/privacy` utworzone (23.08.2026), linki w Footer.tsx dzialaja.

### Stan obecny

| Element | Status | Zrodlo |
|---------|--------|--------|
| Regulamin (Terms of Service) | **WDROZONY** — strona `/terms` utworzona (23.08.2026), link w Footer.tsx | `src/app/terms/page.tsx`, `src/components/Footer.tsx` |
| Polityka Prywatnosci (Privacy Policy) | **WDROZONA** — strona `/privacy` utworzona (23.08.2026), link w Footer.tsx | `src/app/privacy/page.tsx`, `src/components/Footer.tsx` |
| Strona `/legal` | **CZESC_CIOWA** — `/terms` i `/privacy` utworzone (23.08.2026), brak centralnej strony `/legal` | `src/app/terms/page.tsx`, `src/app/privacy/page.tsx` |
| Rejestracja dzialalnosci | **BRAK - do uzupelnienia** — `00_CZYTAJ_NAJPIERW.txt` sugeruje "Register business (optional first, required M3+)" | `doku/00_CZYTAJ_NAJPIERW.txt` |
| Ubezpieczenie OC | **BRAK - do uzupelnienia** | — |
| Numer NIP/VAT | **BRAK - do uzupelnienia** | — |
| Fakturowanie/VAT dla prowizji platformy | **BRAK** — wymagane do legalnego dzialania w PL na wieksza skale | `MEGA_PLATFORM_BLUEPRINT.md` §9.2 |
| Klauzula RODO w formularzach | **BRAK - do uzupelnienia** — brak widocznej zgody na przetwarzanie danych osobowych | audit kodu |

### VAT i podatki transgraniczne (co juz istnieje w kodzie)

`backend/app/utils/currency.py` zawiera orientacyjne notatki VAT - **nie sa porada prawną**, wyraznie oznaczone jako "not legal advice":

| Kraj | VAT | Notatka |
|------|-----|---------|
| PL | 23% | Usluga B2B krajowa: 23% VAT (chyba ze freelancer jest zwolniony) |
| DE | 19% | Reverse-charge w UE B2B (0% faktura, kupujacy rozlicza) |
| US | 0% | Brak VAT; sprawdzic reguly sales-tax per stan |
| GB | 20% | Post-Brexit: possible reverse-charge B2B |
| UA | 20% | Uslugi transgraniczne B2B zazwyczaj zwolnione z VAT po stronie ukrainskiej |
| Inne | 0% | Default: weryfikacja reverse-charge / VAT przed fakturowaniem |

Endpoint `GET /api/fx/tax-hint/{country}` zwraca powyzsze dane.

### Wymagania prawne przed startem (checklist)

1. **Regulamin** - sporzadzic (szablon online, ~500 PLN za prawnika - z `00_CZYTAJ_NAJPIERW.txt`)
2. **Polityka Prywatnosci / RODO** - sporzadzic (wymog prawny w UE)
3. **Rejestracja dzialalnosci** - wymagane od M3+ (JDG/Sp. z o.o.)
4. **NIP + VAT-UE** - wymagane do faktur B2B w UE
5. **Fakturowanie prowizji** - system generujacy faktury VAT dla platformy
6. ~~**Klauzule RODO**~~ - w formularzach rejestracji i newsletterze — **WDROZONE** (23.08.2026) — checkbox + backend validation
7. **Ubezpieczenie OC** - zalecane dla platformy laczącej strony


---

## 15. Pelny wykaz funkcji (20 + F1-F8)

### Legenda statusow

| Status | Znaczenie |
|--------|-----------|
| WDROZONA | Dziala w kodzie, przeszla testy |
| CZESCIOWA | Kod istnieje, ale brakuje elementow |
| PLANOWANA | W dokumentacji, nie ma kodu |

### Grupa A: AI - Matching i zaufanie (Sprint 1-2, P0)

| # | Nazwa | Status | Opis biznesowy | Opis techniczny |
|---|-------|--------|----------------|-----------------|
| 1 | AI Instant Interviews | WDROZONA | Automatyczne rozmowy kwalifikacyjne - freelancer odpowiada na 3-5 pytan, Claude ocenia 0-100 | generate_interview_questions, fallback semantyczny, event n8n |
| 2 | AI Deliverable Checker | WDROZONA | Automatyczna weryfikacja dostarczonej pracy - AI QA report (score 0-100, checklist wymagan) | POST /api/jobs/{id}/deliverables, fallback regułowy |
| 3 | AI Price Negotiator | WDROZONA | Automatyczna negocjacja ceny w ramach kontraktu (2-3 rundy) | GET /api/jobs/{id}/fair-price, propose/confirm/decline-price |
| 4 | Best Match Guarantee | WDROZONA | Gwarancja jakosci matcha - odrzucenie triggeruje ponowny matching z wykluczeniem dotychczasowych | tasks/matching.py chain na statusach |

### Grupa B: Platnosci i escrow (Sprint 3, P0)

| # | Nazwa | Status | Opis biznesowy | Opis techniczny |
|---|-------|--------|----------------|-----------------|
| 5 | Milestones + Auto-Release Escrow | WDROZONA | Kontrakt na 2-4 etapy, auto-zwolnienie po 48h ciszy klienta | Model Milestone, auto_release_milestones co 30 min |
| 6 | Crypto/Stablecoin payouts | WDROZONA | Wyplaty w USDT/stablecoinach dla freelancerow spoza UE | Preferencje w profilu, process_payouts 04:00 |
| 7 | Deposit Refund Guarantee | WDROZONA | Gwarancja zwrotu zaliczki przy no-show freelancera | request-refund, AI weryfikacja, automatyczny re-matching |
| 8 | Dynamiczna prowizja | WDROZONA | Top-rated 5%, nowi 12%, reszta 8% | calculate_fee_rate(), Contract.fee_rate |

### Grupa C: E-commerce / Dropshipping (Sprint 4, P0-P1)

| # | Nazwa | Status | Opis biznesowy | Opis techniczny |
|---|-------|--------|----------------|-----------------|
| 9 | WooCommerce Plugin | CZESCIOWA | Wtyczka WordPress: tworzenie zlecen z produktow, statusy sync | PHP plugin integrations/woocommerce/, API REST |
| 10 | Shopify App | CZESCIOWA | Analogicznie dla Shopify (App Store) | routes/integrations.py, webhooks |
| 11 | Allegro / BaseLinker | CZESCIOWA | Sync produktow i zlecen z Allegro | routes/integrations.py, BaseLinker API |
| 12 | Product Source Finder | WDROZONA | Klient wkleja link produktu -> AI rozbija na komponenty uslug + gotowe zlecenia | POST /api/factory/source-finder, create-jobs |

### Grupa D: Automatyzacja pracy (Sprint 2, P1)

| # | Nazwa | Status | Opis biznesowy | Opis techniczny |
|---|-------|--------|----------------|-----------------|
| 13 | AI Proposal Autopilot | WDROZONA | System sam odpowiada na matchy wg szablonow freelancera | auto_accept_enabled/min_budget/min_score, auto-akcept |
| 14 | AI Onboarding 30s | WDROZONA | Kreator zlecen w 3 krokach z AI | POST /api/jobs/generate, formularz auto-wypelnia |
| 15 | Referral 2.0 Earn Forever | WDROZONA | 2% prowizji od zlecen zaproszonego x 12 mies. + 1% od jego referali | Model Commission, task Celery 03:15 |
| 16 | Daily AI Revenue Report | WDROZONA | Dzienny raport z anomaliami i AI insights | daily_summary rozszerzony, event n8n |

### Grupa E: Spolecznosc, reputacja i UX (P1-P2)

| # | Nazwa | Status | Opis biznesowy | Opis techniczny |
|---|-------|--------|----------------|-----------------|
| 17 | Skill Badges + AI-Verified Portfolio | **WDROZONA** (23.08.2026) — model Badge, utils/badges.py, routes/badges.py, 8 kategorii, 3 poziomy (bronze/silver/gold), portfolio stats | Wymaga integracji z Claude do generowania pytan testowych |
| 18 | Time-to-Hire Dashboard | WDROZONA | Realtime wskazniki: sredni czas do matcha, aktywne matchy, statusy milestone'ow | analytics/dashboard |
| 19 | Multilingual Matching | CZESCIOWA | Zlecenia w DE/ES/CZ - Claude rozumie, embeddingi matchuja mimo jezyka | i18n PL/EN dziala, brak plikow DE/ES |
| 20 | Transparent Fees Page | WDROZONA | Interaktywny kalkulator DROPIFY vs Upwork vs Fiverr | Strona /fees, link w nawigacji |

### Funkcje F1-F8 (iteracja 19-20.08.2026)

| # | Nazwa | Status | Opis biznesowy | Opis techniczny |
|---|-------|--------|----------------|-----------------|
| F1 | AI Listing Factory | WDROZONA | Z nazwy/linku produktu -> gotowa oferta (tytul, opis, SEO, meta) | routes/factory.py, utils/ai.py::generate_listing |
| F2 | Global Currency and Tax Auto-Engine | WDROZONA | Przeliczenia PLN->EUR/USD/GBP/UAH/CZK/SEK + notatka VAT | routes/fx.py, utils/currency.py |
| F3 | AI Contract and Compliance Generator | WDROZONA | Generuje umowe serwisowa (PL/EN) dla kazdego kontraktu | routes/contracts.py::contract_agreement |
| F4 | Smart Supplier Risk Score | WDROZONA | Wykaznik zaufania 0-100 | routes/users.py::user_risk_score, utils/risk.py |
| F5 | AI Co-Pilot | WDROZONA | Czat AI w kazdym zleceniu (kontekst tego zlecenia) | routes/copilot.py, utils/ai.py::answer_copilot |
| F6 | Marketing Video Script Generator | WDROZONA | Scenariusz 20-30s (hook + tresc + CTA) do TikTok/Reels | utils/ai.py::generate_video_script |
| F7 | Global Time-Zone Scheduler | WDROZONA | Sugestia nakladajacych sie godzin lub async 24/7 | routes/matches.py::match_schedule |
| F8 | White-Label / Reseller API | WDROZONA | Klucze API dla agencji (osobna marka, ten sam backend) | routes/developer.py, model ApiKey |

### Funkcje Frontendowe F9-F11 (iteracja 23.08.2026)

| # | Nazwa | Status | Opis biznesowy | Opis techniczny |
|---|-------|--------|----------------|-----------------|
| F9 | Regulamin (Terms of Service) | WDROZONA | Pelny regulamin PL, 11 paragrafow (postanowienia ogolne, definicje, konto, matching, escrow, prowizje, odpowiedzialnosc, reklamacje, RODO, postanowienia koncowe) | `src/app/terms/page.tsx` |
| F10 | Polityka Prywatnosci (Privacy Policy) | WDROZONA | Pelna polityka PL, 12 sekcji (administrator, dane, cele, podstawa prawna, udostepnianie, przekazywanie poza EOG, okres przechowywania, prawa, bezpieczenstwo, cookies, zmiany, kontakt) | `src/app/privacy/page.tsx` |
| F11 | Custom 404 + Error Boundary | WDROZONA | Strona bledu 404 z linkiem do strony glownej + error boundary z przyciskiem reset | `src/app/not-found.tsx`, `src/app/error.tsx` |

### Status podsumowanie

| Status | Liczba |
|--------|--------|
| WDROZONA | 28 (#1-#8, #12-#16, #17, #18, #20, F1-F8, F9-F11) |
| CZESCIOWA | 5 (#9, #10, #11, #19, F2 live rates) |
| BRAK | 0 |
| **RAZEM** | **33** |


---

## 16. Pelna roadmapa (chronologiczna)

> Zrodla: PLAN_20_FUNKCJI_PONAD_KONKURENCJA.md, MEGA_PLATFORM_BLUEPRINT.md, Biznes_Plan_DROPIFY_Zero_Budget.docx, audit kodu 19-20.08.2026.

### Zamkniete (zrobione)

| Data | Milestone | Szczegoly |
|------|-----------|-----------|
| Czerwiec 2026 | Biznes Plan v1.0 | Biznes_Plan_DROPIFY_Zero_Budget.docx - 5 strumieni przychodu, unit economics, roadmapa 24 mies. |
| Przed 19.08.2026 | Rdzen platformy ~70-75% | Audit: marketplace core 90%, AI matching 85%, frontend 90%, monetyzacja 40% |
| 19.08.2026 | Sprint 1 (#4, #8, #15, #16, #18, #20) | Best Match Guarantee, dynamic fee, referral 2.0, daily report, time-to-hire, fee comparator |
| 19.08.2026 | Sprint 2 (#1, #2, #3, #13, #14) | AI interviews, deliverable checker, price negotiator, autopilot, onboarding 30s |
| 19.08.2026 | Sprint 3 (#5, #6, #7) | Milestones escrow, stablecoin payouts, refund guarantee |
| 19-20.08.2026 | Stripe Checkout (naprawa platnosci) | payments.py, webhooks.py - realne platnosci zamiast demo |
| 19-20.08.2026 | 47 testow pytest | auth, matching, escrow, Stripe fixes, Sprint 4, password reset, disputes |
| 19-20.08.2026 | Sprint 4 (#9-#12) integracje e-commerce | WooCommerce plugin (PHP), Shopify, BaseLinker + Allegro, Product Source Finder |
| 19-20.08.2026 | Reset hasla + weryfikacja email | /forgot-password, /reset-password, /verify-email, JWT purpose-scoped |
| 19-20.08.2026 | Obsluga sporow | POST /contracts/{id}/dispute + AI ocena + resolve-dispute (admin) |
| 19-20.08.2026 | Kategorie Tier 1+2 | 6 nowych kategorii: Real Estate, Audio and Podcast, Publishing, Events, Music Production, Data and AI Services |
| 19-20.08.2026 | F1-F8 (8 nowych funkcji) | AI Listing Factory, Currency/Tax Engine, Contract Generator, Risk Score, Co-Pilot, Video Script, Time-Zone Scheduler, White-Label API |

### W toku / Do zrobienia (wg §11 i §9.2 MEGA_PLATFORM_BLUEPRINT)

| Priorytet | Zadanie | Zrodlo |
|-----------|---------|--------|
| ~~WYSOKI~~ | ~~Regulamin + Polityka Prywatnosci (strony /terms, /privacy)~~ | **WDROZONE** — strony utworzone 23.08.2026, linki w Footer.tsx |
| WYSOKI | Rejestracja dzialalnosci + NIP/VAT-UE | §14 |
| WYSOKI | Fakturowanie/VAT dla prowizji platformy | §11, MEGA_PLATFORM_BLUEPRINT §9.2 |
| SREDNI | ~~F2 extension - zywe API kursow walut zamiast statycznej migawki~~ | **ULEPSZONE** — cache 1h + fallback statyczny | §11 |
| SREDNI | ~~F5 extension - historia czatu widoczna dla obu stron kontraktu~~ | **WDROZONE** — endpoint copilot/history zwraca wiadomości wszystkich uczestników | §11 |
| SREDNI | Aktywacja n8n - domyslne wlaczenie 5 workflow przy starcie | §11 |
| SREDNI | CI/CD - .github/workflows (testy + build recznie) | §11 |
| NISKI | Rozstrzyganie sporow - podzial proporcjonalny (60/40 zamiast binarnego) | §11 |
| NISKI | Multilingual - pliki DE/ES dla i18n | §15, #19 |
| NISKI | Skill Badges + AI-Verified Portfolio (#17) | §15 |

### Roadmapa strategiczna (z Biznes_Plan, zaktualizowana)

| Faza | Okres | Cele |
|------|-------|------|
| MVP | M1-M2 | Landing page + waitlist, 10+ beta users, pierwsze zlecenie, NPS > 40 |
| Polish and Iterate | M2-M3 | Claude AI pelna integracja, rating system, 30+ aktywnych uzytkownikow, 100+ zlecen/mies. |
| Integrations | M3-M6 | WooCommerce plugin, API docs, affiliate program, premium tiers, 350+ zlecen/mies., rentownosc |
| Scale | M6-M12 | Shopify app, Allegro, mobile app, zaawansowane AI, 1000+ zlecen/mies., 11.5k PLN/mies. |
| Dominate | M12-M24 | Regionalna ekspansja EU, potencjalne finansowanie, 10k+ zlecen/mies. |


---

## 17. Rozszerzony model biznesowy - konkurencja i segmenty

### Analiza konkurencji (sierpien 2026)

> Zrodlo: PLAN_20_FUNKCJI_PONAD_KONKURENCJA.md - na podstawie publicznych danych rynkowych (Upwork Spring 2026 z Uma, Fiverr Go Q1 2026, raporty inwestorskie UPWK/FVRR).

#### Upwork (2026)

| Co maja | Slabosc do wykorzystania |
|---------|--------------------------|
| Uma AI work agent: instant interviews, shortlisting, generator kontraktow, work-history summaries | Take rate ~19-20% (fee 0-15% freelancer + ~5% client) - drogo |
| Aplikacja w ChatGPT / Claude - szukanie talentow przez chat | Czas do zatrudnienia ~3 dni; wciaz reczny wybor z aplikujacych |
| AI-native homepage, majority of job posts przez Uma | Matching dziala tylko na tym KTO SAM SIE ZGLOSCI - najlepsi sie nie zgłaszaja |
| OpenAI partnership - 10 mln certyfikowanych freelancerow | Brak lokalnego rynku PL/EU, brak integracji dropshipping |

#### Fiverr (2026)

| Co maja | Slabosc do wykorzystania |
|---------|--------------------------|
| Fiverr Go - AI asystent/klon stylu sprzedawcy | Take rate 27.7% - najdrozsza prowizja na rynku |
| Kategoria AI Agents, agentic workflows | Spadek aktywnych kupujacych -13.6% YoY; gig-owy model bez kontraktow |
| Gigs - zakup z polki | Brak milestone'ow, escrow na slowo, brak ochrony przy duzych zleceniach |

#### Reszta rynku

Toptal (2-3% najlepszych, drogi, bez self-service), Guru/PeoplePerHour (przestarzale UX), platformy niszowe (bez AI).

### Luka rynkowa DROPIFY

1. **Prowizja 8% flat** vs 19-28% u konkurencji
2. **Matching proaktywny** - AI sam znajduje najlepszych (nie ci, ktorzy klikna apply)
3. **Local-first PL/EN + EU** - konkurencja globalna, my lokalni i szybcy
4. **E-commerce native** - WooCommerce/Shopify/Allegro pod dropshipping (nikt tego nie ma w 1 produkcie)

### Segmenty klientow

| Segment | Potrzeba | Propozycja wartosci |
|---------|----------|---------------------|
| E-commerce / dropshipperzy | Szybkie znalezienie dostawcy/freelancera do produktu | AI matching + WooCommerce plugin + Product Source Finder |
| Agencje marketingu | Outsourcing zdjec, opisow, filmow dla klientow | AI Listing Factory + Video Script Generator |
| Freelancerzy (design, foto, dev) | Nowe zlecenia bez recznego szukania | Proaktywny matching + autopilot + referral 2.0 |
| Agencje / resellerzy | Osobna marka na silniku DROPIFY | White-Label API (#F8) |

### Go-to-Market Strategy

> Zrodlo: Biznes_Plan_DROPIFY_Zero_Budget.docx - scenariusz oryginalny, niezweryfikowany z obecnym kodem.

#### Phase 0: MVP Launch (M1-M2)

- **Landing Page**: prosta strona + Typeform do waitlist
- **SEO**: frazy dropshipping matching, freelance matching Poland
- **Early Users (20-50)**: outreach DM na grupach FB (dropshipping, e-commerce), oferta FREE tier + 3 mies. PRO gratis
- **Cel**: 10 placacych, 20+ waitlist

#### Phase 1: Traction (M3-M6)

- WooCommerce plugin MVP (cel: 100 instalacji)
- Case studies: 3-5 historii sukcesu
- Blog 2x/tydzien (SEO hacking)
- YouTube: 1-2 min demo, unboxing, ROI stories
- **Cel**: 50+ aktywnych uzytkownikow, 200 transakcji/mies.

#### Phase 2: Scale (M7-M12)

- Shopify app na App Store
- Partnerships: reseller programy z agencjami
- Affiliate program (20% commission)
- Paid ads: 500-1000 PLN/mies.
- **Cel**: 200+ aktywnych uzytkownikow, 1000+ transakcji/mies.

### Risk and Mitigation

> Zrodlo: Biznes_Plan_DROPIFY_Zero_Budget.docx - scenariusz oryginalny.

| Ryzyko | Opis | Mitigacja |
|--------|------|-----------|
| Brak product-market fit | Zly problem, brak popytu | Wczesne petle feedbacku, iteracja co tydzien na MVP |
| Koszty Claude API ekspluzuja | Pay-per-token, wysoki wolumen | Cache wynikow, batch processing, lokalny model jako backup |
| Chicken-egg problem marketplace | Brak podazy (freelancerow) lub popytu (klientow) | Start z 1 niszy (fotografia), reczne seedowanie obu stron |
| Brak pozyskiwania uzytkownikow | Nie mozna znalezc uzytkownikow | Cold outreach do 50 grup FB, darmowy premium M1-M3 |
| VPS pada | Serwer sie wysypuje, utrata danych | Automatyczne backupy dzienne, redundancja od M6+ |

### Scenariusze finansowe (Conservative vs Aggressive)

> **UWAGA:** Ponizsze tabelki pochodza z Biznes_Plan_DROPIFY_Zero_Budget.docx (czerwiec 2026). Sa to SCENARIUSZE/ZALOZENIA sprzed obecnego audytu kodu, NIE zweryfikowane dane. Obecny handbook uzywa wartosci zwymiarowanych (itemized) z §8 jako wiążące - ponizsze wartosci sluza do porownania.

#### Conservative Scenario (Safe Forecast)

| Miesiac | Uzytkownicy | Zlecenia/mies. | Przychod/mies. |
|---------|-------------|----------------|----------------|
| M1 | 10 | 5 | 320 PLN |
| M2 | 20 | 15 | 960 PLN |
| M3 | 30 | 50 | 3 200 PLN |
| M6 | 80 | 150 | 9 600 PLN |
| M12 | 200 | 500 | 32 000 PLN |
| M24 | 500 | 1 500 | 96 000 PLN |

#### Aggressive Scenario (Viral Growth)

| Miesiac | Uzytkownicy | Zlecenia/mies. | Przychod/mies. |
|---------|-------------|----------------|----------------|
| M1 | 20 | 10 | 640 PLN |
| M3 | 100 | 200 | 12 800 PLN |
| M6 | 300 | 800 | 51 200 PLN |
| M12 | 1 000 | 3 000 | 192 000 PLN |
| M24 | 5 000 | 10 000 | 640 000 PLN |

> Porownanie z §8: obecny handbook uzywa wartosci zwymiarowanej M12 = ~11 500 PLN (bezpieczna prognoza, itemized). Scenariusz Conservative z Biznes_Plan przewiduje 32 000 PLN - jest to 2.8x wiecej, co zaklada wyzsza konwersje na subskrypcje i wiecej zlecen niz udowodniono w obecnym stanie.

### CAC and LTV - BRAK KRYTYCZNYCH DANYCH

> **BRAK - do uzupelnienia.** Zaden z dokumentow projektowych nie zawiera danych dotyczacych:
>
> - **CAC (Customer Acquisition Cost)** - koszt pozyskania jednego klienta (marketing + outreach + onboarding). Bez tego nie wiadomo, ile moznaloby wydac na reklame przy obecnej marzy 57.4 PLN/transakcja.
> - **LTV (Lifetime Value)** - wartosc klienta w calego cykl zycia (ile transakcji x ile prowizji przez czas korzystania z platformy). Bez tego nie mozna ocenic, czy koszt pozyskania sie zwraca.
>
> **Dlaczego to wazne:** Przy marzy netto 57.4 PLN na transakcji, jesli sredni klient robi 3 transakcje/mies. przez 6 mies., to LTV = ~1 033 PLN. Jesli CAC < 344 PLN (1/3 LTV), model sie oplaca. Ale **nie mamy zadnych danych** - nie wiemy, ile kosztuje pozyskanie klienta, ile transakcji robi srednio, ani jak dlugo zostaje na platformie. To czyni calkowita prognoze rentownosci spekulacja.


---

## 18. Inwentarz brakow prawnych i biznesowych

> Pelna lista oznaczonych jako BRAK - do uzupelnienia w calej dokumentacji.

### Prawne / regulacyjne

| # | Brak | Dlaczego wazne | Status | Zrodlo |
|---|------|----------------|--------|--------|
| 1 | ~~Regulamin (Terms of Service)~~ | Wymog prawny | **WDROZONY** (23.08.2026) — `src/app/terms/page.tsx` | §14 |
| 2 | ~~Polityka Prywatnosci (Privacy Policy)~~ | Wymog RODO | **WDROZONA** (23.08.2026) — `src/app/privacy/page.tsx` | §14 |
| 3 | Rejestracja dzialalnosci | Wymagane od M3+ (JDG/Sp. z o.o.) | DO REJESTRACJI — zalozyciel prowadzi JDG (niezarejestrowana) | §14, 00_CZYTAJ_NAJPIERW.txt |
| 4 | NIP + VAT-UE | Wymagane do faktur B2B w UE | DO UZUPEŁNIENIA — brak NIP (rejestracja JDG wciaz w toku) | §14 |
| 5 | ~~Fakturowanie/VAT dla prowizji platformy~~ | Legalne dzialanie w PL na wieksza skale | **WDROZONE** (23.08.2026) — model Invoice, logika generowania, trasy API, config NIP | §11, MEGA_PLATFORM_BLUEPRINT §9.2 |
| 6 | ~~Klauzule RODO w formularzach~~ | Brak widocznej zgody na przetwarzanie danych | **WDROZONE** (23.08.2026) — checkbox RODO w rejestracji, pole rodo_consent + timestamp w modelu User, walidacja backend | audit kodu |
| 7 | Ubezpieczenie OC | Zalecane dla platformy laczacej strony | DO UZUPEŁNIENIA — brak OC | §14 |

### Biznesowe / finansowe

| # | Brak | Dlaczego wazne | Zrodlo |
|---|------|----------------|--------|
| 8 | CAC (Customer Acquisition Cost) | Nie mozna ocenic rentownosci marketingu | §17 |
| 9 | LTV (Lifetime Value) | Nie mozna ocenic, czy koszt pozyskania sie zwraca | §17 |
| 10 | Dane o realnej konwersji (zlecenie -> zaplacone) | Prognozy oparte na zalozeniach, nie pomiarach | §8 uwaga |
| 11 | Realna liczba aktywnych uzytkownikow | Wszystkie prognozy sa celami/zalozeniami | §8 uwaga |

### Techniczne (z §11)

| # | Brak | Dlaczego wazne | Status | Zrodlo |
|---|------|----------------|--------|--------|
| 12 | ~~CI/CD (.github/workflows)~~ | | **WDROZONE** — `.github/workflows/ci.yml` | §11 |
| 13 | ~~Zywe API kursow walut~~ | F2 uzywa statycznej migawki | **WDROZONE** — Frankfurter API (free) z cache 1h + static fallback | §11 |
| 14 | ~~Historia czatu F5 dla obu stron~~ | | **WDROZONE** — endpoint copilot/history | §11 |
| 15 | ~~Aktywacja n8n domyslna~~ | 5 workflow wymaga recznej aktywacji | **CZESC_CIOWO WDROZONE** — mount + setup.sh | §11 |
| 16 | ~~Proporcjonalne rozstrzyganie sporow~~ | Obecnie binarne (pelne zwolnienie/pelny zwrot) | **WDROZONE** (23.08.2026) — 3 opcje: release, refund, proportional | §11 |
| 17 | ~~Security: DEBUG, CORS, warningi~~ | | **WDROZONE** (23.08.2026) — DEBUG=False, CORS ograniczone, warnings | §10 |
| 18 | ~~Brakujace i18n keys~~ | | **WDROZONE** (23.08.2026) — contracts.status.cancelled/disputed | §11 |
| 19 | ~~Custom 404 + Error boundary~~ | | **WDROZONE** (23.08.2026) — not-found.tsx, error.tsx | §11 |
| 20 | ~~Security: /docs, Flower, Redis~~ | | **WDROZONE** (23.08.2026) — nginx 404, Flower auth, Redis auth | §10 |
| 21 | ~~i18n: brakujace tlumaczenia dashboard~~ | | **WDROZONE** (23.08.2026) — ~25 nowych kluczy | §11 |



---

## 19. Pakiet inwestorski / Pitch Deck

> Sekcja przeznaczona dla potencjalnych inwestorow i wspolnikow. Format: seed-stage pitch deck / one-pager. Kod zrodlowy jest zrodlem prawdy; dane niezweryfikowane oznaczone jawnie. Nic nie jest fabrykowane.

---

### 19.1 Executive Summary

**DROPIFY** to platforma B2B typu marketplace, ktora za pomoca AI automatycznie dopasowuje zlecenia (e-commerce, dropshipping, uslugi cyfrowe) do freelancerow i dostawcow, a nastepnie samodzielnie prowadzi cala transakcje — od dopasowania po wyplate. Czlowiek potrzebny jest tylko do decyzji strategicznych; reszta dziala 24/7.

**Zalozyciel / Wlasciciel:** HardbanRecords Lab, Wiercień, Polska
**Email kontaktowy:** dropify@hardbanrecordslab.online
**Trademark:** DROPIFY — all rights reserved, HardbanRecords Lab

**Problem:** Zleceniodawcy z e-commerce/dropshippingu szukaja tanich, wiarygodnych dostawcow. Matching jest reczny i nieefektywny. Konkurencja (Upwork 19-20%, Fiverr 27.7%) pobiera wysoke prowizje, a najlepsi freelancerzy nie zgłaszaja sie sami.

**Rozwiazanie:** AI proaktywnie znajduje najlepszych freelancerow (nie czeka na aplikacje), prowizja 8% flat (dynamicznie 5-12%), pelna automatyzacja end-to-end (matching → kontrakt → escrow → QA → wyplata), lokalny fokus PL/EU + integracje e-commerce (WooCommerce, Shopify, Allegro).

**Traction:**
> WYMAGA UZUPEŁNIENIA PRZEZ ZAŁOŻYCIELA — patrz §19.6 Traction.

**Ask:**
> WYMAGA UZUPEŁNIENIA PRZEZ ZAŁOŻYCIELA — patrz §19.12 Financial Ask & Use of Funds.

---

### 19.2 Problem & Solution

#### Problem — Scenariusze uzytkownika

**Klient (e-commerce / dropshipper):**
- *Przed:* Wkleja produkt z Aliexpress/Allegro i szuka fotografa, copywritera, grafika recznie — porownuje oferty godzinami, nie wie, kto jest wiarygodny, placi 20-30% prowizji platformie (Upwork/Fiverr). Brak escrow z etapami — albo placi z gory (Fiverr), albo negocjuje godzinami (Upwork). Nie ma integracji ze swoim sklepem — kazde zlecenie tworzy recznie.
- *Po DROPIFY:* Wkleja link do produktu → AI Listing Factory generuje gotowe zlecenie w 30 sek. → matching trwa <60 sek. → kontrakt z milestone'ami → escrow z auto-zwolnieniem → AI QA weryfikuje dostarczona prace → wyplata. Calosc z poziomu dashboardu, bez opuszczania platformy.

**Freelancer:**
- *Przed:* Szuka zlecen na Upwork/Fiverr, aplikuje razem z setkami innych (najlepsi sie nie zgłaszaja — passive matching). Prowizja 19-28%. Brak gwarancji platnosci. Czas do pierwszej odpowiedzi klienta: 2-4 dni.
- *Po DROPIFY:* Dostaje match od AI (proaktywny, nie musi szukac). odpowiada na 3-5 pytan (AI interview), klient decyduje w 10 minut. Prowizja 5-12% (zalezy od reputacji). Escrow z auto-zwolnieniem — gwarancja platnosci. Referral 2.0 — pasywny dochod z poleconych.

#### Rozwiazanie — Dlaczego teraz

1. **LLM APIs dostepne za grosze** — Claude API pozwala na pelna analize zlecen i matching za ~2 PLN/transakcja
2. **Boom dropshippingu w Polsce** — e-commerce 50 mld PLN/rok, rosnacy popyt na outsourcing
3. **Konkurencja fragmentaryczna** — Upwork/Fiverr drogie, nie maja integracji e-commerce, brak lokalnego rynku PL/EU
4. **Zero-budget MVP** — VPS 20 PLN/mies. + Claude API ~150 PLN/mies. = 190 PLN/mies. kosztow stalych

---

### 19.3 Product & Technology

#### Co robimy (dla nie-technicznego czytelnika)

DROPIFY to platforma, ktora laczy klientow z e-commerce z freelancerami i dostawcami uslug. Roznica wobec konkurencji: **kazdy etap transakcji odbywa sie automatycznie** — czlowiek musi tylko podjac decyzje strategiczne.

**Jak dziala (krok po kroku):**

1. **Klient tworzy zlecenie** — moze wpisac 1 zdanie (AI wygeneruje pelny opis) lub wklejac link do produktu (AI rozbije na komponenty uslug)
2. **AI analizuje zlecenie** — kategoria, umiejetnosci, pilnosc, uczciwa cena (fallback: reguly, gdy brak klucza API)
3. **AI znajduje najlepszych freelancerow** — embeddingi wektorowe (1536 wymiarow) + scoring: zgodnosc semantyczna (40%), ocena (25%), dopasowanie ceny (20%), dostepnosc (15%)
4. **Top 3 matche trafiaja do klienta** — kazdy z podsumowaniem AI (wynik interview, risk score, sugerowany czas realizacji)
5. **Freelancer akceptuje** → kontrakt z milestone'ami (AI proponuje podzial etapow)
6. **Escrow** — klient placi (Stripe Checkout lub tryb demo), srodki zablokowane do potwierdzenia realizacji
7. **Freelancer oddaje prace** → AI QA report (checklista wymagan, score 0-100)
8. **Klient zwalnia platnosc** (recznie lub auto po 48h) → wyplata
9. **Ocena** — obustronna, wplywa na scoring przyszlych matchy

#### Architektura techniczna

```
Frontend: Next.js 16 (Vercel, globalny CDN, PL/EN)
    ↓ HTTPS REST
Backend: FastAPI (VPS, Docker, 19 routerow API)
    ↓
PostgreSQL + pgvector (dane + embeddingi) | Redis + Celery (kolejka zadan)
    ↓
Claude API + OpenAI embeddings (fallback: reguly lokalne)
    ↓
n8n (self-hosted) → Telegram / Slack / Sheets / webhooki
```

**Kluczowe cechy technologiczne:**
- **Fallbacki AI** — kazda funkcja dziala bez kluczy API (reguly/heurystyki) = platforma dziala od 1. dnia bez kosztow AI
- **Inline execution** — gdy Redis nie dziala, zadania Celery execute inline = brak single point of failure
- **47 testow pytest** — zero infrastruktury do uruchomienia (SQLite), pelne pokrycie escrow/matching/auth
- **Stripe Checkout** — realne platnosci (nie demo) z weryfikacja podpisu webhooka

#### Co juz zbudowano

| Obszar | Status |
|--------|--------|
| Rdzen marketplace (zlecenie → match → kontrakt → escrow → ocena) | ~90% |
| Silnik AI matching (Celery, embeddingi, autopilot, raporty) | ~85% |
| Frontend (wszystkie sciezki klienta i freelancera) | ~90% |
| Automatyzacje n8n (5 gotowych workflow) | dzialajace szablony |
| Platnosci Stripe (Checkout + webhooks + refundacje) | dziala (dodane 19-20.08.2026) |
| 28 funkcji (20 + F1-F8) | 23 wdrozone, 5 czesciowych, 1 planowana |

> Zrodlo: pelny audyt kodu, §4 i §15 niniejszego handbooka.

---

### 19.4 Market Sizing (TAM/SAM/SOM)

> **UWAGA:** Ponizsze szacunki sa METODOLOGICZNE — podajemy sposob liczenia, NIE wymyslone liczby. Wszystkie wartosci wymagaja weryfikacji z zewnetrznych zródel danych.

#### Metodologia

| Metryka | Jak liczyc | Zrodlo danych | BRAK |
|---------|-----------|---------------|------|
| **TAM** (Total Addressable Market) | Liczba wszystkich transakcji B2B w kategoriach obslugiwanych przez DROPIFY (e-commerce, dropshipping, uslugi cyfrowe) x srednia wartosc transakcji x potencjalna prowizja 8% | GUS (e-commerce PL), Statista, raporty branżowe | WYMAGA RESEARCHU RYNKOWEGO |
| **SAM** (Serviceable Addressable Market) | Tylko segment PL/EU, w ktorym DROPIFY moze realnie dzialac (klienci mowiacy PL/EN/DE, korzystajacy z WooCommerce/Shopify/Allegro) | GUS, dane Shopify/WooCommerce, raporty e-commerce PL | WYMAGA RESEARCHU RYNKOWEGO |
| **SOM** (Serviceable Obtainable Market) | Czesc SAM, ktora mozna pozyskac w ciagu 12-24 mies. przy realistycznym budgetcie marketingowym i zespole 1-2 osob | Wewneczne zalozenia (CAC, konwersja, budzet) | WYMAGA UZUPEŁNIENIA PRZEZ ZAŁOŻYCIELA |

#### Przykladowa metodologia liczenia (do weryfikacji)

**TAM (orientacyjny framework):**
- E-commerce w Polsce: ~50 mld PLN/rok (GUS)
- Uslugi cyfrowe/freelance w Polsce: ~5 mld PLN/rok (szacunek)
- Potencjalne B2B transactions w kategoriach DROPIFY: BRAK DANYCH — wymaga researchu

**SAM (orientacyjny framework):**
- Uzytkownicy WooCommerce w PL: ~30-50 tys. sklepow (szacunek, wymaga weryfikacji)
- Uzytkownicy Shopify w PL: ~5-10 tys. sklepow (szacunek, wymaga weryfikacji)
- Aktywni freelancerzy w kategoriach DROPIFY w PL/EU: BRAK DANYCH

**SOM:**
> WYMAGA UZUPEŁNIENIA PRZEZ ZAŁOŻYCIELA — na podstawie budzetu marketingowego, CAC i realistycznej konwersji.

#### Uwaga dla inwestora

> Nie podajemy szacunkow TAM/SAM/SOM jako liczb, poniewaz:
> 1. Nie mamy dostepu do aktualnych danych rynkowych (GUS, Statista, raporty branżowe)
> 2. Nie chcemy fabrykowac liczb, ktore wygladaja wiarygodnie, ale sa wymyslone
> 3. Prawidlowa metodologia jest wazniejsza niz konkretne liczby — inwestor moze sam zweryfikowac
>
> **Rekomendacja:** przed prezentacja inwestorska przeprowadzic research rynkowy z wykorzystaniem: GUS (e-commerce PL), Shopify/WooCommerce partner dashboards, raporty E-commerce Polska, statystyki Upwork/Fiverr (dostepne publicznie).

### 19.5 Business Model

#### Strumienie przychodu (zweryfikowane z kodu)

| Strumien | Stawka | Status | Zrodlo |
|----------|--------|--------|--------|
| Prowizja transakcyjna | 5-12% (dynamicznie, zalezy od reputacji freelancera) | DZIALA | config.py, fees.py |
| Subskrypcje (Free/Starter 49/Pro 149/Enterprise 499+) |rozne stawki | CZESCIOWO WDROZONE | routes/plans.py |
| WooCommerce plugin | 49 PLN jednorazowo | CZESCIOWE (plugin gotowy, brak systemu platnosci) | integrations/woocommerce/ |
| Shopify App | 29 PLN/mies. | CZESCIOWE (routes/integrations.py, brak App Store) | routes/integrations.py |
| API / White-label | 500-2000 PLN/mies. | WDROZONE (API keys, partner endpoint) | routes/developer.py |

#### Unit Economics (zweryfikowane z kodu)

```
Srednia wartosc zlecenia:        800 PLN (ZAŁOŻENIE — placeholder do zweryfikowania)
Prowizja 8%:                     +64.00 PLN
Minus: platnosc Stripe (2.5%):   -1.60 PLN
Minus: AI (Claude):              -2.00 PLN
Minus: wsparcie:                 -3.00 PLN
= NETTO NA TRANSAKCJE:           57.40 PLN (≈71% marzy)
```

> Zrodlo: §8 niniejszego handbooka. Wartosci zweryfikowane z config.py i currency.py.

#### Prowizja dynamiczna (#8)

| Typ freelancera | Prowizja | Kryterium |
|-----------------|----------|-----------|
| Top-rated | 5% | rating >= 4.8, >= 20 ocen |
| Nowi | 12% | <= 3 oceny |
| Reszta | 8% | default |

Stawka zapisywana na kontrakcie (`Contract.fee_rate`), nie zmienia sie w trakcie realizacji.

#### Porownanie z konkurencja (prowizja)

| Platforma | Prowizja freelancera | Prowizja klienta | Laczny take rate |
|-----------|---------------------|-------------------|------------------|
| **DROPIFY** | **5-12%** | **0%** | **5-12%** |
| Upwork | 0-15% (fee per proposal) | ~5% | ~19-20% |
| Fiverr | 20% | 5.5% | 27.7% |
| Toptal | 0% (platform placi) | 30%+ | ~30%+ |

> Zrodlo: publiczne dane rynkowe (Upwork Spring 2026, Fiverr Go Q1 2026).

#### Scenariusze porownawcze

> ⚠️ Ponizsze wartosci to SCENARIUSZE/ZALOZENIA z Biznes_Plan (czerwiec 2026), nie prognoza dla inwestora. Podajemy je jako punkt porownawczy z jawnie oznaczonymi zalozeniami.

| Scenariusz | M6 przychod | M12 przychod | Zalozenia |
|------------|-------------|--------------|-----------|
| Conservative (itemized, §8) | ~2 100 PLN | ~11 500 PLN | 3-4 transakcje/mies. (breakeven) do 500 transakcji/mies. |
| Conservative (Biznes_Plan) | 9 600 PLN | 32 000 PLN | 150 transakcji/mies. (M6) do 500 (M12), wyzsza konwersja na subskrypcje |
| Aggressive (Biznes_Plan) | 51 200 PLN | 192 000 PLN | Viral growth, 800 transakcji (M6) do 3000 (M12) |

> Roznica miedzy itemized (§8) a Conservative (Biznes_Plan) wynika z zalozenia wyzszej konwersji na subskrypcje i wiecej transakcji. Obecny handbook uzywa wartosci itemized (~11 500 PLN M12) jako bezpieczniejszej prognozy.

---

### 19.6 Traction

> **Pre-launch / faza MVP** — brak jeszcze metryk produkcyjnych.

**Co juz dziala (zweryfikowane z kodu):**
- 23 funkcje wdrozone i przetestowane (47 testow pytest)
- 19 endpointow API (pelna referencja w §5)
- 15 modeli bazy danych
- Stripe Checkout z weryfikacja webhookow
- 5 gotowych workflow n8n (Telegram/Slack)
- WooCommerce plugin (PHP)
- System sporow + AI ocena
- Reset hasla + weryfikacja email
- White-label API (#F8)

**Czego brakuje do launcha:**
- ~~Regulamin + Polityka Prywatnosci (§14)~~ **WDROZONE** (23.08.2026)
- Rejestracja dzialalnosci + NIP/VAT (§14)
- Pierwszy prawdziwy klient (beta)
- Pierwsza kampania pozyskiwania uzytkownikow

> WYMAGA UZUPEŁNIENIA PRZEZ ZAŁOŻYCIELA — daty milestone'ow, status beta-testow, feedback od uzytkownikow, jakiekolwiek realne metryki.

---

### 19.7 Go-to-Market

#### Phase 0: MVP Launch (M1-M2)

**Cel:** 10 placacych klientow, 20+ waitlist, NPS > 40.

**Kanalwy:**
- **Landing page** + Typeform do waitlist
- **SEO**: frazy "dropshipping matching", "freelance matching Poland"
- **Outreach**: DM na 50+ grup FB (dropshipping, e-commerce, freelance PL)
- **Oferta**: FREE tier + 3 mies. PRO gratis (normalnie 149 PLN/mies.)

**Dzialania operacyjne:**
- Seed 3-5 freelancerow recznie (fotografia, design, marketing)
- Force pierwsze 5 transakcji recznie jesli trzeba
- Tygodniowy feedback call z beta-userami

#### Phase 1: Traction (M3-M6)

**Cel:** 50+ aktywnych uzytkownikow, 200 transakcji/mies.

**Kanalwy:**
- WooCommerce plugin MVP (cel: 100 instalacji)
- Case studies: 3-5 historii sukcesu
- Blog 2x/tydzien (SEO hacking)
- YouTube: 1-2 min demo, unboxing, ROI stories

**Dzialania operacyjne:**
- Iteracja na podstawie feedbacku (co tydzien)
- Dodanie premium tiers
- API documentation + partnerski program

#### Phase 2: Scale (M7-M12)

**Cel:** 200+ aktywnych uzytkownikow, 1000+ transakcji/mies.

**Kanalwy:**
- Shopify App na App Store
- Partnerships: reseller programy z agencjami
- Affiliate program (20% commission)
- Paid ads: 500-1000 PLN/mies.

**Dzialania operacyjne:**
- Allegro integration (#11)
- Mobile-responsive UI
- Rozszerzenie na 2-3 nisze (foto, marketing, e-commerce)

> Zrodlo: Biznes_Plan_DROPIFY_Zero_Budget.docx — scenariusz oryginalny, niezweryfikowany z obecnym kodem. Zalozenia wymagaja weryfikacji.

---

### 19.8 Competitive Landscape

#### Pozycjonowanie DROPIFY

| Cecha | DROPIFY | Upwork | Fiverr | Toptal |
|-------|---------|--------|--------|--------|
| **Prowizja** | 5-12% (dynamiczna) | 19-20% | 27.7% | 30%+ |
| **Matching** | Proaktywny (AI sam znajduje) | Passive (klikasz apply) | Passive (gigs) | Passive (rekrutacja) |
| **Automatyzacja** | End-to-end (matching → wyplata) | Czesciowa (Uma AI) | Minimalna | Reczna |
| **Lokalny fokus** | PL/EU (jezyk, waluty, VAT) | Globalny (EN主导) | Globalny (EN主导) | Globalny (EN主导) |
| **Integracje e-commerce** | WooCommerce, Shopify, Allegro | Brak | Brak | Brak |
| **Escrow z etapami** | Tak (milestones + auto-release) | Tak (godziny/work diary) | Nie (z gory) | Tak (enterprise) |
| **AI QA (weryfikacja dostawy)** | Tak (deliverable checker) | Nie | Nie | Nie |
| **Contract generator** | Tak (AI, PL/EN) | Czesciowy (Uma) | Nie | Tak (reczny) |
| **White-label API** | Tak (#F8) | Nie | Nie | Nie |

#### Kluczowe przewagi konkurencyjne

1. **Prowizja 8% flat vs 19-28%** — bezposrednia oszczednosc dla klienta i freelancera. Przy zleceniu 1000 PLN: DROPIFY 80 PLN vs Upwork ~190 PLN vs Fiverr ~277 PLN.

2. **Matching proaktywny** — AI sam znajduje najlepszych freelancerow (nie czeka na aplikacje). Wedlug danych Upwork, "najlepsi sie nie zgłaszaja" — DROPIFY rozwiązuje ten problem.

3. **Local-first PL/EU** — konkurencja jest globalna (EN主导). DROPIFY startuje z polskim rynkiem, rosnac do EU. Lokalne waluty (PLN/EUR/UAH), lokalne podatki (VAT/reverse-charge), lokalne integracje (Allegro, BaseLinker).

4. **E-commerce native** — WooCommerce/Shopify/Allegro pod dropshipping. Nikt z konkurencji nie oferuje pelnej integracji e-commerce w jednym produkcie.

5. **Automatyzacja end-to-end** — od zlecenia do wyplaty: AI matching → kontrakt → escrow → QA → wyplata. Konkurencja wymaga recznych krokow na kazdym etapie.

#### Slabe strony (honest assessment)

- **Brak uzytkownikow** — platforma jest w fazie MVP, brak dowodu na product-market fit
- **Malу zespól** — 1 osoba, ograniczenia w skali
- **Brak finansowania** — zero-budget, co ogranicza marketing i szybkosc rozwoju
- **Wtyczki sklepowe** — WooCommerce czesciowy, Shopify/Allegro niegotowe do App Store

### 19.9 Model Wrazliwosci — CAC/LTV Symulator

> ⚠️ **MODEL SYMULACYJNY** — wszystkie wartosci wejsciowe to ZALOZENIA do przetestowania, nie zweryfikowane dane. Pokazuje mechanike jednostki ekonomicznej, nie prognoze finansowa.

#### Zmienne wejściowe

| Zmienna | Wartosc | Status | Zrodlo |
|---------|---------|--------|--------|
| Prowizja srednia | 8% | **ZNANE** | config.py (PLATFORM_FEE_RATE = 0.08) |
| Koszt operacyjny/transakcje | 6.60 PLN | **ZNANE** | §8: platnosc (2.5% = 2.00 PLN z 800) + AI (2.00 PLN) + wsparcie (3.00 PLN) minus korekta za zmienna cene |
| Srednia wartosc zlecenia | 800 PLN | **ZALOZENIE** | placeholder do zweryfikowania |
| CAC (Customer Acquisition Cost) | 50-500 PLN | **ZALOZENIE** | zakres testowy |
| Czestotliwosc transakcji/klient/mies. | 1-5 | **ZALOZENIE** | zakres testowy |
| Retencja (miesiace) | 3-12 | **ZALOZENIE** | zakres testowy |

> **Co to jest CAC:** koszt pozyskania jednego klienta (marketing + outreach + onboarding + koszt pierwszej transakcji). Bez tego nie wiadomo, ile moznaloby wydac na reklame przy obecnej marzy.

> **Co to jest LTV:** wartosc klienta w calym cyklu zycia (ile transakcji x ile prowizji netto przez czas korzystania z platformy). LTV:CAC ratio okresla, czy model sie oplaca.

> **Co to jest Retencja:** jak dlugo sredni klient zostaje na platformie (w miesiacach). Im dluzej, tym wiecej transakcji i wyzszy LTV.

#### Kalkulacja LTV

```
Marza netto/transakcje = Prowizja srednia x Srednia wartosc zlecenia - Koszt operacyjny
                       = 8% x 800 PLN - 6.60 PLN
                       = 64.00 PLN - 6.60 PLN
                       = 57.40 PLN

LTV = Marza netto x Czestotliwosc x Retencja
    = 57.40 PLN x Trans./mies. x Retencja (mies.)

LTV:CAC = LTV / CAC
```

#### 3 Scenariusze symulacyjne

> ⚇ Ponizsze wartosci to WYNIKI SYMULACJI na podstawie powyzszych zmiennych. Nie sa prognoza — sa pokazaniem mechaniki. Kazda wartosc wejsciowa moze byc zmieniona.

| Scenariusz | CAC | Trans./mies | Retencja | LTV | LTV:CAC | Ocena |
|-----------|-----|-------------|----------|-----|---------|-------|
| **Pesymistyczny** | 300 PLN | 1 | 3 mies. | 172 PLN | 0.57x | NIEOPŁACALNE — kazdy klient generuje stratę |
| **Bazowy** | 150 PLN | 2 | 6 mies. | 689 PLN | 4.6x | ZDROWE — powyzej progu 3x |
| **Optymistyczny** | 80 PLN | 3 | 9 mies. | 1 550 PLN | 19.4x | BARDZO DOBRE — silna jednostka ekonomiczna |

#### Wrazliwosc na CAC (przy stalych: 2 trans./mies, 6 mies. retencji)

| CAC | LTV | LTV:CAC | Ocena |
|-----|-----|---------|-------|
| 50 PLN | 689 PLN | 13.8x | BARDZO DOBRE |
| 100 PLN | 689 PLN | 6.9x | DOBRE |
| 150 PLN | 689 PLN | 4.6x | ZDROWE |
| 200 PLN | 689 PLN | 3.4x | NA GRANICY |
| 230 PLN | 689 PLN | 3.0x | PROG OPŁACALNOSCI |
| 300 PLN | 689 PLN | 2.3x | NIEOPŁACALNE |
| 500 PLN | 689 PLN | 1.4x | NIEOPŁACALNE |

#### Prog opłacalnosci

Standard branżowy dla SaaS/marketplace to **LTV:CAC >= 3x** jako granica opłacalnosci. Powyzej 3x model sie oplaca; ponizej — kazdy nowy klient generuje stratę.

Dla DROPIFY (przy zalozeniach bazowych 2 trans./mies, 6 mies. retencji):
- **Max CAC = 230 PLN** — powyzej tego progu model staje sie nieopłacalny
- **Komfortowy CAC = 100-150 PLN** — daje bufor bezpieczenstwa

#### Uwaga metodologiczna

> Realne wartosci beda znane po zebraniu danych z pierwszych kampanii i faktycznej bazy klientow. Model sluzy do:
> (a) pokazania ze rozumiemy mechanike jednostkowa,
> (b) wyznaczenia celow operacyjnych do zweryfikowania,
> (c) identyfikacji kluczowych zmiennych (CAC, czestotliwosc, retencja) — ktore musza byc zmierzone.
>
> **NIE sluzy do:** prognozowania przychodow, obiecowania zwrotow, ani jako baza do wyceny.

### 19.10 Risks & Mitigations

> Rozwiazanie tabeli z §17 z dodaniem wplywu na inwestycje.

| Ryzyko | Prawdopodobienstwo | Wplyw | Mitigacja | Status |
|--------|-------------------|-------|-----------|--------|
| **Brak product-market fit** | SREDNIE | KRYTYCZNY | Wczesne petle feedbacku (co tydzien), iteracja na MVP, beta z 10+ uzytkownikami przed skala | W toku |
| **Konkurencja obniza prowizje** | SREDNIE | WYSOKI | AI matching jako moat (trudny do skopiowania), integracje e-commerce (nikt tego nie ma), lokalny fokus PL/EU | Czesciowo |
| **Koszty AI eksploduja** | NISKIE | SREDNI | Cache wynikow, batch processing, lokalny fallback (reguly) gdy brak API, monitorowanie kosztow | Zaimplementowane |
| **Chicken-egg problem** | WYSOKIE | WYSOKI | Start z 1 niszy (fotografia/dropshipping), reczne seedowanie obu stron, FREE tier M1-M3 | Planowane |
| **VPS pada / utrata danych** | NISKIE | WYSOKI | Automatyczne backupy dzienne (cron 03:00), redundancja od M6+ | Zaimplementowane |
| **Regulacje prawne (RODO)** | SREDNIE | SREDNI | ~~Regulamin + Polityka Prywatnosci przed launchem (§14)~~ **WDROZONE** (23.08.2026); klauzule RODO w formularzach | CZESC_CIOWO WDROZONE |
| **Brak pozyskiwania uzytkownikow** | SREDNIE | KRYTYCZNY | Cold outreach 50+ grup FB, darmowy premium M1-M3, SEO + content, affiliate 20% | Planowane |
| **Zaleznosc od Claude API** | NISKIE | SREDNI | Lokalny fallback (reguly/heurystyki), mozliwosc zamiany na inny LLM | Zaimplementowane |
| **Brak zespolu** | WYSOKIE | WYSOKI | Automatyzacja end-to-end (self-working), priorytetyzacja, potencjalny wspolnik/wspolzalozyciel | DO ROZWAZENIA |

### 19.11 Team

> **WYMAGA UZUPEŁNIENIA PRZEZ ZAŁOŻYCIELA**

Potencjalne sekcje do wypelnienia:

**Zalozyciel / CEO:**
- Kim jestes? (imie, tlo zawodowe, doswiadczenie)
- Dlaczego Ty? (unikalne kompetencje, znajdosc rynku, doswiadczenie w e-commerce/freelance)
- Ile czasu poświęcasz na projekt? (full-time / part-time)
- Czy masz wczesniejsze exit / startupy / relevannte projekty?

**Zespol (jesli istnieje):**
- Wspolzalozyciel? (kompetencje, rola, equity)
- Developerzy? (backend/frontend/AI)
- Advisory board? (branżowi eksperci)

**Kluczowe kompetencje w zespole:**
- AI/ML (Claude API, embeddingi, matching)
- Full-stack development (FastAPI, Next.js, PostgreSQL)
- E-commerce / dropshipping (znajdosc rynku, klientow)
- Marketing / growth (SEO, content, paid ads)

> **Uwaga dla inwestora:** Dla projektu seed-stage w fazie MVP, zalozyciel-technik (1 osobowy zespol) to standardowa konfiguracja. Kluczowe pytanie: czy zalozyciel ma doswiadczenie w pozyskiwaniu uzytkownikow (growth), nie tylko w budowaniu produktu.

### 19.12 Financial Ask & Use of Funds

> **WYMAGA UZUPEŁNIENIA PRZEZ ZAŁOŻYCIELA**

Potencjalne sekcje do wypelnienia:

**Ask:**
- Ile kapitalu potrzebujesz? (kwota w PLN/EUR/USD)
- Jaki % equity oferujesz? (lub instrument: SAFE, konvertible note)
- Na jaki okres wystarczy ten kapital? (np. 12-18 mies.)

**Use of Funds (przykladowa struktura):**

| Kategoria | Kwota | Uzasadnienie |
|-----------|-------|--------------|
| Marketing / pozyskiwanie uzytkownikow | ?% | Budżet na kampanie (FB Ads, Google Ads, content) |
| Hosting / infrastruktura | ?% | VPS, domain, potential bigger server |
| Narzedzia / API | ?% | Claude API, Stripe fees, email (SendGrid) |
| Prawne / regulacje | ?% | ~~Regulamin, Polityka Prywatnosci~~ WDROZONE; rejestracja dzialalnosci, NIP/VAT (~500 PLN) |
| Rezerwa | ?% | Na nieprzewidziane koszty |

**Milestones zwiazane z inwestycja:**

| Milestone | Horyzont | Zaleznosci |
|-----------|----------|------------|
| Launch (pierwsi klienci) | M1-M2 | Regulamin + NIP + landing page |
| 50 aktywnych uzytkownikow | M3-M6 | Budżet marketingowy, WooCommerce plugin |
| 200+ transakcji/mies. | M6-M12 | Scale marketingu, Allegro integration |
| Rentownosc (revenue > costs) | M6-M12 | Zalezy od CAC i czestotliwosci transakcji |

> **Uwaga dla inwestora:** Aktualne koszty stałe platformy to ~190 PLN/mies. (VPS 20 + Claude API 150 + domena 5). Przy marzy 57.4 PLN/transakcja, breakeven to 3-4 transakcje/mies. Glownym kosztem skali bedzie marketing (CAC) i potencjalnie wiekszy zespol.

---

## Podsumowanie pakietu inwestorskiego

**Co mamy:**
- Dzialajaca platforme (23 funkcje wdrozone, 47 testow, realne platnosci Stripe)
- Niski koszt operacyjny (190 PLN/mies.)
- Wyrazny moat (AI matching proaktywny, integracje e-commerce, lokalny fokus PL/EU)
- 5 strumieni przychodu (prowizja 5-12%, subskrypcje, pluginy, API)

**Czego brakuje:**
- Regulamin + Polityka Prywatnosci (§14)
- Rejestracja dzialalnosci + NIP/VAT (§14)
- Pierwsi prawdziwi klienci (beta)
- Metryki trakcji (CAC, LTV, konwersja, retencja)
- Zespol / wspolzalozyciel
- Finansowanie na marketing

**Najwazniejsze liczby do zweryfikowania przed prezentacja inwestorska:**
1. CAC — ile kosztuje pozyskanie jednego klienta?
2. LTV — ile transakcji robi sredni klient i jak dlugo zostaje?
3. TAM/SAM/SOM — jaki jest realny rozmiar rynku?
4. Konwersja — ile % matchy konczy sie kontraktem?

> **Zasada nadrzednia:** Lepiej powiedziec "nie wiemy, ale oto jak to zmierzymy" niz podac wymyslona liczbe. Inwestorzy cenia szczerosc i founder-friendly mindset wiecej niz zawyzone prognozy.


---

**MIT License** — używaj swobodnie do celów komercyjnych i prywatnych.
