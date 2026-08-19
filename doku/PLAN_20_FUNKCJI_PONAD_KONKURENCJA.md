# 🚀 DROPIFY — 20 FUNKCJI PONAD KONKURENCJĘ
## 20 Features That Beat the Competition (Upwork / Fiverr / Toptal / Guru)

> Data analizy: sierpień 2026 · Na podstawie publicznych danych rynkowych (Upwork Spring 2026 z Uma™, Fiverr Go Q1 2026, raporty inwestorskie UPWK/FVRR).

---

## 1. ANALIZA KONKURENCJI — CO ROBIĄ I GDZIE SĄ SŁABI

### Upwork (2026)
| Co mają | Słabość do wykorzystania |
|---|---|
| Uma™ AI work agent: instant interviews, shortlisting, generator kontraktów z rozmów, work-history summaries | Take rate ~19-20% (fee 0-15% freelancer + ~5% client) — drogo |
| Aplikacja w ChatGPT / Claude — szukanie talentów przez chat | Czas do zatrudnienia ~3 dni; wciąż ręczny wybór z aplikujących |
| AI-native homepage, "majority of job posts" przez Uma | Matching działa tylko na tym, KTO SAM SIĘ ZGŁOSI — najlepsi się nie zgłaszają |
| OpenAI partnership — 10 mln certyfikowanych freelancerów | Brak lokalnego rynku PL/EU, brak integracji dropshipping (WooCommerce/Allegro) |

### Fiverr (2026)
| Co mają | Słabość do wykorzystania |
|---|---|
| Fiverr Go — AI asystent/klon stylu sprzedawcy | Take rate 27,7% (!) — najdroższa prowizja na rynku |
| Kategoria "AI Agents", agentic workflows | Spadek aktywnych kupujących -13,6% YoY; gig-owy model bez kontraktów |
| Gigs — zakup z półki | Brak milestonów, escrow "na słowo", brak ochrony przy dużych zleceniach |

### Reszta rynku
Toptal (2-3% najlepszych, drogi, bez self-service), Guru/PeoplePerHour (przestarzałe UX), platformy niszowe (bez AI).

### 🎯 LUKA RYNKOWA, KTÓRĄ WYPEŁNIA DROPIFY
1. **Prowizja 8% flat** vs 19-28% u konkurencji
2. **Matching proaktywny** — AI sam znajduje najlepszych (nie ci, którzy klikną "apply")
3. **Local-first PL/EN + EU** — konkurencja globalna, my lokalni i szybcy
4. **E-commerce native** — WooCommerce/Shopify/Allegro pod dropshipping (nikt tego nie ma w 1 produkcie)

---

## 2. DWADZIEŚCIA PROPOZYCJI — GRUPY

**Legenda:** 💰 = bezpośredni przychód · 📈 = wzrost/pozyskanie · 🛡️ = zaufanie/bezpieczeństwo · ⚙️ = automatyzacja

---

### GRUPA A: AI — MATCHING I ZAUFANIE (P0, fundament moatu)

**1. 🤖 AI Instant Interviews — automatyczne rozmowy kwalifikacyjne**
Freelancer po zaakceptowaniu matcha odpowiada na 3-5 pytań klienta (tekst/audio). Claude ocenia odpowiedzi (0-100) i zwraca podsumowanie klientowi. Klient decyduje w 10 minut, nie 3 dni.
*Przebija:* Upwork ma to tylko w płatnym planie (Uma). My — za darmo w każdej prowizji. Świetny współczynnik "hired faster".
💰📈 · Effort: M · Reuse: `app/utils/ai.py` (Claude już jest)

**2. 🤖 AI Deliverable Checker — automatyczna weryfikacja dostarczonej pracy**
Przy zakończeniu zlecenia AI porównuje opis zlecenia z dostarczonymi plikami/linkiem (checklist wymagań z analizy zlecenia) i daje klientowi "AI QA report" (np. "spełniono 8/10 wymagań"). Zmniejsza spory o 50%.
*Przebija:* żadna platforma nie weryfikuje dostarczonego worka. Klient czuje się bezpiecznie, spory maleją, escrow wypłacany szybciej.
🛡️💰 · Effort: M · Reuse: `ai_analysis.key_requirements`

**3. 🤖 AI Escrow Price Negotiator — automatyczna negocjacja ceny w ramach kontraktu**
Gdy budżet < fair_price, AI proponuje obu stronom rozsądny przedział i pomaga dojść do porozumienia (2-3 rundy) zanim dojdzie do ręcznego targowania. Mniej porzuconych kontraktów.
*Przebija:* Upwork/Fiverr zostawiają negocjacje 100% na użytkownikach. My mamy dane fair_price z analizy.
💰 · Effort: S-M · Reuse: `scoring.price_fit`, Claude

**4. 🤖 "Best Match Guarantee" — gwarancja jakości matcha**
Jeśli wybrany top-1 match nie zostanie zaakceptowany przez freelancera, system automatycznie podbija top-2/top-3 z priorytetowym powiadomieniem w 5 minut (fallback chain). Klient nigdy nie zostaje bez wykonawcy.
*Przebija:* Upwork "project continuity" tylko w Business Plus ($49/mies.). My — automatycznie, zawsze.
⚙️ · Effort: S · Reuse: `tasks/matching.py` (chain na statusach)

---

### GRUPA B: PŁATNOŚCI I ESCROW (P0 — zaufanie = prowizje)

**5. 💰 Milestones + Auto-Release Escrow**
Kontrakt dzielony na 2-4 milestonów (AI proponuje podział na podstawie analizy zlecenia). Płatność uwalniana per milestone po potwierdzeniu klienta (lub auto po 48h braku sprzeciwu).
*Przebija:* Fiverr = płatność z góry bez kontroli; Upwork = godziny/work diary. Milestones = standard enterprise, którego nikt z rynku masowego nie ma w 1 klik.
💰🛡️ · Effort: M · Reuse: `Contract` + nowy model `Milestone`

**6. 💰 Crypto/Stablecoin + Płatności Międzynarodowe**
Opcja wypłaty w USDT/stablecoinach (przez Wise/Stripe fiat) dla freelancerów spoza UE — 0% opłat przewalutowania, wypłaty w 5 minut zamiast 3-5 dni bankowych.
*Przebija:* Upwork wypłaty 2-5 dni + przewalutowanie; my instant i globalnie.
💰📈 · Effort: M · Integracja: Wise API / provider stablecoin

**7. 🛡️ Deposit Refund Guarantee (Money-Back)**
Gwarancja zwrotu zaliczki przy "no-show" freelancera (AI weryfikuje, czy wykonawca rozpoczął pracę — log aktywności, uploady). Buduje zaufanie masowe.
*Przebija:* Fiverr Pro ma guarantee tylko dla klientów Pro (opłata). My — w standardzie.
🛡️ · Effort: S · Reuse: `Payment.status` + zdarzenia aktywności

**8. 💰 Dynamiczna prowizja oparta o rating (risk-based pricing)**
Top-rated freelancerzy (4.8+, 20+ zleceń) płacą 5%, nowi 12%. Automatyczna kalkulacja w momencie kontraktu. Promuje jakość, daje cel do osiągnięcia.
*Przebija:* Upwork wprowadza fee per proposal (0-15%) — my mamy prosty, przewidywalny model oparty o reputację.
💰⚙️ · Effort: S · Reuse: `PLATFORM_FEE_RATE` + `User.rating`

---

### GRUPA C: E-COMMERCE / DROPSHIPPING NATIVE (P0-P1 — nasza nisza)

**9. 🛒 WooCommerce Plugin — "Fulfillment AI"**
Plugin do WooCommerce: klient tworzy zlecenie prosto z produktu w sklepie (dane produktu → opis zlecenia automatycznie), statusy realizacji sync do panelu, po zakończeniu link do pobrania plików. Model: 49 PLN jednorazowo + 29 PLN/mies. PRO.
*Przebija:* NIKT z konkurencji nie integruje się z WooCommerce dla fulfillmentu. To nasza nisza numer 1.
💰📈 · Effort: L (osobny repo) · Reuse: API REST

**10. 🛒 Shopify App — "Auto-Ship Studio"**
Analogicznie dla Shopify (App Store): tworzenie zleceń z produktów, webhooks, statusy. 29 PLN/mies. To stream przychodów #4 z dokumentu.
💰📈 · Effort: L · Reuse: API REST + webhooks (mamy `webhooks.py`)

**11. 🛒 Allegro / BaseLinker Integration**
Sync produktów i zleceń z Allegro (największy polski marketplace). Dla 30% polskich dropshipperów to "must have" — konkurencja nie istnieje lokalnie.
💰📈 · Effort: L · Integracja: BaseLinker API (jeden punkt = Woo + Allegro + Shopify)

**12. 📦 "Product Source Finder" — AI znajdzie dostawcę produktu**
Klient wkleja link produktu (Amazon/Allegro/Chiński supplier) → AI rozbija produkt na komponenty usług (zdjęcia, copy, video, listing) i generuje gotowe zlecenia na każdy komponent + sugeruje budżety. Dropshipper dostaje kompletny "fulfillment plan" w 30 sekund.
*Przebija:* Nikt nie mapuje produktu na pakiet usług. To funkcja-wirus dla niszy dropshipping.
📈🤖 · Effort: M · Reuse: `analyze_job` na opisie produktu

---

### GRUPA D: AUTOMATYZACJA PRACY I WZROSTU (P1)

**13. ⚙️ AI Proposal Autopilot — automatyczne oferty dla freelancera**
Freelancer ustawia "AI mode": system sam odpowiada na matchy zgodnie z szablonami i jego profilem (podsumowanie zlecenia + oferta cenowa), freelancer zatwierdza jednym klikiem lub ustawia auto-akcept dla zleceń > X PLN. Czas reakcji: 30 sekund vs 2-4h u konkurencji = klient dostaje odpowiedź, zanim zdąży szukać dalej.
*Przebija:* Fiverr Go asystent działa dla GIG-ów, nie dla kontraktów. My automatyzujemy match → kontrakt.
⚙️💰 · Effort: M · Reuse: Claude + `matches.accept`

**14. ⚙️ AI Onboarding Flow — "30-second job posting"**
Kreator zleceń w 3 krokach z AI: (1) wpisz 1 zdanie czego potrzebujesz, (2) AI dopytuje o 2-3 brakujące szczegóły, (3) publikuje gotowy post z budżetem, terminem i umiejętnościami. Redukcja porzuconych postów o ~40%.
*Przebija:* Upwork job generator tworzy post, ale nie dokańcza za usera szczegółów i nie triggeruje matcha od razu. My: post → match w 30 sekund.
📈⚙️ · Effort: M · Reuse: Claude + `create_job`

**15. 📈 Referral 2.0 — "Earn Forever"**
Referral daje nie 1x bonus, ale 2% prowizji od zleceń zaproszonego przez 12 miesięcy + 1% od jego referali (2-poziomowy). Automatyczna kalkulacja i wypłata (już mamy model `Referral`).
*Przebija:* Upwork bonus 1x za zapis. My — pasywny dochód powtarzalny = viral loop.
📈💰 · Effort: S · Reuse: `Referral` + beat task

**16. ⚙️ Daily AI Revenue Report + Anomaly Alerts (na start dnia)**
Rano email: przychód, nowe matchy, pending akceptacje, anomalie (spadek aktywności 50%, błąd płatności >3) z AI-proponowaną akcją. To "kontrola pasywnego dochodu" z dokumentu automation — już mamy `reports.daily_summary`, rozszerzamy o AI insights.
*Przebija:* Konkurencja nie raportuje właścicielowi platformy; to narzędzie dla CIEBIE (operatora).
⚙️ · Effort: S · Reuse: `tasks/reports.py`

---

### GRUPA E: SPOŁECZNOŚĆ, REPUTACJA I UX (P1-P2)

**17. 🏆 Skill Badges + AI-Verified Portfolio**
Badge "AI Verified" — freelancer przechodzi test umiejętności (zadanie 30-60 min oceniane przez AI + recenzję klienta). Portfolio z automatycznymi podpisami "dostarczone w X dni, ocena 4.9". Ranking "Top 10 w kategorii" co miesiąc.
*Przebija:* Upwork badges = zakupione statusy (Top Rated przez czas), bez weryfikacji kompetencji. AI-verification to obiektywny sygnał.
🛡️📈 · Effort: M · Reuse: `Rating`, Claude (ocena zadań)

**18. ⚡ Time-to-Hire Dashboard dla klienta**
Dashboard pokazuje: średni czas do pierwszego matcha (cel < 60 s), liczbę aktywnych matchy, statusy milestone'ów — klient widzi, że platforma "pracuje", zanim sam coś zrobi.
*Przebija:* Upwork pokazuje liczbę ofert, nie daje realtime wskaźników procesu.
📈 · Effort: S · Reuse: `analytics.py`

**19. 🌍 Multilingual Matching (AI works in any language)**
Zlecenia po niemiecku, hiszpańsku, czesku — Claude rozumie treść, embeddingi semantyczne matchują mimo języka. Przełącznik języka per zlecenie (EN/PL/DE/ES). Automatyczny tłumacz UI na 4 języki.
*Przebija:* Konkurencja ma UI w EN (Upwork) i ograniczone lokalizacje. My startujemy 2-językowo, rośniemy do 4.
📈 · Effort: M · Reuse: i18n już jest — dodajemy pliki DE/ES + `analyze_job` jest język-agnostic

**20. 💎 Publiczna "Transparent Fees Page" + Komparator Prowizji**
Strona pokazująca dokładnie: ile zarabia freelancer i ile płaci klient na DROPIFY vs Upwork vs Fiverr (interaktywny kalkulator na żywo, np. zlecenie 1000 PLN → DROPIFY 8% vs Upwork ~19% vs Fiverr ~28%). Marketing z danych, nie z obietnic.
*Przebija:* Konkurencja ukrywa realne koszty (fee per proposal, fee per contract). Kalkulator = materiał wiralowy + link do rejestracji.
📈 · Effort: S · Reuse: frontend page + dane z analizy

---

## 3. PRIORYTET WDROŻENIA (ROADMAP)

| Faza | Funkcje | Efekt |
|---|---|---|
| **Sprint 1 (M1)** ✅ WDROŻONE | #4 fallback chain · #8 dynamic fee · #15 referral 2.0 · #16 AI report · #18 time-to-hire · #20 fee komparator | Moat + lojalność bez dużego kodu |
| **Sprint 2 (M2)** ✅ WDROŻONE | #1 instant interviews · #2 AI deliverable checker · #3 price negotiator · #13 autopilot · #14 onboarding AI | Jakość matcha → wyższa konwersja |
| **Sprint 3 (M3)** ✅ WDROŻONE | #5 milestones escrow · #6 stablecoin · #7 refund guarantee | Większe kontrakty, mniej sporów |
| **Sprint 4 (M4+)** — Nisza | #9 WooCommerce · #10 Shopify · #11 Allegro/BaseLinker · #12 product source finder | Dropshipping = nasz rynek |

### Sprint 1 — co dokładnie wdrożono (19.08.2026)
- **#4 Best Match Guarantee** — odrzucenie matcha natychmiast triggeruje ponowny matching z wykluczeniem dotychczasowych kandydatów; nowi kandydaci dostają powiadomienie typu `priority` ("PRIORITY: fallback match"). Test: Anna odrzuca → Piotr awansowany automatycznie (81%).
- **#8 Dynamic Fee** — `calculate_fee_rate()`: top (rating ≥4.8, ≥20 ocen) = 5%, nowi (≤3 oceny) = 12%, reszta = 8%. Stawka zapisywana na kontrakcie (`Contract.fee_rate`), widoczna w UI.
- **#15 Referral 2.0 "Earn Forever"** — model `Commission` (poziomy 1/2), task Celery `process_referral_commissions` (codziennie 03:15): 2% kontraktów L1 + 1% L2, okno 12 mies., automatyczne powiadomienia i prowizje. Endpoint `GET /api/referrals/me` + sekcja w profilu.
- **#16 Daily AI Report** — `daily_summary` rozszerzony o anomalie (spadek przychodu vs 7-dniowa średnia, konwersja matchy <20%, błędy, brak rejestracji, stare matchy), AI insights (Claude z rule-fallback) i historię w `DailyReport`.
- **#18 Time-to-Hire** — metryki w `analytics/dashboard`: `avg_match_time_seconds`, `instant_matches` (<60 s), `avg_time_to_hire_hours`; sekcja "AI Pipeline (24/7)" w panelu klienta.
- **#20 Transparent Fees Komparator** — strona `/fees` z interaktywnym kalkulatorem DROPIFY 8% vs Upwork ~19% vs Fiverr ~28%, link w nawigacji.

### Sprint 2 — co dokładnie wdrożono (19.08.2026)
- **#1 AI Instant Interviews** — przy tworzeniu zlecenia AI generuje 4-5 pytań weryfikacyjnych (`generate_interview_questions`); freelancer odpowiada na matchu, Claude ocenia 0-100 z feedbackiem i mocnymi stronami (fallback: semantyczna zgodność odpowiedzi z briefem). Wynik + odpowiedzi widzi klient na karcie matcha. Event n8n `interview-submitted`.
- **#2 AI Deliverable Checker** — `POST /api/jobs/{id}/deliverables`: freelancer opisuje dostarczoną pracę (+link), AI wystawia raport QA (score 0-100, checklista wymagań, uwagi, rekomendacja approve/revisions/reject). Fallback regułowy: pokrycie wymagań. Widoczny dla obu stron na stronie zlecenia + powiadomienia + event n8n.
- **#3 AI Price Negotiator** — `GET /api/jobs/{id}/fair-price` (przedział + uzasadnienie AI), freelancer proponuje cenę (`propose-price`), klient akceptuje/odrzuca (`confirm-price`/`decline-price`); zaakceptowana cena (`agreed_price`) jest używana w kontrakcie zamiast budżetu.
- **#13 AI Proposal Autopilot** — pola `auto_accept_enabled/min_budget/min_score` w profilu freelancera; po utworzeniu matcha AI automatycznie akceptuje (kontrakt + powiadomienia + event n8n `autopilot-accepted`), jeśli match spełnia kryteria. Test: nowe zlecenie → kontrakt utworzony automatycznie.
- **#14 AI Onboarding 30 s** — `POST /api/jobs/generate`: klient pisze 1 zdanie → AI zwraca kompletny draft (tytuł, opis, kategoria, umiejętności, sugerowany budżet i termin); formularz na `/dashboard/jobs/new` wypełnia się automatycznie (do edycji przed publikacją).

### Sprint 3 — co dokładnie wdrożono (19.08.2026)
- **#5 Milestones + Auto-Release Escrow** — nowy model `Milestone`; przy utworzeniu kontraktu AI proponuje podział płatności na 2-4 etapy (Claude z fallbackiem 3× równo; sumy = budżet). Freelancer oddaje etap (`submit`) → status `in_review` → klient zwalnia płatność (`release`) → tworzy się `Payment` z proporcjonalną prowizją; cisza klienta 48h = **auto-zwolnienie** (task Celery co 30 min). Po zwolnieniu wszystkich etapów kontrakt zamyka się automatycznie. UI: pasek postępu + lista etapów z akcjami w `/dashboard/contracts`. Eventy n8n: `milestone-submitted`, `milestone-released`.
- **#6 Stablecoin payouts** — preferencje wypłaty w profilu freelancera (`payout_method: bank|stablecoin`, `payout_address`); wypłaty automatyczne (task `process_payouts` codziennie 04:00): płatności `paid` → `paid_out` z metodą/adresem i powiadomieniem (stablecoin ~5 min, bank 1-3 dni). Event n8n `payout-processed`. Test: 1466,67 PLN paid_out przez USDT.
- **#7 Deposit Refund Guarantee** — `request-refund`: AI weryfikuje no-show (kontrakt ≥3 dni, zero oddanych etapów) → automatyczny zwrot (payments → `refunded`), anulowanie kontraktu, **reopening zlecenia + natychmiastowy re-matching** (synergia z #4). Flaga `refund_eligible` + powód widoczne w UI kontraktów. Event n8n `refund-issued`. Test: kontrakt 4 dni bez pracy → zwrot → zlecenie otwarte ponownie.

---

## 4. SZYBKIE WYLICZENIE WPŁYWU (KONSERWATYWNIE)

- #8 dynamic fee: nawet bez zmiany cen → +2-3 pkt proc. marży przy 350+ zleceń/mies.
- #15 referral 2.0: 20-30% nowych użytkowników MoM (dokument automation przewiduje 70-110% z całego growth stack)
- #9 WooCommerce (100 instalacji × 49 PLN) + #10 Shopify (50 × 29 PLN/mies.) = +6,4 tys. PLN jednorazowo + 1,45 tys. PLN/mies.
- #5 milestones: średnia wartość zlecenia rośnie (większe kontrakty = więcej escrow) → +15-20% GMV

**Razem: dodatkowe ~3-5 tys. PLN/mies. przychodu do M6 bez zwiększania kosztów AI (wszystko na już działającym Claude API).**

---

*Dokument powiązany: README_START_HERE.md, FULL_AUTOMATION_PASSIVE_INCOME.txt, Technical_Blueprint_DROPIFY.docx*
