import { getCollection } from 'astro:content';
import { entrySlug, isPublished } from './content';
import { buildTagIndex, MIN_HUB_USES } from './tags';

export type ContentType = 'note' | 'project' | 'course' | 'book' | 'software';

const sources = [
  { collection: 'notes' as const, typeId: 'note' as const, typeLabel: 'یادداشت', path: 'notes' },
  { collection: 'projects' as const, typeId: 'project' as const, typeLabel: 'پروژه', path: 'projects' },
  { collection: 'courses' as const, typeId: 'course' as const, typeLabel: 'دوره', path: 'courses' },
  { collection: 'books' as const, typeId: 'book' as const, typeLabel: 'کتاب', path: 'books' },
  { collection: 'softwares' as const, typeId: 'software' as const, typeLabel: 'نرم‌افزار', path: 'softwares' },
];

export interface SeoIssue {
  severity: 'error' | 'warning';
  code: string;
  message: string;
}

export interface SeoPage {
  id: string;
  title: string;
  typeId: ContentType;
  typeLabel: string;
  url: string;
  filePath: string;
  titleLength: number;
  descriptionLength: number;
  wordCount: number;
  readingTimeMin: number;
  tagCount: number;
  tags: string[];
  headingCount: number;
  internalLinks: string[];
  externalLinkCount: number;
  bodyImageCount: number;
  avgSentenceLength: number;
  longestParagraphWords: number;
  hasBodyH1: boolean;
  hasImage: boolean;
  hasImageAlt: boolean;
  issues: SeoIssue[];
  score: number; // 0-100, higher is better
}

// آستانه‌ها — همان اعدادی که در «راهنمای نوشتن مطلب سئوشده» در صفحه‌ی سئو
// هم به نویسنده نشان داده می‌شود، تا تحلیل و راهنما همیشه هم‌خوان بمانند.
export const THRESHOLDS = {
  titleMin: 20,
  titleMax: 65,
  descriptionMin: 70,
  descriptionMax: 165,
  thinContentWords: 150,
  goodContentWords: 300,
  longContentForHeadings: 300,
  maxParagraphWords: 130,
  maxAvgSentenceWords: 32,
  longContentForImages: 600,
};

function countWords(markdown: string): number {
  const stripped = markdown
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/[#>*_~`-]/g, ' ');
  const matches = stripped.match(/[\p{L}\p{N}]+/gu);
  return matches ? matches.length : 0;
}

function countHeadings(markdown: string): number {
  const withoutCode = markdown.replace(/```[\s\S]*?```/g, ' ').replace(/`[^`]*`/g, ' ');
  const matches = withoutCode.match(/^#{2,3}\s+\S/gm);
  return matches ? matches.length : 0;
}

function hasBodyH1(markdown: string): boolean {
  const withoutCode = markdown.replace(/```[\s\S]*?```/g, ' ').replace(/`[^`]*`/g, ' ');
  return /^#\s+\S/m.test(withoutCode);
}

function extractInternalLinks(markdown: string): string[] {
  const matches = [...markdown.matchAll(/]\((\/[^)\s]*)\)/g)];
  return matches.map(m => m[1]);
}

function countExternalLinks(markdown: string): number {
  const matches = markdown.match(/]\(https?:\/\/[^)\s]*\)/g);
  return matches ? matches.length : 0;
}

function countBodyImages(markdown: string): number {
  const matches = markdown.match(/!\[[^\]]*\]\([^)]*\)/g);
  return matches ? matches.length : 0;
}

/** Cleans markdown to plain text for sentence/paragraph analysis. */
function toPlainText(markdown: string): string {
  return markdown
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/[*_~`]/g, '');
}

function avgSentenceLength(markdown: string): number {
  const text = toPlainText(markdown);
  const sentences = text.split(/[.!؟?]\s+|\n{2,}/).map(s => s.trim()).filter(Boolean);
  if (sentences.length === 0) return 0;
  const totalWords = sentences.reduce((sum, s) => sum + (s.match(/[\p{L}\p{N}]+/gu)?.length ?? 0), 0);
  return Math.round(totalWords / sentences.length);
}

function longestParagraphWords(markdown: string): number {
  const text = toPlainText(markdown);
  const paragraphs = text.split(/\n{2,}/).map(p => p.trim()).filter(Boolean);
  let max = 0;
  for (const p of paragraphs) {
    const words = p.match(/[\p{L}\p{N}]+/gu)?.length ?? 0;
    if (words > max) max = words;
  }
  return max;
}

function scorePage(issues: SeoIssue[]): number {
  let score = 100;
  for (const issue of issues) score -= issue.severity === 'error' ? 20 : 10;
  return Math.max(0, score);
}

interface RawPage {
  source: (typeof sources)[number];
  entry: any;
  title: string;
  description: string;
  tags: string[];
  body: string;
  wordCount: number;
  headingCount: number;
  internalLinks: string[];
  externalLinkCount: number;
  bodyImageCount: number;
  avgSentenceLength: number;
  longestParagraphWords: number;
  hasBodyH1: boolean;
  hasImage: boolean;
  hasImageAlt: boolean;
}

async function collectRawPages(): Promise<RawPage[]> {
  const collections = await Promise.all(
    sources.map(async source => ({ source, entries: await getCollection(source.collection, isPublished) })),
  );
  const raw: RawPage[] = [];
  for (const { source, entries } of collections) {
    for (const entry of entries) {
      const body: string = entry.body ?? '';
      raw.push({
        source,
        entry,
        title: entry.data.title ?? '',
        description: entry.data.description ?? '',
        tags: Array.isArray(entry.data.tags) ? entry.data.tags : [],
        body,
        wordCount: countWords(body),
        headingCount: countHeadings(body),
        internalLinks: extractInternalLinks(body),
        externalLinkCount: countExternalLinks(body),
        bodyImageCount: countBodyImages(body),
        avgSentenceLength: avgSentenceLength(body),
        longestParagraphWords: longestParagraphWords(body),
        hasBodyH1: hasBodyH1(body),
        hasImage: Boolean(entry.data.image),
        hasImageAlt: Boolean(entry.data.imageAlt && String(entry.data.imageAlt).trim()),
      });
    }
  }
  return raw;
}

/** Every real, currently-buildable URL on the site — used to catch links to pages that don't exist. */
async function buildValidPathSet(rawPages: RawPage[]): Promise<Set<string>> {
  const set = new Set<string>();
  set.add('/');
  for (const p of rawPages) set.add(`/${p.source.path}/${entrySlug(p.entry)}/`);

  const modules = import.meta.glob('/src/pages/**/*.{astro,js,ts,md,mdx}');
  for (const key of Object.keys(modules)) {
    let rel = key.replace('/src/pages/', '').replace(/\.(astro|js|ts|md|mdx)$/, '');
    if (rel.includes('[')) continue;
    if (rel === 'index') { set.add('/'); continue; }
    if (rel.endsWith('/index')) { set.add(`/${rel.slice(0, -'/index'.length)}/`); continue; }
    if (/\.[a-zA-Z0-9]+$/.test(rel)) { set.add(`/${rel}`); continue; }
    set.add(`/${rel}/`);
  }

  const tagIndex = await buildTagIndex();
  for (const bucket of tagIndex.values()) {
    if (bucket.items.length >= MIN_HUB_USES) set.add(`/tags/${bucket.slug}/`);
  }
  return set;
}

function normalizePath(link: string): string {
  const withoutHash = link.split('#')[0];
  const withoutQuery = withoutHash.split('?')[0];
  if (!withoutQuery) return '/';
  return withoutQuery.endsWith('/') ? withoutQuery : `${withoutQuery}/`;
}

let cached: Promise<SeoPage[]> | null = null;

async function computeSeoReport(): Promise<SeoPage[]> {
  const rawPages = await collectRawPages();
  const validPaths = await buildValidPathSet(rawPages);
  const t = THRESHOLDS;

  const titleCounts = new Map<string, number>();
  const descCounts = new Map<string, number>();
  for (const p of rawPages) {
    const tt = p.title.trim().toLocaleLowerCase('fa-IR');
    const d = p.description.trim().toLocaleLowerCase('fa-IR');
    if (tt) titleCounts.set(tt, (titleCounts.get(tt) ?? 0) + 1);
    if (d) descCounts.set(d, (descCounts.get(d) ?? 0) + 1);
  }

  const pages: SeoPage[] = rawPages.map(p => {
    const issues: SeoIssue[] = [];
    if (p.title.length < t.titleMin) issues.push({ severity: 'warning', code: 'title-short', message: `عنوان کوتاه است (${p.title.length} نویسه؛ پیشنهاد: ${t.titleMin}-${t.titleMax})` });
    if (p.title.length > t.titleMax) issues.push({ severity: 'warning', code: 'title-long', message: `عنوان بلند است (${p.title.length} نویسه) و ممکن است در نتایج گوگل قطع شود` });
    if (p.description.length < t.descriptionMin) issues.push({ severity: 'error', code: 'desc-short', message: `توضیحات کوتاه است (${p.description.length} نویسه؛ پیشنهاد: ${t.descriptionMin}-${t.descriptionMax})` });
    if (p.description.length > t.descriptionMax) issues.push({ severity: 'warning', code: 'desc-long', message: `توضیحات بلند است (${p.description.length} نویسه) و ممکن است قطع شود` });
    if (!p.hasImage) issues.push({ severity: 'warning', code: 'no-image', message: 'بدون تصویر شاخص (برای اشتراک‌گذاری و نتایج جستجو مهم است)' });
    if (p.hasImage && !p.hasImageAlt) issues.push({ severity: 'error', code: 'no-alt', message: 'تصویر شاخص متن جایگزین (alt) ندارد' });
    if (p.tags.length === 0) issues.push({ severity: 'warning', code: 'no-tags', message: 'هیچ تگی ندارد (شانس دیده‌شدن از طریق صفحات تگ را از دست می‌دهد)' });
    if (p.wordCount < t.thinContentWords) issues.push({ severity: 'error', code: 'thin-content', message: `محتوای متنی کم است (~${p.wordCount} کلمه؛ پیشنهاد حداقل ${t.thinContentWords})` });
    if (p.wordCount >= t.longContentForHeadings && p.headingCount === 0) issues.push({ severity: 'warning', code: 'no-headings', message: 'متن طولانی است ولی زیرعنوان (## یا ###) ندارد؛ خوانایی و ساختار سئو ضعیف می‌شود' });
    if (p.wordCount >= t.thinContentWords && p.internalLinks.length === 0) issues.push({ severity: 'warning', code: 'no-internal-links', message: 'هیچ لینک داخلی به صفحات دیگر سایت ندارد' });
    if (p.hasBodyH1) issues.push({ severity: 'error', code: 'h1-conflict', message: 'متن یک تیتر سطح ۱ (# ...) دارد که با عنوان اصلی صفحه تداخل ایجاد می‌کند؛ در بدنه فقط از ## یا ### استفاده کنید' });
    if (p.longestParagraphWords > t.maxParagraphWords) issues.push({ severity: 'warning', code: 'long-paragraph', message: `طولانی‌ترین پاراگراف حدود ${p.longestParagraphWords} کلمه است؛ برای خوانایی بهتر آن را به چند پاراگراف کوتاه‌تر بشکنید` });
    if (p.avgSentenceLength > t.maxAvgSentenceWords) issues.push({ severity: 'warning', code: 'long-sentences', message: `میانگین طول جملات حدود ${p.avgSentenceLength} کلمه است؛ جملات کوتاه‌تر خوانایی را بهتر می‌کند` });
    if (p.wordCount >= t.longContentForImages && p.bodyImageCount === 0) issues.push({ severity: 'warning', code: 'no-body-images', message: 'متن طولانی است ولی هیچ تصویری داخل بدنه ندارد؛ تصویر یا نمودار میانی می‌تواند خوانایی و زمان ماندگاری کاربر را بهبود دهد' });

    const brokenLinks = p.internalLinks.filter(link => !validPaths.has(normalizePath(link)));
    if (brokenLinks.length > 0) {
      const sample = [...new Set(brokenLinks)].slice(0, 3).join('، ');
      issues.push({ severity: 'error', code: 'broken-link', message: `${brokenLinks.length} لینک داخلی شکسته: ${sample}${brokenLinks.length > 3 ? ' و...' : ''}` });
    }

    const titleKey = p.title.trim().toLocaleLowerCase('fa-IR');
    if (titleKey && (titleCounts.get(titleKey) ?? 0) > 1) issues.push({ severity: 'error', code: 'dup-title', message: 'این عنوان دقیقاً در یک صفحه‌ی دیگر هم استفاده شده (محتوای تکراری)' });
    const descKey = p.description.trim().toLocaleLowerCase('fa-IR');
    if (descKey && (descCounts.get(descKey) ?? 0) > 1) issues.push({ severity: 'error', code: 'dup-desc', message: 'این توضیحات دقیقاً در یک صفحه‌ی دیگر هم استفاده شده (محتوای تکراری)' });

    return {
      id: p.entry.id,
      title: p.title,
      typeId: p.source.typeId,
      typeLabel: p.source.typeLabel,
      url: `/${p.source.path}/${entrySlug(p.entry)}/`,
      filePath: p.entry.filePath ?? '',
      titleLength: p.title.length,
      descriptionLength: p.description.length,
      wordCount: p.wordCount,
      readingTimeMin: Math.max(1, Math.round(p.wordCount / 200)),
      tagCount: p.tags.length,
      tags: p.tags,
      headingCount: p.headingCount,
      internalLinks: p.internalLinks,
      externalLinkCount: p.externalLinkCount,
      bodyImageCount: p.bodyImageCount,
      avgSentenceLength: p.avgSentenceLength,
      longestParagraphWords: p.longestParagraphWords,
      hasBodyH1: p.hasBodyH1,
      hasImage: p.hasImage,
      hasImageAlt: p.hasImageAlt,
      issues,
      score: scorePage(issues),
    };
  });

  return pages.sort((a, b) => a.score - b.score);
}

export function buildSeoReport(): Promise<SeoPage[]> {
  if (!cached) cached = computeSeoReport();
  return cached;
}

export interface SeoIssueSummary {
  code: string;
  message: string;
  severity: 'error' | 'warning';
  count: number;
}

export function summarizeIssues(pages: SeoPage[]): SeoIssueSummary[] {
  const byCode = new Map<string, SeoIssueSummary>();
  for (const page of pages) {
    for (const issue of page.issues) {
      const existing = byCode.get(issue.code);
      if (existing) existing.count += 1;
      else byCode.set(issue.code, { code: issue.code, message: issue.message.replace(/\(.*?\)/g, '').replace(/:.*$/, '').trim(), severity: issue.severity, count: 1 });
    }
  }
  return [...byCode.values()].sort((a, b) => (b.severity === 'error' ? 2 : 1) * b.count - (a.severity === 'error' ? 2 : 1) * a.count);
}

export interface TypeSummary {
  typeId: ContentType;
  typeLabel: string;
  count: number;
  avgScore: number;
  issueCount: number;
}

export function summarizeByType(pages: SeoPage[]): TypeSummary[] {
  const byType = new Map<ContentType, { typeLabel: string; scores: number[]; issues: number }>();
  for (const page of pages) {
    const bucket = byType.get(page.typeId) ?? { typeLabel: page.typeLabel, scores: [], issues: 0 };
    bucket.scores.push(page.score);
    bucket.issues += page.issues.length;
    byType.set(page.typeId, bucket);
  }
  return [...byType.entries()]
    .map(([typeId, b]) => ({
      typeId,
      typeLabel: b.typeLabel,
      count: b.scores.length,
      avgScore: Math.round(b.scores.reduce((s, v) => s + v, 0) / b.scores.length),
      issueCount: b.issues,
    }))
    .sort((a, b) => a.avgScore - b.avgScore);
}
