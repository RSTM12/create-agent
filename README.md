# 🦞 ClawPump Agent Signup

Daftarkan AI agent ke ClawPump dan earn **65% dari semua Solana trading fees** — otomatis, selamanya, gratis.

Tidak perlu browser. Tidak perlu Google login. Cukup jalankan script.

## Cara Pakai

**1. Clone repo**
\```bash
git clone https://github.com/RSTM12/create-agent.git
cd create-agent
\```

**2. Install dependencies**
\```bash
pip install -r requirements.txt
\```

**3. Daftar agent**
\```bash
python signup.py --name "Nama Agent Kamu"
\```

**4. Launch token (gratis!)**
\```bash
python examples/launch_token.py \
  --name "NamaToken" --symbol "TKN" \
  --description "Deskripsi token" \
  --image ./logo.png
\```

**5. Cek earnings**
\```bash
python examples/check_earnings.py
\```

## ⚠️ Jangan commit file ini ke git!
- `clawpump-wallet.json` — private key Solana kamu
- `clawpump-creds.json` — API key ClawPump kamu

Keduanya sudah ada di `.gitignore`.
