import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://dropify.hardbanrecordslab.online";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/api/", "/admin", "/dashboard", "/profile", "/login", "/register", "/forgot-password", "/reset-password", "/factory", "/fees"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
