import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { unified } from '@astrojs/markdown-remark';
import sitemap from '@astrojs/sitemap';
import fs from 'node:fs';

const gamsGrammar = JSON.parse(
  fs.readFileSync(
    new URL('./src/syntaxes/gams.tmLanguage.json', import.meta.url),
    'utf-8',
  ),
);

const siteUrl = 'https://optexpert.org';

export default defineConfig({
  site: siteUrl,
  output: 'static',
  trailingSlash: 'always',
  compressHTML: true,

  integrations: [
    sitemap({
      filter: (page) => {
        const url = new URL(page);
        return !['/search/', '/404/'].includes(url.pathname);
      },
    }),
  ],

  redirects: {
    '/posts/2026/06/20/Advanced-Power-System-Course': '/courses/advanced-power-system/',
    '/posts/2026/06/24/vrp-python-course': '/courses/vrp-python/',
  },

  vite: {
    plugins: [tailwindcss()],
  },

  markdown: {
    syntaxHighlight: 'shiki',
    processor: unified({
      remarkPlugins: [remarkMath],
      rehypePlugins: [rehypeKatex],
    }),
    shikiConfig: {
      theme: 'github-dark',
      langs: [gamsGrammar],
    },
  },
});
