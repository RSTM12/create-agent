#!/usr/bin/env python3
"""
Launch token di pump.fun via ClawPump (GRATIS/gasless).

Usage:
    # Pakai file lokal:
    python examples/launch_token.py --name "NamaToken" --symbol "TKN" \
        --description "Deskripsi token" --image ./logo.png --apikey "cpk_xxx"

    # Pakai link gambar:
    python examples/launch_token.py --name "NamaToken" --symbol "TKN" \
        --description "Deskripsi token" --image "https://i.imgur.com/xxx.png" --apikey "cpk_xxx"
"""

import os, sys, json, argparse, requests

BASE_URL = "https://clawpump.tech"

GREEN="\033[92m"; YELLOW="\033[93m"; RED="\033[91m"
CYAN="\033[96m";  BOLD="\033[1m";    RESET="\033[0m"

def log(m, c=""): print(f"{c}{m}{RESET}")

def is_url(s):
    return s.startswith("http://") or s.startswith("https://")

def upload_image(path, api_key):
    log("  📤 Uploading gambar dari file lokal...", YELLOW)
    if not os.path.exists(path):
        log(f"  ❌ File tidak ditemukan: {path}", RED); sys.exit(1)
    with open(path, "rb") as f:
        r = requests.post(f"{BASE_URL}/api/upload",
            files={"image": f},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        log(f"  ❌ Upload gagal: {data}", RED); sys.exit(1)
    log(f"  ✅ Uploaded: {data['imageUrl']}", GREEN)
    return data["imageUrl"]

def resolve_image(image, api_key):
    if is_url(image):
        log(f"  🔗 Pakai URL langsung: {image}", GREEN)
        return image
    else:
        return upload_image(image, api_key)

def launch(api_key, name, symbol, desc, img, website=None, twitter=None, telegram=None):
    payload = {"name": name, "symbol": symbol, "description": desc, "imageUrl": img}
    if website:  payload["website"]  = website
    if twitter:  payload["twitter"]  = twitter
    if telegram: payload["telegram"] = telegram

    log("  🚀 Launching ke pump.fun (gasless)...", YELLOW)
    r = requests.post(f"{BASE_URL}/api/launch", json=payload,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        timeout=60)

    if r.status_code == 401:
        log("  ❌ API key invalid!", RED); sys.exit(1)
    if r.status_code == 429:
        h = r.json().get("retryAfterHours", "?")
        log(f"  ⏳ Rate limited. Coba lagi dalam {h} jam.", YELLOW); sys.exit(0)
    if r.status_code == 503:
        log("  ⚠️  Gasless tidak tersedia saat ini. Coba beberapa saat lagi.", YELLOW); sys.exit(1)
    r.raise_for_status()
    return r.json()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name",        required=True, help="Nama token (max 32 karakter)")
    p.add_argument("--symbol",      required=True, help="Ticker (max 10 karakter, contoh: TKN)")
    p.add_argument("--description", required=True, help="Deskripsi token (min 20 karakter)")
    p.add_argument("--image",       required=True, help="Path file lokal ATAU link URL gambar")
    p.add_argument("--apikey",      required=True, help="ClawPump API key (cpk_...)")
    p.add_argument("--website",     default=None,  help="Website URL (opsional)")
    p.add_argument("--twitter",     default=None,  help="Twitter handle tanpa @ (opsional)")
    p.add_argument("--telegram",    default=None,  help="Telegram group (opsional)")
    a = p.parse_args()

    print()
    log("╔══════════════════════════════════════════════════╗", CYAN)
    log("║       ClawPump — Token Launch Script            ║", CYAN)
    log("║    Gasless launch di pump.fun (Solana)          ║", CYAN)
    log("╚══════════════════════════════════════════════════╝", CYAN)
    print()

    log("[1/2] Proses Gambar", BOLD)
    image_url = resolve_image(a.image, a.apikey)
    print()

    log("[2/2] Launch Token", BOLD)
    result = launch(a.apikey, a.name, a.symbol, a.description,
                    image_url, a.website, a.twitter, a.telegram)
    print()

    log("╔══════════════════════════════════════════════════╗", GREEN)
    log("║          🎉 TOKEN LAUNCHED SUCCESSFULLY!        ║", GREEN)
    log("╚══════════════════════════════════════════════════╝", GREEN)
    print()
    log(f"  Token    :  {a.name} (${a.symbol})", BOLD)
    log(f"  Mint     :  {result.get('mintAddress')}")
    log(f"  pump.fun :  {result.get('pumpUrl')}", CYAN)
    log(f"  Explorer :  {result.get('explorerUrl')}", CYAN)
    print()

    social = result.get("socialAmplification", {})
    tmpl   = social.get("twitter", {}).get("template", "")
    intent = social.get("twitter", {}).get("tweetIntentUrl", "")
    if tmpl:
        log("  📣 Template tweet:", BOLD)
        log(f"\n{tmpl}\n", YELLOW)
    if intent:
        log(f"  🐦 One-click tweet: {intent}", CYAN)

    log(f"\n  💰 Kamu earn 65% dari setiap trading fee!", GREEN)
    print()

if __name__ == "__main__":
    main()
