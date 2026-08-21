import fs from 'node:fs';
import path from 'node:path';
import { normalizeTag, slugifyTag } from './tag-text';

/**
 * «بانک محتوای آماده» — پوشه‌ی potential/ در ریشه‌ی پروژه (کنار src/) یک
 * انبار محتوای کاملاً نوشته و مصورشده است که عمداً بیرون از src/content
 * نگه داشته می‌شود تا Astro اصلاً آن را در build نبیند (نه صفحه‌ای برایش
 * ساخته می‌شود، نه در sitemap/RSS/جستجو ظاهر می‌شود). این فایل همان پوشه
 * را در زمان build (فقط برای نمایش در پنل ادمین) اسکن می‌کند.
 *
 * توجه: این یک پارسر YAML کامل نیست — فقط همان الگوی ساده‌ی تک‌خطی
 * frontmatter را که در این پروژه استفاده می‌شود می‌خواند (دقیقاً همان
 * الگوی scripts/tags-report.mjs). برای انتشار واقعی محتوا هیچ نیازی به
 * این فایل نیست؛ فقط برای گزارش‌گیری در پنل ادمین است.
 */

const ROOT = process.cwd();
const BANK_DIR = path.join(ROOT, 'potential');

export interface ContentBankEntry {
  /** نام پوشه، معمولاً همان اسلاگ نهایی مطلب */
  folder: string;
  title: string;
  description: string;
  pubDate: string | null;
  tags: string[];
  /** تگ‌هایی از این مطلب که دقیقاً با یک تگ موجود در سایت مطابقت دارند */
  matchedTags: string[];
  /** تگ‌هایی که در سایت وجود ندارند (احتمالاً تگ جدید یا نیازمند بررسی املا) */
  newTags: string[];
  /** تعداد فایل‌های غیر md داخل پوشه (تصاویر و امثال آن) */
  assetCount: number;
  hasMiniImage: boolean;
  hasMainImage: boolean;
  relatedCourses: string[];
  relatedNotes: string[];
  /** مسیر نسبی پوشه از ریشه‌ی پروژه، فقط برای نمایش دستورِ کپی */
  relativePath: string;
  /**
   * اگر یک مطلب منتشرشده (در notes/projects/...) از قبل همین اسلاگ را
   * دارد، یعنی این مورد یا نسخه‌ی قدیمیِ همان مطلب است (که باید حذف شود)
   * یا یک برداشت متفاوت از همان موضوع (که باید قبل از انتشار بازبینی و
   * با نسخه‌ی زنده مقایسه شود تا محتوای نزدیک‌به‌تکراری منتشر نشود).
   */
  collidesWithPublishedSlug: boolean;
}

function extractScalarField(frontmatter: string, key: string): string | null {
  const match = frontmatter.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'));
  if (!match) return null;
  let value = match[1].trim();
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    value = value.slice(1, -1);
  }
  return value || null;
}

function extractArrayField(frontmatter: string, key: string): string[] {
  const match = frontmatter.match(new RegExp(`^${key}:\\s*(\\[[^\\]]*\\])`, 'm'));
  if (!match) return [];
  try {
    const parsed = JSON.parse(match[1].replace(/'/g, '"'));
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}

/**
 * تگ‌های این مقاله‌ی آماده را با نقشه‌ی تگ‌های زنده‌ی سایت مقایسه می‌کند تا
 * نویسنده قبل از انتشار بداند کدام تگ از قبل هست (و باید همان املا را
 * حفظ کند) و کدام تگ کاملاً جدید خواهد بود.
 */
function splitTagsByExistence(tags: string[], liveTagSlugs: Set<string>) {
  const matchedTags: string[] = [];
  const newTags: string[] = [];
  for (const tag of tags) {
    if (liveTagSlugs.has(slugifyTag(tag))) matchedTags.push(tag);
    else newTags.push(tag);
  }
  return { matchedTags, newTags };
}

export function buildContentBank(liveTagSlugs: Set<string>, publishedSlugs: Set<string>): ContentBankEntry[] {
  if (!fs.existsSync(BANK_DIR)) return [];

  const folders = fs
    .readdirSync(BANK_DIR, { withFileTypes: true })
    .filter(entry => entry.isDirectory());

  const results: ContentBankEntry[] = [];

  for (const folder of folders) {
    const dirPath = path.join(BANK_DIR, folder.name);
    const files = fs.readdirSync(dirPath);
    const mdFile = files.find(f => f.endsWith('.md') || f.endsWith('.mdx'));
    if (!mdFile) continue;

    const raw = fs.readFileSync(path.join(dirPath, mdFile), 'utf8');
    const frontmatterMatch = raw.match(/^---\n([\s\S]*?)\n---/);
    if (!frontmatterMatch) continue;
    const fm = frontmatterMatch[1];

    const tags = extractArrayField(fm, 'tags');
    const { matchedTags, newTags } = splitTagsByExistence(tags, liveTagSlugs);
    const nonMarkdownFiles = files.filter(f => f !== mdFile);

    results.push({
      folder: folder.name,
      title: extractScalarField(fm, 'title') ?? folder.name,
      description: extractScalarField(fm, 'description') ?? '',
      pubDate: extractScalarField(fm, 'pubDate'),
      tags,
      matchedTags,
      newTags,
      assetCount: nonMarkdownFiles.length,
      hasMiniImage: nonMarkdownFiles.some(f => /_mini\.(svg|webp|png|jpe?g)$/i.test(f)),
      hasMainImage: nonMarkdownFiles.some(f => !/_mini\.(svg|webp|png|jpe?g)$/i.test(f)),
      relatedCourses: extractArrayField(fm, 'relatedCourses'),
      relatedNotes: extractArrayField(fm, 'relatedNotes'),
      relativePath: path.relative(ROOT, dirPath).split(path.sep).join('/'),
      collidesWithPublishedSlug: publishedSlugs.has(folder.name),
    });
  }

  return results.sort((a, b) => (b.pubDate ?? '').localeCompare(a.pubDate ?? ''));
}

export { normalizeTag };
