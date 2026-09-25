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

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        r = requests.post(
            url,
            data=data,
            timeout=20
        )

        if r.ok:
            print("📨 پیام تلگرام ارسال شد")
        else:
            print(
                "❌ خطای تلگرام:",
                r.text
            )

    except Exception as e:
        print(
            "❌ Telegram Error:",
            e
        )



def main():


    start_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    if not EMAIL or not PASSWORD:

        send_telegram(
            "❌ Katabump Renew Failed\n\n"
            "Login credentials missing"
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
            viewport={
                "width":1280,
                "height":720
            }
        )


        page = context.new_page()



        try:


            page.goto(
                "https://control.katabump.com/auth/login",
                wait_until="domcontentloaded",
                timeout=60000
            )


            page.wait_for_timeout(3000)



            page.locator(
                'input[name="username"],input[name="email"],input[type="email"],input[type="text"]'
            ).first.fill(
                EMAIL
            )


            page.locator(
                'input[name="password"],input[type="password"]'
            ).first.fill(
                PASSWORD
            )


            page.locator(
                'button[type="submit"],input[type="submit"]'
            ).first.click()


            page.wait_for_timeout(5000)



            if "/auth/login" in page.url:

                raise Exception(
                    "Login failed"
                )



            print("✅ Login موفق")



            server_url = (
                f"https://control.katabump.com/server/{SERVER_ID}"
            )


            page.goto(
                server_url,
                wait_until="domcontentloaded",
                timeout=60000
            )


            page.wait_for_timeout(4000)



            if f"/server/{SERVER_ID}" not in page.url:

                raise Exception(
                    "Server page failed"
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



            print("🔄 کلیک Renew")

            renew.click()



            page.wait_for_timeout(
                15000
            )



            message = f"""
✅ Katabump Renew موفق

🖥 Server:
{SERVER_ID}

🕒 Time:
{start_time}

🔄 Status:
Restart triggered
"""


            send_telegram(
                message
            )


            print(
                "🎉 عملیات موفق"
            )



        except Exception as e:


            message = f"""
❌ Katabump Renew Failed

🖥 Server:
{SERVER_ID}

🕒 Time:
{start_time}

⚠️ Error:
{e}
"""


            send_telegram(
                message
            )


            raise



        finally:

            browser.close()



if __name__ == "__main__":
    main()
