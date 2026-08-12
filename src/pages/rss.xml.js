// src/pages/rss.xml.js
// فید RSS سایت — این فایل قبلاً وجود نداشت با اینکه Layout.astro به /rss.xml لینک می‌داد
// (یعنی هم کاربران و هم گوگل با یک لینک شکسته مواجه می‌شدند).
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

// نگاشت هر Collection به مسیر واقعی صفحاتش در سایت
const ROUTES = {
  notes: 'notes',
  courses: 'courses',
  projects: 'projects',
  books: 'books',
  softwares: 'softwares',
};

export async function GET(context) {
  const collections = await Promise.all(
    Object.keys(ROUTES).map((name) =>
      getCollection(name, ({ data }) => !data.draft)
    )
  );

  const items = Object.keys(ROUTES)
    .flatMap((name, i) =>
      collections[i].map((entry) => ({ entry, route: ROUTES[name] }))
    )
    // فقط محتوایی که تاریخ انتشار واقعی دارد وارد فید می‌شود؛ تاریخ فرضی ساخته نمی‌شود
    .filter(({ entry }) => Boolean(entry.data.pubDate))
    .sort(
      (a, b) =>
        new Date(b.entry.data.pubDate).getTime() -
        new Date(a.entry.data.pubDate).getTime()
    )
    .slice(0, 50);

  return rss({
    title: 'Optimization Expert',
    description:
      'پلتفرم تخصصی آموزش، مقالات و پروژه‌های بهینه‌سازی، الگوریتم‌ها و پژوهش‌های عملیاتی',
    site: context.site,
    items: items.map(({ entry, route }) => {
      const slug = entry.id.replace(/\.md$/, '').split('/').pop();
      return {
        title: entry.data.title,
        description: entry.data.description,
        pubDate: entry.data.pubDate,
        link: `/${route}/${slug}/`,
      };
    }),
    customData: '<language>fa-ir</language>',
  });
}
