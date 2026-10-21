/* Jednolity zestaw ikon (inline SVG, styl Lucide) — zamiast emoji w całym panelu. Ico przyjmuje nazwę ikony albo dawny znak emoji. */
import React from "react";

const PATHS: Record<string, string> = {
  "alert": "<path d=\"m21.7 18-8-14a2 2 0 0 0-3.5 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3z\"/><path d=\"M12 9v4M12 17h.01\"/>",
  "award": "<circle cx=\"12\" cy=\"8\" r=\"6\"/><path d=\"M15.5 13 17 22l-5-3-5 3 1.5-9\"/>",
  "bot": "<rect x=\"3\" y=\"8\" width=\"18\" height=\"12\" rx=\"3\"/><path d=\"M12 8V4\"/><circle cx=\"12\" cy=\"3\" r=\"1\"/><path d=\"M8 14h.01M16 14h.01M9 17h6\"/>",
  "building": "<rect x=\"4\" y=\"2\" width=\"16\" height=\"20\" rx=\"2\"/><path d=\"M9 22v-4h6v4M8 6h.01M12 6h.01M16 6h.01M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01\"/>",
  "check": "<path d=\"M20 6 9 17l-5-5\"/>",
  "clipboard": "<rect x=\"8\" y=\"2\" width=\"8\" height=\"4\" rx=\"1\"/><path d=\"M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2\"/><path d=\"M9 12h6M9 16h4\"/>",
  "clock": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"M12 6v6l4 2\"/>",
  "credit-card": "<rect x=\"2\" y=\"5\" width=\"20\" height=\"14\" rx=\"2\"/><path d=\"M2 10h20\"/>",
  "file-text": "<path d=\"M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z\"/><path d=\"M14 2v4a2 2 0 0 0 2 2h4\"/><path d=\"M10 9H8M16 13H8M16 17H8\"/>",
  "globe": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><path d=\"M2 12h20\"/><path d=\"M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10 15 15 0 0 1-4-10 15 15 0 0 1 4-10z\"/>",
  "handshake": "<path d=\"m11 17 2 2a1 1 0 1 0 3-3\"/><path d=\"m14 14 2.5 2.5a1 1 0 1 0 3-3l-3.9-3.9a3 3 0 0 0-4.2 0l-.9.9a1.5 1.5 0 0 1-2.1 0L7.5 8.5\"/><path d=\"m21 3 1 11h-2\"/><path d=\"M3 3 2 14l6.5 6.5a1 1 0 1 0 3-3\"/><path d=\"M3 4h8\"/>",
  "laptop": "<rect x=\"2\" y=\"3\" width=\"20\" height=\"14\" rx=\"2\"/><path d=\"M8 21h8M12 17v4\"/>",
  "lightbulb": "<path d=\"M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5\"/><path d=\"M9 18h6M10 22h4\"/>",
  "lock": "<rect x=\"3\" y=\"11\" width=\"18\" height=\"11\" rx=\"2\"/><path d=\"M7 11V7a5 5 0 0 1 10 0v4\"/>",
  "mail": "<rect x=\"2\" y=\"4\" width=\"20\" height=\"16\" rx=\"2\"/><path d=\"m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7\"/>",
  "message": "<path d=\"M7.9 20A9 9 0 1 0 4 16.1L2 22z\"/>",
  "mic": "<rect x=\"9\" y=\"2\" width=\"6\" height=\"12\" rx=\"3\"/><path d=\"M5 10a7 7 0 0 0 14 0\"/><path d=\"M12 17v5\"/><path d=\"M8 22h8\"/>",
  "package": "<path d=\"m7.5 4.3 9 5.2\"/><path d=\"M21 8v8a2 2 0 0 1-1 1.7l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 3 16V8a2 2 0 0 1 1-1.7l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8z\"/><path d=\"m3.3 7 8.7 5 8.7-5\"/><path d=\"M12 22V12\"/>",
  "palette": "<circle cx=\"13.5\" cy=\"6.5\" r=\".5\"/><circle cx=\"17.5\" cy=\"10.5\" r=\".5\"/><circle cx=\"8.5\" cy=\"7.5\" r=\".5\"/><circle cx=\"6.5\" cy=\"12.5\" r=\".5\"/><path d=\"M12 2a10 10 0 0 0 0 20 1.7 1.7 0 0 0 1.7-1.7c0-.4-.2-.8-.4-1.1-.3-.3-.4-.7-.4-1.1a1.7 1.7 0 0 1 1.7-1.7H16a6 6 0 0 0 6-6c0-5-4.5-8.4-10-8.4z\"/>",
  "repeat": "<path d=\"m17 2 4 4-4 4\"/><path d=\"M3 11v-1a4 4 0 0 1 4-4h14\"/><path d=\"m7 22-4-4 4-4\"/><path d=\"M21 13v1a4 4 0 0 1-4 4H3\"/>",
  "search": "<circle cx=\"11\" cy=\"11\" r=\"8\"/><path d=\"m21 21-4.3-4.3\"/>",
  "shield": "<path d=\"M20 13c0 5-3.5 7.5-7.7 8.9a1 1 0 0 1-.6 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.2-2.7a1.2 1.2 0 0 1 1.6 0C14.5 3.8 17 5 19 5a1 1 0 0 1 1 1z\"/><path d=\"m9 12 2 2 4-4\"/>",
  "shopping-bag": "<path d=\"M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z\"/><path d=\"M3 6h18\"/><path d=\"M16 10a4 4 0 0 1-8 0\"/>",
  "sparkles": "<path d=\"M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z\"/><path d=\"M19 15l.7 1.8 1.8.7-1.8.7L19 20l-.7-1.8-1.8-.7 1.8-.7z\"/>",
  "star": "<path d=\"m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.9-6.2-3.3-6.2 3.3L7 14.2 2 9.3l6.9-1z\"/>",
  "target": "<circle cx=\"12\" cy=\"12\" r=\"10\"/><circle cx=\"12\" cy=\"12\" r=\"6\"/><circle cx=\"12\" cy=\"12\" r=\"2\"/>",
  "trending-up": "<path d=\"m22 7-8.5 8.5-5-5L2 17\"/><path d=\"M16 7h6v6\"/>",
  "users": "<path d=\"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2\"/><circle cx=\"9\" cy=\"7\" r=\"4\"/><path d=\"M22 21v-2a4 4 0 0 0-3-3.9\"/><path d=\"M16 3.1a4 4 0 0 1 0 7.8\"/>",
  "wrench": "<path d=\"M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9z\"/>",
  "x": "<path d=\"M18 6 6 18M6 6l12 12\"/>",
  "zap": "<path d=\"M13 2 3 14h9l-1 8 10-12h-9z\"/>"
};

const EMOJI: Record<string, string> = {
  "👥": "users",
  "🎨": "palette",
  "🏢": "building",
  "📋": "clipboard",
  "🤝": "handshake",
  "📄": "file-text",
  "💰": "credit-card",
  "✓": "check",
  "⚠️": "alert",
  "🤖": "bot",
  "🔎": "search",
  "⭐": "star",
  "✕": "x",
  "⚡": "zap",
  "💳": "credit-card",
  "🎉": "sparkles",
  "🛡️": "shield",
  "🛍️": "shopping-bag",
  "📦": "package",
  "🎙️": "mic",
  "🧭": "target",
  "❓": "lightbulb",
  "🕐": "clock",
  "🔍": "search",
  "💬": "message",
  "✨": "sparkles",
  "💸": "credit-card",
  "💶": "credit-card",
  "★": "star",
  "🛠️": "wrench",
  "🎯": "target",
  "📈": "trending-up",
  "✉️": "mail",
  "↩️": "repeat",
  "🏆": "award",
  "🌍": "globe",
  "🖥️": "laptop",
  "🔒": "lock",
  "💡": "lightbulb"
};

export function Ico({ e, name, size = "1.1em", style }: { e?: string; name?: string; size?: string | number; style?: React.CSSProperties }) {
  const key = name ?? (e ? EMOJI[e.replace(/️/g, "")] ?? EMOJI[e] : undefined);
  const d = key ? PATHS[key] : undefined;
  if (!d) return e ? <>{e}</> : null;
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      style={{ verticalAlign: "-0.2em", flex: "none", ...style }}
      dangerouslySetInnerHTML={{ __html: d }}
    />
  );
}
