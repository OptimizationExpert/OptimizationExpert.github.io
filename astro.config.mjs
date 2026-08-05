import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://optexpert.org",
  output: "static",
  trailingSlash: "always",

  redirects: {
    "/posts/2026/06/20/Advanced-Power-System-Course":
      "https://optexpert.org/courses/advanced-power-system/",

    "/posts/2026/06/24/vrp-python-course":
      "https://optexpert.org/courses/vrp-python/",
  },

  vite: {
    plugins: [tailwindcss()],
  },
});
