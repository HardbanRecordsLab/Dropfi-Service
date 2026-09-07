"use client";

import PortalNav from "@/components/PortalNav";
import Footer from "@/components/Footer";

export default function PrivacyPage() {
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
            Polityka Prywatnosci / Privacy Policy
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Ostatnia aktualizacja: 23 sierpień 2026 · Wersja 1.0
          </p>
        </div>
      </section>

      <section style={{ padding: "2rem 2rem 6rem" }}>
        <div style={{ maxWidth: "800px", margin: "0 auto" }} className="premium-card">
          <div style={{ padding: "3rem", lineHeight: "1.8", color: "var(--text-secondary)" }}>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>1. Administrator danych</h2>
            <p>
              Administratorem danych osobowych zbieranych za posrednictwem platformy DROPIFY jest:
            </p>
            <p>
              <strong>HardbanRecords Lab</strong><br />
              Wiercień, Polska<br />
              Email: <a href="mailto:dropify@hardbanrecordslab.online" style={{ color: "var(--accent-gold)" }}>dropify@hardbanrecordslab.online</a>
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>2. Jakie dane zbieramy</h2>
            <p>Zbieramy nastepujace kategorie danych osobowych:</p>
            <ul style={{ paddingLeft: "1.5rem" }}>
              <li><strong>Dane konta:</strong> imie, nazwisko, adres email, haslo (szyfrowane bcrypt), rola (klient/freelancer/admin)</li>
              <li><strong>Dane profilu:</strong> opis, umiejetnosci, stawki, portfolio, zdjecie profilowe</li>
              <li><strong>Dane transakcji:</strong> historia zlecen, kontraktow, platnosci, ocen</li>
              <li><strong>Dane techniczne:</strong> adres IP, przegladarka, device ID, logi dostepu</li>
              <li><strong>Dane platnosci:</strong> przetwarzane przez Stripe — nie przechowujemy numerow kart platniczych</li>
            </ul>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>3. W jakim celu przetwarzamy dane</h2>
            <ul style={{ paddingLeft: "1.5rem" }}>
              <li>Realizacja uslug Platformy (dostarczanie, matching, rozliczania)</li>
              <li>Zarzadzanie kontem uzytkownika i uwierzytelnianie</li>
              <li>Komunikacja dotyczaca zlecen, matchy i transakcji</li>
              <li>Analiza i ulepszanie dzialania Platformy (AI matching, raporty)</li>
              <li>Wysylanie powiadomien email (transakcyjne i marketingowe — za zgoda)</li>
              <li>Wypelnianie obowiazkow prawnych (faktury, podatki)</li>
            </ul>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>4. Podstawa prawna przetwarzania</h2>
            <ul style={{ paddingLeft: "1.5rem" }}>
              <li><strong>Art. 6 ust. 1 lit. b RODO</strong> — przetwarzanie niezbedne do wykonania umowy (korzystanie z Platformy)</li>
              <li><strong>Art. 6 ust. 1 lit. a RODO</strong> — zgoda uzytkownika (newsletter, marketing)</li>
              <li><strong>Art. 6 ust. 1 lit. f RODO</strong> — uzasadniony interes administratora (analiza, bezpieczenstwo, rozwijanie Platformy)</li>
              <li><strong>Art. 6 ust. 1 lit. c RODO</strong> — obowiazek prawny (faktury, rozliczenia podatkowe)</li>
            </ul>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>5. Komu udostepniamy dane</h2>
            <ul style={{ paddingLeft: "1.5rem" }}>
              <li><strong>Stripe Inc.</strong> — przetwarzanie platnosci (USA, RODO: SCC)</li>
              <li><strong>Anthropic / OpenAI</strong> — przetwarzanie danych tekstowych przez AI (analityka zlecen, matching)</li>
              <li><strong>Hosting (Vercel / VPS)</strong> — przechowywanie danych technicznych</li>
              <li><strong>Organy panstwowe</strong> — na podstawie obowiazujacego prawa</li>
            </ul>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>6. Przekazywanie danych poza EOG</h2>
            <p>
              Czesc dostawcow (Stripe, Anthropic, OpenAI) moze przetwarzac dane poza Europejskim Obszarem Gospodarczym.
              W takich przypadkach stosujemy Standardowe Klauzule Umowne (SCC) lub inne mechanizmy zgodnosci z RODO.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>7. Okres przechowywania danych</h2>
            <ul style={{ paddingLeft: "1.5rem" }}>
              <li><strong>Dane konta:</strong> do momentu usuniecia konta lub 3 lata od ostatniej aktywnosci</li>
              <li><strong>Dane transakcji:</strong> 5 lat (obowiazek podatkowy/księgowy)</li>
              <li><strong>Logi dostepu:</strong> 12 miesiecy</li>
              <li><strong>Dane marketingowe:</strong> do wycofania zgody</li>
            </ul>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>8. Twoje prawa</h2>
            <p>Zgodnie z RODO przysluguja Ci nastepujace prawa:</p>
            <ul style={{ paddingLeft: "1.5rem" }}>
              <li><strong>Prawo dostepu</strong> do swoich danych osobowych</li>
              <li><strong>Prawo sprostowania</strong> nieprawidlowych danych</li>
              <li><strong>Prawo usuniecia</strong> (&quot;prawo do zapomnienia&quot;)</li>
              <li><strong>Prawo ograniczenia</strong> przetwarzania</li>
              <li><strong>Prawo przenoszenia</strong> danych do innego administratora</li>
              <li><strong>Prawo wniesienia skargi</strong> do Prezesa UODO (uodo.gov.pl)</li>
              <li><strong>Prawo cofniecia zgody</strong> w dowolnym momencie</li>
            </ul>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>9. Bezpieczenstwo danych</h2>
            <p>
              Stosujemy odpowiednie srodki techniczne i organizacyjne w celu ochrony danych osobowych,
              w tym: szyfrowanie bcrypt (hasla), HTTPS/TLS, JWT z wygasaniem, rate limiting w nginx,
              RBAC (role-based access control), regularne kopie zapasowe bazy danych.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>10. Cookies i technologie sledzace</h2>
            <p>
              Platforma uzywa cookies niezbednych do dzialania (sesja JWT, preferencje jezykowe).
              Nie uzywamy cookies sledzacych ani reklamowych stron trzecich.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>11. Zmiany w Polityce Prywatnosci</h2>
            <p>
              Zastrzegamy sobie prawo do zmiany niniejszej Polityki Prywatnosci. O istotnych zmianach
              uzytkownicy zostana powiadomieni droga elektroniczna (email) z wyprzedzeniem min. 7 dni.
            </p>

            <h2 style={{ color: "var(--text-primary)", fontSize: "1.3rem", marginTop: "2rem", marginBottom: "1rem" }}>12. Kontakt</h2>
            <p>
              W sprawach dotyczacych ochrony danych osobowych prosimy o kontakt:
            </p>
            <p>
              <strong>HardbanRecords Lab</strong><br />
              Email: <a href="mailto:dropify@hardbanrecordslab.online" style={{ color: "var(--accent-gold)" }}>dropify@hardbanrecordslab.online</a><br />
              Wiercień, Polska
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
