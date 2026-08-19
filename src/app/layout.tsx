import type { Metadata } from "next";
import { Outfit, Playfair_Display } from "next/font/google";
import { LangProvider } from "@/lib/i18n";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin", "latin-ext"],
  variable: "--font-outfit",
});

const playfair = Playfair_Display({
  subsets: ["latin", "latin-ext"],
  variable: "--font-playfair",
});

export const metadata: Metadata = {
  title: "DROPIFY | AI Job Matching Platform for Freelancers & Businesses",
  description:
    "Automatyczne dopasowanie zleceń do najlepszych freelancerów dzięki AI — e-commerce, dropshipping, marketing, nieruchomości, muzyka i więcej. Automatic AI job matching for freelancers across e-commerce, dropshipping, marketing, real estate, music production and more. Polski + English.",
  keywords: [
    "dropshipping",
    "freelance matching",
    "AI matching",
    "e-commerce",
    "marketplace",
    "zlecenia",
    "dopasowanie zleceń",
    "real estate marketing",
    "music production",
    "white-label marketplace API",
  ],
  authors: [{ name: "DROPIFY" }],
  openGraph: {
    title: "DROPIFY | AI Job Matching Platform",
    description: "Global marketplace connecting jobs with top freelancers automatically.",
    type: "website",
    locale: "pl_PL",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl" className={`${outfit.variable} ${playfair.variable}`}>
      <body style={{ fontFamily: "var(--font-outfit), sans-serif" }}>
        <LangProvider>
          <AuthProvider>{children}</AuthProvider>
        </LangProvider>
      </body>
    </html>
  );
}
