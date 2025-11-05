import os
import requests
from flask import Flask, render_template, redirect, session, request
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = "HyvinSalainenAvain"

APP_ID = os.getenv("DISCORD_APP_ID")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ADMIN_PASS = os.getenv("ADMIN_PASS")
BASE_URL = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}

COMMANDS = [{"name": "kissa", "description": "Hae kissankuva", "options": [{"type": 3, "name": "tag", "description": "Kissan tyyppi (esim. cute, funny)", "required": False}]}]

@app.route("/")
def index():
    if not session.get("op"):
        return redirect("/login")
    return render_template("admin.html", commands=requests.get(BASE_URL, headers=HEADERS).json())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # sessioneilla niinkuin pitää
        if request.form.get("password") == ADMIN_PASS:
            session["op"] = True
            return redirect("/")
        return render_template("wrong.html")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("op", None)
    return redirect("/login")

@app.route("/register", methods=["POST"])
def register():
    if not session.get("op"):
        return redirect("/login")
    for cmd in COMMANDS:
        requests.post(BASE_URL, json=cmd, headers=HEADERS)
    return redirect("/")

@app.route("/clear", methods=["POST"])
def clear():
    if not session.get("op"):
        return redirect("/login")
    requests.put(BASE_URL, json=[], headers=HEADERS)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
