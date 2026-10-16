// Single source of truth for job categories, mirroring backend/app/utils/ai.py::CATEGORIES.
// Tier-2 verticals added per doku/MEGA_PLATFORM_BLUEPRINT.md §11 — same AI matching/
// escrow engine, just recognized categories so jobs route correctly instead of
// falling through to "Other".
export const CATEGORIES = [
  "Photography",
  "Coding",
  "Design",
  "Writing",
  "Marketing",
  "Video & Animation",
  "E-commerce",
  "Translation",
  "Consulting",
  "Real Estate",
  "Audio & Podcast",
  "Publishing",
  "Events",
  "Music Production",
  "Data & AI Services",
  "Accounting & Finance",
  "Legal",
  "Admin & Virtual Assistant",
  "Customer Support",
  "Engineering & Architecture",
  "Education & Tutoring",
  "HR & Recruitment",
  "Sales & Lead Generation",
  "Health & Fitness",
  "Construction & Renovation",
  "Logistics & Supply Chain",
];

const PL_LABELS: Record<string, string> = {
  Photography: "Fotografia",
  Coding: "Programowanie",
  Design: "Projektowanie graficzne",
  Writing: "Teksty i copywriting",
  Marketing: "Marketing",
  "Video & Animation": "Wideo i animacja",
  "E-commerce": "E-commerce",
  Translation: "Tłumaczenia",
  Consulting: "Doradztwo",
  "Real Estate": "Nieruchomości",
  "Audio & Podcast": "Audio i podcasty",
  Publishing: "Wydawnictwo",
  Events: "Wydarzenia",
  "Music Production": "Produkcja muzyczna",
  "Data & AI Services": "Dane i AI",
  "Accounting & Finance": "Księgowość i finanse",
  "Legal": "Prawo",
  "Admin & Virtual Assistant": "Administracja i asystent",
  "Customer Support": "Obsługa klienta",
  "Engineering & Architecture": "Inżynieria i architektura",
  "Education & Tutoring": "Edukacja i korepetycje",
  "HR & Recruitment": "HR i rekrutacja",
  "Sales & Lead Generation": "Sprzedaż i leady",
  "Health & Fitness": "Zdrowie i fitness",
  "Construction & Renovation": "Budownictwo i remonty",
  "Logistics & Supply Chain": "Logistyka",
  Other: "Inne",
};

export function categoryLabel(category: string, lang: "pl" | "en"): string {
  return lang === "pl" ? PL_LABELS[category] ?? category : category;
}
