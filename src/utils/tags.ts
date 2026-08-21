import { getCollection } from 'astro:content';
import { resolveCanonicalTag, slugifyTag, normalizeTag } from './tag-text';
import { entrySlug, isPublished } from './content';

export { normalizeTag, resolveCanonicalTag, slugifyTag };

export type ContentType = 'note' | 'project' | 'course' | 'book' | 'software';

const sources = [
  { collection: 'notes' as const, typeId: 'note' as const, typeLabel: 'یادداشت', path: 'notes' },
  { collection: 'projects' as const, typeId: 'project' as const, typeLabel: 'پروژه', path: 'projects' },
  { collection: 'courses' as const, typeId: 'course' as const, typeLabel: 'دوره', path: 'courses' },
  { collection: 'books' as const, typeId: 'book' as const, typeLabel: 'کتاب', path: 'books' },
  { collection: 'softwares' as const, typeId: 'software' as const, typeLabel: 'نرم‌افزار', path: 'softwares' },
];

export interface TagItem {
  id: string;
  slug: string;
  title: string;
  typeId: ContentType;
  typeLabel: string;
  url: string;
}

export interface TagBucket {
  slug: string;
  name: string; // canonical display text, e.g. "برنامه ریزی خطی"
  items: TagItem[];
}

// Below this many uses, a tag doesn't get its own indexable hub page — a
// page built from one or two items is thin content and hurts SEO more than
// it helps. Those tags still display on content pages, just link to /search/.
export const MIN_HUB_USES = 3;

/**
 * Scans every published content entry once and groups tags by their
 * canonical slug. Cached for the lifetime of the process (one static build,
 * or one `astro dev` run) since content reads are otherwise repeated on
 * every page that renders tag badges.
 */
let cachedIndex: Promise<Map<string, TagBucket>> | null = null;

async function computeTagIndex(): Promise<Map<string, TagBucket>> {
  const index = new Map<string, TagBucket>();
  const collections = await Promise.all(
    sources.map(async source => ({ source, entries: await getCollection(source.collection, isPublished) })),
  );
  for (const { source, entries } of collections) {
    for (const entry of entries) {
      const rawTags: string[] = Array.isArray(entry.data.tags) ? entry.data.tags : [];
      const seenSlugs = new Set<string>();
      for (const raw of rawTags) {
        const name = resolveCanonicalTag(raw);
        if (!name) continue;
        const slug = slugifyTag(name);
        if (seenSlugs.has(slug)) continue; // guard against slug collisions within one entry
        seenSlugs.add(slug);
        const bucket = index.get(slug) ?? { slug, name, items: [] };
        bucket.items.push({
          id: entry.id,
          slug: entrySlug(entry),
          title: entry.data.title,
          typeId: source.typeId,
          typeLabel: source.typeLabel,
          url: `/${source.path}/${entrySlug(entry)}/`,
        });
        index.set(slug, bucket);
      }
    }
  }
  return index;
}

export function buildTagIndex(): Promise<Map<string, TagBucket>> {
  if (!cachedIndex) cachedIndex = computeTagIndex();
  return cachedIndex;
}

/** Auto-generated, always-unique meta description for a tag hub page. */
export function describeTag(name: string, items: TagItem[]): string {
  const counts: Partial<Record<ContentType, number>> = {};
  for (const item of items) counts[item.typeId] = (counts[item.typeId] ?? 0) + 1;
  const labelByType: Record<ContentType, string> = {
    note: 'یادداشت',
    project: 'پروژه',
    course: 'دوره',
    book: 'کتاب',
    software: 'نرم‌افزار',
  };
  const parts = (Object.keys(counts) as ContentType[])
    .filter(t => (counts[t] ?? 0) > 0)
    .map(t => `${counts[t]} ${labelByType[t]}`);
  const breakdown = parts.length ? parts.join('، ') : `${items.length} مطلب`;
  return `مطالب مرتبط با «${name}» در Optimization Expert: ${breakdown}.`;
}
