# اجرای روزانه بات SEO با GitHub Actions

این نسخه هیچ سرویس ایمیل خارجی، دامنه، API Key یا App Password نیاز ندارد.

## فایل‌هایی که باید در مخزن قرار دهید

- `seo_opportunity_bot_v3.py` در ریشه مخزن، کنار `_config.yml`
- `.github/workflows/daily-seo.yml` با همین ساختار پوشه

## نصب

1. فایل ZIP را Extract کنید.
2. محتویات آن را داخل ریشه مخزن `OptimizationExpert.github.io` کپی کنید.
3. فایل‌های قدیمی Workflow مربوط به Resend، Brevo یا Gmail API را از `.github/workflows/` حذف کنید تا چند بات هم‌زمان اجرا نشوند.
4. همه فایل‌ها را Commit و Push کنید.

## آزمایش فوری

در GitHub وارد مخزن شوید و بروید به:

`Actions -> Daily SEO Opportunity Bot -> Run workflow`

بعد از پایان اجرا:

- خلاصه گزارش در صفحه همان Run و بخش **Summary** دیده می‌شود.
- فایل کامل گزارش در پایین صفحه Run، بخش **Artifacts** با نامی شبیه `seo-opportunity-report-12` قابل دانلود است.
- پوشه `seo_opportunity_output` نیز در مخزن Commit می‌شود.

## فعال‌کردن ایمیل اعلان GitHub

در حساب GitHub بروید به:

`Settings -> Notifications`

ایمیل `optimizationteamonline@gmail.com` باید در حساب GitHub اضافه و Verify شده باشد. در تنظیمات اعلان‌ها، دریافت اعلان‌های Actions از طریق Email را فعال کنید.

نکته: GitHub معمولاً اعلان اجرای ناموفق Workflow را ایمیل می‌کند. برای دریافت اعلان همه اجراها، مخزن را Watch کنید و تنظیمات Actions/Email حساب را فعال نگه دارید. خود فایل گزارش از بخش Artifacts دانلود می‌شود.

## زمان اجرا

Workflow فعلی هر روز در `08:10 UTC` اجرا می‌شود که در دوره ساعت تابستانی ایرلند برابر با `09:10` است. GitHub cron بر اساس UTC است. در زمستان اجرا ساعت `08:10` ایرلند خواهد بود.

برای اجرای ثابت 09:10 در زمستان، cron را به `10 9 * * *` تغییر دهید. GitHub cron به‌تنهایی تغییر ساعت تابستانی را خودکار مدیریت نمی‌کند.
