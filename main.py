import os
import time
import requests
from flask import Flask, request, jsonify
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY")
if not PUBLIC_KEY:
    print("DISCORD_PUBLIC_KEY puuttuu")
    exit(1)


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


@app.route("/", methods=["POST"])
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
    
    # komennot
    if data.get("type") == 2:
        command_name = data.get("data", {}).get("name")
        
        if command_name == "kissa":
            options = data.get("data", {}).get("options", [])
            tag = options[0].get("value", "") if options else ""
            
            try:
                image_url = get_cat(tag)
                return jsonify({
                    "type": 4,
                    "data": {"embeds": [{"image": {"url": image_url}}]}
                })
            except:
                return jsonify({
                    "type": 4,
                    "data": {
                        "content": "Sopivan kissan löytyminen ei onnistunut",
                        "flags": 64 # ephemeral viesti
                    }
                })
    
    return jsonify({"error": "unknown interaction"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
