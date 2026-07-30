# راه‌اندازی اجرای روزانه در GitHub

این بسته را در ریشه مخزن `OptimizationExpert.github.io` کپی کنید؛ یعنی فایل پایتون کنار `_config.yml` قرار بگیرد و پوشه `.github` نیز در ریشه مخزن باشد.

## ۱) ساخت App Password برای Gmail

1. وارد حساب Gmail فرستنده شوید.
2. احراز هویت دومرحله‌ای (2-Step Verification) را فعال کنید.
3. در بخش App passwords یک رمز ۱۶ کاراکتری برای GitHub Actions بسازید.
4. رمز اصلی Gmail را داخل GitHub قرار ندهید.

## ۲) ساخت GitHub Secrets

در مخزن GitHub بروید به:

`Settings → Secrets and variables → Actions → New repository secret`

دو Secret بسازید:

- `SMTP_USER` = آدرس Gmail فرستنده؛ برای نمونه `optimizationteamonline@gmail.com`
- `SMTP_APP_PASSWORD` = همان App Password شانزده‌کاراکتری Gmail

گیرنده از قبل روی `optimizationteamonline@gmail.com` تنظیم شده است.

## ۳) Commit و Push

فایل‌های زیر باید داخل مخزن باشند:

- `seo_opportunity_bot_v4.py`
- `seo_bot_config.json`
- `.github/workflows/daily-seo.yml`

پس از Push، در زبانه Actions، workflow با نام `Daily SEO Opportunity Report` ظاهر می‌شود.

## ۴) تست فوری

به مسیر زیر بروید:

`Actions → Daily SEO Opportunity Report → Run workflow`

پس از پایان، ایمیل باید دریافت شود. گزارش کامل نیز در بخش Artifacts همان اجرا برای ۳۰ روز باقی می‌ماند.

## زمان اجرا

Workflow هر روز ساعت **09:10 به وقت Europe/Dublin** اجرا می‌شود. تنظیم timezone باعث می‌شود تغییر ساعت تابستانی و زمستانی ایرلند خودکار لحاظ شود.

## نکته

GitHub ممکن است اجرای زمان‌بندی‌شده را در زمان شلوغی چند دقیقه دیرتر شروع کند. زمان 09:10 به‌جای ابتدای ساعت انتخاب شده تا احتمال تأخیر کمتر شود.
