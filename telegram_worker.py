import os
import requests
import json


BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN"
)

PANEL = os.environ.get(
    "PANEL_URL"
)

CHAT_IDS = [
    x.strip()
    for x in os.environ.get(
        "TELEGRAM_CHAT_IDS",
        ""
    ).split(",")
    if x.strip()
]


GH_PAT = os.environ.get(
    "GH_PAT"
)


OWNER = os.environ.get(
    "GITHUB_OWNER",
    "baranatomic"
)

REPO = os.environ.get(
    "GITHUB_REPO",
    "TestAutoRunServer"
)


OFFSET_FILE = "telegram_offset.txt"



def send_message(chat_id, text):

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": text
        },
        timeout=20
    )



def get_offset():

    try:

        with open(
            OFFSET_FILE,
            "r"
        ) as f:
            return int(f.read())

    except:

        return 0



def save_offset(offset):

    with open(
        OFFSET_FILE,
        "w"
    ) as f:
        f.write(
            str(offset)
        )



def run_renew():

    url = (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/actions/workflows/"
        f"renew.yml/dispatches"
    )


    headers = {

        "Accept":
        "application/vnd.github+json",

        "Authorization":
        f"Bearer {GH_PAT}"

    }


    response = requests.post(
        url,
        headers=headers,
        json={
            "ref":"main"
        },
        timeout=30
    )


    return response.status_code == 204




def main():


    offset = get_offset()


    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/getUpdates"
    )


    response = requests.get(
        url,
        params={
            "offset": offset + 1,
            "timeout": 10
        },
        timeout=20
    )


    data = response.json()


    for update in data.get(
        "result",
        []
    ):


        save_offset(
            update["update_id"]
        )


        message = update.get(
            "message"
        )


        if not message:
            continue


        chat_id = str(
            message["chat"]["id"]
        )


        if chat_id not in CHAT_IDS:

            continue


        text = message.get(
            "text",
            ""
        )


        if text == "/help":


            send_message(
                chat_id,
                """
🤖 Katabump Bot

/renew
🔄 Restart Server

/panel
🌐 Open Panel

/help
ℹ️ Help
"""
            )


        elif text == "/panel":


            send_message(
                chat_id,
                """
🌐 Panel:

f"{PANEL}"
"""
            )



        elif text == "/renew":


            ok = run_renew()


            if ok:

                send_message(
                    chat_id,
                    """
⏳ Renew request sent

GitHub Action started.
You will receive result notification.
"""
                )

            else:

                send_message(
                    chat_id,
                    """
❌ Cannot start GitHub Action
"""
                )



if __name__ == "__main__":

    main()
