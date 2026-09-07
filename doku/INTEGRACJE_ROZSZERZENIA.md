# DROPIFY — Roadmapa integracji i rozszerzeń

**Wersja:** 2026‑09‑07
Priorytety właściciela: **portale freelance globalne**, **portale PL**, **komunikacja / płatności / AI**.

Legenda nakładu: **S** ≈ 1 dzień · **M** ≈ 2–5 dni · **L** ≈ >1 tydzień lub zależne od zewnętrznej akceptacji.
„Strona": **popyt** = źródło zleceń (zleceniodawcy), **podaż** = źródło wykonawców (zleceniobiorcy).

---

## 0. Co już działa (baza pod rozszerzenia)

| Element | Gdzie |
|---|---|
| **Portal Radar** — skan portali przez oficjalne API/RSS | `backend/app/connectors/`, `routes/radar.py`, `tasks/radar.py`, `/dashboard/radar` |
| WooCommerce (wtyczka) | `integrations/woocommerce/` → White‑Label API |
| Shopify (Custom App token) | `routes/integrations.py` |
| BaseLinker (+ Allegro, WooCommerce, Shopify) | `routes/integrations.py` |
| n8n — eventy wychodzące + `POST /api/n8n/trigger` | `utils/n8n.py`, `routes/n8n.py`, `n8n-workflows/` |
| White‑label / Reseller API (klucze partnerskie) | `routes/developer.py` |
| Kursy walut na żywo (Frankfurter) | `utils/currency.py` |

---

## 1. Portale freelance — globalne

Nowy konektor = plik w `backend/app/connectors/` + wpis w `registry.ALL_CONNECTORS`.
Klasa `Connector` (`base.py`): ustaw `slug/name/kind/region`, nadpisz `fetch_listings` i/lub `fetch_talent`.

| Portal | Dostęp | Legalność | Strona | Nakład | Wartość | Uwagi wdrożeniowe |
|---|---|---|---|---|---|---|
| Remotive | publiczne JSON API | OK (API publiczne) | popyt | ✅ zrobione | średnia | `connectors/remotive.py` |
| RemoteOK | publiczne JSON API | OK (wymaga User‑Agent) | popyt | ✅ zrobione | średnia | może chwilowo blokować boty |
| Arbeitnow | publiczne JSON API (EU) | OK (oferowane do agregacji) | popyt | ✅ zrobione | wysoka (EU) | `connectors/arbeitnow.py` |
| Jobicy | publiczne JSON API | OK | popyt | ✅ zrobione | średnia | remote, globalne |
| We Work Remotely | RSS | OK (publiczny RSS) | popyt | ✅ zrobione | wysoka | `remote-jobs.rss` |
| HN „Who is hiring" | Algolia HN API | OK (publiczne) | popyt | ✅ zrobione | wysoka (kontakty!) | co miesiąc świeży wątek |
| Adzuna | REST API (darmowy klucz) | OK (ToS API) | popyt | ✅ konektor gotowy | wysoka (20+ krajów, w tym PL) | ustaw `ADZUNA_APP_ID/KEY` |
| USAJOBS | REST API (darmowy klucz) | OK | popyt | ✅ konektor gotowy | niska‑średnia (rząd US) | ustaw `USAJOBS_API_KEY/EMAIL` |
| **Upwork** | oficjalne API + OAuth2 | tylko po akceptacji wniosku dev | popyt+podaż | **L** | bardzo wysoka | wniosek o dostęp do Upwork API; GraphQL; limit rate |
| **Freelancer.com** | oficjalne API (klucz) | OK w ramach API ToS | popyt+podaż | **M** | wysoka | `/api/projects/0.1/projects/active`, paginacja |
| **Fiverr** | brak publicznego API zleceń | tylko program afiliacyjny | podaż (pośrednio) | **L** | niska | realnie: tylko linki afiliacyjne, nie dane |
| PeoplePerHour | brak oficjalnego API | ToS zabrania scrapowania | popyt | **L** | średnia | pominąć do czasu partnerstwa |
| Guru.com | RSS kategorii (ograniczony) | do weryfikacji per feed | popyt | **M** | średnia | sprawdzić aktualność feedów |
| Malt (FR/DE/ES) | brak publicznego API | ToS restrykcyjny | podaż | **L** | wysoka (EU) | tylko kontakt partnerski |
| Workana (LATAM/ES) | brak oficjalnego API | ToS | popyt | **L** | średnia | rynek hiszpańskojęzyczny |
| Twago / Freelancermap (DE) | RSS ofert | zależnie od feedu | popyt | **M** | wysoka (DACH) | dobre uzupełnienie rynku niemieckiego |
| Contra | brak API | ToS | podaż | **L** | średnia | — |
| Wellfound (AngelList) | API po kluczu | OK w ramach ToS | popyt | **M** | wysoka (startupy) | wymaga rejestracji |

**Rekomendacja kolejności:** Adzuna (klucz) → Freelancer.com API → Twago/Freelancermap RSS → wniosek do Upwup API (długi lead time, zacząć wcześnie).

**Talent (podaż) — źródła legalne przez API:**

| Źródło | Dostęp | Nakład | Uwagi |
|---|---|---|---|
| GitHub Search API | publiczne (token podnosi limit) | ✅ zrobione | `connectors/github.py`, `GITHUB_TOKEN` |
| Stack Overflow (Stack Exchange API) | publiczne | ✅ zrobione | top‑answerers wg tagów |
| dev.to API | publiczne | ✅ zrobione | autorzy wg tagów |
| Behance API | wymaga klucza Adobe | **M** | portfolio graficzne/foto — bardzo trafne dla e‑commerce |
| Dribbble API | OAuth | **M** | jw. |
| Polywork / Read.cv | brak stabilnego API | **L** | — |

---

## 2. Portale PL

| Portal | Dostęp | Legalność | Strona | Nakład | Uwagi |
|---|---|---|---|---|---|
| Useme | RSS zleceń (`/pl/rss/jobs/`) | OK (publiczny RSS) | popyt | ✅ konektor gotowy | `connectors/useme.py` — zweryfikować feed po wdrożeniu |
| Just Join IT | publiczne JSON API v2 | OK (API publiczne) | popyt | ✅ konektor gotowy | `connectors/justjoinit.py`, nagłówek `version: 2` |
| NoFluffJobs | publiczne API postings | OK (używane przez ich front) | popyt | **S** | `POST /api/search/posting` — dołożyć konektor |
| theProtocol.it | brak oficjalnego API | ToS — ostrożnie | popyt | **M** | ewentualnie RSS kategorii |
| RocketJobs.pl | ten sam operator co JJIT | jak JJIT | popyt | **S** | prawdopodobnie wspólne API |
| Oferia.pl | brak API | ToS zabrania scrapowania | popyt | **L** | tylko partnerstwo |
| Fixly (Grupa OLX) | brak publicznego API | ToS | popyt (usługi lokalne) | **L** | wymaga umowy z OLX |
| OLX Praca | OLX API (OAuth, partner) | tylko po umowie | popyt | **L** | duży wolumen, długi proces |
| Allegro (oferty/zlecenia) | Allegro REST API (OAuth2) | OK w ramach ToS | popyt/e‑commerce | **M** | już pośrednio przez BaseLinker; bezpośrednie OAuth = większa kontrola |
| Freelancehunt (PL/UA) | oficjalne API (token) | OK | popyt+podaż | **M** | dobre API, warto |
| Pracuj.pl | brak API | ToS | popyt | **L** | — |
| Bazy zamówień publicznych (TED / e‑Zamówienia) | oficjalne API/RSS | OK (dane publiczne) | popyt (duże kontrakty) | **M** | wysoki potencjał B2B dla usług cyfrowych |

**Rekomendacja kolejności:** NoFluffJobs (S) → RocketJobs (S) → Freelancehunt API (M) → Allegro OAuth bezpośrednio (M) → TED/e‑Zamówienia (M).

---

## 3. Komunikacja

| Integracja | Dostęp | Nakład | Wartość | Uwagi |
|---|---|---|---|---|
| Telegram bot (dwustronny) | Bot API | **M** | wysoka | n8n już wysyła eventy; dodać komendy: `/jobs`, `/match <id> accept`, `/radar` |
| Slack app | Slack API (OAuth, slash‑commands) | **M** | średnia‑wysoka | powiadomienia + akcje w wątku; App Directory = kanał dystrybucji |
| Discord bot | Discord API | **M** | średnia | społeczności freelancerów |
| WhatsApp Business | Cloud API (Meta) | **L** | wysoka (PL/LATAM) | wymaga weryfikacji firmy, szablony wiadomości |
| E‑mail digest | istniejący `utils/emailer.py` | **S** | średnia | dzienny/tygodniowy digest nowych zleceń i leadów Radaru |
| Web push | VAPID + service worker | **M** | średnia | powiadomienia w przeglądarce dla freelancerów |

**Rekomendacja:** e‑mail digest (S, natychmiastowa wartość) → Telegram bot dwustronny (M) → Slack app (M, przy okazji dystrybucja).

---

## 4. Płatności / wypłaty

| Integracja | Dostęp | Nakład | Uwagi |
|---|---|---|---|
| **Stripe Connect** | API | **L** | „marketplace‑grade" escrow i wypłaty do wykonawców; docelowy model zamiast ręcznego payout |
| PayPal Payouts | REST API | **M** | szeroki zasięg, prosty payout batch |
| Wise (TransferWise) API | API (klucz) | **M** | tanie przelewy międzynarodowe, wiele walut — dobre dla globalnych wykonawców |
| Przelewy24 / PayU | API | **M** | lokalne metody PL (BLIK!) — konwersja klientów PL |
| Stablecoin payout (USDC) | dostawca (np. Circle) lub on‑chain | **L** | pola `payout_method`/`payout_address` już w profilu; brakuje realizacji |
| Faktury — KSeF (PL) | API Ministerstwa Finansów | **M** | obowiązkowy e‑fakturowanie; model `Invoice` już jest, dodać eksport do KSeF |

**Rekomendacja:** BLIK przez Przelewy24/PayU (konwersja PL) → PayPal Payouts (M) → Stripe Connect (L, docelowo) → KSeF gdy wejdzie obowiązek.

---

## 5. Automatyzacja / AI

| Integracja | Nakład | Uwagi |
|---|---|---|
| Aplikacja Zapier (publiczna) | **M** | triggery: new job / new match / new radar lead; akcje: create job. Kanał dystrybucji. |
| Aplikacja Make (Integromat) | **M** | jw., popularne w PL/EU |
| Upgrade modeli Claude | **S** | `utils/ai.py` → `claude-sonnet-5` (jakość) / `claude-opus-5` (najtrudniejsze analizy); dziś kod używa starszych ID |
| Embeddingi — alternatywy | **S** | obok OpenAI: lokalny model (np. `bge-m3`) dla trybu zero‑cost o lepszej jakości niż hash |
| Publikacja w Shopify App Store | **L** | z „Custom App token" → publiczna aplikacja OAuth + review Shopify; `29 PLN/mies.` wg modelu biznesowego |
| AI QA obrazów (deliverables foto) | **M** | Claude vision do sprawdzania zdjęć produktowych (białe tło, ostrość, kadr) |
| Radar → auto‑import wg reguł | **S** | reguła: „jeśli lead pasuje do kategorii X i budżet > Y → importuj automatycznie" (rozszerzenie `tasks/radar.py`) |
| Wektorowa deduplikacja leadów | **M** | ten sam lead z 3 portali → jeden rekord (embedding + próg podobieństwa) |

**Rekomendacja:** upgrade modeli Claude (S) → reguły auto‑importu Radaru (S) → aplikacja Zapier (M) → Shopify App Store (L).

---

## 6. Sugerowany plan 3 sprintów

**Sprint 6 — „więcej źródeł, mniej klików":**
NoFluffJobs + RocketJobs konektory · Adzuna (klucz) · reguły auto‑importu Radaru ·
e‑mail digest · upgrade modeli Claude.

**Sprint 7 — „dwustronna komunikacja + PL płatności":**
Telegram bot dwustronny · BLIK (Przelewy24/PayU) · Freelancehunt API ·
deduplikacja leadów.

**Sprint 8 — „dystrybucja i skala":**
Aplikacja Zapier · Slack app · wniosek + integracja Upwork API ·
Stripe Connect (start) · Shopify App Store (start review).
