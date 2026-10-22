import LegalSummary from "@/components/LegalSummary";

export default function TermsPage() {
  return (
    <LegalSummary
      title={{ pl: "Regulamin", en: "Terms of Service" }}
      points={{
        pl: [
          "DROPIFY łączy zlecających z wykonawcami. Konto jest bezpłatne; możesz je usunąć w każdej chwili.",
          "Płatności i depozyt (escrow) nie są obecnie uruchomione — strony rozliczają się poza platformą i same odpowiadają za swoją umowę.",
          "Publikuj tylko prawdziwe ogłoszenia i profile. Nie wolno zamieszczać treści niezgodnych z prawem ani podszywać się pod inne osoby.",
          "Treść niezgodną z prawem zgłoś na legal@hardbanrecordslab.online, podając jej adres i powód — rozpatrzymy zgłoszenie niezwłocznie.",
          "Reklamacje: legal@hardbanrecordslab.online — odpowiadamy w ciągu 14 dni.",
        ],
        en: [
          "DROPIFY connects clients with contractors. An account is free and you can delete it at any time.",
          "Payments and escrow are not currently live — the parties settle outside the platform and are responsible for their own agreement.",
          "Publish only genuine listings and profiles. Unlawful content and impersonating other people are not allowed.",
          "Report unlawful content to legal@hardbanrecordslab.online, giving its address and the reason — we will consider the report without delay.",
          "Complaints: legal@hardbanrecordslab.online — we reply within 14 days.",
        ],
      }}
    />
  );
}
