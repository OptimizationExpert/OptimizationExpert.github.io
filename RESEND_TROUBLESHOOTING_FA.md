# رفع مشکل ارسال ایمیل Resend در GitHub Actions

## 1. Secret را بررسی کنید
در مخزن GitHub:

`Settings → Secrets and variables → Actions → Secrets`

باید Secret زیر دقیقاً وجود داشته باشد:

- Name: `RESEND_API_KEY`
- Value: کلید واقعی Resend که با `re_` شروع می‌شود

Secret را در بخش **Variables** نسازید؛ باید در بخش **Secrets** باشد.

## 2. محدودیت فرستنده آزمایشی Resend
در حالت پیش‌فرض برنامه از این فرستنده استفاده می‌کند:

`Optimization Expert <onboarding@resend.dev>`

این فرستنده فقط می‌تواند به ایمیلی ارسال کند که حساب Resend با همان ایمیل ساخته شده است.
بنابراین حساب Resend باید با `optimizationteamonline@gmail.com` ساخته شده باشد.

اگر حساب Resend با ایمیل دیگری ساخته شده است، یکی از این دو کار را انجام دهید:

1. گیرنده آزمایشی را موقتاً به ایمیل مالک حساب Resend تغییر دهید؛ یا
2. یک دامنه شخصی در Resend تأیید کنید و GitHub Variable زیر را بسازید:

- Name: `RESEND_FROM`
- Value: `Optimization Expert <reports@YOUR-DOMAIN.COM>`

## 3. اجرای آزمایشی
به این مسیر بروید:

`Actions → Daily SEO Opportunity Report → Run workflow`

نسخه اصلاح‌شده اگر ایمیل ارسال نشود، اجرای GitHub را قرمز می‌کند و خطای واقعی را در مرحله زیر نشان می‌دهد:

`Run SEO bot and require successful email`

در Log دنبال خطی با این عنوان بگردید:

`EMAIL_STATUS:`

خطاهای رایج:

- `401/403 invalid_api_key`: کلید اشتباه یا منقضی است.
- `403 validation_error`: استفاده از `onboarding@resend.dev` برای ایمیلی غیر از مالک حساب Resend.
- `domain_not_found` یا domain mismatch: مقدار `RESEND_FROM` با دامنه تأییدشده یکسان نیست.
- `429`: محدودیت نرخ یا سهمیه.

## 4. داشبورد Resend
در Resend به بخش Emails یا Logs بروید. اگر درخواست در آنجا دیده نمی‌شود، Secret به Workflow نرسیده یا کد قبل از ارسال متوقف شده است. اگر وضعیت Delivered است ولی ایمیل دیده نمی‌شود، پوشه Spam/Promotions را بررسی کنید.
