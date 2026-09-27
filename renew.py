import os
import time
import requests

from datetime import datetime

from playwright.sync_api import sync_playwright


# ============================================================
# ENV
# ============================================================

WORKER_URL = os.environ.get(
    "WORKER_URL"
)

WORKER_SECRET = os.environ.get(
    "WORKER_SECRET"
)

SERVER_KEY = os.environ.get(
    "SERVER_KEY",
    "all"
)

RUN_ID = os.environ.get(
    "RUN_ID",
    ""
)

# ------------------------------------------------------------
# فاصله بین سرورها
# فقط برای اجرای Scheduled
# مقدار بر حسب ثانیه
# 30 دقیقه = 1800
# ------------------------------------------------------------

RENEW_DELAY_SECONDS = int(
    os.environ.get(
        "RENEW_DELAY_SECONDS",
        "1800"
    )
)

# ------------------------------------------------------------
# مشخص می‌کند اجرا از Schedule آمده یا دستی
# ------------------------------------------------------------

EVENT_NAME = os.environ.get(
    "GITHUB_EVENT_NAME",
    ""
)


# ============================================================
# WORKER API
# ============================================================

def worker_headers():

    return {
        "X-Worker-Secret": WORKER_SECRET
    }


def worker_get(
    action,
    server_key=None
):

    if not WORKER_URL:

        raise Exception(
            "WORKER_URL تنظیم نشده است"
        )


    params = {
        "action": action
    }


    if server_key:

        params["server_key"] = server_key


    response = requests.get(

        WORKER_URL,

        params=params,

        headers=worker_headers(),

        timeout=30
    )


    if not response.ok:

        raise Exception(

            f"Worker API error "
            f"{response.status_code}: "
            f"{response.text}"
        )


    return response.json()


def get_server_keys():

    data = worker_get(
        "server_keys"
    )


    if not data.get("ok"):

        raise Exception(

            data.get(
                "error",
                "Unknown Worker error"
            )
        )


    return data.get(
        "servers",
        []
    )


def get_server_config(
    server_key
):

    data = worker_get(

        "server_config",

        server_key
    )


    if not data.get("ok"):

        raise Exception(

            data.get(
                "error",
                "Unknown Worker error"
            )
        )


    server = data.get(
        "server"
    )


    if not server:

        raise Exception(

            f"Server config not found: "
            f"{server_key}"
        )


    return server


# ============================================================
# REPORT RESULT TO WORKER
# ============================================================

def report_result(
    server_key,
    server,
    success,
    status,
    error=None,
    run_id=None
):

    if not WORKER_URL:

        return


    payload = {

        "action":
            "renew_result",

        "run_id":
            run_id or RUN_ID,

        "server_key":
            server_key,

        "server_id":
            server.get(
                "server_id",
                ""
            ),

        "server_name":
            server.get(
                "name",
                server_key
            ),

        "panel_url":
            server.get(
                "panel_url",
                ""
            ),

        "success":
            bool(success),

        "status":
            status,

        "time":
            datetime.utcnow().isoformat()
            + "Z",

        "error":
            str(error)
            if error
            else None
    }


    try:

        response = requests.post(

            WORKER_URL,

            headers={

                "X-Worker-Secret":
                    WORKER_SECRET,

                "Content-Type":
                    "application/json"
            },

            json=payload,

            timeout=30
        )


        if response.ok:

            print(
                f"✅ Worker result reported: "
                f"{server_key}"
            )

        else:

            print(
                f"⚠️ Worker result failed: "
                f"{response.status_code}"
            )

            print(
                response.text
            )


    except Exception as e:

        print(
            "⚠️ Worker report error:",
            e
        )


# ============================================================
# DEBUG
# ============================================================

def debug_page(
    page,
    server_key
):

    try:

        safe_key = (

            server_key
            .replace("/", "_")
            .replace("\\", "_")
        )


        page.screenshot(

            path=
                f"error_{safe_key}.png",

            full_page=True
        )


        with open(

            f"error_{safe_key}.html",

            "w",

            encoding="utf-8"

        ) as f:

            f.write(
                page.content()
            )


    except Exception as e:

        print(
            "Debug error:",
            e
        )


# ============================================================
# RENEW ONE SERVER
# ============================================================

def renew_server(
    server_key,
    server
):

    start_time = (

        datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


    email = server.get(
        "email"
    )

    password = server.get(
        "password"
    )

    server_id = server.get(
        "server_id"
    )

    panel_url = server.get(
        "panel_url"
    )

    server_name = server.get(
        "name",
        server_key
    )


    print(
        "\n========================================"
    )

    print(
        f"🚀 شروع Renew: "
        f"{server_name}"
    )

    print(
        f"🔑 Key: {server_key}"
    )

    print(
        f"🆔 Server ID: {server_id}"
    )

    print(
        f"🕒 Start: {start_time}"
    )

    print(
        "========================================"
    )


    if not email:

        raise Exception(
            "Email/Username تنظیم نشده است"
        )


    if not password:

        raise Exception(
            "Password تنظیم نشده است"
        )


    if not server_id:

        raise Exception(
            "Server ID تنظیم نشده است"
        )


    with sync_playwright() as p:

        browser = None


        try:

            # ------------------------------------------------
            # Browser
            # ------------------------------------------------

            browser =
                p.chromium.launch(
                    headless=True
                )


            context =
                browser.new_context(

                    user_agent=
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/122.0.0.0 "
                        "Safari/537.36",

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


            # ------------------------------------------------
            # Login
            # ------------------------------------------------

            print(
                "🔄 Login..."
            )


            page.goto(

                "https://control.katabump.com/auth/login",

                wait_until="networkidle"
            )


            username_input =
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


            username_input.fill(
                email
            )


            password_input.fill(
                password
            )


            submit =
                page.locator(

                    'button[type="submit"],'
                    'input[type="submit"]'

                ).first


            submit.click()


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


            # ------------------------------------------------
            # Server page
            # ------------------------------------------------

            server_url = (

                "https://control.katabump.com/server/"
                + server_id
            )


            print(
                f"🌐 Opening: {server_url}"
            )


            page.goto(

                server_url,

                wait_until="networkidle"
            )


            page.wait_for_timeout(
                4000
            )


            # ------------------------------------------------
            # Find Renew
            # ------------------------------------------------

            buttons =
                page.locator(

                    'button:has(svg path[d^="M4 4v5"])'

                )


            renew_button = None


            count =
                buttons.count()


            print(
                f"🔎 Renew candidates: {count}"
            )


            for i in range(count):

                button =
                    buttons.nth(i)


                try:

                    if button.is_visible():

                        renew_button =
                            button

                        print(
                            f"✅ Renew button "
                            f"found: {i}"
                        )

                        break

                except Exception:

                    continue


            if not renew_button:

                raise Exception(
                    "Renew button not found"
                )


            # ------------------------------------------------
            # Click
            # ------------------------------------------------

            print(
                "🔄 کلیک Renew..."
            )


            renew_button.click()


            page.wait_for_timeout(
                15000
            )


            print(
                "🎉 Restart triggered"
            )


            # ------------------------------------------------
            # Report success
            # ------------------------------------------------

            report_result(

                server_key=
                    server_key,

                server=
                    server,

                success=
                    True,

                status=
                    "Restart triggered",

                error=
                    None,

                run_id=
                    RUN_ID
            )


            print(
                f"✅ Renew موفق: "
                f"{server_name}"
            )


            return True


        except Exception as e:

            print(
                f"❌ Renew failed: "
                f"{server_name}"
            )


            print(
                str(e)
            )


            try:

                debug_page(
                    page,
                    server_key
                )

            except Exception:

                pass


            # ------------------------------------------------
            # Report failure
            # ------------------------------------------------

            report_result(

                server_key=
                    server_key,

                server=
                    server,

                success=
                    False,

                status=
                    "Renew failed",

                error=
                    str(e),

                run_id=
                    RUN_ID
            )


            return False


        finally:

            if browser:

                try:

                    browser.close()

                except Exception:

                    pass


# ============================================================
# SELECT SERVERS
# ============================================================

def select_servers():

    servers =
        get_server_keys()


    if not servers:

        raise Exception(
            "هیچ سروری در Worker ثبت نشده است"
        )


    if SERVER_KEY == "all":

        return [
            item["key"]
            for item in servers
        ]


    available = {

        item["key"]
        for item in servers
    }


    if SERVER_KEY not in available:

        raise Exception(

            f"Server key not found: "
            f"{SERVER_KEY}"
        )


    return [
        SERVER_KEY
    ]


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n========================================"
    )

    print(
        "🚀 Katabump Multi-Server Renew"
    )

    print(
        "========================================"
    )


    print(
        f"SERVER_KEY: {SERVER_KEY}"
    )

    print(
        f"RUN_ID: {RUN_ID}"
    )

    print(
        f"GITHUB_EVENT_NAME: {EVENT_NAME}"
    )


    if not WORKER_URL:

        raise Exception(
            "WORKER_URL تنظیم نشده است"
        )


    if not WORKER_SECRET:

        raise Exception(
            "WORKER_SECRET تنظیم نشده است"
        )


    # --------------------------------------------------------
    # Determine servers
    # --------------------------------------------------------

    selected_keys =
        select_servers()


    print(
        "\n🖥 Servers:"
    )


    for index, key in enumerate(
        selected_keys,
        start=1
    ):

        print(
            f"{index}. {key}"
        )


    print(
        f"\n📌 تعداد کل: "
        f"{len(selected_keys)}"
    )


    # --------------------------------------------------------
    # Scheduled or manual
    # --------------------------------------------------------

    scheduled_run = (
        EVENT_NAME == "schedule"
    )


    if scheduled_run:

        print(
            "\n⏰ اجرای Schedule"
        )

        print(
            "⏱ فاصله بین سرورها: "
            f"{RENEW_DELAY_SECONDS // 60} دقیقه"
        )

    else:

        print(
            "\n⚡ اجرای دستی"
        )

        print(
            "⏱ بدون فاصله اجباری"
        )


    success_count = 0

    failed_count = 0


    # --------------------------------------------------------
    # Sequential renew
    # --------------------------------------------------------

    for index, server_key in enumerate(
        selected_keys
    ):

        print(
            "\n"
        )

        print(
            "========================================"
        )

        print(
            f"📍 Server "
            f"{index + 1}/"
            f"{len(selected_keys)}"
        )

        print(
            f"🔑 {server_key}"
        )

        print(
            "========================================"
        )


        # ----------------------------------------------------
        # Get config
        # ----------------------------------------------------

        try:

            server =
                get_server_config(
                    server_key
                )

        except Exception as e:

            failed_count += 1


            print(
                f"❌ دریافت تنظیمات "
                f"{server_key} شکست خورد:"
            )

            print(
                str(e)
            )


            continue


        # ----------------------------------------------------
        # Renew
        # ----------------------------------------------------

        try:

            result =
                renew_server(
                    server_key,
                    server
                )


            if result:

                success_count += 1

            else:

                failed_count += 1


        except Exception as e:

            failed_count += 1


            print(
                f"❌ Error: "
                f"{server_key}"
            )


            print(
                str(e)
            )


            try:

                report_result(

                    server_key=
                        server_key,

                    server=
                        server,

                    success=
                        False,

                    status=
                        "Renew failed",

                    error=
                        str(e),

                    run_id=
                        RUN_ID
                )

            except Exception:

                pass


        # ----------------------------------------------------
        # Wait before next server
        # ----------------------------------------------------

        is_last =
            index == (
                len(selected_keys) - 1
            )


        if (
            scheduled_run
            and
            not is_last
        ):

            minutes =
                RENEW_DELAY_SECONDS // 60


            print(
                "\n"
                "========================================"
            )

            print(
                f"⏳ سرور بعدی "
                f"{minutes} دقیقه دیگر"
            )

            print(
                "========================================"
            )


            time.sleep(
                RENEW_DELAY_SECONDS
            )


    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print(
        "\n========================================"
    )

    print(
        "🏁 Renew تمام شد"
    )

    print(
        f"✅ Success: "
        f"{success_count}"
    )

    print(
        f"❌ Failed: "
        f"{failed_count}"
    )

    print(
        "========================================"
    )


    if failed_count > 0:

        raise SystemExit(1)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
