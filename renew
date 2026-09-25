import os
from playwright.sync_api import sync_playwright

EMAIL = os.environ.get("KATABUMP_EMAIL")
PASSWORD = os.environ.get("KATABUMP_PASSWORD")
SERVER_ID = os.environ.get("SERVER_ID", "bdfe0e85")


def main():
    if not EMAIL or not PASSWORD:
        print("❌ خطا: متغیرهای KATABUMP_EMAIL یا KATABUMP_PASSWORD تعریف نشده‌اند.")
        return

    print("========================================")
    print("🚀 شروع بررسی Katabump")
    print("========================================")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720}
        )

        page = context.new_page()

        try:
            # ----------------------------------------
            # 1. باز کردن صفحه Login
            # ----------------------------------------
            print("🔄 در حال باز کردن صفحه Login...")

            page.goto(
                "https://control.katabump.com/auth/login",
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(3000)

            print(f"🌐 URL فعلی: {page.url}")

            # ----------------------------------------
            # 2. پیدا کردن فیلدهای Login
            # ----------------------------------------
            print("🔍 در حال پیدا کردن فیلدهای Login...")

            user_input = page.locator(
                'input[name="username"], '
                'input[name="email"], '
                'input[type="text"], '
                'input[type="email"]'
            ).first

            pass_input = page.locator(
                'input[name="password"], '
                'input[type="password"]'
            ).first

            user_input.wait_for(state="visible", timeout=15000)
            pass_input.wait_for(state="visible", timeout=15000)

            print("✅ فیلدهای Login پیدا شدند.")

            # ----------------------------------------
            # 3. وارد کردن اطلاعات
            # ----------------------------------------
            print("🔑 در حال وارد کردن اطلاعات Login...")

            user_input.fill(EMAIL)
            pass_input.fill(PASSWORD)

            # ----------------------------------------
            # 4. کلیک روی Login
            # ----------------------------------------
            submit_btn = page.locator(
                'button[type="submit"], '
                'input[type="submit"]'
            ).first

            submit_btn.wait_for(state="visible", timeout=10000)

            print("🔐 در حال ارسال فرم Login...")

            submit_btn.click()

            # کمی زمان برای پردازش Login
            page.wait_for_timeout(5000)

            print(f"🌐 URL بعد از Login: {page.url}")

            # ----------------------------------------
            # 5. بررسی موفقیت Login
            # ----------------------------------------

            # اگر هنوز در صفحه Login هستیم،
            # احتمالاً Login ناموفق بوده است.
            if "/auth/login" in page.url:
                print("❌ Login موفق نبود.")
                print("❌ هنوز در صفحه Login هستیم.")

                page.screenshot(path="login_failed.png")

                return

            print("✅ Login با موفقیت انجام شد.")

            # ----------------------------------------
            # 6. رفتن به صفحه سرور
            # ----------------------------------------
            server_url = f"https://control.katabump.com/server/{SERVER_ID}"

            print("")
            print(f"🌐 در حال ورود به صفحه سرور {SERVER_ID}...")
            print(f"🔗 {server_url}")

            page.goto(
                server_url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(4000)

            print(f"🌐 URL فعلی: {page.url}")

            # ----------------------------------------
            # 7. بررسی اینکه واقعاً صفحه سرور باز شده
            # ----------------------------------------

            if f"/server/{SERVER_ID}" not in page.url:
                print("❌ صفحه سرور باز نشد.")
                print("❌ احتمالاً Session/Login معتبر نیست.")

                page.screenshot(path="server_page_failed.png")

                return

            print("✅ صفحه سرور با موفقیت باز شد.")

            # ----------------------------------------
            # 8. بررسی وجود دکمه Renew
            # ----------------------------------------
            print("")
            print("🔍 در حال بررسی دکمه Renew...")

            # دکمه‌ای که HTML آن را فرستادی:
            #
            # <button class="...">
            #   <svg ...>
            #      ...
            #   </svg>
            # </button>
            #
            # چون متن ندارد، از وجود SVG با path مربوط
            # به آیکون refresh استفاده می‌کنیم.

            renew_btn = page.locator(
                'button:has(svg path[d^="M4 4v5"])'
            )

            count = renew_btn.count()

            print(f"🔎 تعداد دکمه‌های احتمالی Renew: {count}")

            if count > 0:
                if renew_btn.first.is_visible():
                    print("✅ دکمه Renew پیدا شد.")
                    print("⏸️ فعلاً هیچ کلیکی انجام نمی‌شود.")
                else:
                    print("ℹ️ دکمه Renew وجود دارد ولی قابل مشاهده نیست.")
            else:
                print("ℹ️ دکمه Renew پیدا نشد.")

            print("")
            print("========================================")
            print("✅ تست Login و ورود به صفحه Server موفق بود.")
            print("⏸️ Renew هنوز اجرا نشده است.")
            print("========================================")

        except Exception as e:
            print("")
            print("========================================")
            print("❌ خطا")
            print("========================================")
            print(f"{e}")

            try:
                page.screenshot(path="error_screenshot.png")
                print("📸 Screenshot ذخیره شد: error_screenshot.png")
            except Exception:
                pass

            raise

        finally:
            browser.close()


if __name__ == "__main__":
    main()
