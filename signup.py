#!/usr/bin/env python3
"""
ClawPump Agent Signup
Daftarkan AI agent ke ClawPump — tanpa browser, tanpa Google login.
Earn 65% dari semua Solana trading fees secara otomatis.

Usage:
    python signup.py --name "Nama Agent Kamu"
    python signup.py --name "Nama Agent Kamu" --wallet existing_wallet.json
"""

import os, sys, json, time, argparse, requests

try:
    import base58
    import nacl.signing
except ImportError:
    print("❌ Jalankan dulu: pip install -r requirements.txt")
    sys.exit(1)

MCP_URL     = "https://clawpump.tech/api/mcp"
WALLET_FILE = "clawpump-wallet.json"
CREDS_FILE  = "clawpump-creds.json"

GREEN  = "\033[92m"; YELLOW = "\033[93m"; RED   = "\033[91m"
CYAN   = "\033[96m"; BOLD   = "\033[1m";  DIM   = "\033[2m"; RESET = "\033[0m"

def log(msg, color=""): print(f"{color}{msg}{RESET}")
def div(c="─", n=56):   print(f"{DIM}{c*n}{RESET}")


# ── Wallet ─────────────────────────────────────────────────────────────────────

def generate_wallet():
    sk = nacl.signing.SigningKey.generate()
    seed   = bytes(sk)
    pubkey = bytes(sk.verify_key)
    secret = seed + pubkey  # 64-byte Solana format
    return base58.b58encode(pubkey).decode(), list(secret)

def load_wallet(path):
    with open(path) as f:
        d = json.load(f)
    return d["publicKey"], d["secretKey"]

def save_wallet(pub, sec, path=WALLET_FILE):
    with open(path, "w") as f:
        json.dump({"publicKey": pub, "secretKey": sec}, f, indent=2)
    os.chmod(path, 0o600)

def privkey_b58(sec):  return base58.b58encode(bytes(sec)).decode()
def seed_b58(sec):     return base58.b58encode(bytes(sec[:32])).decode()


# ── Sign ───────────────────────────────────────────────────────────────────────

def sign(sec, wallet_address):
    sk        = nacl.signing.SigningKey(bytes(sec[:32]))
    timestamp = int(time.time())
    message   = f"clawpump-signup:{wallet_address}:{timestamp}"
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

def mcp_signup(session_id, name, wallet, sig, ts):
    r = requests.post(MCP_URL,
        json={"jsonrpc":"2.0","id":3,"method":"tools/call",
              "params":{"name":"agent_signup",
                        "arguments":{"name":name,"walletAddress":wallet,
                                     "signature":sig,"timestamp":ts}}},
        headers={"Content-Type":"application/json",
                 "Accept":"application/json, text/event-stream",
                 "Mcp-Session-Id":session_id},
        timeout=30)
    r.raise_for_status()
    for line in r.text.split("\n"):
        if line.startswith("data:"):
            data = json.loads(line[5:].strip())
            content = data.get("result",{}).get("content",[{}])
            if content:
                return json.loads(content[0].get("text","{}"))
            raise Exception(data.get("error", data))
    raise Exception("No response from server")


# ── Save creds ─────────────────────────────────────────────────────────────────

def save_creds(result, name, wallet, sec, path=CREDS_FILE):
    creds = {
        "agentName":        name,
        "agentId":          result.get("agentId"),
        "apiKey":           result.get("apiKey"),
        "walletPublicKey":  wallet,
        "walletPrivateKey": privkey_b58(sec),
        "walletSeed":       seed_b58(sec),
        "walletSecretKey":  sec,
        "dashboard":        f"https://clawpump.tech/agent/{result.get('agentId')}",
        "registeredAt":     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(path, "w") as f:
        json.dump(creds, f, indent=2)
    os.chmod(path, 0o600)
    return creds


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name",   required=True, help='Nama agent, contoh: "My Agent"')
    parser.add_argument("--wallet", default=None,  help="Path wallet JSON existing (opsional)")
    args = parser.parse_args()

    print()
    log("╔══════════════════════════════════════════════════════╗", CYAN)
    log("║         ClawPump Agent Signup Script                 ║", CYAN)
    log("║   Earn 65% of Solana trading fees automatically     ║", CYAN)
    log("╚══════════════════════════════════════════════════════╝", CYAN)
    print()

    # Step 1 — Wallet
    log("[1/4] Wallet Setup", BOLD)
    if args.wallet:
        wallet, sec = load_wallet(args.wallet)
        log(f"  📂 Loaded: {wallet}", GREEN)
    elif os.path.exists(WALLET_FILE):
        wallet, sec = load_wallet(WALLET_FILE)
        log(f"  📂 Found existing: {WALLET_FILE}")
        log(f"  ✅ Using: {wallet}", GREEN)
    else:
        log("  🔑 Generating new Solana Ed25519 keypair...")
        wallet, sec = generate_wallet()
        save_wallet(wallet, sec)
        log(f"  ✅ New wallet: {wallet}", GREEN)
        log(f"  💾 Saved: {WALLET_FILE}", YELLOW)
    print()

    # Step 2 — Sign
    log("[2/4] Signing Registration Message", BOLD)
    sig, ts = sign(sec, wallet)
    log(f"  ✅ Signed (timestamp: {ts})", GREEN)
    log(f"  📝 clawpump-signup:{wallet[:16]}...:{ts}", DIM)
    print()

    # Step 3 — Register
    log("[3/4] Registering Agent on ClawPump", BOLD)
    log("  🌐 Connecting to MCP server...")
    try:
        session_id = mcp_init()
        log("  ✅ MCP session ready", GREEN)
    except Exception as e:
        log(f"  ❌ Koneksi gagal: {e}", RED); sys.exit(1)

    log(f"  📡 Mendaftarkan '{args.name}'...")
    try:
        result = mcp_signup(session_id, args.name, wallet, sig, ts)
    except Exception as e:
        log(f"  ❌ Signup gagal: {e}", RED); sys.exit(1)

    if not result.get("success"):
        log(f"  ❌ Error: {result}", RED); sys.exit(1)

    log("  ✅ Registered!", GREEN)
    print()

    # Step 4 — Save
    log("[4/4] Menyimpan Credentials", BOLD)
    creds = save_creds(result, args.name, wallet, sec)
    log(f"  💾 Saved to: {CREDS_FILE}", YELLOW)
    print()

    # ── HASIL AKHIR ────────────────────────────────────────────────────────────
    log("╔══════════════════════════════════════════════════════╗", GREEN)
    log("║           ✅  REGISTRATION SUCCESSFUL               ║", GREEN)
    log("╚══════════════════════════════════════════════════════╝", GREEN)
    print()

    div("═")
    log("  AGENT INFO", BOLD)
    div()
    log(f"  Name      :  {creds['agentName']}")
    log(f"  Agent ID  :  {creds['agentId']}")
    log(f"  Dashboard :  {creds['dashboard']}", CYAN)
    print()

    div("═")
    log("  API KEY  ⚠️  simpan baik-baik, tidak akan muncul lagi!", BOLD + RED)
    div()
    log(f"  {creds['apiKey']}", YELLOW + BOLD)
    print()

    div("═")
    log("  SOLANA WALLET", BOLD)
    div()
    log(f"  Public Key   :  {creds['walletPublicKey']}", GREEN)
    log(f"  Private Key  :  {creds['walletPrivateKey']}", YELLOW)
    log(f"                  (Base58 64-byte — import ke Phantom/Solflare)")
    print()
    log(f"  Seed (32b)   :  {creds['walletSeed']}", YELLOW)
    log(f"                  (seed phrase alternatif)")
    div("═")
    print()

    log("  ⚠️  PERINGATAN KEAMANAN:", RED + BOLD)
    log("  • Jangan pernah commit clawpump-wallet.json & clawpump-creds.json ke git!", RED)
    log("  • Backup private key — jika hilang, SOL tidak bisa dipulihkan!", RED)
    print()

    log("  🚀 LANGKAH SELANJUTNYA:", BOLD)
    for step in result.get("nextSteps", []):
        log(f"     → {step}")
    print()
    log("  💡 Launch token pertama kamu (GRATIS):", CYAN)
    log("     python examples/launch_token.py \\", CYAN)
    log("       --name 'NamaToken' --symbol 'TKN' \\", CYAN)
    log("       --description 'Deskripsi token' --image ./logo.png", CYAN)
    print()


if __name__ == "__main__":
    main()
