import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
import { resolveCanonicalTag, normalizeTag } from './utils/tag-text';

/**
 * A content image can live either beside the Markdown file (Astro-processed)
 * or in public/ as a normal URL string.
 */
const imageField = (image: any) => z.union([image(), z.string()]).optional();

/**
 * Tags need zero setup. Write anything in frontmatter — new tag, old tag,
 * doesn't matter — and it just works: it shows on the page, it's searchable,
 * and (once used on enough items) it gets its own /tags/<slug>/ page for SEO.
 * The only thing this does automatically:
 *  - trims stray whitespace
 *  - if the tag is listed in src/data/tag-aliases.ts as a variant of another
 *    tag (e.g. "LP" → "Linear Programming"), it's swapped to that canonical
 *    form so both spellings end up on the same tag page
 *  - removes exact/near-duplicates within the same entry
 * Nothing here can fail validation, so a typo in a tag never breaks the site.
 */
const tagsField = () => z.array(z.string()).default([]).transform(values => {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const raw of values) {
    const trimmed = String(raw ?? '').trim();
    if (!trimmed) continue;
    const canonical = resolveCanonicalTag(trimmed);
    const key = normalizeTag(canonical);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(canonical);
  }
  return result;
});

const commonContentFields = (image: any) => ({
  title: z.string(),
  description: z.string(),
  pubDate: z.coerce.date().optional(),
  image: imageField(image),
  imageAlt: z.string().optional(),
  tags: tagsField(),
  draft: z.boolean().default(false),
});

const notesCollection = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/notes' }),
  schema: ({ image }) => z.object({
    ...commonContentFields(image),
    pubDate: z.coerce.date(),
    author: z.string().default('Optimization Expert'),
    category: z.string().optional(),
    minimalImage: imageField(image),
    minimalImageAlt: z.string().optional(),
    relatedCourses: z.array(z.string()).default([]),
    relatedNotes: z.array(z.string()).default([]),
    relatedProjects: z.array(z.string()).default([]),
  }),
});

const projectsCollection = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/projects' }),
  schema: ({ image }) => z.object({
    ...commonContentFields(image),
    category: z.string().optional(),
    author: z.string().optional(),
    minimalImage: imageField(image),
    minimalImageAlt: z.string().optional(),
    instructor: z.string().optional(),
    environment: z.string().optional(),
    status: z.string().optional(),
    level: z.string().optional(),
    relatedCourses: z.array(z.string()).default([]),
    relatedNotes: z.array(z.string()).default([]),
    relatedProjects: z.array(z.string()).default([]),
  }),
});

const coursesCollection = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/courses' }),
  schema: ({ image }) => z.object({
    ...commonContentFields(image),
    duration: z.string().optional(),
    level: z.string().optional(),
    minimalImage: imageField(image),
    minimalImageAlt: z.string().optional(),
    environment: z.string().optional(),
    prerequisite: z.string().optional(),
    prerequisites: z.string().optional(),
    sessions: z.string().optional(),
    instructor: z.string().optional(),
    price: z.string().optional(),
    priceCurrency: z.string().default('IRR'),
    relatedCourses: z.array(z.string()).default([]),
    relatedNotes: z.array(z.string()).default([]),
    relatedProjects: z.array(z.string()).default([]),
  }),
});

const booksCollection = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/books' }),
  schema: ({ image }) => z.object({
    ...commonContentFields(image),
    author: z.string().optional(),
    category: z.string().optional(),
    format: z.string().optional(),
    pages: z.coerce.number().int().positive().optional(),
    price: z.string().optional(),
  }),
});

const softwaresCollection = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/softwares' }),
  schema: ({ image }) => z.object({
    ...commonContentFields(image),
    author: z.string().optional(),
    category: z.string().optional(),
    version: z.string().optional(),
    size: z.string().optional(),
    price: z.string().optional(),
    operatingSystem: z.string().optional(),
  }),
});

const instructorsCollection = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/instructors' }),
  schema: ({ image }) => z.object({
    name: z.string(),
    shortName: z.string().optional(),
    title: z.string().optional(),
    jobTitle: z.string().optional(),
    image: imageField(image),
    imageAlt: z.string().optional(),
    email: z.string().optional(),
    githubUrl: z.string().url().optional(),
    linkedinUrl: z.string().url().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = {
  notes: notesCollection,
  projects: projectsCollection,
  courses: coursesCollection,
  books: booksCollection,
  softwares: softwaresCollection,
  instructors: instructorsCollection,
};
