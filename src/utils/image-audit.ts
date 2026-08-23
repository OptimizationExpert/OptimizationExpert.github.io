import { getCollection } from 'astro:content';
import { entrySlug, isPublished } from './content';

export type ContentType = 'note' | 'project' | 'course' | 'book' | 'software';

const sources = [
  { collection: 'notes' as const, typeId: 'note' as const, typeLabel: 'یادداشت', path: 'notes' },
  { collection: 'projects' as const, typeId: 'project' as const, typeLabel: 'پروژه', path: 'projects' },
  { collection: 'courses' as const, typeId: 'course' as const, typeLabel: 'دوره', path: 'courses' },
  { collection: 'books' as const, typeId: 'book' as const, typeLabel: 'کتاب', path: 'books' },
  { collection: 'softwares' as const, typeId: 'software' as const, typeLabel: 'نرم‌افزار', path: 'softwares' },
];

const GENERIC_ALT_TERMS = new Set(['تصویر', 'عکس', 'image', 'img', 'photo', 'pic', 'picture']);

export interface ImageIssue {
  severity: 'error' | 'warning' | 'info';
  message: string;
}

export interface ImagePage {
  id: string;
  title: string;
  typeId: ContentType;
  typeLabel: string;
  url: string;
  filePath: string;
  featuredImageKind: 'optimized' | 'external' | 'missing';
  bodyImageCount: number;
  issues: ImageIssue[];
}

function isGenericAlt(alt: string): boolean {
  const trimmed = alt.trim();
  if (trimmed.length === 0) return false; // handled separately as "missing"
  if (trimmed.length < 4) return true;
  return GENERIC_ALT_TERMS.has(trimmed.toLocaleLowerCase('fa-IR'));
}

function extractBodyImages(markdown: string): { alt: string; src: string }[] {
  const withoutCode = markdown.replace(/```[\s\S]*?```/g, ' ').replace(/`[^`]*`/g, ' ');
  const matches = [...withoutCode.matchAll(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g)];
  return matches.map(m => ({ alt: m[1], src: m[2] }));
}

let cached: Promise<ImagePage[]> | null = null;

async function computeImageAudit(): Promise<ImagePage[]> {
  const collections = await Promise.all(
    sources.map(async source => ({ source, entries: await getCollection(source.collection, isPublished) })),
  );

  const pages: ImagePage[] = [];
  for (const { source, entries } of collections) {
    for (const entry of entries) {
      const issues: ImageIssue[] = [];
      const imageData: unknown = entry.data.image;
      const imageAlt: string = entry.data.imageAlt ?? '';

      let featuredImageKind: ImagePage['featuredImageKind'] = 'missing';
      if (imageData && (typeof imageData === 'object' || typeof imageData === 'function')) {
        // نکته: برای تصاویر SVG، Astro متادیتای تصویر را به‌صورت یک تابع برمی‌گرداند
        // (نه یک آبجکت ساده)، تا رندر inline SVG هم ممکن باشد — دقیقاً مثل imgSrc در src/utils/image.ts.
        featuredImageKind = 'optimized';
      } else if (typeof imageData === 'string' && imageData.trim()) {
        featuredImageKind = 'external';
        issues.push({ severity: 'info', message: 'تصویر شاخص از یک دامنه‌ی بیرونی بارگذاری می‌شود؛ بهینه‌سازی و سرعت آن به آن سرور وابسته است. در صورت امکان، فایل را دانلود و به‌عنوان تصویر محلی کنار مطلب اضافه کنید تا Astro خودکار فشرده‌اش کند.' });
      }

      if (featuredImageKind !== 'missing') {
        if (!imageAlt.trim()) {
          issues.push({ severity: 'error', message: 'تصویر شاخص متن جایگزین (imageAlt) ندارد.' });
        } else if (isGenericAlt(imageAlt)) {
          issues.push({ severity: 'warning', message: `متن جایگزین تصویر شاخص کلی/کوتاه است: «${imageAlt}» — توصیفی‌تر بنویسید.` });
        }
      }

      const bodyImages = extractBodyImages(entry.body ?? '');
      let missingAltCount = 0, genericAltCount = 0;
      for (const img of bodyImages) {
        if (!img.alt.trim()) missingAltCount++;
        else if (isGenericAlt(img.alt)) genericAltCount++;
      }
      if (missingAltCount > 0) issues.push({ severity: 'error', message: `${missingAltCount} تصویر داخل متن بدون توضیح جایگزین (متن داخل [ ]) است.` });
      if (genericAltCount > 0) issues.push({ severity: 'warning', message: `${genericAltCount} تصویر داخل متن توضیح کلی/خیلی کوتاه دارد.` });

      pages.push({
        id: entry.id,
        title: entry.data.title,
        typeId: source.typeId,
        typeLabel: source.typeLabel,
        url: `/${source.path}/${entrySlug(entry)}/`,
        filePath: entry.filePath ?? '',
        featuredImageKind,
        bodyImageCount: bodyImages.length,
        issues,
      });
    }
  }

  return pages.sort((a, b) => {
    const aErr = a.issues.filter(i => i.severity === 'error').length;
    const bErr = b.issues.filter(i => i.severity === 'error').length;
    return bErr - aErr || b.issues.length - a.issues.length;
  });
}

export function buildImageAudit(): Promise<ImagePage[]> {
  if (!cached) cached = computeImageAudit();
  return cached;
}
