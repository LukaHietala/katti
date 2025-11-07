import os
import time
import requests
from flask import Flask, request, jsonify, render_template, redirect, session, send_file
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from dotenv import load_dotenv
import database

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# alustaa tietokannan automaattisesti
database.init()

PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
APP_ID = os.getenv("DISCORD_APP_ID")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ADMIN_PASS = os.getenv("ADMIN_PASS")

if not PUBLIC_KEY:
    print("DISCORD_PUBLIC_KEY puuttuu")
    exit(1)

BASE_URL = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}", "Content-Type": "application/json"}

COMMANDS = [
    {"name": "kissa", "description": "Hae kissankuva", "options": [{"type": 3, "name": "tagi", "description": "Kissan tyyppi (esim. cute, loaf, lazy)", "required": False, "autocomplete": True}]},
    {
        "name": "kissa-sanoo",
        "description": "Kissa sanoo jotain",
        "options": [
            {"type": 3, "name": "lause", "description": "Mitä kissa sanoo?", "required": True},
            {"type": 3, "name": "id", "description": "Söpö mirri mielessä? Katso katti.wisdurm.fi sivulta tämän ID.", "required": False},
            {"type": 3, "name": "tagi", "description": "Kissan tagi (esim. evil, funny)", "required": False, "autocomplete": True}
        ]
    },
    {"name": "ohjeet", "description": "Ohjeet katin käyttöön"}
]

# Tagejä on oli 1000 niin säilytetään ne muistissa 1 tunti kerrallaan
class TagCache:
    def __init__(self):
        self.tags = []
        self.last_updated = 0
        self.cache_duration = 3600 # 1 tunti
    
    def get_tags(self):
        if not self.tags or (time.time() - self.last_updated) > self.cache_duration:
            self.fetch_tags()
        return self.tags
    
    def fetch_tags(self):
        try:
            response = requests.get("https://cataas.com/api/tags", timeout=5)
            response.raise_for_status()
            self.tags = response.json()
            self.last_updated = time.time()
        except Exception as e:
            print(f"Virhe tagien haussa: {e}")

    def filter(self, query):
        limit = 25 # discordin limit on 25
        tags = self.get_tags()
        
        if not query:
            return tags[:limit]
        
        query_lower = query.lower()
        
        # tagit jotka alkaa queryllä
        starts_with = [tag for tag in tags if tag.lower().startswith(query_lower)]
        
        # tagit jotka sisältää queryn
        if len(starts_with) < limit:
            contains = [tag for tag in tags if query_lower in tag.lower() and tag not in starts_with]
            starts_with.extend(contains)
        
        return starts_with[:limit]


tag_cache = TagCache()


def verify_request(public_key, signature, timestamp, body):
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key))
        verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError):
        return False


def get_cat(tag=""):
    url = f"https://cataas.com/cat/{tag}?json=true" if tag else "https://cataas.com/cat?json=true"
    response = requests.get(url)
    response.raise_for_status()
    cat_data = response.json()
    return f"{cat_data['url']}&t={time.time_ns()}"


@app.route("/api", methods=["POST"])
def interactions():
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    
    if not signature or not timestamp:
        return jsonify({"error": "invalid request"}), 401
    
    if not verify_request(PUBLIC_KEY, signature, timestamp, request.data.decode("utf-8")):
        return jsonify({"error": "invalid request signature... epäilyttävää"}), 401
    
    data = request.json or {}
    
    # discordin ping pong testi
    if data.get("type") == 1:
        return jsonify({"type": 1})
    
    # autocomplete interaktio
    if data.get("type") == 4:
        options = data.get("data", {}).get("options", [])
        
        # etsi fokuksessa oleva kenttä
        for option in options:
            if option.get("focused") and option.get("name") == "tagi":
                query = option.get("value", "")
                filtered_tags = tag_cache.filter(query.strip())
                choices = [{"name": tag, "value": tag} for tag in filtered_tags if tag]
                
                return jsonify({
                    "type": 8,
                    "data": {"choices": choices}
                })
        
        # jos ei tag kenttä fokuksessa
        return jsonify({
            "type": 8,
            "data": {"choices": []}
        })
    
    # komennot
    if data.get("type") == 2:
        command_name = data.get("data", {}).get("name")
        
        if command_name == "kissa":
            options = data.get("data", {}).get("options", [])
            tag = options[0].get("value", "").strip() if options else ""
            user = data.get("member", {}).get("user") or data.get("user", {})
            user_id = user.get("id", "tuntematon?")
            username = user.get("username", "tuntematon?")
            
            try:
                image_url = get_cat(tag)
                
                database.save_cat(user_id, username, image_url, tag if tag else None)
                
                return jsonify({
                    "type": 4,
                    "data": {"embeds": [{"image": {"url": image_url}}]}
                })
            except:
                return jsonify({
                    "type": 4,
                    "data": {
                        "embeds": [{"image": {"url": "https://i.pinimg.com/236x/5e/ba/fa/5ebafa8eb9235024a3fa8b683763f3b8.jpg"}}],
                        "flags": 64 # ephemeral viesti
                    }
                })
        
        if command_name == "kissa-sanoo":
            options = data.get("data", {}).get("options", [])
            
            # gifit tulevaisuudessa koska discord rajoitukset
            # kuvan muokkaus logiikka serverille

            text = ""
            cat_id = None
            tag = None
            
            for option in options:
                if option.get("name") == "lause":
                    text = option.get("value", "").strip()
                elif option.get("name") == "id":
                    cat_id = option.get("value", "").strip()
                elif option.get("name") == "tagi":
                    tag = option.get("value", "").strip()
            
            try:
                if cat_id:
                    url = f"https://cataas.com/cat/{cat_id}/says/{text}?json=true"
                elif tag:
                    url = f"https://cataas.com/cat/{tag}/says/{text}?json=true"
                else:
                    url = f"https://cataas.com/cat/says/{text}?json=true"
                
                response = requests.get(url)
                response.raise_for_status()
                cat_data = response.json()
                image_url = f"{cat_data['url']}&t={time.time_ns()}"
                
                return jsonify({
                    "type": 4,
                    "data": {
                        "embeds": [{"image": {"url": image_url}}],
                    }
                })
            except Exception as e:
                return jsonify({
                    "type": 4,
                    "data": {
                        "content": f"Virhe kissan haussa, ehkä huono tagi?",
                        "flags": 64 
                    }
                })
        
        if command_name == "ohjeet":
            return jsonify({
                "type": 4,
                "data": {
                    "embeds": [{"image": {"url": "https://cataas.com/cat/QAtGIn7ufSOehRp6"}}],
                    "flags": 64 
                }
            })
    
    return jsonify({"error": "unknown interaction"}), 400


# julkinen kissojen galleria
@app.route("/")
def cats_page():
    all_cats = database.get_all_cats(limit=1000)
    return render_template("kissat.html", cats=all_cats)

# jäännös
@app.route("/kissat")
def kissat_empty():
    return render_template("empty.html")

# admin hommat
@app.route("/admin")
def admin_index():
    if not session.get("op"):
        return redirect("/admin/login")
    
    all_cats = database.get_all_cats(limit=1000)
    
    return render_template("admin.html", commands=requests.get(BASE_URL, headers=HEADERS).json(), cats=all_cats)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        # sessioneilla :katti:
        if request.form.get("password") == ADMIN_PASS:
            session["op"] = True
            return redirect("/admin")
        return render_template("wrong.html")
    return render_template("login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("op", None)
    return redirect("/admin/login")

@app.route("/admin/register", methods=["POST"])
def admin_register():
    if not session.get("op"):
        return redirect("/admin/login")
    for cmd in COMMANDS:
        requests.post(BASE_URL, json=cmd, headers=HEADERS)
    return redirect("/admin")

@app.route("/admin/clear", methods=["POST"])
def admin_clear():
    if not session.get("op"):
        return redirect("/admin/login")
    requests.put(BASE_URL, json=[], headers=HEADERS)
    return redirect("/admin")

@app.route("/admin/delete/<int:cat_id>", methods=["POST"])
def admin_delete_cat(cat_id):
    if not session.get("op"):
        return redirect("/admin/login")
    database.delete_cat(cat_id)
    return redirect("/admin")

# cachettaa kissakuvat serverille, ettei apia tarvi rasittaa 😇
@app.route("/kuvat/<path:image_path>")
def cache_image(image_path):
    cache_dir = "static/cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # alkuperäinen cat/dGHQY0rqSzbmiaJO?position=center url
    filename = image_path.replace("/", "_")
    cache_path = os.path.join(cache_dir, filename)
    # -> cat_dGHQY0rqSzbmiaJO tiedostopolku
    
    # lataa jos ei cachessa
    if not os.path.exists(cache_path):
        try:
            img_url = f"https://cataas.com/{image_path}"
            response = requests.get(img_url, timeout=10)
            with open(cache_path, 'wb') as f:
                f.write(response.content)
        except:
            return "virhe", 404
    
    # lähetä kuva clientille
    return send_file(cache_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
