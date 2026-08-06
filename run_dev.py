"""
اسکریپت اجرای خودکار سایت Astro (نسخه پرتابل Node.js)
------------------------------------------------------
فقط کافیه دو مسیر زیر رو با مسیر واقعی خودت جایگزین کنی، بعد همین فایل رو
اجرا کنی (دابل‌کلیک، یا از ترمینال: python run_dev.py).

این اسکریپت خودش:
  ۱. پوشه‌ی Node.js رو موقتاً به PATH همین اجرا اضافه می‌کند
  ۲. وارد پوشه‌ی پروژه می‌شود
  ۳. اگر node_modules وجود نداشت، خودکار npm install می‌زند
  ۴. سرور محلی (npm run dev) را اجرا می‌کند
"""

import os
import subprocess
import sys
from pathlib import Path

# ============================================================
# فقط این دو خط رو با مسیر واقعی خودت عوض کن:
# ============================================================
NODE_DIR = r"C:\Users\Alireza.Soroudi\Downloads\node\node"
PROJECT_DIR = r"C:\Users\Alireza.Soroudi\Desktop\OptimizationExpert.github.io"
# ============================================================


def main() -> None:
    node_dir = Path(NODE_DIR)
    project_dir = Path(PROJECT_DIR)

    if not node_dir.exists():
        print(f"❌ پوشه‌ی Node پیدا نشد: {node_dir}")
        sys.exit(1)

    if not project_dir.exists():
        print(f"❌ پوشه‌ی پروژه پیدا نشد: {project_dir}")
        sys.exit(1)

    npm_cmd = node_dir / "npm.cmd"
    if not npm_cmd.exists():
        print(f"❌ npm.cmd توی این پوشه پیدا نشد: {npm_cmd}")
        sys.exit(1)

    # اضافه‌کردن پوشه‌ی Node به PATH همین پردازش (موقت، فقط برای این اجرا)
    env = os.environ.copy()
    env["PATH"] = str(node_dir) + os.pathsep + env.get("PATH", "")

    print(f"📁 پوشه‌ی پروژه: {project_dir}")
    print(f"🟢 پوشه‌ی Node:   {node_dir}\n")

    node_modules = project_dir / "node_modules"
    if not node_modules.exists():
        print("📦 node_modules پیدا نشد — در حال نصب پکیج‌ها (npm install)...\n")
        result = subprocess.run(
            [str(npm_cmd), "install"],
            cwd=str(project_dir),
            env=env,
        )
        if result.returncode != 0:
            print("\n❌ نصب پکیج‌ها با خطا مواجه شد.")
            sys.exit(1)
        print("\n✅ نصب پکیج‌ها با موفقیت انجام شد.\n")
    else:
        print("📦 node_modules از قبل موجوده — از نصب دوباره صرف‌نظر شد.\n")

    print("🚀 در حال اجرای سرور محلی (npm run dev)...\n")
    print("   برای توقف سرور، کلیدهای Ctrl+C را بزنید.\n")

    subprocess.run(
        [str(npm_cmd), "run", "dev"],
        cwd=str(project_dir),
        env=env,
    )


if __name__ == "__main__":
    main()
