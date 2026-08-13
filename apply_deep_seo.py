from pathlib import Path
import re, json, shutil
root=Path('/mnt/data/seo_latest2')

# 1) content.config: add semantic author/jobTitle where genuinely useful.
p=root/'src/content.config.ts'
s=p.read_text(encoding='utf-8')
s=s.replace("    category: z.string().optional(),\n    minimalImage", "    category: z.string().optional(),\n    author: z.string().optional(),\n    minimalImage", 1)  # projects
# books: add author before category
s=s.replace("const booksCollection = defineCollection({\n  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/books' }),\n  schema: ({ image }) => z.object({\n    ...commonContentFields(image),\n    category", "const booksCollection = defineCollection({\n  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/books' }),\n  schema: ({ image }) => z.object({\n    ...commonContentFields(image),\n    author: z.string().optional(),\n    category")
# software author
s=s.replace("const softwaresCollection = defineCollection({\n  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/softwares' }),\n  schema: ({ image }) => z.object({\n    ...commonContentFields(image),\n    category", "const softwaresCollection = defineCollection({\n  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/softwares' }),\n  schema: ({ image }) => z.object({\n    ...commonContentFields(image),\n    author: z.string().optional(),\n    category")
# instructor jobTitle
s=s.replace("    title: z.string().optional(),\n    image", "    title: z.string().optional(),\n    jobTitle: z.string().optional(),\n    image")
p.write_text(s, encoding='utf-8')

# 2) frontmatter migrations
changes={
    root/'src/content/instructors/dr-soroudi/dr-soroudi.md': [
        ('title: "متخصص ارشد علوم داده | راهبر پروژه‌های بهینه‌سازی و تحقیق در عملیات در شرکت EirGrid | عضو ارشد موسسه مهندسان برق و الکترونیک (Senior Member IEEE)"', 'title: "دکتر علیرضا سرودی"'),
        ('title: "دکتر علیرضا سرودی"\n', 'title: "دکتر علیرضا سرودی"\njobTitle: "متخصص ارشد علوم داده و پژوهشگر بهینه‌سازی و تحقیق در عملیات"\n'),
    ],
    root/'src/content/books/pyomo-optimization-guide.md': [
        ('pubDate: 2026-06-15\n', 'pubDate: 2026-06-15\nauthor: "dr-soroudi"\n'),
    ],
    root/'src/content/softwares/gamsopt.md': [
        ('pubDate: 2026-07-25\n', 'pubDate: 2026-07-25\nauthor: "dr-soroudi"\n'),
    ],
}
for f, reps in changes.items():
    s=f.read_text(encoding='utf-8')
    for a,b in reps:
        if a in s and b not in s:
            s=s.replace(a,b,1)
    f.write_text(s,encoding='utf-8')
for f in (root/'src/content/projects').glob('*/*.md'):
    s=f.read_text(encoding='utf-8')
    if re.search(r'^author:',s,re.M): continue
    s=s.replace('\npubDate:', '\npubDate:',1)
    # Insert author directly after pubDate line.
    s=re.sub(r'(^pubDate:\s*[^\n]+\n)', r'\1author: "dr-soroudi"\n', s, count=1, flags=re.M)
    f.write_text(s,encoding='utf-8')

# 3) Rewrite SEO component with stronger graph + entity linking.
seo = r'''---
interface Props {
  title?: string;
  description?: string;
  image?: string;
  article?: boolean;
  type?: 'website' | 'article' | 'course' | 'software' | 'book';
  pubDate?: Date;
  author?: string;
  authorUrl?: string;
  noindex?: boolean;
  courseDetails?: {
    duration?: string;
    level?: string;
    instructorName?: string;
    instructorUrl?: string;
    price?: string;
    priceCurrency?: string;
  };
  softwareDetails?: {
    category?: string;
    version?: string;
    operatingSystem?: string;
    price?: string;
  };
  bookDetails?: {
    category?: string;
    format?: string;
    pages?: number;
    price?: string;
  };
  breadcrumbs?: { name: string; url?: string }[];
}

const siteName = 'Optimization Expert';
const siteUrl = new URL(Astro.site || Astro.url.origin).origin;
const organizationId = `${siteUrl}/#organization`;
const websiteId = `${siteUrl}/#website`;
const defaultDescription = 'مرجع تخصصی آموزش و محتوای کاربردی در مدل‌سازی ریاضی، بهینه‌سازی، برنامه‌نویسی پایتون و سیستم‌های قدرت';
const defaultImage = '/images/hero2.webp';
const organizationSameAs = [
  'https://github.com/OptimizationExpert',
  'https://t.me/pypyid',
  'https://www.youtube.com/@optexpert-org',
  'https://www.aparat.com/OptimizationOnline',
];

const {
  title,
  description = defaultDescription,
  image = defaultImage,
  article = false,
  type,
  pubDate,
  author = 'Optimization Expert',
  authorUrl,
  noindex = false,
  courseDetails,
  softwareDetails,
  bookDetails,
  breadcrumbs,
} = Astro.props;

const pageType = type ?? (article ? 'article' : 'website');
const pageTitle = title ? `${title} | ${siteName}` : siteName;
const canonicalURL = new URL(Astro.url.pathname, siteUrl).href;
const socialImageURL = new URL(image, siteUrl).href;
const socialImageType = /\.jpe?g(?:$|[?#])/i.test(socialImageURL)
  ? 'image/jpeg'
  : /\.png(?:$|[?#])/i.test(socialImageURL)
    ? 'image/png'
    : /\.svg(?:$|[?#])/i.test(socialImageURL)
      ? 'image/svg+xml'
      : 'image/webp';
const isHomePage = Astro.url.pathname === '/';
const resolvedAuthorUrl = authorUrl ? new URL(authorUrl, siteUrl).href : undefined;
const authorId = resolvedAuthorUrl ? `${resolvedAuthorUrl}#person` : organizationId;

function normalizeDigits(value: string): string {
  return value.replace(/[۰-۹]/g, (digit) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(digit)));
}

function toISODuration(text?: string): string | undefined {
  if (!text) return undefined;
  const normalized = normalizeDigits(text);
  const match = normalized.match(/\d+(?:\.\d+)?/);
  if (!match) return undefined;
  const unit = [
    ['ساعت', 'H'],
    ['دقیقه', 'M'],
    ['هفته', 'W'],
    ['ماه', 'M'],
    ['روز', 'D'],
  ].find(([label]) => text.includes(label));
  if (!unit) return undefined;
  if (unit[0] === 'ماه') return `P${match[0]}M`;
  if (unit[1] === 'H' || unit[1] === 'M') return `PT${match[0]}${unit[1]}`;
  return `P${match[0]}${unit[1]}`;
}

function toOfferPrice(value?: string): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim().replace(/,/g, '');
  if (/^(رایگان|free)$/i.test(trimmed)) return '0';
  if (/^\d+(?:\.\d+)?$/.test(trimmed)) return trimmed;
  return undefined;
}

function toBookFormat(text?: string): string | undefined {
  if (!text) return undefined;
  const value = text.toLowerCase();
  if (value.includes('pdf') || value.includes('epub') || value.includes('الکترونیک')) return 'https://schema.org/EBook';
  if (value.includes('چاپ') || value.includes('کاغذ') || value.includes('paperback')) return 'https://schema.org/Paperback';
  if (value.includes('صوت') || value.includes('audio')) return 'https://schema.org/AudiobookFormat';
  return undefined;
}

const organization = {
  '@type': 'Organization',
  '@id': organizationId,
  name: siteName,
  url: `${siteUrl}/`,
  logo: `${siteUrl}/images/logo-512.png`,
  sameAs: organizationSameAs,
};

const website = {
  '@type': 'WebSite',
  '@id': websiteId,
  name: siteName,
  url: `${siteUrl}/`,
  description: defaultDescription,
  publisher: { '@id': organizationId },
  inLanguage: 'fa-IR',
};

const authorEntity = author && author !== siteName
  ? {
      '@type': 'Person',
      '@id': authorId,
      name: author,
      ...(resolvedAuthorUrl ? { url: resolvedAuthorUrl } : {}),
    }
  : { '@id': organizationId };

const breadcrumbSchema = breadcrumbs && breadcrumbs.length > 1
  ? {
      '@type': 'BreadcrumbList',
      itemListElement: breadcrumbs.map((crumb, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        name: crumb.name,
        ...(crumb.url ? { item: new URL(crumb.url, siteUrl).href } : {}),
      })),
    }
  : undefined;

const webpage = {
  '@type': isHomePage ? 'WebPage' : 'WebPage',
  '@id': `${canonicalURL}#webpage`,
  url: canonicalURL,
  name: title || siteName,
  description,
  isPartOf: { '@id': websiteId },
  about: { '@id': organizationId },
  inLanguage: 'fa-IR',
};

const contentEntity = (() => {
  if (pageType === 'course') {
    const offerPrice = toOfferPrice(courseDetails?.price);
    const workload = toISODuration(courseDetails?.duration);
    const instructorUrl = courseDetails?.instructorUrl
      ? new URL(courseDetails.instructorUrl, siteUrl).href
      : undefined;
    const instructorId = instructorUrl ? `${instructorUrl}#person` : undefined;
    return {
      '@type': 'Course',
      '@id': `${canonicalURL}#course`,
      name: title,
      description,
      url: canonicalURL,
      image: [socialImageURL],
      inLanguage: 'fa-IR',
      provider: { '@id': organizationId },
      ...(courseDetails?.level ? { educationalLevel: courseDetails.level } : {}),
      hasCourseInstance: {
        '@type': 'CourseInstance',
        courseMode: 'online',
        ...(workload ? { courseWorkload: workload } : {}),
        ...(instructorUrl ? {
          instructor: {
            '@type': 'Person',
            '@id': instructorId,
            name: courseDetails.instructorName,
            url: instructorUrl,
          },
        } : {}),
      },
      ...(offerPrice ? {
        offers: {
          '@type': 'Offer',
          price: offerPrice,
          priceCurrency: courseDetails?.priceCurrency || 'IRR',
          availability: 'https://schema.org/InStock',
          url: canonicalURL,
        },
      } : {}),
      mainEntityOfPage: { '@id': `${canonicalURL}#webpage` },
    };
  }

  if (pageType === 'software') {
    const offerPrice = toOfferPrice(softwareDetails?.price);
    return {
      '@type': 'SoftwareApplication',
      '@id': `${canonicalURL}#software`,
      name: title,
      description,
      image: [socialImageURL],
      url: canonicalURL,
      inLanguage: 'fa-IR',
      ...(softwareDetails?.category ? { applicationCategory: softwareDetails.category } : {}),
      ...(softwareDetails?.version ? { softwareVersion: softwareDetails.version } : {}),
      ...(softwareDetails?.operatingSystem ? { operatingSystem: softwareDetails.operatingSystem } : {}),
      ...(offerPrice ? {
        offers: {
          '@type': 'Offer',
          price: offerPrice,
          priceCurrency: 'IRR',
          availability: 'https://schema.org/InStock',
          url: canonicalURL,
        },
      } : {}),
      mainEntityOfPage: { '@id': `${canonicalURL}#webpage` },
    };
  }

  if (pageType === 'book') {
    const offerPrice = toOfferPrice(bookDetails?.price);
    const bookFormat = toBookFormat(bookDetails?.format);
    return {
      '@type': 'Book',
      '@id': `${canonicalURL}#book`,
      name: title,
      description,
      image: [socialImageURL],
      url: canonicalURL,
      inLanguage: 'fa-IR',
      ...(bookDetails?.category ? { genre: bookDetails.category } : {}),
      ...(bookFormat ? { bookFormat } : {}),
      ...(bookDetails?.pages ? { numberOfPages: bookDetails.pages } : {}),
      author: authorEntity,
      ...(pubDate ? { datePublished: pubDate.toISOString() } : {}),
      ...(offerPrice ? {
        offers: {
          '@type': 'Offer',
          price: offerPrice,
          priceCurrency: 'IRR',
          availability: 'https://schema.org/InStock',
          url: canonicalURL,
        },
      } : {}),
      mainEntityOfPage: { '@id': `${canonicalURL}#webpage` },
    };
  }

  if (pageType === 'article') {
    return {
      '@type': 'BlogPosting',
      '@id': `${canonicalURL}#article`,
      headline: title,
      description,
      image: [socialImageURL],
      url: canonicalURL,
      inLanguage: 'fa-IR',
      author: authorEntity,
      publisher: { '@id': organizationId },
      ...(pubDate ? { datePublished: pubDate.toISOString() } : {}),
      mainEntityOfPage: { '@id': `${canonicalURL}#webpage` },
    };
  }

  if (isHomePage) {
    webpage.about = { '@id': organizationId };
  }
  return webpage;
})();

const graph = [organization, website, webpage, contentEntity, ...(breadcrumbSchema ? [breadcrumbSchema] : [])];
---
<title>{pageTitle}</title>
<meta name="description" content={description} />
<meta name="robots" content={noindex ? 'noindex, follow' : 'index, follow'} />
<link rel="canonical" href={canonicalURL} />
<meta name="max-image-preview" content="large" />
<meta name="author" content={author} />

<meta property="og:type" content={pageType === 'article' ? 'article' : 'website'} />
<meta property="og:url" content={canonicalURL} />
<meta property="og:title" content={pageTitle} />
<meta property="og:description" content={description} />
<meta property="og:image" content={socialImageURL} />
<meta property="og:image:alt" content={title || siteName} />
<meta property="og:site_name" content={siteName} />
<meta property="og:locale" content="fa_IR" />
<meta property="og:image:type" content={socialImageType} />

{pageType === 'article' && pubDate && (
  <meta property="article:published_time" content={pubDate.toISOString()} />
)}
{pageType === 'article' && author && <meta property="article:author" content={resolvedAuthorUrl || author} />}

<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content={pageTitle} />
<meta name="twitter:description" content={description} />
<meta name="twitter:image" content={socialImageURL} />
<meta name="twitter:image:alt" content={title || siteName} />

<script type="application/ld+json" set:html={JSON.stringify({ '@context': 'https://schema.org', '@graph': graph })} />
'''
(root/'src/components/SEO.astro').write_text(seo,encoding='utf-8')

# 4) Layout: allow page number to avoid duplicate archive titles.
p=root/'src/layouts/Layout.astro'; s=p.read_text(encoding='utf-8')
s=s.replace("  breadcrumbs?: { name: string; url?: string }[];\n}", "  breadcrumbs?: { name: string; url?: string }[];\n  pageNumber?: number;\n}")
s=s.replace("  breadcrumbs,\n} = Astro.props;", "  breadcrumbs,\n  pageNumber,\n} = Astro.props;\n\nconst resolvedTitle = pageNumber && pageNumber > 1 ? `${title} | صفحه ${pageNumber}` : title;")
s=s.replace("      title={title}\n", "      title={resolvedTitle}\n")
p.write_text(s,encoding='utf-8')

# 5) Pass article author to book/software and improve project author fallback.
p=root/'src/pages/books/[bookSlug].astro'; s=p.read_text(encoding='utf-8')
# insert author resolution in frontmatter
needle="const bookSlug = entrySlug(book);\n"
insert="const bookSlug = entrySlug(book);\n\nconst instructors = await getCollection('instructors', isPublished);\nconst matchedInstructor = book.data.author\n  ? instructors.find((i) => entrySlug(i) === book.data.author || i.data.name === book.data.author)\n  : undefined;\nconst authorFullName = matchedInstructor?.data.name || book.data.author || 'Optimization Expert';\n"
s=s.replace(needle,insert,1)
s=s.replace("  bookDetails={{", "  author={authorFullName}\n  authorUrl={matchedInstructor ? `/instructors/${entrySlug(matchedInstructor)}/` : undefined}\n  bookDetails={{",1)
p.write_text(s,encoding='utf-8')

p=root/'src/pages/softwares/[softwareSlug].astro'; s=p.read_text(encoding='utf-8')
needle="const softwareImg = software.data.image || defaultImage;\n"
insert="const softwareImg = software.data.image || defaultImage;\nconst instructors = await getCollection('instructors', isPublished);\nconst matchedInstructor = software.data.author\n  ? instructors.find((i) => entrySlug(i) === software.data.author || i.data.name === software.data.author)\n  : undefined;\nconst authorFullName = matchedInstructor?.data.name || software.data.author || 'Optimization Expert';\n"
s=s.replace(needle,insert,1)
s=s.replace("  type=\"software\"\n", "  type=\"software\"\n  author={authorFullName}\n  authorUrl={matchedInstructor ? `/instructors/${entrySlug(matchedInstructor)}/` : undefined}\n",1)
p.write_text(s,encoding='utf-8')

p=root/'src/pages/projects/[projectSlug].astro'; s=p.read_text(encoding='utf-8')
s=s.replace("const displayImage = project.data.image || project.data.minimalImage;\n", "const displayImage = project.data.image || project.data.minimalImage;\nconst authorFullName = projectInstructor?.data.name || 'Optimization Expert';\n")
s=s.replace('author={projectInstructor?.data.name || "Optimization Expert"}', 'author={authorFullName}')
p.write_text(s,encoding='utf-8')

# 6) Instructor page: use ProfilePage + Person graph, shorter page title via frontmatter title, jobTitle in schema.
p=root/'src/pages/instructors/[instructorSlug].astro'; s=p.read_text(encoding='utf-8')
# replace the personSchema block heuristically from const personSchema = to ;\n---
start=s.index('const personSchema = {')
end=s.index('\n};\n---', start)+3
new="""const profileUrl = `${siteUrl}/instructors/${instructorSlug}/`;\nconst personId = `${profileUrl}#person`;\nconst sameAs = [instructor.data.githubUrl, instructor.data.linkedinUrl].filter(Boolean);\nconst personSchema = {\n  '@context': 'https://schema.org',\n  '@graph': [\n    {\n      '@type': 'ProfilePage',\n      '@id': profileUrl,\n      url: profileUrl,\n      name: instructor.data.name,\n      inLanguage: 'fa-IR',\n      mainEntity: { '@id': personId },\n      ...(sameAs.length || instructor.data.jobTitle ? {} : {}),\n      ...(instructorCourses.length + instructorNotes.length + instructorProjects.length > 0 ? {\n        hasPart: [\n          ...instructorCourses.map((course) => ({\n            '@type': 'Course',\n            name: course.data.title,\n            url: `${siteUrl}/courses/${entrySlug(course)}/`,\n            provider: { '@id': `${siteUrl}/#organization` },\n          })),\n          ...instructorNotes.map((note) => ({\n            '@type': 'BlogPosting',\n            headline: note.data.title,\n            url: `${siteUrl}/notes/${entrySlug(note)}/`,\n            ...(note.data.pubDate ? { datePublished: note.data.pubDate.toISOString() } : {}),\n            author: { '@id': personId },\n          })),\n          ...instructorProjects.map((project) => ({\n            '@type': 'Article',\n            headline: project.data.title,\n            url: `${siteUrl}/projects/${entrySlug(project)}/`,\n            ...(project.data.pubDate ? { datePublished: project.data.pubDate.toISOString() } : {}),\n            author: { '@id': personId },\n          })),\n        ],\n      } : {}),\n    },\n    {\n      '@type': 'Person',\n      '@id': personId,\n      name: instructor.data.name,\n      ...(instructor.data.jobTitle ? { jobTitle: instructor.data.jobTitle } : {}),\n      ...(sameAs.length ? { sameAs } : {}),\n      url: profileUrl,\n    },\n    {\n      '@type': 'Organization',\n      '@id': `${siteUrl}/#organization`,\n      name: 'Optimization Expert',\n      url: `${siteUrl}/`,\n      logo: `${siteUrl}/images/logo-512.png`,\n    },\n  ],\n};"""
s=s[:start]+new+s[end:]
# remove duplicate extra sameAs property issue expression is harmless but clean it
s=s.replace("      ...(sameAs.length || instructor.data.jobTitle ? {} : {}),\n","")
p.write_text(s,encoding='utf-8')

# 7) Add course ItemList + pageNumber to courses archive; pageNumber to other archives.
p=root/'src/pages/courses/[...page].astro'; s=p.read_text(encoding='utf-8')
# add course list JSON before --- end of frontmatter
needle="const defaultImage = '/images/hero2.webp';\n"
insert=needle+"\nconst courseListSchema = {\n  '@context': 'https://schema.org',\n  '@type': 'ItemList',\n  itemListElement: page.data.map((course, index) => ({\n    '@type': 'ListItem',\n    position: (page.currentPage - 1) * page.size + index + 1,\n    url: new URL(`/courses/${entrySlug(course)}/`, Astro.site || Astro.url.origin).href,\n    item: {\n      '@type': 'Course',\n      name: course.data.title,\n      description: course.data.description,\n      url: new URL(`/courses/${entrySlug(course)}/`, Astro.site || Astro.url.origin).href,\n      provider: { '@type': 'Organization', name: 'Optimization Expert', url: 'https://optexpert.org/' },\n    },\n  })),\n};\n"
s=s.replace(needle,insert,1)
s=s.replace('  <main class="flex-grow">', '  <script type="application/ld+json" set:html={JSON.stringify(courseListSchema)} />\n\n  <main class="flex-grow">',1)
s=s.replace('<Layout \n  title="دوره‌ها و آموزش‌های تخصصی"', '<Layout \n  title="دوره‌ها و آموزش‌های تخصصی"',1)
# inject pageNumber into Layout after description line
s=re.sub(r'(description="[^"]+"\s*)', r'\1\n  pageNumber={page.currentPage}', s, count=1)
p.write_text(s,encoding='utf-8')

for kind in ['notes','projects','books','softwares']:
    p=root/f'src/pages/{kind}/[...page].astro'; s=p.read_text(encoding='utf-8')
    # first Layout tag add pageNumber after description attr, only first occurrence
    s=re.sub(r'(description="[^"]+"\s*)', r'\1\n  pageNumber={page.currentPage}', s, count=1)
    p.write_text(s,encoding='utf-8')

# 8) Improve page title for instructor and add jobTitle as visible subtitle remains content title.
# Already title is short via frontmatter.

# 9) Make article meta type correctly reflect Article, while preserving Open Graph article type.

print('Deep SEO changes applied')
