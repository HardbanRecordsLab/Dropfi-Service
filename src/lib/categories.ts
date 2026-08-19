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
];
