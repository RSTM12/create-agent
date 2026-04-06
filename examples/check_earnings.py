#!/usr/bin/env python3
"""
Cek earnings SOL dari trading fees.
Usage: python examples/check_earnings.py
"""

import os, sys, json, requests

CREDS_FILE = "clawpump-creds.json"
BASE_URL   = "https://clawpump.tech"

GREEN="\033[92m";YELLOW="\033[93m";RED="\033[91m";CYAN="\033[96m";BOLD="\033[1m";RESET="\033[0m"
def log(m, c=""): print(f"{c}{m}{RESET}")

def main():
    if not os.path.exists(CREDS_FILE):
        log(f"❌ {CREDS_FILE} tidak ditemukan. Jalankan signup.py dulu!", RED); sys.exit(1)

    with open(CREDS_FILE) as f: creds = json.load(f)

    log(f"\n💰 Earnings untuk: {creds['agentName']}", BOLD)
    r = requests.get(f"{BASE_URL}/api/fees/earnings",
                     params={"agentId": creds["agentId"]}, timeout=15)
    r.raise_for_status()
    d = r.json()

    print()
    log("╔══════════════════════════════════════╗", GREEN)
    log("║         Earnings Summary             ║", GREEN)
    log("╚══════════════════════════════════════╝", GREEN)
    log(f"  Total Earned   :  {d.get('totalEarned',  0):.6f} SOL", BOLD)
    log(f"  Total Sent     :  {d.get('totalSent',    0):.6f} SOL", GREEN)
    log(f"  Total Pending  :  {d.get('totalPending', 0):.6f} SOL", YELLOW)
    log(f"  Total Held     :  {d.get('totalHeld',    0):.6f} SOL")
    print()

    for token in d.get("tokenBreakdown", []):
        log(f"  Token: ...{token.get('mintAddress','')[-16:]}", BOLD)
        log(f"    Collected  : {token.get('totalCollected', 0):.6f} SOL")
        log(f"    Your 65%   : {token.get('totalAgentShare',0):.6f} SOL", GREEN)
        print()

    if not d.get("tokenBreakdown"):
        log("  Belum ada earnings. Launch token dulu!", YELLOW)
        log("  python examples/launch_token.py --help", CYAN)

    log(f"  📊 Dashboard: https://clawpump.tech/agent/{creds['agentId']}", CYAN)
    print()

if __name__ == "__main__":
    main()
