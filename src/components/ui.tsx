"use client";

import { useState } from "react";

export const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-tertiary)",
  border: "1px solid var(--border-subtle)",
  padding: "1rem 1.2rem",
  color: "#fff",
  borderRadius: "4px",
  fontSize: "0.95rem",
  fontFamily: "inherit",
  outline: "none",
};

export const labelStyle: React.CSSProperties = {
  display: "block",
  fontSize: "0.75rem",
  fontWeight: "700",
  textTransform: "uppercase",
  color: "var(--text-muted)",
  marginBottom: "0.6rem",
  letterSpacing: "1px",
};

export function Btn({
  children,
  onClick,
  variant = "primary",
  disabled,
  type = "button",
  style,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "outline" | "ghost" | "danger";
  disabled?: boolean;
  type?: "button" | "submit";
  style?: React.CSSProperties;
}) {
  const base: React.CSSProperties = {
    padding: "0.9rem 2rem",
    fontWeight: "700",
    borderRadius: "4px",
    textTransform: "uppercase",
    letterSpacing: "1px",
    fontSize: "0.8rem",
    fontFamily: "inherit",
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.5 : 1,
    ...style,
  };
  const variants: Record<string, React.CSSProperties> = {
    primary: { background: "var(--accent-gold)", color: "#000" },
    outline: {
      background: "transparent",
      border: "1px solid var(--border-gold)",
      color: "var(--accent-gold)",
    },
    ghost: { background: "transparent", color: "var(--text-secondary)" },
    danger: { background: "#7f1d1d", color: "#fff" },
  };
  return (
    <button type={type} onClick={onClick} disabled={disabled} style={{ ...base, ...variants[variant] }}>
      {children}
    </button>
  );
}

export function StatCard({
  label,
  value,
  sub,
  icon,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon?: string;
}) {
  return (
    <div className="premium-card" style={{ position: "relative", overflow: "hidden" }}>
      {icon && (
        <div
          style={{
            position: "absolute",
            right: "-10px",
            top: "-10px",
            fontSize: "5rem",
            opacity: 0.03,
            fontWeight: "900",
          }}
        >
          {icon}
        </div>
      )}
      <div
        style={{
          color: "var(--text-muted)",
          fontSize: "0.72rem",
          textTransform: "uppercase",
          letterSpacing: "2px",
          marginBottom: "1rem",
        }}
      >
        {label}
      </div>
      <div
        style={{ fontSize: "2.2rem", fontWeight: "800", marginBottom: "0.4rem" }}
        className="gold-gradient-text"
      >
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", fontWeight: "300" }}>{sub}</div>
      )}
    </div>
  );
}

export function Badge({
  children,
  color = "var(--accent-gold)",
}: {
  children: React.ReactNode;
  color?: string;
}) {
  return (
    <span
      style={{
        fontSize: "0.68rem",
        padding: "0.25rem 0.7rem",
        background: "rgba(255,255,255,0.05)",
        borderRadius: "2px",
        color,
        fontWeight: "600",
        border: `1px solid ${color}33`,
      }}
    >
      {children}
    </span>
  );
}

export function Toast({ message }: { message: string | null }) {
  const [visible] = useState(Boolean(message));
  if (!message || !visible) return null;
  return (
    <div
      style={{
        position: "fixed",
        bottom: "2rem",
        left: "50%",
        transform: "translateX(-50%)",
        background: "var(--accent-gold)",
        color: "#000",
        fontWeight: "700",
        padding: "1rem 2rem",
        borderRadius: "6px",
        zIndex: 999,
        boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
      }}
    >
      {message}
    </div>
  );
}

export function Loading() {
  return (
    <div style={{ padding: "4rem", textAlign: "center", color: "var(--text-muted)" }}>
      <div style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>◈</div>
      Loading…
    </div>
  );
}
