import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { unified } from '@astrojs/markdown-remark';
import sitemap from '@astrojs/sitemap';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const gamsGrammar = JSON.parse(
  fs.readFileSync(
    new URL('./src/syntaxes/gams.tmLanguage.json', import.meta.url),
    'utf-8',
  ),
);

const siteUrl = 'https://optexpert.org';

// نگاشت خودکار «مسیر صفحه → تاریخ آخرین انتشار» برای sitemap. این تاریخ‌ها
// مستقیم از pubDate هر فایل md خوانده می‌شوند — با هر تغییر یا انتشار مطلب
// جدید، sitemap خودش لحظه‌ی build بعدی به‌روز می‌شود، بدون هیچ کار دستی.
const CONTENT_ROUTES = { notes: 'notes', projects: 'projects', courses: 'courses', books: 'books', softwares: 'softwares' };
const lastmodByPath = new Map();
for (const [collection, routeSegment] of Object.entries(CONTENT_ROUTES)) {
  const dir = fileURLToPath(new URL(`./src/content/${collection}/`, import.meta.url));
  if (!fs.existsSync(dir)) continue;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const mdFile = path.join(dir, entry.name, `${entry.name}.md`);
    if (!fs.existsSync(mdFile)) continue;
    const content = fs.readFileSync(mdFile, 'utf-8');
    const match = content.match(/^pubDate:\s*"?(\d{4}-\d{2}-\d{2})"?/m);
    if (match) lastmodByPath.set(`/${routeSegment}/${entry.name}/`, new Date(match[1]));
  }
}

export default defineConfig({
  site: siteUrl,
  output: 'static',
  trailingSlash: 'always',
  compressHTML: true,

  integrations: [
    sitemap({
      filter: (page) => {
        const url = new URL(page);
        return !url.pathname.startsWith('/admin/') && !['/search/', '/404/'].includes(url.pathname);
      },
      serialize: (item) => {
        const url = new URL(item.url);
        const lastmod = lastmodByPath.get(url.pathname);
        return lastmod ? { ...item, lastmod: lastmod.toISOString() } : item;
      },
    }),
  ],

  redirects: {
    '/posts/2026/06/20/Advanced-Power-System-Course': '/courses/advanced-power-system/',
    '/posts/2026/06/24/vrp-python-course': '/courses/vrp-python/',
    '/projects/load_hosting': '/projects/load-hosting/',
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
