import os
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright


TELEGRAM_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_IDS = os.environ.get(
    "TELEGRAM_CHAT_IDS"
)

WORKER_URL = os.environ.get(
    "WORKER_URL"
)

WORKER_SECRET = os.environ.get(
    "WORKER_SECRET"
)

SERVER_KEY = os.environ.get(
    "SERVER_KEY"
)

SERVERS_JSON = os.environ.get(
    "KATABUMP_SERVERS_JSON"
)


def telegram_api(method):

    return (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/{method}"
    )


def load_servers():

    if not SERVERS_JSON:

        raise Exception(
            "KATABUMP_SERVERS_JSON is not configured"
        )

    try:

        data = json.loads(
            SERVERS_JSON
        )

    except Exception as e:

        raise Exception(
            f"Invalid KATABUMP_SERVERS_JSON: {e}"
        )

    if not isinstance(data, dict):

        raise Exception(
            "KATABUMP_SERVERS_JSON must be a JSON object"
        )

    return data


def get_server():

    servers =
    load_servers()

    if not SERVER_KEY:

        raise Exception(
            "SERVER_KEY is not configured"
        )

    server =
    servers.get(SERVER_KEY)

    if not server:

        raise Exception(
            f"Unknown server_key: {SERVER_KEY}"
        )

    required = [
        "name",
        "server_id",
        "panel_url",
        "email",
        "password"
    ]

    for field in required:

        if not server.get(field):

            raise Exception(
                f"Missing '{field}' for server '{SERVER_KEY}'"
            )

    return server


def get_pending_message():

    if not WORKER_URL:

        return None

    try:

        r = requests.get(

            WORKER_URL,

            headers={
                "X-Worker-Secret":
                    WORKER_SECRET
            },

            timeout=10

        )


        if r.ok:

            data =
            r.json()

            if data.get("chat_id"):

                return data


    except Exception as e:

        print(
            "KV read error:",
            e
        )


    return None


def edit_telegram(message):

    state =
    get_pending_message()


    if not state:

        print(
            "No pending message"
        )

        send_telegram(
            message
        )

        return


    try:

        requests.post(

            telegram_api(
                "editMessageText"
            ),

            json={

                "chat_id":
                    state["chat_id"],

                "message_id":
                    state["message_id"],

                "text":
                    message

            },

            timeout=20

        )


        print(
            "✅ Telegram message edited"
        )


    except Exception as e:

        print(
            "Edit error:",
            e
        )

        send_telegram(
            message
        )


def send_telegram(message):

    if (
        not TELEGRAM_TOKEN
        or
        not TELEGRAM_CHAT_IDS
    ):

        print(
            "⚠️ Telegram تنظیم نشده"
        )

        return


    url =
    telegram_api(
        "sendMessage"
    )


    for chat_id in (
        TELEGRAM_CHAT_IDS
        .split(",")
    ):

        chat_id =
        chat_id.strip()


        if not chat_id:

            continue


        try:

            response =
            requests.post(

                url,

                data={

                    "chat_id":
                        chat_id,

                    "text":
                        message

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


def update_worker_success(
    server,
    start_time
):

    if not WORKER_URL:

        print(
            "⚠️ WORKER_URL تنظیم نشده"
        )

        return


    try:

        response =
        requests.post(

            WORKER_URL,

            headers={
                "X-Worker-Secret":
                    WORKER_SECRET,

                "Content-Type":
                    "application/json"
            },

            json={

                "action":
                    "renew_success",

                "server_key":
                    SERVER_KEY,

                "time":
                    start_time

            },

            timeout=20

        )


        if response.ok:

            print(
                "✅ Worker state updated"
            )

        else:

            print(
                "⚠️ Worker state update failed:",
                response.status_code,
                response.text
            )


    except Exception as e:

        print(
            "Worker update error:",
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


def renew_server(
    server
):

    email =
    server["email"]

    password =
    server["password"]

    server_id =
    server["server_id"]

    panel_url =
    server["panel_url"]

    server_name =
    server["name"]


    start_time =
    datetime.now().astimezone().isoformat()


    print(
        "========================================"
    )

    print(
        "🚀 شروع Katabump Renew"
    )

    print(
        f"🖥 Server: {server_name}"
    )

    print(
        f"🆔 Server ID: {server_id}"
    )

    print(
        "========================================"
    )


    with sync_playwright() as p:

        browser =
        p.chromium.launch(
            headless=True
        )


        context =
        browser.new_context(

            user_agent=(
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/122.0.0.0 "
                "Safari/537.36"
            ),

            viewport={
                "width": 1280,
                "height": 720
            }

        )


        page =
        context.new_page()


        page.set_default_timeout(
            60000
        )


        try:

            print(
                "🔄 Login"
            )


            page.goto(

                "https://control.katabump.com/auth/login",

                wait_until="networkidle",

                timeout=60000

            )


            username =
            page.locator(

                'input[name="username"],'
                'input[name="email"],'
                'input[type="email"],'
                'input[type="text"]'

            ).first


            password_input =
            page.locator(

                'input[name="password"],'
                'input[type="password"]'

            ).first


            username.wait_for(
                state="visible"
            )


            password_input.wait_for(
                state="visible"
            )


            username.fill(
                email
            )


            password_input.fill(
                password
            )


            page.locator(

                'button[type="submit"],'
                'input[type="submit"]'

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

                f"https://control.katabump.com/server/{server_id}",

                wait_until="networkidle",

                timeout=60000

            )


            page.wait_for_timeout(
                4000
            )


            if (
                f"/server/{server_id}"
                not in page.url
            ):

                raise Exception(
                    "Server page failed"
                )


            print(
                "✅ صفحه سرور باز شد"
            )


            buttons =
            page.locator(
                'button:has(svg path[d^="M4 4v5"])'
            )


            renew = None


            for i in range(
                buttons.count()
            ):

                btn =
                buttons.nth(i)


                if btn.is_visible():

                    renew =
                    btn

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
{server_name}

🆔 Server ID:
{server_id}

🌐 Panel:
{panel_url}

🕒 Time:
{start_time}

🔄 Status:
Restart triggered
"""


            edit_telegram(
                message
            )


            update_worker_success(
                server,
                start_time
            )


            print(
                "🎉 عملیات موفق"
            )


        except Exception as e:

            debug_page(
                page
            )


            message = f"""
❌ Katabump Renew Failed

🖥 Server:
{server_name}

🆔 Server ID:
{server_id}

🌐 Panel:
{panel_url}

🕒 Time:
{start_time}

⚠️ Error:
{e}
"""


            edit_telegram(
                message
            )


            raise


        finally:

            browser.close()


def main():

    server =
    get_server()

    renew_server(
        server
    )


if __name__ == "__main__":

    main()
