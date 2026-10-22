import LegalSummary from "@/components/LegalSummary";

export default function PrivacyPage() {
  return (
    <LegalSummary
      title={{ pl: "Polityka prywatności", en: "Privacy Policy" }}
      points={{
        pl: [
          "Administrator: Kamil Skomra (HardbanRecords Lab), kontakt w sprawach danych: legal@hardbanrecordslab.online.",
          "Przetwarzamy dane konta, profilu, ogłoszeń i ofert oraz dane techniczne (adres IP, logi) potrzebne do bezpieczeństwa.",
          "Dopasowanie ogłoszeń i ocena profili korzystają z AI przez OpenRouter, wyłącznie u dostawców, którzy nie przechowują i nie trenują na danych. Ocena nie blokuje automatycznie konta ani zlecenia — decyduje człowiek.",
          "Wiadomości marketingowe wysyłamy tylko za Twoją zgodą; możesz ją wycofać w każdej chwili.",
          "Masz prawo dostępu, sprostowania, usunięcia, ograniczenia, przenoszenia danych, sprzeciwu i skargi do Prezesa UODO.",
        ],
        en: [
          "Controller: Kamil Skomra (HardbanRecords Lab); contact for data matters: legal@hardbanrecordslab.online.",
          "We process account, profile, listing and offer data, plus the technical data (IP address, logs) needed for security.",
          "Listing matching and profile assessment use AI through OpenRouter, only with providers that neither store data nor train on it. The assessment never blocks an account or a job automatically — a human decides.",
          "We send marketing messages only with your consent; you can withdraw it at any time.",
          "You have the right of access, rectification, erasure, restriction, portability, objection and the right to complain to the President of the Polish Personal Data Protection Office (UODO).",
        ],
      }}
    />
  );
}
