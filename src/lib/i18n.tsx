"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export type Lang = "pl" | "en";

const DICT: Record<string, { pl: string; en: string }> = {
  // Brand
  "brand.name": { pl: "DROPIFY", en: "DROPIFY" },
  "brand.tagline": {
    pl: "Platforma AI do automatycznego doboru zleceń",
    en: "AI-powered job matching platform",
  },

  // Navigation
  "nav.home": { pl: "Start", en: "Home" },
  "nav.fees": { pl: "Prowizje", en: "Fees" },
  "nav.how": { pl: "Jak to działa", en: "How it works" },
  "nav.pricing": { pl: "Cennik", en: "Pricing" },
  "nav.features": { pl: "Funkcje", en: "Features" },
  "nav.login": { pl: "Logowanie", en: "Sign in" },
  "nav.register": { pl: "Rejestracja", en: "Sign up" },
  "nav.dashboard": { pl: "Panel", en: "Dashboard" },
  "nav.logout": { pl: "Wyloguj", en: "Log out" },
  "nav.profile": { pl: "Profil", en: "Profile" },
  "nav.jobs": { pl: "Zlecenia", en: "Jobs" },
  "nav.matches": { pl: "Matchy", en: "Matches" },
  "nav.contracts": { pl: "Kontrakty", en: "Contracts" },
  // Fees comparator (#20)
  "fees.title": { pl: "Porównaj prowizje", en: "Compare platform fees" },
  "fees.subtitle": {
    pl: "Konkurencja ukrywa prawdziwe koszty. My pokazujemy wszystko.",
    en: "Competitors hide the real costs. We show everything.",
  },
  "fees.label": { pl: "Wartość zlecenia (PLN)", en: "Job value (PLN)" },
  "fees.clientPays": { pl: "Zapłaci klient", en: "Client pays" },
  "fees.freelancerGets": { pl: "Freelancer otrzyma", en: "Freelancer receives" },
  "fees.combined": { pl: "Całkowity koszt prowizji", en: "Total fee cost" },
  "fees.dropify": { pl: "DROPIFY — 8% flat", en: "DROPIFY — 8% flat" },
  "fees.upwork": { pl: "Upwork — ~19%", en: "Upwork — ~19%" },
  "fees.fiverr": { pl: "Fiverr — ~28%", en: "Fiverr — ~28%" },
  "fees.dynamic": {
    pl: "Top wykonawcy płacą tylko 5%, nowi 12% — im lepszy freelancer, tym mniejsza prowizja.",
    en: "Top freelancers pay only 5%, new ones 12% — the better the freelancer, the lower the fee.",
  },
  "fees.source": {
    pl: "Źródła: raporty inwestorskie Upwork i Fiverr 2025-2026 (take rate Fiverr 27,7% za rok fiskalny 2025, Upwork ~19% łącznie).",
    en: "Sources: Upwork & Fiverr investor reports 2025-2026 (Fiverr take rate 27.7% FY2025, Upwork ~19% combined).",
  },
  "fees.save": { pl: "Oszczędzasz", en: "You save" },
  "fees.cta": { pl: "Załóż konto i zacznij oszczędzać", en: "Create an account and start saving" },

  // Time-to-hire (#18)
  "dash.stat.matchTime": { pl: "Śr. czas do matcha", en: "Avg time to match" },
  "dash.stat.instant": { pl: "Matche < 60 s", en: "Matches < 60 s" },
  "dash.stat.hireTime": { pl: "Śr. czas do zatrudnienia", en: "Avg time to hire" },
  "dash.aiPipeline": { pl: "AI Pipeline (pracuje 24/7)", en: "AI Pipeline (working 24/7)" },
  "dash.pipelineLive": { pl: "Aktywny", en: "Live" },
  "dash.pipelineDesc": {
    pl: "Analiza, matchowanie, powiadomienia i kontrakty działają automatycznie.",
    en: "Analysis, matching, notifications and contracts run automatically.",
  },
  "dash.noData": { pl: "Brak danych — opublikuj zlecenie", en: "No data yet — post a job" },

  // Referral (#15)
  "profile.referralTitle": { pl: "Program poleceń — Earn Forever", en: "Referral program — Earn Forever" },
  "profile.referralEarned": { pl: "Łącznie zarobione", en: "Total earned" },
  "profile.referralReferred": { pl: "Poleconych użytkowników", en: "People referred" },
  "profile.referralRate": { pl: "2% od kontraktów poleconych · 1% z drugiego poziomu · przez 12 mies.", en: "2% of referred contracts · 1% second level · for 12 months" },
  "profile.referralNone": { pl: "Brak prowizji — poleć znajomych i zarabiaj pasywnie", en: "No commissions yet — refer friends and earn passively" },

  // Contracts (#8)
  "contracts.rate": { pl: "Stawka prowizji", en: "Fee rate" },
  "contracts.feeTier": { pl: "Prowizja dynamiczna", en: "Dynamic fee" },

  // Sprint 2: AI Instant Interviews (#1)
  "interview.title": { pl: "AI Interview", en: "AI Interview" },
  "interview.desc": {
    pl: "Odpowiedz na pytania — AI oceni odpowiedzi (0-100) i pokaże wynik klientowi.",
    en: "Answer the questions — AI scores your answers (0-100) for the client.",
  },
  "interview.submit": { pl: "Wyślij odpowiedzi", en: "Submit answers" },
  "interview.score": { pl: "Ocena AI", en: "AI score" },
  "interview.answers": { pl: "Odpowiedzi", en: "Answers" },
  "interview.feedback": { pl: "Opinia AI", en: "AI feedback" },
  "interview.done": { pl: "Przeprowadzono", en: "Completed" },
  "interview.notDone": { pl: "Brak odpowiedzi", en: "No answers" },
  "interview.noQuestions": { pl: "To zlecenie nie ma pytań.", en: "This job has no questions." },

  // Sprint 2: AI Deliverable Checker (#2)
  "deliver.title": { pl: "Deliverables + AI QA", en: "Deliverables + AI QA" },
  "deliver.desc": {
    pl: "Opisz co dostarczasz (i wklej link). AI porówna z wymaganiami i wystawi raport QA.",
    en: "Describe what you deliver (paste a link). AI compares against requirements and issues a QA report.",
  },
  "deliver.description": { pl: "Opis dostarczonej pracy", en: "Delivered work description" },
  "deliver.url": { pl: "Link do plików (opcjonalnie)", en: "Files link (optional)" },
  "deliver.submit": { pl: "Sprawdź przez AI", en: "Check with AI" },
  "deliver.report": { pl: "Raport AI QA", en: "AI QA report" },
  "deliver.score": { pl: "Zgodność z wymaganiami", en: "Requirements coverage" },
  "deliver.recommendation": { pl: "Rekomendacja", en: "Recommendation" },
  "deliver.issues": { pl: "Uwagi", en: "Issues" },
  "deliver.approve": { pl: "zatwierdź", en: "approve" },
  "deliver.revisions": { pl: "poprawki", en: "revisions" },
  "deliver.reject": { pl: "odrzuć", en: "reject" },
  "deliver.none": { pl: "Brak dostarczonej pracy", en: "No deliverables yet" },

  // Sprint 2: AI Price Negotiator (#3)
  "nego.title": { pl: "Negocjacje ceny", en: "Price negotiation" },
  "nego.fairPrice": { pl: "Cena uczciwa wg AI", en: "AI fair price" },
  "nego.range": { pl: "Proponowany przedział", en: "Suggested range" },
  "nego.rationale": { pl: "Uzasadnienie AI", en: "AI rationale" },
  "nego.propose": { pl: "Zaproponuj cenę", en: "Propose price" },
  "nego.proposed": { pl: "Propozycja wysłana", en: "Proposal sent" },
  "nego.accept": { pl: "Zaakceptuj cenę", en: "Accept price" },
  "nego.decline": { pl: "Odrzuć", en: "Decline" },
  "nego.accepted": { pl: "Cena zaakceptowana", en: "Price accepted" },
  "nego.declined": { pl: "Odrzucona", en: "Declined" },
  "nego.amount": { pl: "Twoja cena (PLN)", en: "Your price (PLN)" },

  // Sprint 2: Autopilot (#13)
  "auto.title": { pl: "AI Proposal Autopilot", en: "AI Proposal Autopilot" },
  "auto.desc": {
    pl: "AI sam akceptuje matchy spełniające Twoje kryteria — kontrakt tworzy się automatycznie.",
    en: "AI auto-accepts matches that meet your criteria — contracts are created automatically.",
  },
  "auto.enable": { pl: "Włącz autopilota", en: "Enable autopilot" },
  "auto.minScore": { pl: "Min. dopasowanie (0-1)", en: "Min. match score (0-1)" },
  "auto.minBudget": { pl: "Min. budżet zlecenia (PLN)", en: "Min. job budget (PLN)" },

  // Sprint 2: AI Onboarding (#14)
  "gen.title": { pl: "⚡ Szybkie tworzenie z AI", en: "⚡ Quick create with AI" },
  "gen.desc": {
    pl: "Napisz 1 zdanie czego potrzebujesz — AI wypełni cały formularz.",
    en: "Write one sentence about what you need — AI fills the whole form.",
  },
  "gen.idea": { pl: "Np. „Fotograf produktowy do 50 zdjęć ubrań z retuszem”", en: "E.g. \"Product photographer for 50 clothing photos with retouching\"" },
  "gen.button": { pl: "Wygeneruj zlecenie", en: "Generate job" },
  "gen.used": { pl: "Formularz uzupełniony przez AI — sprawdź i edytuj przed publikacją.", en: "Form filled by AI — review and edit before publishing." },

  // Sprint 3: Milestones escrow (#5)
  "ms.title": { pl: "Milestones (escrow)", en: "Milestones (escrow)" },
  "ms.desc": {
    pl: "AI podzieliło płatność na etapy. Wykonawca oddaje etap → klient zwalnia płatność (lub auto-zwolnienie po 48h bez sprzeciwu).",
    en: "AI split the payment into stages. Freelancer delivers a stage → client releases payment (or auto-release after 48h of silence).",
  },
  "ms.progress": { pl: "Postęp płatności", en: "Payment progress" },
  "ms.submit": { pl: "Oddaj etap", en: "Submit stage" },
  "ms.release": { pl: "Zwalniam płatność", en: "Release payment" },
  "ms.released": { pl: "Zwolnione", en: "Released" },
  "ms.in_review": { pl: "Do weryfikacji", en: "In review" },
  "ms.pending": { pl: "Oczekuje", en: "Pending" },
  "ms.autoHint": {
    pl: "Brak reakcji klienta przez 48h = auto-zwolnienie.",
    en: "Client silence for 48h = auto-release.",
  },
  "ms.completed": { pl: "Kontrakt zakończony — wszystkie etapy zwolnione", en: "Contract completed — all stages released" },

  // Sprint 3: Refund guarantee (#7)
  "refund.title": { pl: "Gwarancja zwrotu depozytu", en: "Deposit Refund Guarantee" },
  "refund.desc": {
    pl: "Jeśli wykonawca nie zacznie pracy w ciągu 3 dni, AI zweryfikuje i automatycznie zwróci Ci pieniądze.",
    en: "If the freelancer doesn't start within 3 days, AI verifies and automatically refunds you.",
  },
  "refund.request": { pl: "Poproś o zwrot", en: "Request refund" },
  "refund.eligible": { pl: "Zwrot dostępny", en: "Refund available" },
  "refund.reason": { pl: "Powód", en: "Reason" },
  "refund.done": { pl: "Zwrot przyznany — szukamy nowego wykonawcy", en: "Refund issued — looking for a new freelancer" },

  // Sprint 3: Stablecoin payouts (#6)
  "payout.title": { pl: "Wypłaty", en: "Payouts" },
  "payout.method": { pl: "Metoda wypłaty", en: "Payout method" },
  "payout.bank": { pl: "Przelew bankowy (1-3 dni)", en: "Bank transfer (1-3 days)" },
  "payout.stablecoin": { pl: "Stablecoin (USDT, ~5 min)", en: "Stablecoin (USDT, ~5 min)" },
  "payout.address": { pl: "Adres portfela (USDT)", en: "Wallet address (USDT)" },
  "payout.note": {
    pl: "Wypłaty stablecoin są przetwarzane automatycznie przy zakończeniu płatności.",
    en: "Stablecoin payouts are processed automatically when payments settle.",
  },

  "nav.talent": { pl: "Specjaliści", en: "Specialists" },
  "nav.admin": { pl: "Admin", en: "Admin" },
  "nav.createJob": { pl: "+ Nowe zlecenie", en: "+ New job" },
  "nav.factory": { pl: "AI Factory", en: "AI Factory" },
  "nav.developer": { pl: "Deweloper / API", en: "Developer / API" },

  // #F1/#F6 AI Listing & Video Factory
  "factory.title": { pl: "AI Factory — fabryka ofert", en: "AI Factory" },
  "factory.subtitle": {
    pl: "Wklej nazwę produktu lub link do dostawcy — AI wygeneruje gotowy opis, SEO i scenariusz wideo dla Twojego sklepu dropshipping.",
    en: "Paste a product name or supplier link — AI generates a ready listing, SEO tags and a video script for your dropshipping store.",
  },
  "factory.productName": { pl: "Nazwa produktu", en: "Product name" },
  "factory.description": { pl: "Notatki / opis (opcjonalnie)", en: "Notes / description (optional)" },
  "factory.sourceUrl": { pl: "Link do produktu / dostawcy (opcjonalnie)", en: "Product / supplier link (optional)" },
  "factory.marketplace": { pl: "Marketplace", en: "Marketplace" },
  "factory.language": { pl: "Język treści", en: "Content language" },
  "factory.generateListing": { pl: "Wygeneruj ofertę AI", en: "Generate AI listing" },
  "factory.generateVideo": { pl: "Wygeneruj scenariusz wideo", en: "Generate video script" },
  "factory.listingTitle": { pl: "Tytuł oferty", en: "Listing title" },
  "factory.bullets": { pl: "Punkty korzyści", en: "Benefit bullets" },
  "factory.seoTags": { pl: "Tagi SEO", en: "SEO tags" },
  "factory.meta": { pl: "Meta opis (Google)", en: "Meta description (Google)" },
  "factory.videoHook": { pl: "Hook (pierwsze 3 sekundy)", en: "Hook (first 3 seconds)" },
  "factory.videoScript": { pl: "Scenariusz / voiceover", en: "Script / voiceover" },
  "factory.videoCta": { pl: "Call to action", en: "Call to action" },
  "factory.history": { pl: "Historia wygenerowanych ofert", en: "Generated listings history" },
  "factory.empty": { pl: "Brak wygenerowanych ofert — zacznij powyżej.", en: "No listings yet — start above." },

  // #F8 White-label / Reseller API
  "dev.title": { pl: "Deweloper / White-label API", en: "Developer / White-label API" },
  "dev.subtitle": {
    pl: "Osadź AI matching DROPIFY jako usługę pod własną marką w portalu Twojej agencji.",
    en: "Embed DROPIFY's AI matching as a branded service inside your own agency portal.",
  },
  "dev.keyName": { pl: "Nazwa klucza", en: "Key name" },
  "dev.brandName": { pl: "Nazwa marki (opcjonalnie)", en: "Brand name (optional)" },
  "dev.createKey": { pl: "Utwórz klucz API", en: "Create API key" },
  "dev.yourKeys": { pl: "Twoje klucze API", en: "Your API keys" },
  "dev.revoke": { pl: "Unieważnij", en: "Revoke" },
  "dev.newKeyWarning": { pl: "Zapisz ten klucz teraz — nie zostanie pokazany ponownie.", en: "Store this key now — it won't be shown again." },
  "dev.endpoint": { pl: "Endpoint dla partnerów", en: "Partner endpoint" },
  "dev.requests": { pl: "zapytań", en: "requests" },
  "dev.noKeys": { pl: "Brak kluczy API — utwórz pierwszy powyżej.", en: "No API keys yet — create your first above." },

  // #F5 AI Co-Pilot
  "copilot.title": { pl: "AI Co-Pilot", en: "AI Co-Pilot" },
  "copilot.desc": { pl: "Zapytaj AI o cokolwiek związanego z tym zleceniem.", en: "Ask the AI anything about this job." },
  "copilot.placeholder": { pl: "Np. Jaki jest status tego zlecenia?", en: "E.g. What's the status of this job?" },
  "copilot.ask": { pl: "Zapytaj", en: "Ask" },
  "copilot.empty": { pl: "Brak wiadomości — zadaj pierwsze pytanie.", en: "No messages yet — ask your first question." },

  // Payments (Stripe checkout)
  "pay.title": { pl: "Płatność", en: "Payment" },
  "pay.stripe": { pl: "Zapłać kartą (Stripe)", en: "Pay with card (Stripe)" },
  "pay.demoNote": {
    pl: "Stripe nieskonfigurowany na serwerze — użyj przycisku „Zwalniam płatność” (tryb demo).",
    en: "Stripe isn't configured on this server — use 'Release payment' (demo mode).",
  },
  "pay.redirecting": { pl: "Przekierowywanie do Stripe…", en: "Redirecting to Stripe…" },

  // #F3 AI Contract & Compliance Generator
  "agreement.title": { pl: "Umowa (AI)", en: "Agreement (AI)" },
  "agreement.download": { pl: "Pobierz umowę", en: "Download agreement" },
  "agreement.desc": { pl: "Automatycznie wygenerowane podsumowanie umowy dla tego kontraktu.", en: "Auto-generated plain-language agreement for this contract." },

  // #F4 Smart Supplier Risk Score
  "risk.low": { pl: "Niskie ryzyko", en: "Low risk" },
  "risk.medium": { pl: "Średnie ryzyko", en: "Medium risk" },
  "risk.high": { pl: "Nowy / niezweryfikowany", en: "New / unverified" },

  // #F7 Global Talent Time-Zone Auto-Scheduler
  "sched.title": { pl: "Sugerowany harmonogram", en: "Suggested schedule" },
  "sched.overlap": { pl: "godz. pokrycia dziennie", en: "hrs overlap / day" },
  "sched.apart": { pl: "godz. różnicy stref", en: "hrs apart" },
  "sched.live": { pl: "Wystarczające pokrycie na bieżącą komunikację", en: "Enough overlap for live communication" },
  "sched.handoff": { pl: "Krótkie okno — zaplanuj codzienny sync", en: "Small window — plan a daily sync" },
  "sched.async": { pl: "Praca asynchroniczna 24/7 (różne strefy czasowe)", en: "Async 24/7 coverage (different time zones)" },

  // #F2 Global Currency & Tax
  "fx.title": { pl: "Waluta i podatki", en: "Currency & tax" },
  "fx.convert": { pl: "Przelicz na", en: "Convert to" },
  "fx.taxNote": { pl: "Uwaga transgraniczna", en: "Cross-border note" },

  // Sprint 4 (#12) Product Source Finder
  "nav.integrations": { pl: "Integracje", en: "Integrations" },
  "sf.title": { pl: "Product Source Finder", en: "Product Source Finder" },
  "sf.desc": {
    pl: "Wklej link do produktu (Amazon, Allegro, dostawca) — AI rozpisze pełny plan realizacji z sugerowanymi zleceniami.",
    en: "Paste a product link (Amazon, Allegro, supplier) — AI breaks it into a full fulfillment plan with suggested jobs.",
  },
  "sf.productRef": { pl: "Link lub nazwa produktu", en: "Product link or name" },
  "sf.run": { pl: "Zbuduj plan realizacji", en: "Build fulfillment plan" },
  "sf.summary": { pl: "Podsumowanie", en: "Summary" },
  "sf.suggestedJobs": { pl: "Sugerowane zlecenia", en: "Suggested jobs" },
  "sf.totalBudget": { pl: "Szacowany łączny budżet", en: "Total estimated budget" },
  "sf.createAll": { pl: "Utwórz wszystkie zlecenia (AI dopasuje wykonawców)", en: "Create all jobs (AI will match freelancers)" },
  "sf.created": { pl: "Utworzono zleceń", en: "Jobs created" },

  // Sprint 4 (#9-#11) store integrations
  "int.title": { pl: "Integracje sklepowe", en: "Store integrations" },
  "int.subtitle": {
    pl: "Podepnij Shopify lub BaseLinker (obejmuje też Allegro) — nowe produkty/zamówienia automatycznie staną się zleceniami AI. WooCommerce: zobacz integrations/woocommerce w repozytorium.",
    en: "Connect Shopify or BaseLinker (also covers Allegro) — new products/orders automatically become AI-matched jobs. WooCommerce: see integrations/woocommerce in the repo.",
  },
  "int.shopify": { pl: "Shopify", en: "Shopify" },
  "int.baselinker": { pl: "BaseLinker (+ Allegro)", en: "BaseLinker (+ Allegro)" },
  "int.shopDomain": { pl: "Domena sklepu (np. sklep.myshopify.com)", en: "Shop domain (e.g. store.myshopify.com)" },
  "int.accessToken": { pl: "Token dostępu API", en: "API access token" },
  "int.webhookSecret": { pl: "Sekret webhooka (opcjonalnie)", en: "Webhook secret (optional)" },
  "int.label": { pl: "Nazwa konta", en: "Account label" },
  "int.connect": { pl: "Połącz", en: "Connect" },
  "int.disconnect": { pl: "Odłącz", en: "Disconnect" },
  "int.sync": { pl: "Synchronizuj teraz", en: "Sync now" },
  "int.connected": { pl: "Połączone konta", en: "Connected accounts" },
  "int.none": { pl: "Brak połączonych sklepów", en: "No stores connected yet" },
  "int.lastSynced": { pl: "Ostatnia synchronizacja", en: "Last synced" },
  "int.never": { pl: "nigdy", en: "never" },
  "int.webhookUrl": { pl: "URL webhooka Shopify", en: "Shopify webhook URL" },

  // Portal Radar — global scan of external job portals
  "nav.radar": { pl: "Portal Radar", en: "Portal Radar" },
  "radar.title": { pl: "Portal Radar", en: "Portal Radar" },
  "radar.subtitle": {
    pl: "Skan portali z całego świata przez oficjalne API i kanały RSS — zlecenia (zleceniodawcy) i wykonawcy (zleceniobiorcy). Importuj zlecenie jednym kliknięciem, a silnik AI dopasuje wykonawców z DROPIFY.",
    en: "Worldwide portal scan via official APIs and RSS feeds — jobs (demand) and contractors (supply). Import a lead in one click and the AI engine matches DROPIFY freelancers.",
  },
  "radar.tab.listings": { pl: "Zlecenia", en: "Job leads" },
  "radar.tab.talent": { pl: "Wykonawcy", en: "Contractors" },
  "radar.tab.sources": { pl: "Źródła", en: "Sources" },
  "radar.search": { pl: "Szukaj…", en: "Search…" },
  "radar.filter.source": { pl: "Wszystkie źródła", en: "All sources" },
  "radar.filter.remote": { pl: "Tylko zdalne", en: "Remote only" },
  "radar.filter.status": { pl: "Wszystkie statusy", en: "All statuses" },
  "radar.import": { pl: "Importuj jako zlecenie", en: "Import as job" },
  "radar.dismiss": { pl: "Odrzuć", en: "Dismiss" },
  "radar.imported": { pl: "Zaimportowano", en: "Imported" },
  "radar.dismissed": { pl: "Odrzucone", en: "Dismissed" },
  "radar.open": { pl: "Otwórz oryginał", en: "Open original" },
  "radar.contact": { pl: "Kontakt", en: "Contact" },
  "radar.none": { pl: "Brak wyników — uruchom skan w zakładce Źródła.", en: "Nothing here yet — run a scan from the Sources tab." },
  "radar.scanNow": { pl: "Skanuj teraz", en: "Scan now" },
  "radar.scanAll": { pl: "Skanuj wszystkie źródła", en: "Scan all sources" },
  "radar.scanQueued": { pl: "Skan uruchomiony", en: "Scan started" },
  "radar.lastScan": { pl: "Ostatni skan", en: "Last scan" },
  "radar.status.ok": { pl: "OK", en: "OK" },
  "radar.status.fail": { pl: "Błąd", en: "Failed" },
  "radar.status.never": { pl: "nigdy", en: "never" },
  "radar.needsKey": { pl: "wymaga klucza API", en: "needs API key" },
  "radar.disabled": { pl: "wyłączone", en: "disabled" },
  "radar.kind.listings": { pl: "zlecenia", en: "job leads" },
  "radar.kind.talent": { pl: "wykonawcy", en: "contractors" },
  "radar.talent.contacted": { pl: "Skontaktowano", en: "Contacted" },
  "radar.talent.invited": { pl: "Zaproszono", en: "Invited" },
  "radar.adminOnly": { pl: "Skan może uruchomić tylko administrator.", en: "Only an admin can run a scan." },

  // Dispute handling
  "dispute.title": { pl: "Spór", en: "Dispute" },
  "dispute.raise": { pl: "Zgłoś spór", en: "Raise a dispute" },
  "dispute.reason": { pl: "Opisz problem", en: "Describe the problem" },
  "dispute.submit": { pl: "Zgłoś do administratora", en: "Submit to admin" },
  "dispute.raisedBy": { pl: "Zgłoszone przez", en: "Raised by" },
  "dispute.aiAssessment": { pl: "Wstępna ocena AI", en: "AI first-pass assessment" },
  "dispute.pending": { pl: "Spór w trakcie rozpatrywania przez administratora.", en: "Dispute pending admin review." },
  "dispute.status": { pl: "Sporne", en: "Disputed" },
  "admin.disputes": { pl: "Spory", en: "Disputes" },
  "admin.disputes.none": { pl: "Brak aktywnych sporów", en: "No active disputes" },
  "admin.disputes.resolveRelease": { pl: "Zwolnij do wykonawcy", en: "Release to freelancer" },
  "admin.disputes.resolveRefund": { pl: "Zwróć klientowi", en: "Refund client" },
  "admin.disputes.resolved": { pl: "Spór rozstrzygnięty", en: "Dispute resolved" },

  // Hero
  "hero.title1": {
    pl: "Automatyczne dopasowanie",
    en: "Automatic matching",
  },
  "hero.title2": {
    pl: "zleceń do najlepszych specjalistów",
    en: "of jobs to the best specialists",
  },
  "hero.subtitle": {
    pl: "DROPIFY to globalny rynek, w którym sztuczna inteligencja łączy e-commerce i dropshipping z wykwalifikowanymi freelancerami w 30 sekund. Po polsku i po angielsku.",
    en: "DROPIFY is a global marketplace where AI connects e-commerce and dropshipping with skilled freelancers in 30 seconds. In Polish and English.",
  },
  "hero.cta.start": { pl: "Zacznij za darmo", en: "Start for free" },
  "hero.cta.learn": { pl: "Zobacz jak działa", en: "See how it works" },
  "hero.stat.jobs": { pl: "zleceń zrealizowanych", en: "jobs completed" },
  "hero.stat.users": { pl: "użytkowników", en: "users" },
  "hero.stat.fee": { pl: "prowizja", en: "platform fee" },

  // Features
  "features.title": { pl: "Dlaczego DROPIFY?", en: "Why DROPIFY?" },
  "features.ai.title": { pl: "AI Matching Engine", en: "AI Matching Engine" },
  "features.ai.desc": {
    pl: "Claude analizuje zlecenie i w 30 sekund dopasowuje 3 najlepszych wykonawców.",
    en: "Claude analyzes each job and matches the top 3 freelancers in 30 seconds.",
  },
  "features.fee.title": { pl: "Prowizja 8%", en: "8% flat fee" },
  "features.fee.desc": {
    pl: "Zamiast 20–30% jak na Upwork/Fiverr. Zleceniodawcy płacą mniej, freelancerzy zarabiają więcej.",
    en: "Instead of 20–30% like Upwork/Fiverr. Clients pay less, freelancers earn more.",
  },
  "features.auto.title": { pl: "100% automatyzacji", en: "100% automation" },
  "features.auto.desc": {
    pl: "Analiza, matchowanie, kontrakty i powiadomienia działają bez Twojego udziału 24/7.",
    en: "Analysis, matching, contracts and notifications run 24/7 with no manual work.",
  },
  "features.bilingual.title": { pl: "Polski + English", en: "Polish + English" },
  "features.bilingual.desc": {
    pl: "Platforma dostępna na całym świecie — przełącz język jednym kliknięciem.",
    en: "Available worldwide — switch language with one click.",
  },
  "features.saas.title": { pl: "SaaS & VPS", en: "SaaS & VPS" },
  "features.saas.desc": {
    pl: "Frontend na Vercel, backend na Twoim VPS. Pełna kontrola, minimalne koszty.",
    en: "Frontend on Vercel, backend on your VPS. Full control, minimal cost.",
  },
  "features.escrow.title": { pl: "Bezpieczne płatności", en: "Safe payments" },
  "features.escrow.desc": {
    pl: "System kontraktów, escrow i automatycznych wypłat dla obu stron.",
    en: "Contracts, escrow and automated payouts for both sides.",
  },

  // How it works
  "how.title": { pl: "Jak to działa?", en: "How it works?" },
  "how.s1.title": { pl: "Opublikuj zlecenie", en: "Post a job" },
  "how.s1.desc": {
    pl: "Zleceniodawca opisuje zadanie, budżet i termin.",
    en: "The client describes the task, budget and deadline.",
  },
  "how.s2.title": { pl: "AI analizuje i matchuje", en: "AI analyzes & matches" },
  "how.s2.desc": {
    pl: "Claude wyciąga kategorię, umiejętności i uczciwą cenę. Silnik znajdzie top 3 wykonawców.",
    en: "Claude extracts category, skills and fair price. The engine finds the top 3 freelancers.",
  },
  "how.s3.title": { pl: "Wykonawca akceptuje", en: "Freelancer accepts" },
  "how.s3.desc": {
    pl: "Powiadomienia wysyłane automatycznie. Jeden klik tworzy kontrakt.",
    en: "Notifications are automatic. One click creates a contract.",
  },
  "how.s4.title": { pl: "Zarobek i ocena", en: "Earn & review" },
  "how.s4.desc": {
    pl: "Po realizacji środki trafiają do wykonawcy, a Ty otrzymujesz 8% prowizji.",
    en: "After delivery the freelancer gets paid and you keep 8%.",
  },

  // Pricing
  "pricing.title": { pl: "Cennik", en: "Pricing" },
  "pricing.subtitle": {
    pl: "Zacznij za darmo. Rośnij, kiedy chcesz.",
    en: "Start free. Scale when you want.",
  },
  "pricing.month": { pl: "/mies.", en: "/mo" },
  "pricing.popular": { pl: "Najpopularniejszy", en: "Most popular" },
  "pricing.free.jobs": { pl: "5 zleceń / miesiąc", en: "5 jobs / month" },
  "pricing.starter.jobs": { pl: "50 zleceń / miesiąc", en: "50 jobs / month" },
  "pricing.pro.jobs": { pl: "Bez limitu zleceń", en: "Unlimited jobs" },
  "pricing.feature.matching": { pl: "AI matching", en: "AI matching" },
  "pricing.feature.analytics": { pl: "Analityka", en: "Analytics" },
  "pricing.feature.priority": { pl: "Priorytetowe matchy", en: "Priority matches" },
  "pricing.feature.support": { pl: "Wsparcie email", en: "Email support" },
  "pricing.feature.slack": { pl: "Wsparcie Slack", en: "Slack support" },
  "pricing.cta.free": { pl: "Zacznij", en: "Start" },
  "pricing.cta.starter": { pl: "Wybierz Starter", en: "Choose Starter" },
  "pricing.cta.pro": { pl: "Wybierz Pro", en: "Choose Pro" },
  "pricing.cta.enterprise": { pl: "Kontakt", en: "Contact" },

  // CTA
  "cta.title": { pl: "Gotowy do startu?", en: "Ready to get started?" },
  "cta.desc": {
    pl: "Dołącz do globalnej społeczności freelancerów i e-commerce.",
    en: "Join the global community of freelancers and e-commerce.",
  },
  "cta.button": { pl: "Załóż darmowe konto", en: "Create a free account" },

  // Auth
  "auth.login.title": { pl: "Zaloguj się", en: "Sign in" },
  "auth.register.title": { pl: "Utwórz konto", en: "Create account" },
  "auth.email": { pl: "Email", en: "Email" },
  "auth.password": { pl: "Hasło", en: "Password" },
  "auth.firstName": { pl: "Imię", en: "First name" },
  "auth.lastName": { pl: "Nazwisko", en: "Last name" },
  "auth.company": { pl: "Firma", en: "Company" },
  "auth.role": { pl: "Jestem…", en: "I am…" },
  "auth.role.client": { pl: "Zleceniodawcą (e-commerce / dropshipping)", en: "A client (e-commerce / dropshipping)" },
  "auth.role.freelancer": { pl: "Freelancerem / dostawcą usług", en: "A freelancer / service provider" },
  "auth.referral": { pl: "Kod polecający (opcjonalnie)", en: "Referral code (optional)" },
  "auth.login.btn": { pl: "Zaloguj", en: "Sign in" },
  "auth.register.btn": { pl: "Zarejestruj się", en: "Create account" },
  "auth.noAccount": { pl: "Nie masz konta?", en: "No account yet?" },
  "auth.hasAccount": { pl: "Masz już konto?", en: "Already have an account?" },
  "auth.logout": { pl: "Wyloguj", en: "Log out" },
  "auth.passwordHint": {
    pl: "Minimum 8 znaków",
    en: "Minimum 8 characters",
  },
  "auth.forgotPassword": { pl: "Nie pamiętasz hasła?", en: "Forgot your password?" },
  "auth.forgotPassword.title": { pl: "Reset hasła", en: "Reset password" },
  "auth.forgotPassword.desc": {
    pl: "Podaj e-mail — wyślemy link do zresetowania hasła.",
    en: "Enter your email — we'll send a password reset link.",
  },
  "auth.forgotPassword.submit": { pl: "Wyślij link", en: "Send reset link" },
  "auth.forgotPassword.sent": {
    pl: "Jeśli ten e-mail jest zarejestrowany, link do resetu został wysłany.",
    en: "If that email is registered, a reset link has been sent.",
  },
  "auth.resetPassword.title": { pl: "Ustaw nowe hasło", en: "Set a new password" },
  "auth.resetPassword.new": { pl: "Nowe hasło", en: "New password" },
  "auth.resetPassword.submit": { pl: "Zapisz nowe hasło", en: "Save new password" },
  "auth.resetPassword.success": { pl: "Hasło zaktualizowane — możesz się zalogować.", en: "Password updated — you can now sign in." },
  "auth.resetPassword.invalid": { pl: "Link jest nieprawidłowy lub wygasł.", en: "This link is invalid or has expired." },
  "auth.backToLogin": { pl: "Wróć do logowania", en: "Back to sign in" },
  "auth.verifyEmail.title": { pl: "Weryfikacja e-mail", en: "Email verification" },
  "auth.verifyEmail.verifying": { pl: "Weryfikowanie…", en: "Verifying…" },
  "auth.verifyEmail.success": { pl: "E-mail zweryfikowany!", en: "Email verified!" },
  "auth.verifyEmail.invalid": { pl: "Link weryfikacyjny jest nieprawidłowy lub wygasł.", en: "This verification link is invalid or has expired." },
  "auth.verifyEmail.notVerified": { pl: "E-mail niezweryfikowany", en: "Email not verified" },
  "auth.verifyEmail.resend": { pl: "Wyślij ponownie link weryfikacyjny", en: "Resend verification email" },
  "auth.verifyEmail.resent": { pl: "Wysłano link weryfikacyjny — sprawdź skrzynkę.", en: "Verification email sent — check your inbox." },

  // RODO consent
  "auth.rodo.consent": { pl: "Wyrażam zgodę na przetwarzanie moich danych osobowych zgodnie z Polityką Prywatności", en: "I consent to the processing of my personal data in accordance with the Privacy Policy" },
  "auth.rodo.privacyLink": { pl: "Polityką Prywatności", en: "Privacy Policy" },
  "auth.rodo.and": { pl: "oraz", en: "and" },
  "auth.rodo.termsLink": { pl: "Regulaminem", en: "Terms of Service" },
  "auth.rodo.required": { pl: "Zgoda na RODO jest wymagana do rejestracji.", en: "GDPR consent is required to register." },

  // Dashboard
  "dash.title": { pl: "Panel", en: "Dashboard" },
  "dash.welcome": { pl: "Witaj", en: "Welcome" },
  "dash.client": { pl: "Panel zleceniodawcy", en: "Client dashboard" },
  "dash.freelancer": { pl: "Panel freelancera", en: "Freelancer dashboard" },
  "dash.myJobs": { pl: "Moje zlecenia", en: "My jobs" },
  "dash.myMatches": { pl: "Moje matchy", en: "My matches" },
  "dash.recommended": { pl: "Polecane zlecenia", en: "Recommended jobs" },
  "dash.stat.jobs": { pl: "Zlecenia", en: "Jobs" },
  "dash.stat.active": { pl: "Aktywne", en: "Active" },
  "dash.stat.completed": { pl: "Zakończone", en: "Completed" },
  "dash.stat.spent": { pl: "Wydano", en: "Spent" },
  "dash.stat.earned": { pl: "Zarobiono", en: "Earned" },
  "dash.stat.matches": { pl: "Matchy", en: "Matches" },
  "dash.stat.pending": { pl: "Oczekujące", en: "Pending" },
  "dash.stat.rating": { pl: "Ocena", en: "Rating" },
  "dash.stat.month": { pl: "Zleceń w tym miesiącu", en: "Jobs this month" },
  "dash.createFirst": {
    pl: "Opublikuj pierwsze zlecenie",
    en: "Post your first job",
  },
  "dash.findJobs": {
    pl: "Zobacz polecane zlecenia",
    en: "Browse recommended jobs",
  },
  "dash.emptyJobs": { pl: "Brak zleceń", en: "No jobs yet" },
  "dash.emptyMatches": { pl: "Brak matchy", en: "No matches yet" },
  "dash.recentJobs": { pl: "Ostatnie zlecenia", en: "Recent jobs" },
  "dash.recentMatches": { pl: "Ostatnie matchy", en: "Recent matches" },
  "dash.revenue": { pl: "Przychód platformy", en: "Platform revenue" },

  // Jobs
  "jobs.title": { pl: "Zlecenia", en: "Jobs" },
  "jobs.browse": { pl: "Przeglądaj zlecenia", en: "Browse jobs" },
  "jobs.new": { pl: "Nowe zlecenie", en: "New job" },
  "jobs.detail": { pl: "Szczegóły zlecenia", en: "Job details" },
  "jobs.titleLabel": { pl: "Tytuł", en: "Title" },
  "jobs.desc": { pl: "Opis", en: "Description" },
  "jobs.descPlaceholder": {
    pl: "Opisz dokładnie czego potrzebujesz…",
    en: "Describe exactly what you need…",
  },
  "jobs.category": { pl: "Kategoria", en: "Category" },
  "jobs.budget": { pl: "Budżet (PLN)", en: "Budget (PLN)" },
  "jobs.deadline": { pl: "Termin", en: "Deadline" },
  "jobs.location": { pl: "Lokalizacja", en: "Location" },
  "jobs.skills": { pl: "Wymagane umiejętności", en: "Required skills" },
  "jobs.skillsHint": {
    pl: "Oddziel przecinkami, np. photography, retouching",
    en: "Comma separated, e.g. photography, retouching",
  },
  "jobs.post": { pl: "Opublikuj zlecenie", en: "Post job" },
  "jobs.ai.willAnalyze": {
    pl: "AI automatycznie przeanalizuje zlecenie i znajdzie najlepszych wykonawców.",
    en: "AI will automatically analyze the job and find the best freelancers.",
  },
  "jobs.status.open": { pl: "Otwarte", en: "Open" },
  "jobs.status.matched": { pl: "Dopasowane", en: "Matched" },
  "jobs.status.in_progress": { pl: "W realizacji", en: "In progress" },
  "jobs.status.completed": { pl: "Zakończone", en: "Completed" },
  "jobs.status.cancelled": { pl: "Anulowane", en: "Cancelled" },
  "jobs.search": { pl: "Szukaj zleceń…", en: "Search jobs…" },
  "jobs.allCategories": { pl: "Wszystkie kategorie", en: "All categories" },
  "jobs.matches": { pl: "Matchy", en: "Matches" },
  "jobs.noMatches": {
    pl: "AI jeszcze nie znalazło wykonawców. Sprawdź później.",
    en: "AI hasn't found freelancers yet. Check back soon.",
  },
  "jobs.retrigger": { pl: "Wygeneruj ponownie", en: "Re-run matching" },
  "jobs.complete": { pl: "Zakończ zlecenie", en: "Complete job" },
  "jobs.client": { pl: "Zleceniodawca", en: "Client" },
  "jobs.rating": { pl: "Ocena", en: "Rating" },

  // Matches
  "match.score": { pl: "Dopasowanie", en: "Match score" },
  "match.accept": { pl: "Akceptuj", en: "Accept" },
  "match.reject": { pl: "Odrzuć", en: "Decline" },
  "match.budget": { pl: "Budżet", en: "Budget" },
  "match.deadline": { pl: "Termin", en: "Deadline" },
  "match.location": { pl: "Lokalizacja", en: "Location" },
  "match.accepted": { pl: "Zaakceptowane", en: "Accepted" },
  "match.rejected": { pl: "Odrzucone", en: "Rejected" },
  "match.pending": { pl: "Oczekujące", en: "Pending" },
  "match.hourly": { pl: "stawka", en: "rate" },
  "match.viewProfile": { pl: "Profil", en: "Profile" },

  // Contracts
  "contracts.title": { pl: "Kontrakty", en: "Contracts" },
  "contracts.none": { pl: "Brak kontraktów", en: "No contracts" },
  "contracts.amount": { pl: "Kwota", en: "Amount" },
  "contracts.fee": { pl: "Prowizja", en: "Fee" },
  "contracts.pay": { pl: "Zapłać", en: "Pay" },
  "contracts.markComplete": { pl: "Oznacz jako zakończone", en: "Mark complete" },
  "contracts.status.in_progress": { pl: "W realizacji", en: "In progress" },
  "contracts.status.completed": { pl: "Zakończony", en: "Completed" },
  "contracts.status.cancelled": { pl: "Anulowany", en: "Cancelled" },
  "contracts.status.disputed": { pl: "W sporze", en: "Disputed" },

  // Profile
  "profile.title": { pl: "Mój profil", en: "My profile" },
  "profile.bio": { pl: "O mnie", en: "Bio" },
  "profile.skills": { pl: "Umiejętności", en: "Skills" },
  "profile.languages": { pl: "Języki", en: "Languages" },
  "profile.hourlyRate": { pl: "Stawka godzinowa (PLN)", en: "Hourly rate (PLN)" },
  "profile.availability": { pl: "Dostępność", en: "Availability" },
  "profile.available": { pl: "Dostępny", en: "Available" },
  "profile.busy": { pl: "Zajęty", en: "Busy" },
  "profile.save": { pl: "Zapisz zmiany", en: "Save changes" },
  "profile.saved": { pl: "Zapisano!", en: "Saved!" },
  "profile.referral": { pl: "Twój kod polecający", en: "Your referral code" },
  "profile.plan": { pl: "Plan", en: "Plan" },
  "profile.rating": { pl: "Ocena", en: "Rating" },

  // Admin
  "admin.title": { pl: "Panel administratora", en: "Admin panel" },
  "admin.users": { pl: "Użytkownicy", en: "Users" },
  "admin.freelancers": { pl: "Freelancerzy", en: "Freelancers" },
  "admin.clients": { pl: "Zleceniodawcy", en: "Clients" },
  "admin.jobs": { pl: "Zlecenia", en: "Jobs" },
  "admin.openJobs": { pl: "Otwarte zlecenia", en: "Open jobs" },
  "admin.matches": { pl: "Matchy", en: "Matches" },
  "admin.contracts": { pl: "Kontrakty", en: "Contracts" },
  "admin.revenue": { pl: "Przychód", en: "Revenue" },
  "admin.forbidden": { pl: "Brak dostępu.", en: "Forbidden." },

  // Matches / Jobs actions
  "matches.contractCreated": { pl: "Kontrakt utworzony!", en: "Contract created!" },
  "matches.declined": { pl: "Match odrzucony", en: "Match declined" },
  "matches.answerAll": { pl: "Odpowiedz na wszystkie pytania", en: "Answer all questions" },
  "matches.interviewSubmitted": { pl: "Interview wysłane — AI oceniło Twoje odpowiedzi!", en: "Interview submitted — AI scored your answers!" },
  "matches.enterPrice": { pl: "Podaj prawidłową cenę", en: "Enter a valid price" },
  "matches.priceProposal": { pl: "Propozycja ceny wysłana do klienta", en: "Price proposal sent to the client" },

  // Jobs detail
  "jobs.completed": { pl: "Zlecenie zakończone", en: "Job completed" },
  "jobs.describeWork": { pl: "Opisz wykonaną pracę", en: "Describe the delivered work" },
  "jobs.qaReport": { pl: "Raport AI QA:", en: "AI QA report:" },

  // Contracts actions
  "contracts.milestoneSubmitted": { pl: "Milestone przesłany", en: "Milestone submitted" },
  "contracts.paymentReleased": { pl: "Płatność zwolniona", en: "Payment released" },
  "contracts.refundIssued": { pl: "Zwrot wystawiony", en: "Refund issued" },

  // Freelancers
  "freelancers.searchPlaceholder": { pl: "Szukaj po umiejętnościach…", en: "Search by skills…" },
  "freelancers.none": { pl: "Nie znaleziono freelancerów.", en: "No freelancers found." },

  // Profile
  "profile.country": { pl: "Kraj", en: "Country" },
  "profile.reviews": { pl: "opinii", en: "reviews" },
  "profile.shareReferral": { pl: "Udostępnij ten kod — znajomi dostają darmowy PRO trial.", en: "Share this code — friends get free PRO trial." },

  // Jobs new
  "jobs.onlyClients": { pl: "Tylko klienci mogą tworzyć zlecenia.", en: "Only clients can post jobs." },

  // Notifications
  "notif.title": { pl: "Powiadomienia", en: "Notifications" },
  "notif.empty": { pl: "Brak powiadomień", en: "No notifications" },
  "notif.readAll": { pl: "Oznacz jako przeczytane", en: "Mark all read" },

  // Common
  "common.loading": { pl: "Ładowanie…", en: "Loading…" },
  "common.error": { pl: "Błąd", en: "Error" },
  "common.back": { pl: "Wstecz", en: "Back" },
  "common.save": { pl: "Zapisz", en: "Save" },
  "common.cancel": { pl: "Anuluj", en: "Cancel" },
  "common.search": { pl: "Szukaj", en: "Search" },
  "common.view": { pl: "Zobacz", en: "View" },
  "common.delete": { pl: "Usuń", en: "Delete" },
  "common.close": { pl: "Zamknij", en: "Close" },
  "common.pln": { pl: "PLN", en: "PLN" },
  "common.currency": { pl: "zł", en: "PLN" },
  "common.all": { pl: "Wszystko", en: "All" },
  "common.language": { pl: "Język", en: "Language" },
  "common.remote": { pl: "Zdalnie", en: "Remote" },
  "common.verified": { pl: "Zweryfikowany", en: "Verified" },
  "common.required": { pl: "Wymagane", en: "Required" },

  // Footer
  "footer.rights": { pl: "Wszystkie prawa zastrzeżone.", en: "All rights reserved." },
  "footer.platform": { pl: "Platforma", en: "Platform" },
  "footer.legal": { pl: "Prawne", en: "Legal" },
  "footer.regulamin": { pl: "Regulamin", en: "Terms of Service" },
  "footer.privacy": { pl: "Polityka prywatności", en: "Privacy Policy" },
};

const LangContext = createContext<{
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}>({
  lang: "pl",
  setLang: () => {},
  t: (key: string) => key,
});

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("pl");

  useEffect(() => {
    let active = true;
    (async () => {
      const saved = localStorage.getItem("dropify_lang") as Lang | null;
      if (saved === "pl" || saved === "en") {
        if (active) setLangState(saved);
      } else {
        const nav = navigator.language?.toLowerCase() || "";
        if (active) setLangState(nav.startsWith("pl") ? "pl" : "en");
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    localStorage.setItem("dropify_lang", l);
  }, []);

  const t = useCallback(
    (key: string) => {
      const entry = DICT[key];
      if (!entry) return key;
      return entry[lang];
    },
    [lang]
  );

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang() {
  return useContext(LangContext);
}
