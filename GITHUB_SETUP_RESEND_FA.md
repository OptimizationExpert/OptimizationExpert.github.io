# راه‌اندازی ارسال گزارش با Resend

این نسخه دیگر به Gmail App Password یا SMTP وابسته نیست.

## ۱) ساخت حساب و API Key در Resend

1. وارد Resend شوید و حساب بسازید.
2. از بخش **API Keys** یک کلید جدید بسازید.
3. کلید با `re_` شروع می‌شود. آن را فقط یک‌بار کپی کنید.

## ۲) افزودن Secret در GitHub

در مخزن بروید به:

`Settings → Secrets and variables → Actions → Secrets → New repository secret`

Secret زیر را بسازید:

- Name: `RESEND_API_KEY`
- Value: کلید Resend که با `re_` شروع می‌شود

گیرنده در workflow از قبل روی این نشانی تنظیم شده است:

`optimizationteamonline@gmail.com`

## ۳) فرستنده ایمیل

### راه سریع برای آزمایش

هیچ Variable دیگری نسازید. برنامه از این فرستنده آزمایشی استفاده می‌کند:

`Optimization Expert <onboarding@resend.dev>`

در حالت آزمایشی Resend معمولاً ارسال را به ایمیل مالک حساب محدود می‌کند. بنابراین بهتر است حساب Resend را با `optimizationteamonline@gmail.com` بسازید.

### راه دائمی و حرفه‌ای

یک دامنه متعلق به خودتان را در Resend تأیید کنید. سپس در GitHub بروید به:

`Settings → Secrets and variables → Actions → Variables → New repository variable`

Variable زیر را بسازید:

- Name: `RESEND_FROM`
- Value: برای مثال `Optimization Expert <reports@yourdomain.com>`

پس از تأیید دامنه، می‌توانید از هر آدرس روی همان دامنه به‌عنوان فرستنده استفاده کنید.

## ۴) فایل‌های لازم در ریشه مخزن

- `seo_opportunity_bot_v5.py`
- `seo_bot_config.json`
- `.github/workflows/daily-seo.yml`

فایل قدیمی workflow را با نسخه جدید جایگزین کنید. Secretهای قدیمی `SMTP_USER` و `SMTP_APP_PASSWORD` دیگر استفاده نمی‌شوند و می‌توانید آن‌ها را حذف کنید.

## ۵) آزمایش فوری

`Actions → Daily SEO Opportunity Report → Run workflow`

پس از اجرا:

- ایمیل به `optimizationteamonline@gmail.com` ارسال می‌شود.
- گزارش‌ها در بخش **Artifacts** همان اجرای GitHub تا ۳۰ روز باقی می‌مانند.
- اگر ارسال ایمیل شکست بخورد، علت دقیق Resend در log مرحله اجرای بات نوشته می‌شود.

## زمان اجرا

هر روز ساعت **09:10 به وقت Europe/Dublin**.
