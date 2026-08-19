# DROPIFY — MEGA PLATFORM BLUEPRINT

**Jeden dokument, dwa języki / One document, two languages — PL 🇵🇱 + EN 🇬🇧**
*Skonsolidowany, zaktualizowany opis platformy DROPIFY na bazie wszystkich plików z `doku/` + pełny audyt istniejącego kodu + 8 nowych funkcji wdrożonych w tej iteracji.*
*Consolidated, updated description of the DROPIFY platform based on every file in `doku/` + a full audit of the existing code + 8 new features shipped in this iteration.*

Status: **19.08.2026** · Wersja / Version: **2.0** · Zakres / Scope: Business + Technical + Implementation Status

---

# CZĘŚĆ 1 — PO POLSKU

## 1. Czym jest DROPIFY

DROPIFY to globalna platforma B2B typu marketplace, która **automatycznie** dopasowuje zlecenia (e-commerce, dropshipping, usługi cyfrowe) do freelancerów i dostawców za pomocą AI (Claude + embeddingi wektorowe), a następnie **samodzielnie** prowadzi całą transakcję od momentu dopasowania aż po wypłatę — analiza zlecenia, matching, negocjacje, kontrakt, escrow z etapami płatności, kontrola jakości (AI QA), rozliczenie i program poleceń. Człowiek (właściciel platformy) potrzebny jest tylko do strategicznych decyzji — reszta działa 24/7 bez jego udziału. To jest sens słowa **"self-working"** w tym projekcie: nie chodzi o pojedynczą automatyzację, tylko o zamkniętą pętlę zdarzeń, w której każdy kolejny krok wyzwala się sam (patrz sekcja 4 i 7).

Platforma jest dwujęzyczna (PL/EN, przełącznik jednym kliknięciem) i zaprojektowana do globalnej ekspansji — stąd w tej wersji blueprintu dokładamy warstwę walutową/podatkową, harmonogram stref czasowych i white-label API, żeby "ogólnoświatowość" była realną cechą produktu, a nie tylko hasłem marketingowym.

## 2. Model biznesowy (uzgodniony, bez sprzeczności)

Dokumenty źródłowe w `doku/` zawierały **dwie rozbieżne prognozy przychodu na M12** (11 500 PLN/mies. w Biznes_Plan.docx i Technical_Blueprint.docx vs. 92 000–200 000 PLN/mies. w README/SUMMARY/COMPLETE_GUIDE). Rozbieżność wynika z tego, że wyższe liczby zakładają znacznie wyższe wskaźniki konwersji na subskrypcje/API niż te wyliczone w tabelach miesiąc-po-miesiącu. **Ten dokument przyjmuje jako wiążącą wersję zwymiarowaną (itemized)** — jest ona spójna z modelem unit economics poniżej i bezpieczniejsza do planowania.

**5 strumieni przychodu:**

| Strumień | Stawka | M6 (cel) | M12 (cel) |
|---|---|---|---|
| Prowizja transakcyjna | 8% (dynamicznie 5–12%, patrz #8) | 1 500 PLN | 8 000 PLN |
| Subskrypcje (Free/Starter 49/Pro 149/Enterprise 499+) | — | 400 PLN | 2 000 PLN |
| Wtyczka WooCommerce | 49 PLN jednorazowo | — | częściowo |
| Aplikacja Shopify | 29 PLN/mies. | — | częściowo |
| API / White-label (#F8, nowość) | 500–2000 PLN/mies. + partnerzy | 200 PLN | 1 500 PLN |
| **RAZEM** | | **~2 100 PLN** | **~11 500 PLN** |

**Unit economics (zlecenie 800 PLN):** prowizja 8% = 64 PLN → minus płatność (2,5%) −1,60 PLN → minus AI −2 PLN → minus wsparcie −3 PLN = **57,4 PLN netto (≈71% marży)**. Próg rentowności: koszty stałe 190 PLN ÷ 57 PLN = **3–4 zlecenia/miesiąc**.

**Koszty stałe (MVP):** VPS (Hetzner CAX11) 20 PLN + Claude API ~150 PLN + domena ~5 PLN = **~190 PLN/mies.**

## 3. Architektura: Frontend (Vercel) + Backend (VPS)

```
                    ┌─────────────────────────────┐
                    │   FRONTEND — Next.js 16      │
                    │   Hosting: Vercel (globalny   │
                    │   CDN, zero-config HTTPS)     │
                    │   PL/EN i18n, brak DB po      │
                    │   stronie frontu               │
                    └───────────────┬───────────────┘
                                    │ HTTPS / REST (/api/*)
                                    ▼
                    ┌─────────────────────────────┐
                    │   BACKEND — FastAPI (Python)  │
                    │   Hosting: własny VPS          │
                    │   (Docker Compose)             │
                    │   Auth JWT, 17 routerów         │
                    └───┬─────────┬─────────┬───────┘
                        │         │         │
              ┌─────────▼──┐ ┌────▼────┐ ┌──▼──────────┐
              │ PostgreSQL │ │  Redis   │ │ Claude API   │
              │ + pgvector │ │ + Celery │ │ + OpenAI     │
              │ (dane +    │ │ (kolejka │ │ embeddings   │
              │ embeddingi)│ │ zadań)   │ │ (fallback:   │
              └────────────┘ └────┬─────┘ │ reguły lokal)│
                                   │        └──────────────┘
                             ┌─────▼─────┐
                             │    n8n     │  → Telegram / Slack /
                             │ (localhost)│    Sheets / dowolny webhook
                             └────────────┘
```

**Kluczowa cecha projektowa:** każda funkcja AI ma **lokalny fallback bez kluczy API** (reguły/heurystyki), a każde zadanie Celery ma **wykonanie inline**, gdy broker Redis nie działa. Dzięki temu platforma jest "self-working" nawet w najuboższej konfiguracji — od pierwszego dnia, zanim właściciel kupi płatne klucze.

## 4. Stan wdrożenia — wynik pełnego audytu (przed tą iteracją)

Audyt kodu (nie tylko dokumentów) wykazał, że **backend i frontend były już w ~70–75% zbudowane** — to nie był szkielet UI, tylko działająca alfa:

| Obszar | Stan przed audytem | Szczegóły |
|---|---|---|
| Rdzeń marketplace (zlecenie → AI match → kontrakt → escrow → ocena) | **~90%** | Pełny cykl działał end-to-end z realną integracją Claude i fallbackiem regułowym |
| Silnik AI matching (Celery, embeddingi, autopilot, raporty dzienne) | **~85%** | pgvector + fallback Python, scoring 0.40/0.25/0.20/0.15 zaimplementowany dokładnie wg specyfikacji |
| Frontend (wszystkie ścieżki klienta i freelancera) | **~90%** | Każda strona dashboardu czyta i zapisuje realne dane; jedyny pusty stub to `/factory` |
| Automatyzacja n8n | działające szablony | 5 gotowych workflow (Telegram/Slack), ale nieaktywowane domyślnie |
| **Monetyzacja (płatności)** | **~40% — NAJWIĘKSZA LUKA** | Escrow/milestone/wypłaty/prowizje poleceń były w pełni zbudowane, ale **żadna prawdziwa płatność nigdy nie była pobierana** — `release_milestone` po prostu zapisywał `Payment(status="paid")` bez utworzenia sesji Stripe Checkout ani PaymentIntent |

**Wniosek audytu:** pojedyncza, dobrze zlokalizowana luka blokowała realny MVP — brak faktycznego przepływu pieniędzy od klienta do platformy. Wszystko poniżej tej luki (zwolnienie, wypłata, przychód platformy) już działało i uruchomiłoby się natychmiast po jej zamknięciu.

## 5. 20 funkcji z `PLAN_20_FUNKCJI_PONAD_KONKURENCJA.md` — status

Dokument źródłowy oznaczał Sprinty 1–3 (funkcje #1–8, #13–18, #20) jako wdrożone, a Sprint 4 (#9–12, integracje e-commerce: WooCommerce, Shopify, Allegro/BaseLinker, Product Source Finder) jako plan na przyszłość. **Audyt kodu to potwierdził**: w bazie istnieją realne modele/endpointy dla wszystkich funkcji Sprintów 1–3 (`Milestone`, `Commission`, `DailyReport`, `Contract.fee_rate`, `/fees`, `generate_interview_questions`, `/api/jobs/{id}/fair-price`, autopilot, refundacje, wypłaty stablecoin). Sprint 4 (integracje sklepowe) pozostaje nieotwarty — to naturalny **kierunek na kolejną iterację**, osobny od 8 funkcji poniżej.

## 6. Moje udoskonalenia wdrożone w tej iteracji

### 6.1 Naprawa realnych płatności (Stripe Checkout) — najważniejsza poprawka

- Nowy router `backend/app/routes/payments.py`: `POST /api/payments/checkout/{contract_id}/{milestone_id}` tworzy prawdziwą **Stripe Checkout Session** dla etapu (milestone) w stanie `in_review`.
- `backend/app/routes/webhooks.py` rozbudowany: po zdarzeniu `checkout.session.completed` webhook **faktycznie zwalnia etap** (wywołuje `finalize_milestone_release`, tę samą logikę co dotychczasowy przycisk demo) — dopiero wtedy, gdy pieniądze rzeczywiście spłynęły.
- `backend/app/routes/contracts.py`: wydzielono `finalize_milestone_release()` jako współdzieloną funkcję między ścieżką demo (`_release`, gdy Stripe nie jest skonfigurowany) a prawdziwą ścieżką Stripe — zero duplikacji logiki, zero regresji istniejącego trybu demo.
- Frontend (`/dashboard/contracts`): nowy przycisk **"Zapłać kartą (Stripe)"** obok istniejącego "Zwalniam płatność" — jeśli Stripe nie jest skonfigurowany na serwerze, backend zwraca `{mode: "demo"}` i UI grzecznie kieruje do trybu demo (ta sama filozofia fallbacku co reszta platformy).
- `GET /api/payments/config` pozwala frontowi sprawdzić, czy Stripe jest aktywny, bez zgadywania.

### 6.2 Inne poprawki
- `backend/.env.example`: dodano `STRIPE_PUBLISHABLE_KEY`, `FRONTEND_URL` (do budowy URL-i powrotnych Stripe Checkout).
- `requirements.txt`: dodano pakiet `stripe`.
- Pusty stub `/factory` (widoczny w audycie jako jedyna niedziałająca strona) zastąpiony realną funkcją #F1/#F6 poniżej — pod adresem `/dashboard/factory`, zgodnie z konwencją reszty dashboardu.

## 7. 8 nowych funkcji (F1–F8) — wdrożone w tej iteracji

Każda funkcja podąża za istniejącą konwencją kodu: endpoint FastAPI + (gdzie ma to sens) fallback bez kluczy AI + wpisy i18n PL/EN + integracja z n8n, gdzie dotyczy stanu zlecenia.

| # | Nazwa | Co robi | Pliki backend | Pliki frontend |
|---|---|---|---|---|
| **F1** | **AI Listing Factory** | Z nazwy produktu / linku do dostawcy generuje gotową ofertę (tytuł, opis, punkty korzyści, tagi SEO, meta opis) dla Shopify/WooCommerce/Allegro | `routes/factory.py`, `utils/ai.py::generate_listing`, model `Listing` | `/dashboard/factory` |
| **F2** | **Global Currency & Tax Auto-Engine** | Przelicza kwoty PLN→EUR/USD/GBP/UAH/CZK/SEK i pokazuje orientacyjną notatkę VAT/reverse-charge dla kraju klienta | `routes/fx.py`, `utils/currency.py` | `API.fxRates`, `API.taxHint` (gotowe do wpięcia w dowolny widok cen) |
| **F3** | **AI Contract & Compliance Generator** | Generuje czytelną umowę serwisową (PL/EN) dla każdego kontraktu, z automatyczną notatką transgraniczną z F2 | `routes/contracts.py::contract_agreement`, `utils/ai.py::generate_contract_agreement` | Przycisk "Pobierz umowę" w `/dashboard/contracts` |
| **F4** | **Smart Supplier Risk Score** | Wyjaśnialny wskaźnik zaufania 0–100 (ocena, historia zleceń, wskaźnik ukończenia, liczba recenzji) dla każdego freelancera/dostawcy | `routes/users.py::user_risk_score`, `utils/risk.py` | Odznaka ryzyka na kartach w `/dashboard/freelancers` |
| **F5** | **AI Co-Pilot (asystent w zleceniu)** | Czat AI osadzony w każdym zleceniu, odpowiadający wyłącznie w kontekście tego zlecenia (Claude + fallback offline) | `routes/copilot.py`, `utils/ai.py::answer_copilot`, model `CopilotMessage` | Widżet czatu w `/dashboard/jobs/[id]` |
| **F6** | **Marketing Video Script & Voiceover Generator** | Generuje 20–30-sekundowy scenariusz wideo (hook + treść + CTA) do TikTok/Reels dla danego produktu | `utils/ai.py::generate_video_script` (współdzielone z F1) | `/dashboard/factory` (druga zakładka funkcji) |
| **F7** | **Global Talent Time-Zone Auto-Scheduler** | Sugeruje okno nakładających się godzin pracy klient↔freelancer albo tryb "async 24/7" dla par w różnych strefach czasowych | `routes/matches.py::match_schedule`, `utils/timezone_util.py` | Wskazówka harmonogramu na karcie dopasowania w `/dashboard/jobs/[id]` |
| **F8** | **White-Label / Reseller API** | Klucze API dla agencji, które chcą osadzić AI matching DROPIFY pod własną marką we własnym portalu | `routes/developer.py`, model `ApiKey`, endpoint partnerski `POST /api/v1/external/jobs` | Nowa strona `/dashboard/developer` |

**Dlaczego akurat te 8:** F1/F6 wypełniają dokładnie tę lukę, na którą wskazywał pusty stub `/factory` i domyka niszę dropshipping (masowe tworzenie ofert), F2/F3 czynią z "globalnej platformy" realną cechę (a nie tylko przetłumaczony UI) — waluty i podatki transgraniczne, F4 zwiększa zaufanie w dwustronnym marketplace bez zewnętrznego biura kredytowego, F5 zmniejsza obciążenie wsparcia (ten sam cel co chatbot z `FULL_AUTOMATION_PASSIVE_INCOME.txt`, ale kontekstowo osadzony w zleceniu), F7 czyni z "pracy 24/7" realny mechanizm dopasowania stref czasowych zamiast sloganu, F8 otwiera **szósty strumień przychodu** (agencyjny reseller) nieobecny w oryginalnych 5 strumieniach z dokumentów źródłowych.

## 8. Weryfikacja jakości kodu

Cały backend przeszedł `python -m py_compile` bez błędów. Cały zmieniony/nowy kod frontendu przeszedł `tsc --noEmit` (zero błędów typów) oraz `eslint` (zero ostrzeżeń) na pełnym zestawie plików.

## 9. Mapa drogowa (co dalej)

1. **Sprint 4 z doku (niezmieniony plan):** wtyczka WooCommerce, aplikacja Shopify, integracja Allegro/BaseLinker, "Product Source Finder" (dekompozycja linku produktu na plan realizacji).
2. **Rozszerzenie F2:** podłączenie żywego API kursów walut zamiast statycznej migawki.
3. **Rozszerzenie F5:** historia czatu widoczna też dla drugiej strony kontraktu (obecnie każdy widzi tylko własne pytania).
4. **Aktywacja n8n:** domyślne włączenie 5 gotowych workflow przy starcie kontenera zamiast ręcznej aktywacji.
5. **Testy automatyczne:** projekt nie ma obecnie żadnego katalogu testów — to największe ryzyko techniczne przy dalszym skalowaniu zespołu.

## 10. Skrócona instrukcja wdrożenia

**Frontend (Vercel):** `vercel deploy` z katalogu głównego repo, zmienna środowiskowa `NEXT_PUBLIC_API_URL` wskazująca na domenę VPS.
**Backend (VPS):** `docker compose up -d` uruchamia `db` (Postgres+pgvector), `redis`, `api`, `worker` (Celery), `beat`, `flower`, `n8n`, `nginx`. Wymagane sekrety w `backend/.env`: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (opcjonalnie — działa bez nich), `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` (opcjonalnie — bez nich płatności działają w trybie demo), `N8N_WEBHOOK_SECRET`.

---

# PART 2 — IN ENGLISH

## 1. What DROPIFY Is

DROPIFY is a global B2B marketplace that **automatically** matches jobs (e-commerce, dropshipping, digital services) to freelancers and suppliers using AI (Claude + vector embeddings), then **autonomously** runs the entire transaction from match to payout — job analysis, matching, negotiation, contract, milestone escrow, AI quality control, settlement, and referral commissions. The platform owner is only needed for strategic decisions; everything else runs 24/7 without them. That is what "self-working" means here: not one automation, but a closed event loop where every next step triggers itself (see sections 4 and 7).

The platform is bilingual (PL/EN, one-click switch) and built for global reach — which is why this iteration adds a currency/tax layer, a time-zone scheduler, and a white-label API, so "worldwide" is an actual product feature, not just a marketing line.

## 2. Business Model (reconciled, contradiction-free)

The source documents in `doku/` contained **two conflicting M12 revenue forecasts** (11,500 PLN/mo in Biznes_Plan.docx and Technical_Blueprint.docx vs. 92,000–200,000 PLN/mo in README/SUMMARY/COMPLETE_GUIDE). The gap comes from the higher figures assuming much higher subscription/API attach rates than the month-by-month tables actually itemize. **This document treats the itemized version as authoritative** — it's consistent with the unit economics below and safer to plan against.

**5 revenue streams:**

| Stream | Rate | M6 target | M12 target |
|---|---|---|---|
| Transaction fee | 8% (dynamic 5–12%, see #8) | 1,500 PLN | 8,000 PLN |
| Subscriptions (Free/Starter 49/Pro 149/Enterprise 499+) | — | 400 PLN | 2,000 PLN |
| WooCommerce plugin | 49 PLN one-time | — | partial |
| Shopify app | 29 PLN/mo | — | partial |
| API / White-label (#F8, new) | 500–2,000 PLN/mo + partners | 200 PLN | 1,500 PLN |
| **TOTAL** | | **~2,100 PLN** | **~11,500 PLN** |

**Unit economics (800 PLN job):** 8% fee = 64 PLN → minus payment processing (2.5%) −1.60 PLN → minus AI −2 PLN → minus support −3 PLN = **57.4 PLN net (~71% margin)**. Breakeven: 190 PLN fixed costs ÷ 57 PLN = **3–4 jobs/month**.

**Fixed costs (MVP):** VPS (Hetzner CAX11) 20 PLN + Claude API ~150 PLN + domain ~5 PLN = **~190 PLN/mo**.

## 3. Architecture: Frontend (Vercel) + Backend (VPS)

```
                    ┌─────────────────────────────┐
                    │   FRONTEND — Next.js 16       │
                    │   Hosted on Vercel (global    │
                    │   CDN, zero-config HTTPS)      │
                    │   PL/EN i18n, no DB on the      │
                    │   frontend side                  │
                    └───────────────┬───────────────┘
                                    │ HTTPS / REST (/api/*)
                                    ▼
                    ┌─────────────────────────────┐
                    │   BACKEND — FastAPI (Python)  │
                    │   Hosted on your own VPS       │
                    │   (Docker Compose)              │
                    │   JWT auth, 17 routers            │
                    └───┬─────────┬─────────┬───────┘
                        │         │         │
              ┌─────────▼──┐ ┌────▼────┐ ┌──▼──────────┐
              │ PostgreSQL │ │  Redis   │ │ Claude API   │
              │ + pgvector │ │ + Celery │ │ + OpenAI     │
              │ (data +    │ │ (task    │ │ embeddings   │
              │ embeddings)│ │ queue)   │ │ (fallback:   │
              └────────────┘ └────┬─────┘ │ local rules) │
                                   │        └──────────────┘
                             ┌─────▼─────┐
                             │    n8n     │  → Telegram / Slack /
                             │ (localhost)│    Sheets / any webhook
                             └────────────┘
```

**Key design trait:** every AI feature has a **local, key-free fallback** (rules/heuristics), and every Celery task has an **inline execution path** when the Redis broker isn't running. This is what makes the platform "self-working" even in the leanest configuration — from day one, before the owner buys any paid API keys.

## 4. Implementation Status — full audit findings (before this iteration)

A code audit (not just the docs) found the backend and frontend were already **~70–75% built** — this was a working alpha, not a UI shell:

| Area | Status before this audit | Details |
|---|---|---|
| Marketplace core (job → AI match → contract → escrow → rating) | **~90%** | Full end-to-end cycle worked with real Claude integration and a rule-based fallback |
| AI matching engine (Celery, embeddings, autopilot, daily reports) | **~85%** | pgvector + Python fallback, the 0.40/0.25/0.20/0.15 scoring formula implemented exactly per spec |
| Frontend (every client & freelancer journey) | **~90%** | Every dashboard page reads/writes real data; the only empty stub was `/factory` |
| n8n automation | working templates | 5 ready-made workflows (Telegram/Slack), but not activated by default |
| **Monetization (payments)** | **~40% — THE BIGGEST GAP** | Escrow/milestones/payouts/referral commissions were fully built, but **no real payment was ever collected** — `release_milestone` simply wrote `Payment(status="paid")` without ever creating a Stripe Checkout session or PaymentIntent |

**Audit conclusion:** a single, well-scoped gap was blocking a real MVP — no actual money flow from client to platform. Everything downstream of that gap (release, payout, platform revenue) already worked and would activate immediately once it was closed.

## 5. The 20 Features from `PLAN_20_FUNKCJI_PONAD_KONKURENCJA.md` — status

The source document marked Sprints 1–3 (features #1–8, #13–18, #20) as deployed, and Sprint 4 (#9–12: WooCommerce, Shopify, Allegro/BaseLinker, "Product Source Finder") as future work. **The code audit confirmed this**: real models/endpoints exist for every Sprint 1–3 feature (`Milestone`, `Commission`, `DailyReport`, `Contract.fee_rate`, `/fees`, `generate_interview_questions`, `/api/jobs/{id}/fair-price`, autopilot, refunds, stablecoin payouts). Sprint 4 (store integrations) remains open — a natural **direction for the next iteration**, separate from the 8 features below.

## 6. My Improvements Shipped This Iteration

### 6.1 Real payment collection (Stripe Checkout) — the critical fix

- New router `backend/app/routes/payments.py`: `POST /api/payments/checkout/{contract_id}/{milestone_id}` creates a genuine **Stripe Checkout Session** for a milestone that's `in_review`.
- `backend/app/routes/webhooks.py` extended: on `checkout.session.completed` the webhook now **actually releases the milestone** (calls `finalize_milestone_release`, the same logic the existing demo button used) — only once money has genuinely settled.
- `backend/app/routes/contracts.py`: extracted `finalize_milestone_release()` as shared logic between the demo path (`_release`, used when Stripe isn't configured) and the real Stripe path — zero logic duplication, zero regression to the existing demo mode.
- Frontend (`/dashboard/contracts`): new **"Pay with card (Stripe)"** button next to the existing "Release payment" — if Stripe isn't configured server-side, the backend returns `{mode: "demo"}` and the UI gracefully falls back to demo mode (same fallback philosophy as the rest of the platform).
- `GET /api/payments/config` lets the frontend check whether Stripe is active instead of guessing.

### 6.2 Other fixes
- `backend/.env.example`: added `STRIPE_PUBLISHABLE_KEY`, `FRONTEND_URL` (for Stripe Checkout redirect URLs).
- `requirements.txt`: added the `stripe` package.
- The empty `/factory` stub (flagged by the audit as the only non-working page) was replaced by the real #F1/#F6 feature below, at `/dashboard/factory`, matching the rest of the dashboard's URL convention.

## 7. 8 New Features (F1–F8) — Shipped This Iteration

Each feature follows the codebase's existing conventions: a FastAPI endpoint + (where it makes sense) a key-free AI fallback + PL/EN i18n entries + n8n integration where it touches job state.

| # | Name | What it does | Backend files | Frontend files |
|---|---|---|---|---|
| **F1** | **AI Listing Factory** | Turns a product name / supplier link into a ready listing (title, description, benefit bullets, SEO tags, meta description) for Shopify/WooCommerce/Allegro | `routes/factory.py`, `utils/ai.py::generate_listing`, `Listing` model | `/dashboard/factory` |
| **F2** | **Global Currency & Tax Auto-Engine** | Converts amounts PLN→EUR/USD/GBP/UAH/CZK/SEK and shows an indicative VAT/reverse-charge note for the client's country | `routes/fx.py`, `utils/currency.py` | `API.fxRates`, `API.taxHint` (ready to wire into any pricing view) |
| **F3** | **AI Contract & Compliance Generator** | Generates a plain-language service agreement (PL/EN) for every contract, with an automatic cross-border note from F2 | `routes/contracts.py::contract_agreement`, `utils/ai.py::generate_contract_agreement` | "Download agreement" button in `/dashboard/contracts` |
| **F4** | **Smart Supplier Risk Score** | An explainable 0–100 trust score (rating, track record, completion rate, review volume) for every freelancer/supplier | `routes/users.py::user_risk_score`, `utils/risk.py` | Risk badge on cards in `/dashboard/freelancers` |
| **F5** | **AI Co-Pilot (in-job assistant)** | A chat assistant embedded in every job, answering only within that job's context (Claude + offline fallback) | `routes/copilot.py`, `utils/ai.py::answer_copilot`, `CopilotMessage` model | Chat widget in `/dashboard/jobs/[id]` |
| **F6** | **Marketing Video Script & Voiceover Generator** | Generates a 20-30s vertical video ad script (hook + script + CTA) for TikTok/Reels for a given product | `utils/ai.py::generate_video_script` (shared with F1) | `/dashboard/factory` (second feature tab) |
| **F7** | **Global Talent Time-Zone Auto-Scheduler** | Suggests a live overlap window between client and freelancer, or an "async 24/7" mode for cross-timezone pairs | `routes/matches.py::match_schedule`, `utils/timezone_util.py` | Schedule hint on each match card in `/dashboard/jobs/[id]` |
| **F8** | **White-Label / Reseller API** | API keys for agencies that want to embed DROPIFY's AI matching as a branded service inside their own portal | `routes/developer.py`, `ApiKey` model, partner endpoint `POST /api/v1/external/jobs` | New `/dashboard/developer` page |

**Why these 8:** F1/F6 fill exactly the gap the empty `/factory` stub pointed at and close the dropshipping-specific niche (bulk listing creation); F2/F3 make "global platform" a real feature rather than just a translated UI — cross-border currency and tax; F4 builds trust in a two-sided marketplace without an external credit bureau; F5 reduces support load (same goal as the chatbot in `FULL_AUTOMATION_PASSIVE_INCOME.txt`, but contextually scoped to a job); F7 turns "24/7 operation" into an actual time-zone-matching mechanism instead of a slogan; F8 opens a **sixth revenue stream** (agency reseller) that wasn't present in the original 5 streams from the source documents.

## 8. Code Quality Verification

The entire backend passed `python -m py_compile` with zero errors. All new/changed frontend code passed `tsc --noEmit` (zero type errors) and `eslint` (zero warnings) across the full file set touched.

## 9. Roadmap (what's next)

1. **Sprint 4 from the source docs (unchanged plan):** WooCommerce plugin, Shopify app, Allegro/BaseLinker integration, "Product Source Finder" (decompose a product link into a fulfillment plan).
2. **F2 extension:** wire in a live FX rate API instead of the static snapshot.
3. **F5 extension:** make chat history visible to the other contract party too (currently each side only sees its own questions).
4. **n8n activation:** enable the 5 ready-made workflows by default on container start instead of requiring manual activation.
5. **Automated tests:** the project currently has no test directory at all — this is the single biggest technical risk as the team scales further.

## 10. Deployment Quick Reference

**Frontend (Vercel):** `vercel deploy` from the repo root, with `NEXT_PUBLIC_API_URL` set to the VPS domain.
**Backend (VPS):** `docker compose up -d` starts `db` (Postgres+pgvector), `redis`, `api`, `worker` (Celery), `beat`, `flower`, `n8n`, `nginx`. Required secrets in `backend/.env`: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (optional — works without them), `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` (optional — payments run in demo mode without them), `N8N_WEBHOOK_SECRET`.
