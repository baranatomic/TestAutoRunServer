import os
from playwright.sync_api import sync_playwright


EMAIL = os.environ.get("KATABUMP_EMAIL")
PASSWORD = os.environ.get("KATABUMP_PASSWORD")
SERVER_ID = os.environ.get("SERVER_ID", "bdfe0e85")


def main():

    if not EMAIL or not PASSWORD:
        print("❌ اطلاعات Login موجود نیست")
        return


    print("========================================")
    print("🚀 شروع Katabump Renew")
    print("========================================")


    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )


        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/122 Safari/537.36"
            ),
            viewport={
                "width":1280,
                "height":720
            }
        )


        page = context.new_page()


        try:


            print("🔄 Login...")


            page.goto(
                "https://control.katabump.com/auth/login",
                wait_until="domcontentloaded",
                timeout=60000
            )


            page.wait_for_timeout(3000)


            page.locator(
                'input[name="username"],input[name="email"],input[type="email"],input[type="text"]'
            ).first.fill(EMAIL)


            page.locator(
                'input[name="password"],input[type="password"]'
            ).first.fill(PASSWORD)



            page.locator(
                'button[type="submit"],input[type="submit"]'
            ).first.click()



            page.wait_for_timeout(5000)



            if "/auth/login" in page.url:

                print("❌ Login شکست خورد")
                return


            print("✅ Login موفق")


            server_url = (
                f"https://control.katabump.com/server/{SERVER_ID}"
            )


            print(
                "🌐 رفتن به:",
                server_url
            )


            page.goto(
                server_url,
                wait_until="domcontentloaded",
                timeout=60000
            )


            page.wait_for_timeout(4000)


            if f"/server/{SERVER_ID}" not in page.url:

                print("❌ صفحه سرور باز نشد")
                return


            print("✅ صفحه سرور باز شد")



            # پیدا کردن دکمه Renew واقعی

            buttons = page.locator(
                'button:has(svg path[d^="M4 4v5"])'
            )


            renew = None


            for i in range(buttons.count()):

                btn = buttons.nth(i)

                if btn.is_visible():

                    renew = btn
                    print(
                        f"✅ Renew پیدا شد - Button {i}"
                    )

                    break



            if renew is None:

                print(
                    "❌ دکمه Renew پیدا نشد"
                )

                return



            print("🔄 در حال کلیک Renew...")


            renew.click()


            print(
                "✅ کلیک انجام شد"
            )


            print(
                "⏳ انتظار برای اعمال Restart..."
            )


            page.wait_for_timeout(
                15000
            )


            print(
                "🌐 URL بعد از کلیک:",
                page.url
            )


            print(
                "========================================"
            )

            print(
                "🎉 عملیات Renew انجام شد"
            )

            print(
                "========================================"
            )



        except Exception as e:


            print(
                "❌ خطا:",
                e
            )


            try:

                page.screenshot(
                    path="error.png"
                )

                print(
                    "📸 error.png ذخیره شد"
                )

            except:

                pass


            raise



        finally:

            browser.close()



if __name__ == "__main__":
    main()
