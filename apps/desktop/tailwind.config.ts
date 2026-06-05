import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101820",
        sand: "#f5efe1",
        ember: "#c34f2d",
        moss: "#4f6d4a"
      }
    }
  },
  plugins: []
} satisfies Config;

