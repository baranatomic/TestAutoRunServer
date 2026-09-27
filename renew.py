import os
import json
import requests
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright


# ============================================================
# Environment
# ============================================================

WORKER_URL = os.environ.get("WORKER_URL", "").strip()
WORKER_SECRET = os.environ.get("WORKER_SECRET", "").strip()

SERVER_KEY = os.environ.get("SERVER_KEY", "all").strip()
RUN_ID = os.environ.get("RUN_ID", "").strip()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_IDS = os.environ.get("TELEGRAM_CHAT_IDS", "").strip()

SERVERS_JSON = os.environ.get("KATABUMP_SERVERS_JSON", "").strip()

# Old single-server compatibility
OLD_EMAIL = os.environ.get("KATABUMP_EMAIL", "").strip()
OLD_PASSWORD = os.environ.get("KATABUMP_PASSWORD", "").strip()
OLD_SERVER_ID = os.environ.get("SERVER_ID", "bdfe0e85").strip()
OLD_PANEL_URL = os.environ.get("PANEL_URL", "").strip()


# ============================================================
# Helpers
# ============================================================

def now_local_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()


def generate_run_id():
    if RUN_ID:
        return RUN_ID

    github_run_id = os.environ.get("GITHUB_RUN_ID", "").strip()

    if github_run_id:
        return f"github-{github_run_id}"

    return f"manual-{int(datetime.now().timestamp())}"


# ============================================================
# Server Configuration
# ============================================================

def load_servers():
    """
    Load multi-server configuration from KATABUMP_SERVERS_JSON.

    Expected format:

    {
        "main": {
            "name": "Main Server",
            "server_id": "bdfe0e85",
            "panel_url": "http://51.75.118.5:20086",
            "email": "email@example.com",
            "password": "password"
        },

        "backup": {
            "name": "Backup Server",
            "server_id": "SERVER_ID_2",
            "panel_url": "http://...",
            "email": "email@example.com",
            "password": "password"
        }
    }
    """

    if SERVERS_JSON:
        try:
            data = json.loads(SERVERS_JSON)

            if not isinstance(data, dict):
                raise ValueError(
                    "KATABUMP_SERVERS_JSON must be a JSON object"
                )

            servers = {}

            for key, value in data.items():

                if not isinstance(value, dict):
                    continue

                server_id = str(
                    value.get("server_id", "")
                ).strip()

                email = str(
                    value.get("email", "")
                ).strip()

                password = str(
                    value.get("password", "")
                ).strip()

                if not server_id:
                    raise ValueError(
                        f"Server '{key}' has no server_id"
                    )

                if not email:
                    raise ValueError(
                        f"Server '{key}' has no email"
                    )

                if not password:
                    raise ValueError(
                        f"Server '{key}' has no password"
                    )

                servers[str(key)] = {
                    "key": str(key),
                    "name": str(
                        value.get("name", key)
                    ),
                    "server_id": server_id,
                    "panel_url": str(
                        value.get("panel_url", "")
                    ).strip(),
                    "email": email,
                    "password": password,
                }

            if not servers:
                raise ValueError(
                    "No valid servers found in KATABUMP_SERVERS_JSON"
                )

            return servers

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid KATABUMP_SERVERS_JSON: {e}"
            )

    # --------------------------------------------------------
    # Old single-server compatibility
    # --------------------------------------------------------

    if not OLD_EMAIL:
        raise ValueError(
            "KATABUMP_EMAIL is not configured"
        )

    if not OLD_PASSWORD:
        raise ValueError(
            "KATABUMP_PASSWORD is not configured"
        )

    return {
        "main": {
            "key": "main",
            "name": "Main Server",
            "server_id": OLD_SERVER_ID,
            "panel_url": OLD_PANEL_URL,
            "email": OLD_EMAIL,
            "password": OLD_PASSWORD,
        }
    }


def select_servers(all_servers):
    """
    SERVER_KEY:
      all      -> all servers
      main     -> main only
      backup   -> backup only
    """

    if SERVER_KEY.lower() == "all":
        return list(all_servers.values())

    if SERVER_KEY not in all_servers:
        available = ", ".join(all_servers.keys())

        raise ValueError(
            f"Unknown SERVER_KEY '{SERVER_KEY}'. "
            f"Available servers: {available}"
        )

    return [
        all_servers[SERVER_KEY]
    ]


# ============================================================
# Telegram
# ============================================================

def telegram_api(method):
    if not TELEGRAM_TOKEN:
        return None

    return (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/{method}"
    )


def send_telegram(message):
    if not TELEGRAM_TOKEN:
        print("⚠️ Telegram token is not configured")
        return

    if not TELEGRAM_CHAT_IDS:
        print("⚠️ TELEGRAM_CHAT_IDS is not configured")
        return

    url = telegram_api("sendMessage")

    for chat_id in TELEGRAM_CHAT_IDS.split(","):

        chat_id = chat_id.strip()

        if not chat_id:
            continue

        try:
            response = requests.post(
                url,
                data={
                    "chat_id": chat_id,
                    "text": message,
                },
                timeout=20,
            )

            if response.ok:
                print(
                    f"📨 Telegram message sent to {chat_id}"
                )
            else:
                print(
                    f"Telegram error for {chat_id}: "
                    f"{response.text}"
                )

        except Exception as e:
            print(
                f"Telegram connection error: {e}"
            )


# ============================================================
# Worker Communication
# ============================================================

def report_to_worker(
    server,
    success,
    status,
    error=None,
):
    """
    Notify Cloudflare Worker about the result.

    Worker receives:

    {
        "action": "renew_result",
        "run_id": "...",
        "server_key": "main",
        "success": true,
        "status": "Restart triggered",
        "server_id": "...",
        "server_name": "...",
        "panel_url": "...",
        "time": "...",
        "error": null
    }
    """

    if not WORKER_URL:
        print(
            "⚠️ WORKER_URL is not configured"
        )
        return False

    payload = {
        "action": "renew_result",
        "run_id": generate_run_id(),
        "server_key": server["key"],
        "server_id": server["server_id"],
        "server_name": server["name"],
        "panel_url": server["panel_url"],
        "success": bool(success),
        "status": status,
        "time": now_utc_iso(),
        "error": error,
    }

    headers = {
        "Content-Type": "application/json",
    }

    if WORKER_SECRET:
        headers["X-Worker-Secret"] = WORKER_SECRET

    try:
        response = requests.post(
            WORKER_URL,
            headers=headers,
            json=payload,
            timeout=20,
        )

        if response.ok:
            print(
                f"✅ Worker updated: {server['key']}"
            )
            return True

        print(
            f"⚠️ Worker update failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

    except Exception as e:
        print(
            f"⚠️ Worker connection error: {e}"
        )

    return False


# ============================================================
# Debug
# ============================================================

def debug_page(page, server_key):
    try:
        safe_key = (
            server_key
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        screenshot_name = (
            f"error_{safe_key}.png"
        )

        html_name = (
            f"error_{safe_key}.html"
        )

        page.screenshot(
            path=screenshot_name,
            full_page=True,
        )

        with open(
            html_name,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(
                page.content()
            )

        print(
            f"🐞 Debug files created: "
            f"{screenshot_name}, {html_name}"
        )

    except Exception as e:
        print(
            f"Debug capture failed: {e}"
        )


# ============================================================
# Katabump Renew
# ============================================================

def renew_server(server):
    server_key = server["key"]
    server_name = server["name"]
    server_id = server["server_id"]
    panel_url = server["panel_url"]
    email = server["email"]
    password = server["password"]

    start_time = now_local_string()

    print()
    print("========================================")
    print(
        f"🚀 Starting Katabump Renew"
    )
    print(
        f"🔑 Server Key: {server_key}"
    )
    print(
        f"🖥 Server Name: {server_name}"
    )
    print(
        f"🆔 Server ID: {server_id}"
    )
    print("========================================")

    browser = None

    with sync_playwright() as p:

        try:
            # ------------------------------------------------
            # Browser
            # ------------------------------------------------

            browser = p.chromium.launch(
                headless=True
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={
                    "width": 1280,
                    "height": 720,
                },
            )

            page = context.new_page()

            page.set_default_timeout(
                60000
            )

            # ------------------------------------------------
            # Login
            # ------------------------------------------------

            print("🔄 Login")

            page.goto(
                "https://control.katabump.com/auth/login",
                wait_until="networkidle",
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
                "✅ Login successful"
            )

            # ------------------------------------------------
            # Server page
            # ------------------------------------------------

            server_url = (
                "https://control.katabump.com/"
                f"server/{server_id}"
            )

            print(
                f"🌐 Opening server: {server_url}"
            )

            page.goto(
                server_url,
                wait_until="networkidle",
            )

            page.wait_for_timeout(
                4000
            )

            # ------------------------------------------------
            # Find Renew button
            # ------------------------------------------------

            buttons = page.locator(
                'button:has(svg path[d^="M4 4v5"])'
            )

            renew_button = None

            button_count = buttons.count()

            print(
                f"🔎 Renew buttons found: "
                f"{button_count}"
            )

            for i in range(button_count):

                button = buttons.nth(i)

                try:
                    if button.is_visible():
                        renew_button = button
                        break

                except Exception:
                    continue

            if renew_button is None:
                raise Exception(
                    "Renew button not found"
                )

            # ------------------------------------------------
            # Renew
            # ------------------------------------------------

            print(
                "🔄 Clicking Renew"
            )

            renew_button.click()

            page.wait_for_timeout(
                15000
            )

            print(
                "✅ Renew action triggered"
            )

            # ------------------------------------------------
            # Success
            # ------------------------------------------------

            report_to_worker(
                server=server,
                success=True,
                status="Restart triggered",
                error=None,
            )

            message = (
                "✅ Katabump Renew موفق شد\n\n"
                f"🖥 Server:\n{server_name}\n\n"
                f"🔑 Key:\n{server_key}\n\n"
                f"🆔 Server ID:\n{server_id}\n\n"
                f"🌐 Panel:\n{panel_url}\n\n"
                f"🕒 Time:\n{start_time}\n\n"
                "🔄 Status:\n"
                "Restart triggered"
            )

            print(message)

            return True

        except Exception as e:

            error_text = str(e)

            print(
                f"❌ Renew failed for "
                f"{server_key}: {error_text}"
            )

            try:
                debug_page(
                    page,
                    server_key,
                )
            except Exception:
                pass

            report_to_worker(
                server=server,
                success=False,
                status="Renew failed",
                error=error_text,
            )

            message = (
                "❌ Katabump Renew Failed\n\n"
                f"🖥 Server:\n{server_name}\n\n"
                f"🔑 Key:\n{server_key}\n\n"
                f"🆔 Server ID:\n{server_id}\n\n"
                f"🌐 Panel:\n{panel_url}\n\n"
                f"🕒 Time:\n{start_time}\n\n"
                f"⚠️ Error:\n{error_text}"
            )

            print(message)

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

    print()
    print("========================================")
    print("🤖 Katabump Multi-Server Renew")
    print("========================================")

    print(
        f"SERVER_KEY = {SERVER_KEY}"
    )

    print(
        f"RUN_ID = {generate_run_id()}"
    )

    try:
        servers = load_servers()

    except Exception as e:

        print(
            f"❌ Server configuration error: {e}"
        )

        send_telegram(
            "❌ Katabump configuration error\n\n"
            f"⚠️ Error:\n{e}"
        )

        raise

    print(
        f"📋 Servers configured: "
        f"{len(servers)}"
    )

    print(
        "📋 Available keys: "
        + ", ".join(servers.keys())
    )

    try:
        selected_servers = select_servers(
            servers
        )

    except Exception as e:

        print(
            f"❌ Server selection error: {e}"
        )

        send_telegram(
            "❌ Katabump server selection error\n\n"
            f"⚠️ Error:\n{e}"
        )

        raise

    print(
        f"🎯 Servers selected: "
        f"{len(selected_servers)}"
    )

    successful = 0
    failed = 0

    results = []

    for server in selected_servers:

        success = renew_server(
            server
        )

        results.append(
            {
                "key": server["key"],
                "name": server["name"],
                "success": success,
            }
        )

        if success:
            successful += 1
        else:
            failed += 1

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print()
    print("========================================")
    print("📊 Final Result")
    print("========================================")

    for result in results:

        status = (
            "✅ SUCCESS"
            if result["success"]
            else "❌ FAILED"
        )

        print(
            f"{status} | "
            f"{result['key']} | "
            f"{result['name']}"
        )

    print()
    print(
        f"✅ Successful: {successful}"
    )

    print(
        f"❌ Failed: {failed}"
    )

    print("========================================")

    if failed > 0:

        # Do not send a second Telegram message
        # when the Worker is responsible for result
        # notifications for individual servers.

        raise SystemExit(1)

    print(
        "🎉 All selected servers renewed successfully"
    )


if __name__ == "__main__":
    main()
