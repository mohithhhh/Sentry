import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#11161A",
        panel: "#1A2126",
        "panel-raised": "#212A30",
        paper: "#EDE7D8",
        "paper-dim": "#93A0A0",
        hairline: "rgba(237, 231, 216, 0.12)",
        signal: {
          amber: "#E3A23C",
          green: "#5FB88F",
          rust: "#B5533C",
        },
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        sans: ["var(--font-plex-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-plex-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
