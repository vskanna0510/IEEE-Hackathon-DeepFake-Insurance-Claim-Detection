/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#030712",
        surface: "#0d1117",
        surfaceHover: "#161b22",
        border: "#21262d",
        accent: "#38bdf8",
        accentSoft: "#0ea5e9",
        accentGlow: "#0284c7",
        success: "#22c55e",
        warning: "#f59e0b",
        danger: "#ef4444",
        critical: "#dc2626",
        textPrimary: "#f0f6fc",
        textSecondary: "#8b949e",
        textMuted: "#484f58",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "spin-slow": "spin 3s linear infinite",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "slide-right": "slideRight 0.4s ease-out",
        "glow-pulse": "glowPulse 2s ease-in-out infinite",
        "score-count": "scoreCount 1.2s ease-out",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideRight: {
          "0%": { opacity: "0", transform: "translateX(-12px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(56, 189, 248, 0)" },
          "50%": { boxShadow: "0 0 20px 4px rgba(56, 189, 248, 0.15)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px)",
        "hero-gradient":
          "radial-gradient(ellipse at 50% 0%, rgba(56, 189, 248, 0.12) 0%, transparent 60%)",
        "card-gradient":
          "linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%)",
      },
      backgroundSize: {
        "grid-md": "40px 40px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)",
        "card-hover": "0 4px 16px rgba(0,0,0,0.6), 0 0 0 1px rgba(56,189,248,0.12)",
        glow: "0 0 24px rgba(56, 189, 248, 0.2)",
        "glow-danger": "0 0 24px rgba(239, 68, 68, 0.25)",
        "glow-success": "0 0 24px rgba(34, 197, 94, 0.2)",
      },
    },
  },
  plugins: [],
};
