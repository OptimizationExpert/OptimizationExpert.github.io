// Generates /llms.txt at build time (https://llmstxt.org): a plain-text map of the
// site for AI assistants. Built from the content collections, so it never goes stale.
import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { entrySlug, isPublished } from '../utils/content';
import { isOrtoolsHubMember } from '../data/ortools-hub';

const SITE = 'https://optexpert.org';

type Entry = { data: { title: string; description?: string; pubDate?: Date; tags?: string[] } };

const byDateDesc = (a: Entry, b: Entry) =>
  (b.data.pubDate?.getTime() ?? 0) - (a.data.pubDate?.getTime() ?? 0);

const line = (title: string, url: string, description?: string) =>
  `- [${title}](${url})${description ? `: ${description.replace(/\s+/g, ' ').trim()}` : ''}`;

export const GET: APIRoute = async () => {
  const [courses, notes, projects, instructors] = await Promise.all([
    getCollection('courses', isPublished),
    getCollection('notes', isPublished),
    getCollection('projects', isPublished),
    getCollection('instructors', isPublished),
  ]);

  const founder = instructors[0];
  const founderName = founder?.data.nameEn ?? 'Alireza Soroudi';
  const founderUrl = founder ? `${SITE}/instructors/${entrySlug(founder)}/` : `${SITE}/about/`;

  const sortedNotes = [...notes].sort(byDateDesc);
  const ortoolsNotes = sortedNotes.filter((n) =>
    isOrtoolsHubMember('notes', entrySlug(n), n.data.tags, (n.data as any).hubCluster),
  );
  const ortoolsSlugs = new Set(ortoolsNotes.map((n) => entrySlug(n)));
  const pyomoNotes = sortedNotes.filter(
    (n) => !ortoolsSlugs.has(entrySlug(n)) && (n.data.tags ?? []).some((t) => /pyomo/i.test(t)),
  );
  const pyomoSlugs = new Set(pyomoNotes.map((n) => entrySlug(n)));
  const otherNotes = sortedNotes.filter((n) => !ortoolsSlugs.has(entrySlug(n)) && !pyomoSlugs.has(entrySlug(n)));

  const body = [
    '# Optimization Expert (optexpert.org)',
    '',
    '> Persian-language (Farsi) educational platform for applied mathematical optimization with Python:',
    '> Google OR-Tools and CP-SAT, Pyomo, scheduling, vehicle routing, supply chain, and power system optimization.',
    `> Founded and taught by Dr. ${founderName} (${founderUrl}).`,
    '',
    'All courses and notes are written in Persian. Code, model names and solver names are in English.',
    'The site offers paid video courses, free tutorial notes, worked engineering projects, and consulting.',
    '',
    '## About',
    '',
    line(`Dr. ${founderName}`, founderUrl, founder?.data.descriptionEn),
    line('Consulting and project collaboration', `${SITE}/consultation/`, 'Optimization modeling, OR-Tools/CP-SAT, Pyomo and power system studies for academic and industrial projects.'),
    line('Contact', `${SITE}/contact/`),
    '',
    '## Guides',
    '',
    line('OR-Tools learning guide (hub)', `${SITE}/ortools/`, 'Structured learning path and index of all OR-Tools and CP-SAT tutorials on the site.'),
    line('Pyomo learning guide (hub)', `${SITE}/pyomo/`, 'Structured learning path and index of all Pyomo tutorials: modeling, solvers, GAMS-to-Python, power systems and advanced techniques.'),
    line('Learning roadmap', `${SITE}/roadmap/`),
    '',
    '## Courses',
    '',
    ...courses.map((c) => line(c.data.title, `${SITE}/courses/${entrySlug(c)}/`, c.data.description)),
    '',
    '## OR-Tools and CP-SAT tutorials',
    '',
    ...ortoolsNotes.map((n) => line(n.data.title, `${SITE}/notes/${entrySlug(n)}/`, n.data.description)),
    '',
    '## Pyomo tutorials',
    '',
    ...pyomoNotes.map((n) => line(n.data.title, `${SITE}/notes/${entrySlug(n)}/`, n.data.description)),
    '',
    '## Engineering projects',
    '',
    ...[...projects].sort(byDateDesc).map((p) => line(p.data.title, `${SITE}/projects/${entrySlug(p)}/`, p.data.description)),
    '',
    '## Optional',
    '',
    ...otherNotes.map((n) => line(n.data.title, `${SITE}/notes/${entrySlug(n)}/`, n.data.description)),
    '',
  ].join('\n');

  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
