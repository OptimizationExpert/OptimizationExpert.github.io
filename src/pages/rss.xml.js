import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { entrySlug, isPublished } from '../utils/content';

const ROUTES = {
  notes: 'notes',
  courses: 'courses',
  projects: 'projects',
  books: 'books',
  softwares: 'softwares',
};

export async function GET(context) {
  const collectionNames = Object.keys(ROUTES);
  const collections = await Promise.all(
    collectionNames.map((name) => getCollection(name, isPublished)),
  );

  const items = collections
    .flatMap((entries, index) =>
      entries.map((entry) => ({ entry, route: ROUTES[collectionNames[index]] })),
    )
    .filter(({ entry }) => Boolean(entry.data.pubDate))
    .sort((a, b) => b.entry.data.pubDate.getTime() - a.entry.data.pubDate.getTime())
    .slice(0, 50);

  return rss({
    title: 'Optimization Expert',
    description: 'پلتفرم تخصصی آموزش، مقالات و پروژه‌های بهینه‌سازی، الگوریتم‌ها و پژوهش‌های عملیاتی',
    site: context.site,
    items: items.map(({ entry, route }) => ({
      title: entry.data.title,
      description: entry.data.description,
      pubDate: entry.data.pubDate,
      link: `/${route}/${entrySlug(entry)}/`,
    })),
    customData: '<language>fa-ir</language>',
  });
}
