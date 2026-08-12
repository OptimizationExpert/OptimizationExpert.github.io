import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// هلپر مشترک برای فیلدهای تصویر: هم مسیر رشته‌ای قدیمی (public/ یا URL خارجی)
// و هم تصویر محلی کنار فایل md (که Astro خودکار بهینه می‌کند) را قبول می‌کند.
// این یعنی محتوای موجود با مسیرهای /images/... همچنان بدون هیچ تغییری کار می‌کند،
// و هر فایل جدیدی که عکسش را کنار خودش بگذارد، به‌صورت خودکار از بهینه‌سازی Astro بهره می‌برد.
const imageField = (image) => z.union([image(), z.string()]).optional();

// ۱. اسکیما و تنظیمات مربوط به مقالات و یادداشت‌ها
const notesCollection = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/notes" }),
  schema: ({ image }) => z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    pubDate: z.coerce.date(),
    author: z.string().default('Optimization Expert'),
    minimalImage: imageField(image),
    minimalImageAlt: z.string().optional(),
    image: imageField(image),
    imageAlt: z.string().optional(),
    tags: z.array(z.string()).default([]),
    relatedCourses: z.array(z.string()).default([]),
    relatedNotes: z.array(z.string()).default([]),
    relatedProjects: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

// ۲. اسکیما و تنظیمات مربوط به پروژه‌ها
const projectsCollection = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/projects" }),
  schema: ({ image }) => z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    pubDate: z.coerce.date().optional(),
    category: z.string().optional(),
    minimalImage: imageField(image),
    minimalImageAlt: z.string().optional(),
    image: imageField(image),
    imageAlt: z.string().optional(),
    instructor: z.string().optional(),
    environment: z.string().optional(),
    status: z.string().optional(),
    level: z.string().optional(),
    tags: z.array(z.string()).default([]),
    relatedCourses: z.array(z.string()).default([]),
    relatedNotes: z.array(z.string()).default([]),
    relatedProjects: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

// ۳. اسکیما و تنظیمات مربوط به دوره‌ها
const coursesCollection = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/courses" }),
  schema: ({ image }) => z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    pubDate: z.coerce.date().optional(),
    duration: z.string().optional(),
    level: z.string().optional(),
    minimalImage: imageField(image),
    minimalImageAlt: z.string().optional(),
    image: imageField(image),
    imageAlt: z.string().optional(),
    environment: z.string().optional(),
    prerequisite: z.string().optional(),
    sessions: z.string().optional(),
    instructor: z.string().optional(),
    // اختیاری: در صورت پر شدن، خودکار در Schema.org Offer درج می‌شود (سئوی نتایج غنی دوره).
    // price باید یک رشته‌ی عددی خالص باشد (مثلاً "1500000")، بدون کاما یا واحد پول.
    price: z.string().optional(),
    priceCurrency: z.string().default('IRR'),
    tags: z.array(z.string()).default([]),
    relatedCourses: z.array(z.string()).default([]),
    relatedNotes: z.array(z.string()).default([]),
    relatedProjects: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

// ۴. اسکیما و تنظیمات مربوط به کتاب‌ها و جزوات
const booksCollection = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/books" }),
  schema: ({ image }) => z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    category: z.string().optional(),
    format: z.string().optional(),
    pages: z.coerce.number().optional(),
    price: z.string().optional(),
    image: imageField(image),
    imageAlt: z.string().optional(),
    pubDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

// ۵. اسکیما و تنظیمات مربوط به نرم‌افزارها
const softwaresCollection = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/softwares" }),
  schema: ({ image }) => z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    pubDate: z.coerce.date().optional(),
    category: z.string().optional(),
    version: z.string().optional(),
    size: z.string().optional(),
    price: z.string().optional(),
    // اختیاری: در صورت پر شدن، برای واجد شرایط شدن کامل Schema.org SoftwareApplication
    // در نتایج غنی گوگل استفاده می‌شود (مثلاً "Windows", "Windows, macOS").
    operatingSystem: z.string().optional(),
    image: imageField(image),
    imageAlt: z.string().optional(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

// ۶. اسکیما و تنظیمات مربوط به مدرسان
const instructorsCollection = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/instructors" }),
  schema: ({ image }) => z.object({
    name: z.string(),
    // نام کوتاه (بدون عنوان/پیشوند) برای نمایش فشرده در بخش «نویسنده» یادداشت‌ها.
    // اگر پر نشود، به‌جای آن از name کامل استفاده می‌شود.
    shortName: z.string().optional(),
    seoTitle: z.string().optional(),
    title: z.string().optional(),
    image: imageField(image),
    imageAlt: z.string().optional(),
    email: z.string().optional(),
    githubUrl: z.string().optional(),
    linkedinUrl: z.string().optional(),
  }),
});

export const collections = {
  'notes': notesCollection,
  'projects': projectsCollection,
  'courses': coursesCollection,
  'books': booksCollection,
  'softwares': softwaresCollection,
  'instructors': instructorsCollection,
};