import type { Config } from "tailwindcss";

// Paleta cyberpunk educacional (seção 7.1 do CLAUDE.md)
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        nerv: {
          bg: "#0A0A0F",
          surface: "#13131C",
          border: "#26263A",
          purple: "#7C3AED",
          "purple-dim": "#5B21B6",
          neon: "#39FF14",
          text: "#E5E5F0",
          muted: "#8A8AA3",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
