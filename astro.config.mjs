import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://optimizationexpert.github.io",
  output: "static",

  redirects: {
    "/posts/2026/06/20/Advanced-Power-System-Course":
      "/courses/advanced-power-system",
  },

  vite: {
    plugins: [tailwindcss()],
  },
});
