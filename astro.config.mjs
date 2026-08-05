import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://optimizationexpert.github.io",
  output: "static",
  trailingSlash: "always",

  redirects: {
    "/posts/2026/06/20/Advanced-Power-System-Course":
      "/advanced-power-system-course/",

    "/posts/2026/06/24/vrp-python-course":
      "/vehicle-routing-python-course/",
  },

  vite: {
    plugins: [tailwindcss()],
  },
});
