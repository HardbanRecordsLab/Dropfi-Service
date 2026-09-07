"use client";

import PortalNav from "@/components/PortalNav";
import Footer from "@/components/Footer";

export default function TermsPage() {
  return (
    <main style={{ minHeight: "100vh" }}>
      <PortalNav />

      <section
        style={{
          padding: "6rem 2rem 4rem",
          background: "radial-gradient(ellipse at top, rgba(197,160,89,0.12) 0%, transparent 60%)",
        }}
      >
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", marginBottom: "1rem" }}>
            LEGAL
          </div>
          <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: "1rem" }} className="gold-gradient-text">
            Regulamin / Terms of Service
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Ostatnia aktualizacja: 23 sierpień 2026 · Wersja 1.0
          </p>
        </div>
      </section>

      <section style={{ padding: "2rem 2rem 6rem" }}>
        <div style={{ maxWidth: "800px", margin: "0 auto" }} className="premium-card" data-style={{ padding: "3rem" }}>
          <div style={{ padding: "3rem", lineHeight: "1.8", color: "var(--text-secondary)" }}>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§1 Postanowienia ogolne</h2>
            <p>
              Niniejszy Regulamin okresla zasady korzystania z platformy DROPIFY (dalej: &quot;Platforma&quot;),
              dostepnej pod adresem dropify.app, zarzadzanej przez HardbanRecords Lab z siedziba w Wiercieniu, Polska
              (dalej: &quot;Usługodawca&quot;).
            </p>
            <p>
              Platforma DROPIFY to marketplace B2B typu AI-powered job matching, ktory automatycznie dopasowuje
              zlecenia (e-commerce, dropshipping, uslugi cyfrowe) do freelancerow i dostawcow.
            </p>
            <p>
              Kontakt: <a href="mailto:dropify@hardbanrecordslab.online" style={{ color: "var(--accent-gold)" }}>dropify@hardbanrecordslab.online</a>
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§2 Definicje</h2>
            <ul style={{ paddingLeft: "1.5rem" }}>
              <li><strong>Platforma</strong> — serwis internetowy DROPIFY umozliwiajacy tworzenie zleceń, matching AI, zawieranie umow i rozliczania.</li>
              <li><strong>Uzytkownik</strong> — kazda osoba fizyczna lub prawna korzystajaca z Platformy.</li>
              <li><strong>Klient</strong> — uzytkownik tworzacy zlecenie i zamawiajacy uslugi.</li>
              <li><strong>Freelancer</strong> — uzytkownik realizujacy zlecenia za posrednictwem Platformy.</li>
              <li><strong>Match</strong> — automatyczne dopasowanie zlecenia do freelancera przez system AI.</li>
              <li><strong>Escrow</strong> — mechanizm zabezpieczenia srodkow finansowych do momentu potwierdzenia realizacji zlecenia.</li>
              <li><strong>Milestone</strong> — etap realizacji kontraktu z osobna platnoscia.</li>
            </ul>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§3 Konto uzytkownika</h2>
            <p>
              3.1. Korzystanie z Platformy wymaga założenia konta poprzez formularz rejestracji.
            </p>
            <p>
              3.2. Uzytkownik ponosi odpowiedzialnosc za prawdziwosc podanych danych i bezpieczenstwo swojego konta.
            </p>
            <p>
              3.3. Jeden uzytkownik moze posiadac tylko jedno konto na Platformie.
            </p>
            <p>
              3.4. Usługodawca zastrzega sobie prawo do zablokowania konta w przypadku naruszenia niniejszego Regulaminu.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§4 Tworzenie zlecen i matching AI</h2>
            <p>
              4.1. Klient tworzy zlecenie, podajac opis, kategorie, budzet i preferencje. System AI moze automatycznie
              wygenerowac pelny opis na podstawie podanych informacji lub linku do produktu.
            </p>
            <p>
              4.2. System AI automatycznie dopasowuje zlecenie do najbardziej odpowiednich freelancerow na podstawie
              kryteriow: zgodnosc semantyczna, ocena, dopasowanie ceny i dostepnosc.
            </p>
            <p>
              4.3. Klient otrzymuje top 3 matche i moze wybrac jednego freelancera lub odrzucic wszystkie
              (co triggeruje ponowny matching z wykluczeniem dotychczasowych kandydatow).
            </p>
            <p>
              4.4. Match AI nie stanowi gwarancji jakosci uslug — ostateczna decyzje podejmuje klient.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§5 Kontrakt i escrow</h2>
            <p>
              5.1. Po akceptacji matcha zawierana jest umowa miedzy Klientem a Freelancerem, okreslajaca
              zakres pracy, milestones (etapy) i platnosci.
            </p>
            <p>
              5.2. Klient zasila escrow kwota przewidziana na dany milestone. Srodki sa zablokowane do momentu
              potwierdzenia realizacji (recznie przez Klienta lub automatycznie po 48h ciszy).
            </p>
            <p>
              5.3. Freelancer moze zlozyc prace do weryfikacji. System AI QA generuje raport z checklista wymagan.
            </p>
            <p>
              5.4. Klient moze zatwierdzic realizacje, poprosic o poprawki lub odrzucic prace (z uzasadnieniem).
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§6 Prowizje i platnosci</h2>
            <p>
              6.1. Platforma pobiera prowizje od kazdej transakcji:
            </p>
            <ul style={{ paddingLeft: "1.5rem" }}>
              <li>Standardowa prowizja: 8% wartosci zlecenia</li>
              <li>Top-rated freelancerzy (ocena ≥ 4.8, min. 20 ocen): 5%</li>
              <li>Nowi freelancerzy (max. 3 oceny): 12%</li>
            </ul>
            <p>
              6.2. Platnosci realizowane sa przez Stripe Checkout. Platforma nie przechowuje danych platnosci.
            </p>
            <p>
              6.3. Wyplaty dla freelancerow realizowane sa przelewem bankowym lub w USDT/stablecoinach
              (według preferencji Freelancera).
            </p>
            <p>
              6.4. Zwroty (refunds) sa realizowane zgodnie z polityka zwrotow opisana w §8.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§7 Odpowiedzialnosc</h2>
            <p>
              7.1. Usługodawca nie jest strona umowy miedzy Klientem a Freelancerem — Platforma dziala jako posrednik.
            </p>
            <p>
              7.2. Usługodawca nie ponosi odpowiedzialnosci za jakosc uslug dostarczanych przez Freelancerow,
              terminowosc realizacji ani szkody wynikle ze wspolpracy miedzy stronami.
            </p>
            <p>
              7.3. Odpowiedzialnosc Usługodawcy jest ograniczona do wartosci prowizji pobranej od danej transakcji.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§8 Reklamacje i zwroty</h2>
            <p>
              8.1. Reklamacje nalezy zgłaszac na adres: <a href="mailto:dropify@hardbanrecordslab.online" style={{ color: "var(--accent-gold)" }}>dropify@hardbanrecordslab.online</a>
            </p>
            <p>
              8.2. Klient moze żądac zwrotu srodkow z escrow, jesli Freelancer nie zrealizowal zlecenia
              lub zrealizowal je niezgodnie z wymaganiami. Weryfikacja odbywa sie przez system AI QA
              lub recznie przez administratora.
            </p>
            <p>
              8.3. Prowizja platformy podlega zwrotowi w calosci, jesli transakcja zostala anulowana
              przed akceptacja matcha przez freelancera.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§9 Dane osobowe i RODO</h2>
            <p>
              9.1. Administratorem danych osobowych jest HardbanRecords Lab, Wiercień, Polska.
            </p>
            <p>
              9.2. Dane osobowe sa przetwarzane w celu realizacji uslug Platformy (art. 6 ust. 1 lit. b RODO)
              oraz na podstawie uzasadnionego interesu administratora (art. 6 ust. 1 lit. f RODO).
            </p>
            <p>
              9.3. Uzytkownik ma prawo do dostepu, sprostowania, usuniecia i ograniczenia przetwarzania danych,
              a takze prawo do przenoszenia danych i wniesienia skargi do organu nadzorczego.
            </p>
            <p>
              9.4. Szczegolowe informacje dotyczace przetwarzania danych osobowych zawiera
              Polityka Prywatnosci dostepna pod adresem <a href="/privacy" style={{ color: "var(--accent-gold)" }}>/privacy</a>.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>§10 Postanowienia koncowe</h2>
            <p>
              10.1. Regulamin wchodzi w zycie z dniem opublikowania. Usługodawca zastrzega sobie prawo
              do zmiany Regulaminu — o zmianach uzytkownicy zostana powiadomieni droga elektroniczna.
            </p>
            <p>
              10.2. W sprawach nieuregulowanych niniejszym Regulaminem zastosowanie maja przepisy
              prawa polskiego, w szczegolnosci Kodeksu cywilnego i Ustawy o prawach konsumenta.
            </p>
            <p>
              10.3. Ewentualne spory rozwiazywane beda polubownie, a w przypadku braku porozumienia —
              przez sad wlasciwy ze wzgledu na siedzibe Usługodawcy.
            </p>

            <div style={{ marginTop: "3rem", padding: "1.5rem", background: "rgba(197,160,89,0.06)", border: "1px dashed var(--border-gold)", borderRadius: "4px", fontSize: "0.85rem", color: "var(--text-muted)" }}>
              <strong style={{ color: "var(--accent-gold)" }}>HardbanRecords Lab</strong> · Wiercień, Polska ·{" "}
              <a href="mailto:dropify@hardbanrecordslab.online" style={{ color: "var(--accent-gold)" }}>dropify@hardbanrecordslab.online</a>
              <br />
              © 2026 DROPIFY — All rights reserved.
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
