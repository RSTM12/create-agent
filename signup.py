#!/usr/bin/env python3
"""
ClawPump Agent Signup
Daftarkan AI agent ke ClawPump — tanpa browser, tanpa Google login.
Setiap run = wallet baru + agent baru. Semua detail tampil sekali di terminal.

Usage:
    python signup.py --name "Nama Agent Kamu"
"""

import sys, json, time, argparse, requests

try:
    import base58
    import nacl.signing
except ImportError:
    print("❌ Jalankan dulu: pip install -r requirements.txt")
    sys.exit(1)

MCP_URL = "https://clawpump.tech/api/mcp"

GREEN  = "\033[92m"; YELLOW = "\033[93m"; RED   = "\033[91m"
CYAN   = "\033[96m"; BOLD   = "\033[1m";  DIM   = "\033[2m"; RESET = "\033[0m"

def log(msg, color=""): print(f"{color}{msg}{RESET}")
def div(c="─", n=60):   print(f"{DIM}{c*n}{RESET}")


# ── Generate wallet ────────────────────────────────────────────────────────────

def generate_wallet():
    sk     = nacl.signing.SigningKey.generate()
    seed   = bytes(sk)
    pubkey = bytes(sk.verify_key)
    secret = seed + pubkey          # 64-byte Solana format
    return {
        "signing_key":   sk,
        "public_key":    base58.b58encode(pubkey).decode(),
        "private_key":   base58.b58encode(secret).decode(),
        "seed":          base58.b58encode(seed).decode(),
        "secret_list":   list(secret),
    }


# ── Sign ───────────────────────────────────────────────────────────────────────

def sign(sk, public_key):
    timestamp = int(time.time())
    message   = f"clawpump-signup:{public_key}:{timestamp}"
    signed    = sk.sign(message.encode())
    return base58.b58encode(signed.signature).decode(), timestamp


# ── MCP ────────────────────────────────────────────────────────────────────────

def mcp_init():
    r = requests.post(MCP_URL,
        json={"jsonrpc":"2.0","id":1,"method":"initialize",
              "params":{"protocolVersion":"2024-11-05","capabilities":{},
                        "clientInfo":{"name":"clawpump-signup","version":"1.0"}}},
        headers={"Content-Type":"application/json",
                 "Accept":"application/json, text/event-stream"},
        timeout=20)
    r.raise_for_status()
    return r.headers.get("Mcp-Session-Id", "")

def mcp_signup(session_id, name, public_key, sig, ts):
    r = requests.post(MCP_URL,
        json={"jsonrpc":"2.0","id":3,"method":"tools/call",
              "params":{"name":"agent_signup",
                        "arguments":{"name":name,"walletAddress":public_key,
                                     "signature":sig,"timestamp":ts}}},
        headers={"Content-Type":"application/json",
                 "Accept":"application/json, text/event-stream",
                 "Mcp-Session-Id":session_id},
        timeout=30)
    r.raise_for_status()
    for line in r.text.split("\n"):
        if line.startswith("data:"):
            data    = json.loads(line[5:].strip())
            content = data.get("result",{}).get("content",[{}])
            if content:
                return json.loads(content[0].get("text","{}"))
            raise Exception(data.get("error", data))
    raise Exception("No response from server")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help='Nama agent, contoh: "My Agent"')
    args = parser.parse_args()

    print()
    log("╔════════════════════════════════════════════════════════════╗", CYAN)
    log("║           ClawPump Agent Signup Script                    ║", CYAN)
    log("║   Earn 65% of Solana trading fees automatically          ║", CYAN)
    log("╚════════════════════════════════════════════════════════════╝", CYAN)
    print()

    # Step 1 — Generate wallet baru setiap run
    log("[1/3] Generating New Solana Wallet...", BOLD)
    w = generate_wallet()
    log(f"  ✅ Wallet generated: {w['public_key']}", GREEN)
    print()

    # Step 2 — Sign
    log("[2/3] Signing Registration Message...", BOLD)
    sig, ts = sign(w["signing_key"], w["public_key"])
    log(f"  ✅ Signed (timestamp: {ts})", GREEN)
    print()

    # Step 3 — Register
    log("[3/3] Registering Agent on ClawPump...", BOLD)
    log("  🌐 Connecting to MCP server...")
    try:
        session_id = mcp_init()
        log("  ✅ MCP session ready", GREEN)
    except Exception as e:
        log(f"  ❌ Koneksi gagal: {e}", RED); sys.exit(1)

    log(f"  📡 Mendaftarkan '{args.name}'...")
    try:
        result = mcp_signup(session_id, args.name, w["public_key"], sig, ts)
    except Exception as e:
        log(f"  ❌ Signup gagal: {e}", RED); sys.exit(1)

    if not result.get("success"):
        log(f"  ❌ Error: {result}", RED); sys.exit(1)

    log("  ✅ Registered!", GREEN)
    print()

    # ── HASIL — tampil sekali, tidak disimpan ke file ──────────────────────────
    log("╔════════════════════════════════════════════════════════════╗", GREEN)
    log("║             ✅  REGISTRATION SUCCESSFUL                   ║", GREEN)
    log("║       ⚠️  SIMPAN INFO INI SEKARANG — tidak disimpan!      ║", YELLOW)
    log("╚════════════════════════════════════════════════════════════╝", GREEN)
    print()

    div("═")
    log("  AGENT INFO", BOLD)
    div()
    log(f"  Name      :  {args.name}")
    log(f"  Agent ID  :  {result.get('agentId')}")
    log(f"  Dashboard :  https://clawpump.tech/agent/{result.get('agentId')}", CYAN)
    print()

    div("═")
    log("  API KEY  ⚠️  tidak akan muncul lagi!", BOLD + RED)
    div()
    log(f"  {result.get('apiKey')}", YELLOW + BOLD)
    print()

    div("═")
    log("  SOLANA WALLET", BOLD)
    div()
    log(f"  Public Key   :  {w['public_key']}", GREEN)
    log(f"  Private Key  :  {w['private_key']}", YELLOW + BOLD)
    log(f"                  (Base58 64-byte — import ke Phantom/Solflare)")
    print()
    log(f"  Seed (32b)   :  {w['seed']}", YELLOW)
    log(f"                  (seed phrase alternatif)")
    div("═")
    print()

    log("  ⚠️  PERINGATAN:", RED + BOLD)
    log("  • Tidak ada file yang disimpan — copy info di atas sekarang!", RED)
    log("  • Jika lupa simpan private key, wallet tidak bisa dipulihkan!", RED)
    log("  • Setiap run script = wallet BARU + agent BARU", RED)
    print()

    log("  🚀 NEXT STEPS:", BOLD)
    for step in result.get("nextSteps", []):
        log(f"     → {step}")
    print()
    log("  💡 Launch token pertama kamu (GRATIS):", CYAN)
    log("     python examples/launch_token.py \\", CYAN)
    log("       --name 'NamaToken' --symbol 'TKN' \\", CYAN)
    log("       --description 'Deskripsi token' \\", CYAN)
    log("       --image ./logo.png \\", CYAN)
    log("       --apikey 'cpk_xxx...'", CYAN)
    print()


if __name__ == "__main__":
    main()
