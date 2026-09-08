import type { Config } from "tailwindcss";

/*
 * Tokens do design system NERV.AI (ver src/app/globals.css).
 *
 * As cores em oklch guardam so os componentes na variavel CSS; o <alpha-value>
 * e' o que faz bg-primary/12 e border-primary/40 funcionarem no Tailwind v3.
 */
const oklchVar = (name: string) => `oklch(var(--${name}) / <alpha-value>)`;

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: oklchVar("background"),
        foreground: oklchVar("foreground"),
        surface: {
          DEFAULT: oklchVar("surface"),
          2: oklchVar("surface-2"),
        },
        card: oklchVar("card"),
        primary: {
          DEFAULT: oklchVar("primary"),
          foreground: oklchVar("primary-foreground"),
          glow: oklchVar("primary-glow"),
        },
        secondary: oklchVar("secondary"),
        muted: {
          DEFAULT: oklchVar("muted"),
          foreground: oklchVar("muted-foreground"),
        },
        accent: oklchVar("accent"),
        destructive: oklchVar("destructive"),
        xp: oklchVar("xp"),
        streak: oklchVar("streak"),
        badge: oklchVar("badge"),

        // Semitransparentes por natureza: sem <alpha-value>, entao nao aceitam
        // modificador de opacidade (border-border/70 nao teria efeito).
        border: "var(--border)",
        input: "var(--input)",
        ring: "var(--ring)",

        /*
         * Paleta antiga (cyberpunk roxo), agora apontando para os tokens novos.
         * Sao 207 usos espalhados por 13 telas: remapear em vez de remover faz
         * as telas ainda nao reconstruidas adotarem a identidade nova em vez de
         * ficarem sem cor. Alias de transicao — nao usar em codigo novo.
         */
        nerv: {
          bg: oklchVar("background"),
          surface: oklchVar("surface"),
          border: "var(--border)",
          purple: oklchVar("primary"),
          "purple-dim": oklchVar("primary-glow"),
          neon: oklchVar("primary-glow"),
          text: oklchVar("foreground"),
          muted: oklchVar("muted-foreground"),
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ["DM Sans", "ui-sans-serif", "system-ui", "sans-serif"],
        body: ["DM Sans", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "2xl": "calc(var(--radius) + 12px)",
        "3xl": "calc(var(--radius) + 20px)",
      },
      animation: {
        float: "nerv-float 6s cubic-bezier(0.22, 1, 0.36, 1) infinite",
        "pulse-glow": "nerv-pulse-glow 5s ease-in-out infinite",
        dot: "nerv-dot 1.2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
