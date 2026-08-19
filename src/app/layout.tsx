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
  title: "DROPIFY | AI Job Matching Platform for Freelancers & E-commerce",
  description:
    "Automatyczne dopasowanie zleceń e-commerce i dropshippingu do najlepszych freelancerów dzięki AI. Automatic AI job matching for freelancers, e-commerce and dropshipping. Polski + English.",
  keywords: [
    "dropshipping",
    "freelance matching",
    "AI matching",
    "e-commerce",
    "marketplace",
    "zlecenia",
    "dopasowanie zleceń",
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
