import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright


EMAIL = os.environ.get("KATABUMP_EMAIL")
PASSWORD = os.environ.get("KATABUMP_PASSWORD")
SERVER_ID = os.environ.get("SERVER_ID", "bdfe0e85")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(message):

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram تنظیم نشده")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=20
        )

        print("📨 پیام تلگرام ارسال شد")

    except Exception as e:
        print("Telegram error:", e)



def debug_page(page, name):

    try:
        page.screenshot(
            path=f"{name}.png",
            full_page=True
        )

        with open(
            f"{name}.html",
            "w",
            encoding="utf-8"
        ) as f:
            f.write(page.content())

        print(
            f"📸 Debug saved: {name}.png / {name}.html"
        )

    except Exception as e:
        print(
            "Debug error:",
            e
        )



def main():

    start_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    if not EMAIL or not PASSWORD:

        send_telegram(
            "❌ Katabump Renew\n\n"
            "Missing Login Secrets"
        )

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
                "(KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),

            viewport={
                "width":1280,
                "height":720
            }

        )


        page = context.new_page()


        page.set_default_timeout(60000)



        try:


            print("🔄 باز کردن Login")


            page.goto(
                "https://control.katabump.com/auth/login",
                wait_until="networkidle",
                timeout=60000
            )


            print(
                "URL:",
                page.url
            )


            print(
                "🔍 انتظار برای فیلد Login"
            )


            username = page.locator(
                'input[name="username"],'
                'input[name="email"],'
                'input[type="email"],'
                'input[type="text"]'
            ).first


            password = page.locator(
                'input[name="password"],'
                'input[type="password"]'
            ).first


            username.wait_for(
                state="visible",
                timeout=60000
            )


            password.wait_for(
                state="visible",
                timeout=60000
            )


            print(
                "✅ فیلدها پیدا شدند"
            )


            username.fill(
                EMAIL
            )

            password.fill(
                PASSWORD
            )


            page.locator(
                'button[type="submit"],input[type="submit"]'
            ).first.click()


            page.wait_for_timeout(
                7000
            )


            if "/auth/login" in page.url:

                raise Exception(
                    "Login failed"
                )


            print(
                "✅ Login موفق"
            )



            page.goto(
                f"https://control.katabump.com/server/{SERVER_ID}",
                wait_until="networkidle",
                timeout=60000
            )


            page.wait_for_timeout(
                4000
            )


            print(
                "Server URL:",
                page.url
            )



            buttons = page.locator(
                'button:has(svg path[d^="M4 4v5"])'
            )


            renew = None


            for i in range(buttons.count()):

                btn = buttons.nth(i)

                if btn.is_visible():

                    renew = btn
                    break



            if renew is None:

                raise Exception(
                    "Renew button not found"
                )


            print(
                "🔄 کلیک Renew"
            )


            renew.click()


            page.wait_for_timeout(
                15000
            )


            send_telegram(
                f"""
✅ Katabump Renew موفق

🖥 Server:
{SERVER_ID}

🕒 Time:
{start_time}

Status:
Restart triggered
"""
            )


            print(
                "🎉 موفق"
            )



        except Exception as e:


            debug_page(
                page,
                "error_debug"
            )


            send_telegram(
                f"""
❌ Katabump Renew Failed

Server:
{SERVER_ID}

Time:
{start_time}

Error:
{str(e)}
"""
            )


            raise



        finally:

            browser.close()



if __name__ == "__main__":
    main()
