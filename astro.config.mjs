import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import sitemap from '@astrojs/sitemap';
import fs from 'node:fs';

// خواندن مستقیم فایل گرامر
const gamsGrammar = JSON.parse(
  fs.readFileSync(new URL('./src/syntaxes/gams.tmLanguage.json', import.meta.url), 'utf-8')
);

export default defineConfig({
  output: 'static',
  site: 'https://optexpert.org',
  integrations: [
    sitemap({
      // صفحه‌ی جستجو noindex است؛ نباید در sitemap هم لیست شود (تناقض سیگنال به گوگل)
      filter: (page) => !page.includes('/search'),
    }),
  ],
  
  vite: {
    plugins: [tailwindcss()]
  },

  redirects: {
    "/posts/2026/06/20/Advanced-Power-System-Course":
      "https://optexpert.org/courses/advanced-power-system/",
    "/posts/2026/06/24/vrp-python-course":
      "https://optexpert.org/courses/vrp-python/",
  },
  
  markdown: {
    syntaxHighlight: 'shiki',
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
    shikiConfig: {
      theme: 'github-dark',
      // تغییر اصلی اینجاست: مستقیماً متغیر گرامر را پاس می‌دهیم
      langs: [
        gamsGrammar
      ]
    },
  },
});