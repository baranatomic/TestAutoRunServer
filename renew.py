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
            viewport={
                "width": 1280,
                "height": 720
            }
        )

        page = context.new_page()


        try:

            print("🔄 در حال باز کردن صفحه Login...")

            page.goto(
                "https://control.katabump.com/auth/login",
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_timeout(3000)


            print(f"🌐 URL فعلی: {page.url}")


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


            user_input.wait_for(
                state="visible",
                timeout=15000
            )

            pass_input.wait_for(
                state="visible",
                timeout=15000
            )


            print("✅ فیلدهای Login پیدا شدند.")


            print("🔑 وارد کردن اطلاعات Login...")


            user_input.fill(EMAIL)
            pass_input.fill(PASSWORD)


            submit_btn = page.locator(
                'button[type="submit"], '
                'input[type="submit"]'
            ).first


            submit_btn.click()


            page.wait_for_timeout(5000)


            print(f"🌐 URL بعد از Login: {page.url}")


            if "/auth/login" in page.url:

                print("❌ Login ناموفق")

                page.screenshot(
                    path="login_failed.png"
                )

                return


            print("✅ Login با موفقیت انجام شد.")



            server_url = (
                f"https://control.katabump.com/server/{SERVER_ID}"
            )


            print("")
            print(
                f"🌐 ورود به صفحه سرور {SERVER_ID}"
            )


            page.goto(
                server_url,
                wait_until="domcontentloaded",
                timeout=60000
            )


            page.wait_for_timeout(4000)


            print(
                f"🌐 URL فعلی: {page.url}"
            )


            if f"/server/{SERVER_ID}" not in page.url:

                print("❌ صفحه سرور باز نشد")

                page.screenshot(
                    path="server_failed.png"
                )

                return


            print("✅ صفحه سرور با موفقیت باز شد.")


            print("")
            print("🔍 بررسی دکمه‌های احتمالی Renew")
            print("")


            buttons = page.locator(
                'button:has(svg path[d^="M4 4v5"])'
            )


            count = buttons.count()


            print(
                f"🔎 تعداد دکمه‌ها: {count}"
            )


            for i in range(count):

                print("")
                print("----------------------------")
                print(
                    f"Button شماره {i}"
                )

                btn = buttons.nth(i)


                print(
                    "Visible:",
                    btn.is_visible()
                )


                try:

                    html = btn.evaluate(
                        "(el)=>el.outerHTML"
                    )

                    print(html)


                except Exception as e:

                    print(
                        "خطا در خواندن HTML:",
                        e
                    )


            print("")
            print("========================================")
            print("✅ بررسی کامل شد")
            print("⏸️ هیچ کلیکی انجام نشد")
            print("========================================")


        except Exception as e:

            print("")
            print("❌ خطا:")
            print(e)

            try:

                page.screenshot(
                    path="error.png"
                )

                print(
                    "📸 screenshot ذخیره شد"
                )

            except:
                pass


            raise


        finally:

            browser.close()



if __name__ == "__main__":
    main()
