# DROPIFY — Checklista wdrożenia produkcyjnego (go‑live)

**Wersja:** 2026‑09‑07 · Zakłada: VPS + domena + klucze API gotowe.
Powiązane: `DROPIFY_SERVICE_FULL_HANDBOOK.md` §2 i §10, `doku/30_DNI_LAUNCH_CHECKLIST.txt`.

---

## 0. Stan przed wdrożeniem

- [ ] `cd backend && python -m pytest -q` → **52 passed**
- [ ] `npx tsc --noEmit` → bez błędów
- [ ] `npm run build` → bez błędów
- [ ] `npx eslint .` → bez błędów
- [ ] Gałąź scalona do `main`, CI (`.github/workflows/ci.yml`) zielone

## 1. Zmienne środowiskowe — `backend/.env` na VPS

Skopiuj `backend/.env.example` → `backend/.env` i ustaw **realne** wartości.
Przy `DEBUG=False` aplikacja **nie wystartuje** z domyślnym `SECRET_KEY` / `ADMIN_PASSWORD` (guard w `config.py`).

| Zmienna | Uwaga |
|---|---|
| `SECRET_KEY` | min. 32 znaki, losowe (`openssl rand -hex 32`) |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | realne — pierwszy admin tworzony przy starcie |
| `DATABASE_URL` | Postgres produkcyjny (świeża baza — patrz §3) |
| `REDIS_URL` + `REDIS_PASSWORD` | to samo hasło w obu |
| `FLOWER_USER` / `FLOWER_PASSWORD` | basic‑auth do monitoringu Celery |
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | produkcyjne (bez nich działają fallbacki) |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` | **klucze LIVE** |
| `FRONTEND_URL` | `https://<domena>` (redirecty Stripe Checkout) |
| `SMTP_HOST/PORT/USER/PASSWORD`, `SENDER_EMAIL` | realne SMTP (reset hasła, powiadomienia, weryfikacja e‑mail) |
| `CORS_ORIGINS` | `["https://<domena>","https://<projekt>.vercel.app"]` |
| `N8N_WEBHOOK_URL`, `N8N_WEBHOOK_SECRET`, `N8N_INBOUND_KEY` | jeśli używasz n8n |
| `PLATFORM_NIP`, `PLATFORM_VAT_EU`, `PLATFORM_ADDRESS`, `PLATFORM_NAME` | wymagane do realnych faktur za prowizję |
| `PLATFORM_FEE_RATE` i pochodne | domyślnie 8% / 5% / 12% |
| `RADAR_ENABLED=True` | Portal Radar skanuje co `RADAR_SCAN_INTERVAL_HOURS` (domyślnie 6 h) |
| `ADZUNA_APP_ID/KEY`, `USAJOBS_API_KEY/EMAIL`, `GITHUB_TOKEN` | opcjonalne — włączają dodatkowe konektory Radaru |
| `SEED_DEMO_DATA=False` | na produkcji **False** |

## 2. Backend na VPS

```bash
ssh root@VPS_IP
apt update && apt install -y docker.io docker-compose-v2 certbot
git clone <repo> /opt/dropify && cd /opt/dropify
git checkout main
cp backend/.env.example backend/.env && nano backend/.env    # §1
docker compose up -d --build
curl -s http://localhost:8000/api/health        # {"status":"ok", ...}
```

## 3. Baza danych (brak migracji Alembic)

`init_db()` woła `create_all()` — **tworzy brakujące tabele, nie zmienia istniejących**.

- **Świeży deploy:** nic nie rób — wszystkie tabele powstaną razem.
- **Istniejąca baza z wcześniejszej wersji:** ręcznie dołóż kolumny dodane po
  jej utworzeniu, m.in.:
  - `users`: `rodo_consent`, `rodo_consent_at`, `nip`
  - `jobs`: `external_source`, `external_url`
  - nowe tabele: `invoices`, `badges`, `external_listings`, `external_talent`, `radar_scan_logs`
  ```sql
  ALTER TABLE users ADD COLUMN IF NOT EXISTS rodo_consent boolean DEFAULT false;
  ALTER TABLE users ADD COLUMN IF NOT EXISTS rodo_consent_at timestamptz;
  ALTER TABLE users ADD COLUMN IF NOT EXISTS nip varchar(20);
  ALTER TABLE jobs  ADD COLUMN IF NOT EXISTS external_source varchar(50);
  ALTER TABLE jobs  ADD COLUMN IF NOT EXISTS external_url text;
  ```
  (nowe tabele `create_all()` dołoży samo przy restarcie API)

## 4. Domena + SSL

```bash
# DNS: A‑record  api.<domena>  →  VPS_IP   (oraz <domena> → Vercel wg ich instrukcji)
certbot certonly --standalone -d api.<domena>
sed -i 's/dropify\.app/<domena>/g' nginx.conf     # sprawdź ręcznie po podmianie
docker compose restart nginx
curl -s https://api.<domena>/api/health
```
- [ ] `https://api.<domena>/docs` → **404** (nginx ukrywa docs na produkcji)
- [ ] Port `5555` (Flower) i `5678` (n8n) **niedostępne z zewnątrz** (tylko 127.0.0.1)

## 5. Stripe (tryb live)

- [ ] Dashboard Stripe → Developers → Webhooks → **Add endpoint**:
      `https://api.<domena>/api/webhooks/stripe`
- [ ] Zdarzenia: `checkout.session.completed`, `charge.refunded` (min.)
- [ ] Skopiuj **Signing secret** → `STRIPE_WEBHOOK_SECRET` w `.env`, `docker compose up -d`
- [ ] Test: mały realny płatny milestone → sprawdź `payments` + zwolnienie escrow

## 6. Frontend → Vercel

- [ ] Import repo, branch `main`
- [ ] Env: `NEXT_PUBLIC_API_URL=https://api.<domena>/api`
- [ ] Deploy, otwórz `https://<domena>` → przełącznik PL/EN działa

## 7. Automatyzacje

- [ ] n8n: `bash n8n-workflows/setup.sh` (po starcie kontenera) — import 5 workflowów, aktywacja
- [ ] Cron backupu bazy: `crontab -e` →
      `0 3 * * * bash /opt/dropify/backend/scripts/backup.sh`
- [ ] Celery beat żyje: `docker compose logs -f beat` — widać `daily-summary`,
      `portal-radar-scan`, `auto-release-milestones`

## 8. Smoke‑test produkcyjny (E2E)

1. [ ] `GET /api/health` → `status: ok`
2. [ ] Rejestracja klienta (checkbox RODO wymagany) → e‑mail weryfikacyjny dochodzi
3. [ ] Rejestracja freelancera + uzupełnienie profilu (bio/skills)
4. [ ] Klient tworzy zlecenie → w ciągu ~30 s pojawiają się matche
5. [ ] Freelancer akceptuje match → powstaje kontrakt + milestones
6. [ ] Stripe Checkout (karta testowa lub mała realna kwota) → płatność zapisana
7. [ ] Klient zwalnia milestone → środki „released", rating dostępny
8. [ ] Admin: `/admin` → statystyki, lista sporów, faktura z kontraktu
9. [ ] `/dashboard/radar` → zakładka Źródła → **Skanuj wszystkie** → po chwili
       w „Zlecenia" pojawiają się leady → **Importuj** tworzy zlecenie + matche

## 9. Po starcie

- [ ] Zmień hasło admina z panelu / przez API
- [ ] Ustaw alerty (Sentry `SENTRY_DSN`, jeśli używasz)
- [ ] Zapisz `backend/.env` w menedżerze sekretów (poza repo)
- [ ] Zaplanuj przegląd bezpieczeństwa: `/security-review` na świeżym diffie
