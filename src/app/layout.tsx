import type { Metadata, Viewport } from "next";
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

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://dropify.hardbanrecordslab.online";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "DROPIFY | AI Job Matching Platform for Freelancers & Businesses",
  description:
    "Automatyczne dopasowanie zleceń do najlepszych freelancerów dzięki AI — e-commerce, dropshipping, marketing, nieruchomości, muzyka i więcej. Automatic AI job matching for freelancers across e-commerce, dropshipping, marketing, real estate, music production and more. Polski + English.",
  manifest: "/manifest.webmanifest",
  // favicon.ico / icon.png / apple-icon.png in src/app/ are auto-detected by Next.
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
    url: SITE_URL,
    siteName: "DROPIFY",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "DROPIFY" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "DROPIFY | AI Job Matching Platform",
    description: "Global marketplace connecting jobs with top freelancers automatically.",
    images: ["/og-image.png"],
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0a0a",
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
