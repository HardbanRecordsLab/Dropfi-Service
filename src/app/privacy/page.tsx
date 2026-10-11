import LegalSummary from "@/components/LegalSummary";

export default function PrivacyPage() {
  return (
    <LegalSummary
      title="Polityka prywatności"
      points={[
        "Administrator: Kamil Skomra (HardbanRecords Lab), kontakt w sprawach danych: legal@hardbanrecordslab.online.",
        "Przetwarzamy dane konta, profilu, ogłoszeń i ofert oraz dane techniczne (adres IP, logi) potrzebne do bezpieczeństwa.",
        "Dopasowanie ogłoszeń i ocena profili korzystają z AI przez OpenRouter, wyłącznie u dostawców, którzy nie przechowują i nie trenują na danych. Ocena nie blokuje automatycznie konta ani zlecenia — decyduje człowiek.",
        "Wiadomości marketingowe wysyłamy tylko za Twoją zgodą; możesz ją wycofać w każdej chwili.",
        "Masz prawo dostępu, sprostowania, usunięcia, ograniczenia, przenoszenia danych, sprzeciwu i skargi do Prezesa UODO.",
      ]}
    />
  );
}
