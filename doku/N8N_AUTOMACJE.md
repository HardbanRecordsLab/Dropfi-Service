# 🤖 DROPIFY × n8n — AUTOMATYCZNE WORKFLOWY

**n8n** to self-hostowany silnik automatyzacji (alternatywa dla Zapiera/Make, ale u Ciebie na VPS, bez opłat za workflow). DROPIFY jest zintegrowany z n8n **dwukierunkowo**:

```
DROPIFY API ──(eventy)──▶ n8n webhooki ──▶ Telegram / Slack / Sheets / AI / email…
n8n ──(POST /api/n8n/trigger)──▶ DROPIFY (tworzenie zleceń, powiadomienia)
```

---

## 1. Instalacja (już skonfigurowana w docker-compose)

Usługa `n8n` jest dodana do `docker-compose.yml` (port **5678** tylko na localhost, dane w wolumenie `n8n_data`):

```bash
docker compose up -d n8n
# n8n UI (przez SSH tunnel): ssh -L 5678:127.0.0.1:5678 root@YOUR_VPS_IP
# → otwórz http://localhost:5678
```

**Zmienne środowiskowe** (w pliku `.env` przy docker-compose):

| Zmienna | Do czego |
|---|---|
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | szablony powiadomień Telegram |
| `SLACK_WEBHOOK_URL` | szablon powiadomień Slack |
| `DROPIFY_API_URL` | adres API dla workflow wejściowych (`http://api:8000/api` w dockerze) |
| `DROPIFY_N8N_KEY` | klucz = `N8N_INBOUND_KEY` z `backend/.env` |

**Konfiguracja backendu** (`backend/.env`):
```
N8N_WEBHOOK_URL=http://n8n:5678/webhook
N8N_WEBHOOK_SECRET=<losowy długi string>
N8N_INBOUND_KEY=<losowy klucz API>
```
Zmień wartości — te z `.env.example` są tylko przykładowe!

---

## 2. Eventy wysyłane przez DROPIFY → n8n

Platforma automatycznie wysyła **HMAC-podpisane** eventy (header `X-Dropify-Signature: sha256=...`) na webhooki:
`<N8N_WEBHOOK_URL>/dropify-<event>`:

| Event | Kiedy | Payload (data) |
|---|---|---|
| `dropify-job-created` | nowe zlecenie | job_id, title, budget, deadline, category, location, client_id |
| `dropify-match-created` | AI znalazł wykonawcę | job_id, job_title, freelancer_id, freelancer_name, score, fallback |
| `dropify-contract-created` | akceptacja matcha | contract_id, job_id, job_title, client_id, freelancer_id, amount, platform_fee, fee_rate |
| `dropify-job-completed` | zakończenie zlecenia | job_id, title, budget, completed_by |
| `dropify-payment-created` | płatność kontraktu | payment_id, contract_id, amount, platform_fee, net_amount |
| `dropify-referral-commission` | prowizja referral | level, amount, referrer_id, referred_id, contract_id |
| `dropify-daily-report` | codziennie 07:00 | jobs, matches, accepted, contracts, completed, revenue, new_users, errors, commissions, anomalies, insights |

Struktura każdego eventu:
```json
{
  "event": "dropify-job-created",
  "timestamp": "2026-08-19T06:00:00+00:00",
  "data": { "...": "payload z tabeli" }
}
```

---

## 3. Import szablonów workflow (folder `n8n-workflows/`)

W n8n UI: **Workflows → ⋮ → Import from File** → wybierz szablon. Potem **Activate**.

| Plik | Co robi | Wymagane zmienne |
|---|---|---|
| `dropify-01-job-created-telegram.json` | nowe zlecenie → powiadomienie Telegram | TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID |
| `dropify-02-match-created-slack.json` | nowy AI match → Slack | SLACK_WEBHOOK_URL |
| `dropify-03-contract-completed-telegram.json` | zakończone zlecenie → Telegram | TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID |
| `dropify-04-daily-report-telegram.json` | dzienny raport (metryki + anomalie + AI) → Telegram | TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID |
| `dropify-05-inbound-job-create.json` | **n8n → DROPIFY**: webhook zewnętrzny (formularz/CRM) → tworzy zlecenie + AI matching | DROPIFY_API_URL, DROPIFY_N8N_KEY |

**Weryfikacja podpisu w n8n (opcjonalnie, zalecane):**
Webhook node → **Verify Header** → `X-Dropify-Signature` → wklej `N8N_WEBHOOK_SECRET`.

---

## 4. Endpoint wejściowy (n8n → DROPIFY)

`POST /api/n8n/trigger` — wymaga nagłówka `X-Dropify-Api-Key: <N8N_INBOUND_KEY>`.

Dostępne akcje:
```json
// 1. Powiadomienie użytkownika
{ "action": "notify", "email": "user@example.com", "title": "Hi", "body": "...", "type": "info" }

// 2. Utworzenie zlecenia (klient musi istnieć) + automatyczny AI matching
{
  "action": "job.create",
  "client_email": "client@example.com",
  "title": "10 banerów social media",
  "description": "Opis zlecenia...",
  "budget": 800,
  "deadline": "2026-09-30",
  "location": "Zdalnie",
  "category": "Design",
  "required_skills": ["graphic design"]
}
```

---

## 5. Pomysły na automatyzacje (rozbudowa szablonów)

- **Google Sheets**: każdy kontrakt → wiersz w arkuszu (węzeł Google Sheets)
- **AI follow-up**: po `dropify-match-created` → węzeł Claude/OpenAI generuje spersonalizowaną wiadomość do freelancera → `notify`
- **Lead capture**: Google Form "Zamów zlecenie" → `job.create` (szablon 05)
- **Alerty anomalii**: w `dropify-04` dodaj węzeł IF: wyślij tylko gdy `data.anomalies.length > 0`
- **Powtórne powiadomienia**: niezaakceptowany match po 24h → n8n Schedule trigger → `GET /api/matches/job/{id}` → Telegram przypomnienie
- **Eksport danych**: codzienny backup statystyk do Airtable/Notion przez `dropify-daily-report`

## 6. Bezpieczeństwo

- n8n słucha tylko na `127.0.0.1:5678` — nie jest publiczny; dostępu użyczasz przez SSH tunnel
- Eventy wychodzące są podpisane HMAC (`N8N_WEBHOOK_SECRET`) — n8n może weryfikować
- Endpoint wejściowy wymaga `X-Dropify-Api-Key` (testy: bez klucza → 403)
- Koszt: 0 zł — n8n działa na tym samym VPS co backend
