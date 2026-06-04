/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Culinary Atlas palette — warm paper, ink, and spice accents.
        paper: {
          DEFAULT: "#F4EEE1", // warm cream canvas
          deep: "#EDE5D3", // recessed surfaces
          card: "#FBF7EE", // raised cards
        },
        ink: {
          DEFAULT: "#1C1A15", // near-black warm
          soft: "#46413A", // body on paper
          faint: "#7C766B", // captions
          line: "#DCD2BE", // hairlines on paper
        },
        saffron: {
          DEFAULT: "#E0531F", // tandoor — primary accent (food)
          deep: "#B83C13",
          glow: "#F6A04A", // marigold highlight
          wash: "#F7E3D2",
        },
        pine: {
          DEFAULT: "#234A3A", // travel
          deep: "#16332680",
          ink: "#13261D",
          wash: "#DCE7DE",
        },
        plum: {
          DEFAULT: "#7B2D43", // shopping
          deep: "#5A1E30",
          wash: "#EFDCE1",
        },
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"Hanken Grotesk"', "system-ui", "sans-serif"],
        mono: ['"Space Mono"', "ui-monospace", "monospace"],
      },
      letterSpacing: {
        label: "0.22em",
      },
      boxShadow: {
        card: "0 1px 0 rgba(28,26,21,0.04), 0 18px 40px -24px rgba(28,26,21,0.45)",
        lift: "0 2px 0 rgba(28,26,21,0.05), 0 40px 80px -40px rgba(28,26,21,0.55)",
        inset: "inset 0 0 0 1px rgba(28,26,21,0.08)",
      },
      borderRadius: {
        xl2: "1.4rem",
      },
      keyframes: {
        floaty: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        spinSlow: {
          to: { transform: "rotate(360deg)" },
        },
        blink: {
          "0%,100%": { opacity: "1" },
          "50%": { opacity: "0.15" },
        },
        sheen: {
          "0%": { backgroundPosition: "-160% 0" },
          "100%": { backgroundPosition: "260% 0" },
        },
      },
      animation: {
        floaty: "floaty 7s ease-in-out infinite",
        marquee: "marquee 40s linear infinite",
        "spin-slow": "spinSlow 26s linear infinite",
        blink: "blink 1.1s steps(2) infinite",
        sheen: "sheen 2.2s linear infinite",
      },
    },
  },
  plugins: [],
}
