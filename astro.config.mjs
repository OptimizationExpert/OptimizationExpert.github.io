import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  output: 'static',
  vite: {
    plugins: [tailwindcss()]
  },
  markdown: {
    syntaxHighlight: 'shiki',
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
  },
  site: 'https://optimizationexpert.github.io/',
  integrations: [sitemap()]
});
