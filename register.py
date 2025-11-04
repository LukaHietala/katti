import os
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("DISCORD_APP_ID")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not APP_ID or not BOT_TOKEN:
    print("DISCORD_APP_ID ja DISCORD_BOT_TOKEN pitää olla envissä")
    exit(1)

url = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
headers = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}

commands = [
    {
        "name": "kissa",
        "description": "Hae kissankuva",
        "options": [{
            "type": 3,
            "name": "tag",
            "description": "Kissan tyyppi (esim. orange, white)",
            "required": False
        }]
    }
]

for command in commands:
    response = requests.post(url, json=command, headers=headers)
    if response.ok:
        print(f"/{command['name']} rekisteröity")
    else:
        print(f"Virhe: {response.status_code} {response.text}")
