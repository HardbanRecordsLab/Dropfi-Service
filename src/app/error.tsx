"use client";

import { useEffect } from "react";
import { Btn } from "@/components/ui";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
      }}
    >
      <div style={{ textAlign: "center", maxWidth: "500px" }}>
        <div
          style={{
            fontSize: "4rem",
            fontWeight: "900",
            lineHeight: "1",
            marginBottom: "1rem",
          }}
          className="gold-gradient-text"
        >
          !
        </div>
        <h1 style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>
          Coś poszło nie tak
        </h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem", marginBottom: "2rem" }}>
          Wystąpił nieoczekiwany błąd. Spróbuj ponownie lub wróć na stronę główną.
        </p>
        <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
          <Btn onClick={reset}>Spróbuj ponownie</Btn>
          <Btn variant="outline" onClick={() => (window.location.href = "/")}>
            Strona główna
          </Btn>
        </div>
        {error.digest && (
          <p style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginTop: "2rem" }}>
            Error ID: {error.digest}
          </p>
        )}
      </div>
    </main>
  );
}
