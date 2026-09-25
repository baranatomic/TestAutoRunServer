import os
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright


EMAIL = os.environ.get("KATABUMP_EMAIL")
PASSWORD = os.environ.get("KATABUMP_PASSWORD")
SERVER_ID = os.environ.get("SERVER_ID", "bdfe0e85")

PANEL_URL = os.environ.get("PANEL_URL")

TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_IDS = os.environ.get(
    "TELEGRAM_CHAT_IDS"
)



def send_telegram(message):

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_IDS:
        print("⚠️ Telegram تنظیم نشده")
        return


    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )


    for chat_id in TELEGRAM_CHAT_IDS.split(","):

        chat_id = chat_id.strip()

        if not chat_id:
            continue


        try:

            response = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "text": message
                },
                timeout=20
            )


            if response.ok:
                print(
                    f"📨 پیام ارسال شد به {chat_id}"
                )
            else:
                print(
                    response.text
                )


        except Exception as e:

            print(
                "Telegram error:",
                e
            )



def debug_page(page):

    try:

        page.screenshot(
            path="error_debug.png",
            full_page=True
        )


        with open(
            "error_debug.html",
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                page.content()
            )


    except:

        pass




def main():

    start_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


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
                "Chrome/122.0.0.0 Safari/537.36"
            ),

            viewport={
                "width":1280,
                "height":720
            }
        )


        page = context.new_page()


        page.set_default_timeout(
            60000
        )


        try:


            print("🔄 Login")


            page.goto(
                "https://control.katabump.com/auth/login",
                wait_until="networkidle",
                timeout=60000
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
                state="visible"
            )

            password.wait_for(
                state="visible"
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



            if f"/server/{SERVER_ID}" not in page.url:

                raise Exception(
                    "Server page failed"
                )



            print(
                "✅ صفحه سرور باز شد"
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



            message = f"""
✅ Katabump Renew موفق شد

🖥 Server:
{SERVER_ID}

🌐 Panel:
{PANEL_URL}

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


            debug_page(page)


            message = f"""
❌ Katabump Renew Failed

🖥 Server:
{SERVER_ID}

🌐 Panel:
{PANEL_URL}

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
