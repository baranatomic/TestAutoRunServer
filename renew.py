import os
import sys
import time
import traceback
from datetime import datetime

import requests
from playwright.sync_api import sync_playwright


# ============================================================
# Configuration
# ============================================================

WORKER_URL = os.environ.get("WORKER_URL", "").rstrip("/")
WORKER_SECRET = os.environ.get("WORKER_SECRET", "")

SERVER_KEY = os.environ.get("SERVER_KEY", "all")
RUN_ID = os.environ.get("RUN_ID", "")

# 30 minutes
RENEW_DELAY_SECONDS = int(
    os.environ.get("RENEW_DELAY_SECONDS", "1800")
)

# GitHub event:
# schedule
# workflow_dispatch
EVENT_NAME = os.environ.get(
    "GITHUB_EVENT_NAME",
    ""
)


# ============================================================
# Validation
# ============================================================

def validate_environment():
    if not WORKER_URL:
        raise RuntimeError(
            "WORKER_URL is not configured"
        )

    if not WORKER_SECRET:
        raise RuntimeError(
            "WORKER_SECRET is not configured"
        )

    if not RUN_ID:
        raise RuntimeError(
            "RUN_ID is not configured"
        )


# ============================================================
# Worker API
# ============================================================

def worker_headers():
    return {
        "X-Worker-Secret": WORKER_SECRET,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "katabump-renew/2.0",
    }


def worker_get(action, server_key=None):
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
        raise RuntimeError(
            f"Worker GET failed: "
            f"HTTP {response.status_code} "
            f"{response.text[:1000]}"
        )

    try:
        return response.json()

    except Exception:
        raise RuntimeError(
            "Worker returned invalid JSON: "
            + response.text[:1000]
        )


def worker_post(payload):
    response = requests.post(
        WORKER_URL,
        headers=worker_headers(),
        json=payload,
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"Worker POST failed: "
            f"HTTP {response.status_code} "
            f"{response.text[:1000]}"
        )

    try:
        return response.json()

    except Exception:
        return {
            "ok": True,
            "text": response.text
        }


# ============================================================
# Get server list
# ============================================================

def get_server_keys():
    data = worker_get(
        "server_keys"
    )

    # Supported formats:
    #
    # {
    #   "keys": ["main", "server2"]
    # }
    #
    # or
    #
    # {
    #   "servers": [...]
    # }

    if isinstance(data, list):
        return data

    if isinstance(data.get("keys"), list):
        result = []

        for item in data["keys"]:

            if isinstance(item, str):
                result.append(item)

            elif isinstance(item, dict):

                key = (
                    item.get("key")
                    or item.get("server_key")
                )

                if key:
                    result.append(key)

        return result

    if isinstance(data.get("servers"), list):
        result = []

        for item in data["servers"]:

            if isinstance(item, str):
                result.append(item)

            elif isinstance(item, dict):

                key = (
                    item.get("key")
                    or item.get("server_key")
                )

                if key:
                    result.append(key)

        return result

    raise RuntimeError(
        "Worker server_keys response has no "
        "keys/servers list"
    )


# ============================================================
# Get server configuration
# ============================================================

def get_server_config(server_key):
    data = worker_get(
        "server_config",
        server_key
    )

    # Supported:
    #
    # {
    #   "name": "...",
    #   "server_id": "...",
    #   "panel_url": "...",
    #   "email": "...",
    #   "password": "..."
    # }
    #
    # or:
    #
    # {
    #   "server": {...}
    # }

    if isinstance(data.get("server"), dict):
        config = data["server"]

    else:
        config = data

    required = [
        "server_id",
        "email",
        "password"
    ]

    missing = [
        key
        for key in required
        if not config.get(key)
    ]

    if missing:
        raise RuntimeError(
            f"Server '{server_key}' missing "
            f"configuration: {', '.join(missing)}"
        )

    return config


# ============================================================
# Report result to Worker
# ============================================================

def report_result(
    server_key,
    config,
    success,
    status,
    error=None
):
    payload = {
        "action": "renew_result",

        "run_id": RUN_ID,

        "server_key": server_key,

        "server_id": config.get(
            "server_id",
            ""
        ),

        "server_name": config.get(
            "name",
            server_key
        ),

        "panel_url": config.get(
            "panel_url",
            ""
        ),

        "success": bool(success),

        "status": status,

        "time": datetime.now().isoformat(
            timespec="seconds"
        ),

        "error": error
    }

    try:

        result = worker_post(
            payload
        )

        print(
            f"📡 Worker result: "
            f"{result}"
        )

    except Exception as e:

        print(
            f"⚠️ Could not report result "
            f"to Worker: {e}"
        )


# ============================================================
# Debug
# ============================================================

def save_debug(page, server_key):

    safe_key = (
        server_key
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
    )

    png_file = (
        f"error_{safe_key}.png"
    )

    html_file = (
        f"error_{safe_key}.html"
    )

    try:

        page.screenshot(
            path=png_file,
            full_page=True
        )

        print(
            f"📸 Screenshot saved: "
            f"{png_file}"
        )

    except Exception as e:

        print(
            f"⚠️ Screenshot error: {e}"
        )

    try:

        with open(
            html_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                page.content()
            )

        print(
            f"📄 HTML saved: "
            f"{html_file}"
        )

    except Exception as e:

        print(
            f"⚠️ HTML debug error: {e}"
        )


# ============================================================
# Katabump Renew
# ============================================================

def renew_server(
    server_key,
    config
):
    server_name = config.get(
        "name",
        server_key
    )

    server_id = config.get(
        "server_id"
    )

    email = config.get(
        "email"
    )

    password = config.get(
        "password"
    )

    panel_url = config.get(
        "panel_url",
        ""
    )

    start_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print("")
    print("=" * 60)
    print(
        f"🚀 Starting server: "
        f"{server_name}"
    )
    print(
        f"🔑 Server key: {server_key}"
    )
    print(
        f"🖥 Server ID: {server_id}"
    )
    print("=" * 60)

    browser = None

    try:

        with sync_playwright() as p:

            print(
                "🌐 Launching Chromium..."
            )

            browser = p.chromium.launch(
                headless=True
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/122.0.0.0 "
                    "Safari/537.36"
                ),

                viewport={
                    "width": 1280,
                    "height": 720
                }
            )

            page = context.new_page()

            page.set_default_timeout(
                60000
            )

            # ------------------------------------------------
            # Login
            # ------------------------------------------------

            print(
                "🔐 Login to Katabump..."
            )

            page.goto(
                "https://control.katabump.com/auth/login",
                wait_until="networkidle"
            )

            username_input = page.locator(
                'input[name="username"],'
                'input[name="email"],'
                'input[type="email"],'
                'input[type="text"]'
            ).first

            password_input = page.locator(
                'input[name="password"],'
                'input[type="password"]'
            ).first

            username_input.fill(
                email
            )

            password_input.fill(
                password
            )

            submit_button = page.locator(
                'button[type="submit"],'
                'input[type="submit"]'
            ).first

            submit_button.click()

            page.wait_for_timeout(
                7000
            )

            if "/auth/login" in page.url:

                raise RuntimeError(
                    "Katabump login failed"
                )

            print(
                "✅ Login successful"
            )

            # ------------------------------------------------
            # Server page
            # ------------------------------------------------

            server_url = (
                "https://control.katabump.com/server/"
                f"{server_id}"
            )

            print(
                f"🌐 Opening server page: "
                f"{server_url}"
            )

            page.goto(
                server_url,
                wait_until="networkidle"
            )

            page.wait_for_timeout(
                4000
            )

            # ------------------------------------------------
            # Find Renew button
            # ------------------------------------------------

            print(
                "🔎 Searching for Renew button..."
            )

            buttons = page.locator(
                'button:has(svg path[d^="M4 4v5"])'
            )

            button_count = buttons.count()

            print(
                f"🔎 Found {button_count} "
                f"possible Renew buttons"
            )

            renew_button = None

            for index in range(
                button_count
            ):

                button = buttons.nth(
                    index
                )

                try:

                    if button.is_visible():

                        renew_button = button

                        print(
                            f"✅ Renew button found "
                            f"at index {index}"
                        )

                        break

                except Exception:
                    continue

            if renew_button is None:

                raise RuntimeError(
                    "Renew button not found"
                )

            # ------------------------------------------------
            # Click Renew
            # ------------------------------------------------

            print(
                "🔄 Clicking Renew..."
            )

            renew_button.click()

            print(
                "⏳ Waiting for restart..."
            )

            page.wait_for_timeout(
                15000
            )

            # ------------------------------------------------
            # Success
            # ------------------------------------------------

            print(
                "✅ Restart triggered"
            )

            report_result(
                server_key=server_key,
                config=config,
                success=True,
                status="Restart triggered",
                error=None
            )

            print("")
            print(
                f"🎉 SUCCESS: "
                f"{server_name}"
            )
            print(
                f"🕒 Time: {start_time}"
            )
            print(
                f"🌐 Panel: {panel_url}"
            )

            return True

    except Exception as e:

        error_text = (
            f"{type(e).__name__}: {e}"
        )

        print("")
        print(
            f"❌ FAILED: {server_name}"
        )

        print(
            f"⚠️ Error: {error_text}"
        )

        traceback.print_exc()

        try:

            if "page" in locals():

                save_debug(
                    page,
                    server_key
                )

        except Exception:
            pass

        report_result(
            server_key=server_key,
            config=config,
            success=False,
            status="Renew failed",
            error=error_text
        )

        return False

    finally:

        if browser:

            try:

                browser.close()

            except Exception:
                pass


# ============================================================
# Main
# ============================================================

def main():

    print("")
    print("=" * 60)
    print(
        "🤖 Katabump Auto Renew v2"
    )
    print("=" * 60)

    print(
        f"Worker URL: {WORKER_URL}"
    )

    print(
        f"Server key: {SERVER_KEY}"
    )

    print(
        f"Run ID: {RUN_ID}"
    )

    print(
        f"Event: {EVENT_NAME}"
    )

    print(
        f"Delay: {RENEW_DELAY_SECONDS} seconds"
    )

    print("=" * 60)

    validate_environment()

    # --------------------------------------------------------
    # Determine servers
    # --------------------------------------------------------

    if SERVER_KEY.lower() != "all":

        server_keys = [
            SERVER_KEY
        ]

    else:

        print(
            "📋 Getting server list "
            "from Worker..."
        )

        server_keys = get_server_keys()

    if not server_keys:

        raise RuntimeError(
            "No servers found"
        )

    print("")
    print(
        f"📋 Servers to process: "
        f"{len(server_keys)}"
    )

    for key in server_keys:

        print(
            f"   • {key}"
        )

    # --------------------------------------------------------
    # Schedule mode
    # --------------------------------------------------------

    is_schedule = (
        EVENT_NAME == "schedule"
    )

    if is_schedule:

        print("")
        print(
            "⏰ Schedule mode enabled"
        )

        print(
            "⏱ Servers will run "
            "sequentially with "
            f"{RENEW_DELAY_SECONDS // 60} "
            "minute delay."
        )

    else:

        print("")
        print(
            "🖱 Manual mode enabled"
        )

        print(
            "⏱ No delay between servers."
        )

    # --------------------------------------------------------
    # Process servers
    # --------------------------------------------------------

    successful = 0
    failed = 0

    results = []

    for index, server_key in enumerate(
        server_keys
    ):

        print("")
        print(
            "#" * 60
        )

        print(
            f"SERVER {index + 1}/"
            f"{len(server_keys)}"
        )

        print(
            f"KEY: {server_key}"
        )

        print(
            "#" * 60
        )

        try:

            config = get_server_config(
                server_key
            )

        except Exception as e:

            error_text = (
                f"{type(e).__name__}: {e}"
            )

            print(
                f"❌ Cannot get config "
                f"for {server_key}: "
                f"{error_text}"
            )

            failed += 1

            results.append({
                "server_key": server_key,
                "success": False,
                "error": error_text
            })

            continue

        success = renew_server(
            server_key,
            config
        )

        if success:

            successful += 1

            results.append({
                "server_key": server_key,
                "success": True
            })

        else:

            failed += 1

            results.append({
                "server_key": server_key,
                "success": False
            })

        # ----------------------------------------------------
        # 30-minute delay between scheduled servers
        # ----------------------------------------------------

        if (
            is_schedule
            and index < len(server_keys) - 1
        ):

            print("")
            print("=" * 60)
            print(
                "⏸ Waiting 30 minutes "
                "before next server..."
            )
            print("=" * 60)

            time.sleep(
                RENEW_DELAY_SECONDS
            )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("")
    print("=" * 60)
    print(
        "🏁 Katabump Renew Finished"
    )
    print("=" * 60)

    print(
        f"📊 Total: {len(server_keys)}"
    )

    print(
        f"✅ Successful: {successful}"
    )

    print(
        f"❌ Failed: {failed}"
    )

    print("")
    print("Results:")

    for result in results:

        if result["success"]:

            print(
                f"  ✅ "
                f"{result['server_key']}"
            )

        else:

            print(
                f"  ❌ "
                f"{result['server_key']}"
            )

    print("=" * 60)

    if failed > 0:

        sys.exit(1)

    sys.exit(0)


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()
