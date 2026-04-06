#!/usr/bin/env python3
"""
Launch token pertama di pump.fun via ClawPump (GRATIS / gasless).
Jalankan signup.py dulu sebelum ini.

Usage:
    python examples/launch_token.py \
        --name "NamaToken" --symbol "TKN" \
        --description "Deskripsi token kamu" \
        --image ./logo.png
"""

import os, sys, json, argparse, requests

CREDS_FILE = "clawpump-creds.json"
BASE_URL   = "https://clawpump.tech"

GREEN="\033[92m";YELLOW="\033[93m";RED="\033[91m";CYAN="\033[96m";BOLD="\033[1m";RESET="\033[0m"
def log(m, c=""): print(f"{c}{m}{RESET}")

def load_creds():
    if not os.path.exists(CREDS_FILE):
        log(f"❌ {CREDS_FILE} tidak ditemukan. Jalankan signup.py dulu!", RED); sys.exit(1)
    with open(CREDS_FILE) as f: return json.load(f)

def upload_image(path, api_key):
    log("  📤 Uploading gambar...", YELLOW)
    with open(path, "rb") as f:
        r = requests.post(f"{BASE_URL}/api/upload",
            files={"image": f},
            headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"): raise Exception(f"Upload gagal: {data}")
    log(f"  ✅ Uploaded: {data['imageUrl']}", GREEN)
    return data["imageUrl"]

def launch(api_key, name, symbol, desc, img, website=None, twitter=None, telegram=None):
    payload = {"name":name,"symbol":symbol,"description":desc,"imageUrl":img}
    if website:  payload["website"]  = website
    if twitter:  payload["twitter"]  = twitter
    if telegram: payload["telegram"] = telegram

    log("  🚀 Launching ke pump.fun (gasless)...", YELLOW)
    r = requests.post(f"{BASE_URL}/api/launch", json=payload,
        headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
        timeout=60)

    if r.status_code == 401: log("❌ API key invalid. Re-run signup.py", RED); sys.exit(1)
    if r.status_code == 429:
        h = r.json().get("retryAfterHours","?")
        log(f"⏳ Rate limited. Coba lagi dalam {h} jam.", YELLOW); sys.exit(0)
    if r.status_code == 503:
        log("⚠️  Gasless treasury low. Coba self-funded launch.", YELLOW); sys.exit(1)
    r.raise_for_status()
    return r.json()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name",        required=True)
    p.add_argument("--symbol",      required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--image",       required=True)
    p.add_argument("--website",  default=None)
    p.add_argument("--twitter",  default=None)
    p.add_argument("--telegram", default=None)
    a = p.parse_args()

    print()
    log("╔══════════════════════════════════════════════════╗", CYAN)
    log("║       ClawPump — Token Launch Script            ║", CYAN)
    log("╚══════════════════════════════════════════════════╝", CYAN)
    print()

    creds = load_creds()
    log(f"  ✅ Agent: {creds['agentName']} ({creds['agentId']})", GREEN)
    print()

    if not os.path.exists(a.image):
        log(f"❌ Gambar tidak ditemukan: {a.image}", RED); sys.exit(1)

    log("[1/2] Upload Image", BOLD)
    image_url = upload_image(a.image, creds["apiKey"])
    print()

    log("[2/2] Launch Token", BOLD)
    result = launch(creds["apiKey"], a.name, a.symbol, a.description,
                    image_url, a.website, a.twitter, a.telegram)
    print()

    log("╔══════════════════════════════════════════════════╗", GREEN)
    log("║          🎉 TOKEN LAUNCHED SUCCESSFULLY!        ║", GREEN)
    log("╚══════════════════════════════════════════════════╝", GREEN)
    print()
    log(f"  Token     :  {a.name} (${a.symbol})", BOLD)
    log(f"  Mint      :  {result.get('mintAddress')}")
    log(f"  pump.fun  :  {result.get('pumpUrl')}", CYAN)
    log(f"  Explorer  :  {result.get('explorerUrl')}", CYAN)
    print()

    social = result.get("socialAmplification", {})
    tmpl   = social.get("twitter", {}).get("template", "")
    intent = social.get("twitter", {}).get("tweetIntentUrl", "")
    if tmpl:
        log("  📣 Template tweet:", BOLD)
        log(f"\n{tmpl}\n", YELLOW)
    if intent:
        log(f"  🐦 One-click tweet: {intent}", CYAN)

    log(f"\n  💰 Kamu sekarang earn 65% dari setiap trading fee!", GREEN)
    log(f"  📊 Dashboard: https://clawpump.tech/agent/{creds['agentId']}", CYAN)
    print()

if __name__ == "__main__":
    main()
