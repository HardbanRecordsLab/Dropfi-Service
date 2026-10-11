import LegalSummary from "@/components/LegalSummary";

export default function TermsPage() {
  return (
    <LegalSummary
      title="Regulamin"
      points={[
        "DROPIFY łączy zlecających z wykonawcami. Konto jest bezpłatne; możesz je usunąć w każdej chwili.",
        "Płatności i depozyt (escrow) nie są obecnie uruchomione — strony rozliczają się poza platformą i same odpowiadają za swoją umowę.",
        "Publikuj tylko prawdziwe ogłoszenia i profile. Nie wolno zamieszczać treści niezgodnych z prawem ani podszywać się pod inne osoby.",
        "Treść niezgodną z prawem zgłoś na legal@hardbanrecordslab.online, podając jej adres i powód — rozpatrzymy zgłoszenie niezwłocznie.",
        "Reklamacje: legal@hardbanrecordslab.online — odpowiadamy w ciągu 14 dni.",
      ]}
    />
  );
}
