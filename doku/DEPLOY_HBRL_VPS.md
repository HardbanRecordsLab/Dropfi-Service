# DROPIFY — wdrożenie na VPS HBRL (`84.247.162.167`)

Konkretna procedura dla tego serwera. Ogólna checklista: `LAUNCH_CHECKLIST.md`.
Zasady serwera: `HBRL-VPS/VPS-HANDBOOK.md`, `HBRL-VPS/DB-POLICY.md` (poza tym repo — poufne).

> `$PGPW` w komendach = hasło master roli `hbrl_admin` z `DB-POLICY.md`.
> Ustaw je w sesji przed startem: `export PGPW='...'` — **nie wpisuj na stałe do plików w repo.**

## Topologia

| Warstwa | Gdzie |
|---|---|
| Frontend | Vercel → `dropify.hardbanrecordslab.online` (CNAME, Cloudflare **DNS only**) |
| API | VPS, kontener `dropify-api` na `127.0.0.1:8770`, host nginx → `api.dropify.hardbanrecordslab.online` (A → `84.247.162.167`, Cloudflare **DNS only**) |
| Baza | **centralny `hbrl-postgres`**, baza `dropify`, user `hbrl_admin` (sieć docker `hbrl-db`) — bez pgvector, działa Python fallback |
| Redis / Celery | własny kontener `dropify-redis` (wewn. sieć compose) |
| n8n | **istniejący** host n8n (`auto.hardbanrecordslab.online`) — DROPIFY tylko wysyła webhooki |
| Kod | `/opt/stacks/dropify` (git, branch `main`) |
| Compose | `docker-compose.prod.yml` (bez `db`/`nginx`/`n8n`) |

## Kroki

```bash
ssh -i ~/.ssh/vps_key root@84.247.162.167

# 1. Backup baz przed zmianą
/root/vps-scripts/db-backup-all.sh

# 2. Baza dropify w centralnym Postgresie
docker exec -e PGPASSWORD=$PGPW hbrl-postgres \
  psql -U hbrl_admin -d postgres -c "CREATE DATABASE dropify OWNER hbrl_admin;"

# 3. Kod
git clone https://github.com/<owner>/<repo> /opt/stacks/dropify
cd /opt/stacks/dropify && git checkout main

# 4. Sekrety
cp backend/.env.example backend/.env
#   DATABASE_URL=postgresql://hbrl_admin:$PGPW@hbrl-postgres:5432/dropify
#   REDIS_URL=redis://:<REDIS_PASSWORD>@redis:6379/0   (to samo hasło co REDIS_PASSWORD)
#   SECRET_KEY, ADMIN_PASSWORD, REDIS_PASSWORD, FLOWER_PASSWORD  → wygenerowane
#   OPENROUTER_API_KEY=<klucz od właściciela>
#   FRONTEND_URL=https://dropify.hardbanrecordslab.online
#   CORS_ORIGINS_EXTRA=https://dropify.hardbanrecordslab.online
#   N8N_WEBHOOK_URL=http://host.docker.internal:5678/webhook   (host n8n; extra_hosts w compose)
#   STRIPE_* — puste (tryb demo, dodane na końcu)
chmod 600 backend/.env

# 5. Start
docker compose -f docker-compose.prod.yml up -d --build
#   api uruchamia `alembic upgrade head` przy starcie
docker compose -f docker-compose.prod.yml logs -f api | head -60
curl -s http://127.0.0.1:8770/api/health

# 6. nginx vhost (host)
#   plik: /etc/nginx/sites-available/api.dropify.hardbanrecordslab.online.conf  (patrz niżej)
ln -s /etc/nginx/sites-available/api.dropify.hardbanrecordslab.online.conf \
      /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 7. Cert
certbot certonly --webroot -w /var/www/certbot \
  -d api.dropify.hardbanrecordslab.online --non-interactive --agree-tos \
  -m hardbanrecordslab.pl@gmail.com
#   → odkomentuj blok listen 443 w vhost, nginx -t && systemctl reload nginx

# 8. Backup bazy dropify — dopisz do /root/vps-scripts/db-backup-all.sh listy baz

# 9. Smoke test — patrz LAUNCH_CHECKLIST.md §8
```

## nginx vhost — `/etc/nginx/sites-available/api.dropify.hardbanrecordslab.online.conf`

```nginx
server {
    listen 80;
    server_name api.dropify.hardbanrecordslab.online;
    location /.well-known/acme-challenge/ { root /var/www/certbot; try_files $uri =404; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl http2;
    server_name api.dropify.hardbanrecordslab.online;

    ssl_certificate     /etc/letsencrypt/live/api.dropify.hardbanrecordslab.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.dropify.hardbanrecordslab.online/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 25M;

    # Swagger/docs stay private on prod
    location ~ ^/(docs|redoc|openapi.json)$ { return 404; }

    location / {
        proxy_pass http://127.0.0.1:8770;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

CORS jest robione w aplikacji (FastAPI `CORSMiddleware`, `CORS_ORIGINS_EXTRA`) — nie w nginx.

## Frontend → Vercel

1. Vercel → **Add New… → Project** → import `HardbanRecordsLab/Dropfi-Service`
   (Framework: Next.js — wykryje sam; Root Directory: `./`).
2. **Environment Variables** (Production + Preview):
   - `NEXT_PUBLIC_API_URL` = `https://api.dropify.hardbanrecordslab.online/api`
   - `NEXT_PUBLIC_SITE_URL` = `https://dropify.hardbanrecordslab.online`
3. **Deploy**.
4. Project → **Settings → Domains** → dodaj `dropify.hardbanrecordslab.online`.
   Vercel poda cel CNAME (`cname.vercel-dns.com`). W Cloudflare dodaj:
   `CNAME  dropify  cname.vercel-dns.com`  — **Proxy status: DNS only (szara chmurka)**.
5. Po propagacji DNS Vercel sam wystawi TLS. Sprawdź `https://dropify.hardbanrecordslab.online`.

> CORS: backend już ma `CORS_ORIGINS_EXTRA=https://dropify.hardbanrecordslab.online`
> w `backend/.env`. Jeśli zmienisz domenę frontu — zaktualizuj tam i `docker compose ... up -d`.

## Stan wdrożenia (2026-09-07)

| Element | Status |
|---|---|
| Baza `dropify` w `hbrl-postgres` | ✅ utworzona, 22 tabele (Alembic `0001_baseline`) |
| Kontenery `dropify-{api,worker,beat,flower,redis}` | ✅ up (api healthy) |
| `https://api.dropify.hardbanrecordslab.online/api/health` | ✅ `status: ok` (db+redis ok) |
| `/docs` na produkcji | ✅ 404 |
| Cert `api.dropify...` | ✅ Let's Encrypt, do 2026-12-06, auto-renew |
| Portal Radar | ✅ 9 źródeł działa (346 leadów + 127 profili w 1. skanie); `useme`/`justjoinit` sparkowane |
| AI matching E2E | ✅ zlecenie → match score 0.85 (Python fallback, bez pgvector) |
| Celery async | ✅ `.delay()` z api kolejkuje → worker przetwarza (job create 0.5 s zamiast 4.5 s) |
| Beat scheduler | ✅ `portal-radar-scan` co 6 h + pozostałe zadania |
| `dropify` w backupie DB | ✅ dopisane do `db-backup-all.sh` |
| OpenRouter | ⏳ `OPENROUTER_API_KEY` puste → tryb reguł; wklej klucz do `backend/.env` + `docker compose ... up -d api` |
| Stripe | ⏳ tryb demo; klucze live na końcu |
| Frontend Vercel | ⏳ do zrobienia wg sekcji wyżej |

## Aktualizacja po deployu

```bash
cd /opt/stacks/dropify && git pull
docker compose -f docker-compose.prod.yml up -d --build
# migracje lecą automatycznie (api CMD: alembic upgrade head)
```

## Rollback

```bash
cd /opt/stacks/dropify && git checkout <poprzedni-tag>
docker compose -f docker-compose.prod.yml up -d --build
# jeśli migracja wymaga cofnięcia: docker compose ... exec api alembic downgrade -1
```
