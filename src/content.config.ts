import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// اسکیما و تنظیمات مربوط به مقالات و یادداشت‌ها
const notesCollection = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/notes" }),
  schema: z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    pubDate: z.coerce.date(),
    author: z.string(),
    image: z.string().optional(),
    imageAlt: z.string().optional(),
    tags: z.array(z.string()).optional(),
    relatedCourses: z.array(z.string()).optional(),
    relatedNotes: z.array(z.string()).optional(),
    relatedProjects: z.array(z.string()).optional(),
  }),
});

// اسکیما و تنظیمات مربوط به پروژه‌ها
const projectsCollection = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/projects" }),
  schema: z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    pubDate: z.coerce.date().optional(),
    category: z.string().optional(),
    image: z.string().optional(),
    imageAlt: z.string().optional(),
    demoUrl: z.string().optional(),
    githubUrl: z.string().optional(),
    instructor: z.string().optional(),
    environment: z.string().optional(),
    status: z.string().optional(),
    level: z.string().optional(),
    tags: z.array(z.string()).optional(),
    relatedCourses: z.array(z.string()).optional(),
    relatedNotes: z.array(z.string()).optional(),
    relatedProjects: z.array(z.string()).optional(),
  }),
});

// اسکیما و تنظیمات مربوط به دوره‌ها
const coursesCollection = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/courses" }),
  schema: z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    pubDate: z.coerce.date(),
    duration: z.string().optional(),
    level: z.string().optional(),
    image: z.string().optional(),
    imageAlt: z.string().optional(),
    environment: z.string().optional(),
    prerequisite: z.string().optional(),
    sessions: z.string().optional(),
    instructor: z.string().optional(),
    tags: z.array(z.string()).optional(),
    relatedCourses: z.array(z.string()).optional(),
    relatedNotes: z.array(z.string()).optional(),
    relatedProjects: z.array(z.string()).optional(),
  }),
});

// اسکیما و تنظیمات مربوط به کتاب‌ها و جزوات
const booksCollection = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/books" }),
  schema: z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    category: z.string().optional(),
    format: z.string().optional(),
    pages: z.coerce.number().optional(),
    price: z.string().optional(),
    image: z.string().optional(),
    imageAlt: z.string().optional(),
    pubDate: z.coerce.date().optional(),
    tags: z.array(z.string()).optional(),
  }),
});

// اسکیما و تنظیمات مربوط به نرم‌افزارها
const softwaresCollection = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/softwares" }),
  schema: z.object({
    title: z.string(),
    seoTitle: z.string().optional(),
    description: z.string(),
    pubDate: z.coerce.date().optional(),
    category: z.string().optional(),
    version: z.string().optional(),
    size: z.string().optional(),
    price: z.string().optional(),
    image: z.string().optional(),
    imageAlt: z.string().optional(),
    tags: z.array(z.string()).optional(),
  }),
});

// اسکیما و تنظیمات مربوط به مدرسان
const instructorsCollection = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/instructors" }),
  schema: z.object({
    name: z.string(),
    seoTitle: z.string().optional(),
    title: z.string().optional(),
    image: z.string().optional(),
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