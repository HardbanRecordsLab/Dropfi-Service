import type { Metadata, Viewport } from "next";
import { Outfit, Playfair_Display } from "next/font/google";
import Script from "next/script";
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
    "Automatic AI job matching for freelancers and businesses: e-commerce, dropshipping, marketing, real estate, music and more. Honest 8% flat fee, no hidden costs.",
  manifest: "/manifest.webmanifest",
  alternates: { canonical: "/" },
  // favicon.ico / icon.png / apple-icon.png in src/app/ are auto-detected by Next.
  keywords: [
    "dropshipping",
    "freelance matching",
    "AI matching",
    "e-commerce",
    "marketplace",
    "real estate marketing",
    "music production",
    "white-label marketplace API",
  ],
  authors: [{ name: "DROPIFY" }],
  openGraph: {
    title: "DROPIFY | AI Job Matching Platform",
    description: "Global marketplace connecting jobs with top freelancers automatically.",
    type: "website",
    locale: "en_US",
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
    <html lang="en" className={`${outfit.variable} ${playfair.variable}`}>
      <body style={{ fontFamily: "var(--font-outfit), sans-serif" }}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({"@context":"https://schema.org","@graph":[{"@type":"Organization","@id":"https://hardbanrecordslab.online/#org","name":"HardbanRecords Lab","url":"https://hardbanrecordslab.online/","logo":{"@type":"ImageObject","url":"https://dropify.hardbanrecordslab.online/icon-512.png"}},{"@type":"WebApplication","name":"DROPIFY","url":"https://dropify.hardbanrecordslab.online/","image":"https://dropify.hardbanrecordslab.online/og-image.png","logo":"https://dropify.hardbanrecordslab.online/icon-512.png","applicationCategory":"BusinessApplication","operatingSystem":"Web","publisher":{"@id":"https://hardbanrecordslab.online/#org"}}]}) }} />
        <LangProvider>
          <AuthProvider>{children}</AuthProvider>
        </LangProvider>
        <Script src="https://hardbanrecordslab.online/lp/shared/hrl-analytics.js?v=1" strategy="afterInteractive" />
      </body>
    </html>
  );
}
