import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import sitemap from "@astrojs/sitemap";
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default defineConfig({
  site: "https://optexpert.org",
  output: "static",
  trailingSlash: "always",
  
  export default defineConfig({
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
  },
  
  redirects: {
    "/posts/2026/06/20/Advanced-Power-System-Course":
      "https://optexpert.org/courses/advanced-power-system/",

    "/posts/2026/06/24/vrp-python-course":
      "https://optexpert.org/courses/vrp-python/",
  },

  integrations: [sitemap()],   // ← این خط اضافه شد
  vite: {
    plugins: [tailwindcss()],
  },
});
