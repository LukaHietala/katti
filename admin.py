import os
import requests
from flask import Flask, render_template, redirect
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

APP_ID = os.getenv("DISCORD_APP_ID")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BASE_URL = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}

COMMANDS = [{"name": "kissa", "description": "Hae kissankuva", "options": [{"type": 3, "name": "tag", "description": "Kissan tyyppi (esim. cute, funny)", "required": False}]}]

@app.route("/")
def index():
    return render_template("admin.html", commands=requests.get(BASE_URL, headers=HEADERS).json())

@app.route("/register", methods=["POST"])
def register():
    for cmd in COMMANDS:
        requests.post(BASE_URL, json=cmd, headers=HEADERS)
    return redirect("/")

@app.route("/clear", methods=["POST"])
def clear():
    requests.put(BASE_URL, json=[], headers=HEADERS)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
