# NeuronAI — Self-Hosted AI Chat Agent

Your own private ChatGPT running on any Ubuntu VM. No subscription fees for local models. Supports Groq, Gemini, and local Ollama models — all from one chat interface.

---

## What Gets Installed

| Component | Purpose |
|-----------|---------|
| **Ollama** | Runs AI models locally on your VM |
| **Open WebUI** | ChatGPT-style chat interface (runs in Docker) |
| **Caddy** | HTTPS reverse proxy (auto SSL via Let's Encrypt) |
| **Market Analysis Tool** | Live stock/crypto technical analysis inside chat |

### Included Models
- `qwen2.5-coder:7b` — general coding and reasoning
- `deepseek-coder:1.3b` — lightweight, fast (used for tab autocomplete)

### Cloud Models (optional, free tiers available)
- **Groq** — Llama 3.3 70B, ultra-fast inference
- **Gemini** — Google Gemini 2.5 Pro / Flash

---

## Requirements

- Ubuntu 20.04 / 22.04 / 24.04 (fresh or existing VM)
- Minimum **8GB RAM**, 50GB disk
- Ports **22, 80, 443, 3000, 11434** open in your firewall/security group
- (Optional) A domain name pointing to your VM's public IP

> **Oracle Cloud (OCI) Free Tier** works perfectly — use the Always Free VM shape with 23GB RAM.

---

## Before You Start

### 1. Open ports in your cloud firewall

You must open these ports in your cloud provider's security rules (not just ufw):

| Port | Used For |
|------|----------|
| 22 | SSH |
| 80 | HTTP → redirects to HTTPS |
| 443 | HTTPS (Open WebUI) |
| 3000 | Open WebUI direct access |
| 11434 | Ollama API |

- **OCI**: Networking → VCN → Security Lists → Add Ingress Rules
- **AWS**: EC2 → Security Groups → Inbound Rules
- **GCP**: VPC → Firewall → Add Rule
- **Azure**: Networking → Add Inbound Port Rule

### 2. (Optional) Set up a free domain

If you want HTTPS with a real domain (recommended):

1. Go to [duckdns.org](https://www.duckdns.org) and sign in
2. Create a subdomain e.g. `myai.duckdns.org`
3. Set it to your VM's public IP
4. Use that domain when the install script asks

Without a domain the app runs on `http://YOUR_IP:3000` (no HTTPS).

### 3. (Optional) Get free API keys

| Service | Free Tier | Where to Get |
|---------|-----------|-------------|
| Groq | 500K tokens/day | [console.groq.com](https://console.groq.com) |
| Gemini | 1500 requests/day | [aistudio.google.com](https://aistudio.google.com) |

You can skip these and use local models only.

---

## Installation

### Step 1 — SSH into your VM

```bash
ssh ubuntu@YOUR_VM_IP
```

### Step 2 — Clone this repo

```bash
git clone https://github.com/kirankotha/neuronai-setup
cd neuronai-setup
```

### Step 3 — Run the installer

**Option A — Interactive (script asks you questions):**
```bash
bash install.sh
```

**Option B — Fully automated (no prompts):**
```bash
DOMAIN=myai.duckdns.org \
GROQ_API_KEY=your_groq_key_here \
GEMINI_API_KEY=your_gemini_key_here \
bash install.sh
```

**Option C — Local models only, no domain:**
```bash
bash install.sh
# Press Enter to skip domain and API key prompts
```

The script takes **5–15 minutes** depending on your internet speed (model downloads are the slowest part).

---

## After Installation

### 1. Create your admin account

Open your browser and go to:
- With domain: `https://myai.duckdns.org`
- Without domain: `http://YOUR_VM_IP:3000`

The first account you create becomes the admin.

### 2. Add Groq / Gemini connections (if you skipped them during install)

1. Click your profile icon → **Admin Panel**
2. Go to **Settings → Connections**
3. Add OpenAI-compatible endpoints:
   - Groq: `https://api.groq.com/openai/v1` + your API key
   - Gemini: `https://generativelanguage.googleapis.com/v1beta/openai` + your API key

### 3. Enable the Market Analysis Tool

1. Go to **Workspace → Tools**
2. You should see **Market Technical Analysis** listed
3. In a new chat, click **`+`** next to the message box → **Tools** → toggle it ON
4. Try it:
   ```
   Analyze AAPL and give me support and resistance levels
   Analyze RELIANCE.NS and tell me if I should buy or sell
   What is the RSI on BTC-USD right now?
   ```

### 4. Install as a Mac app (optional)

1. Open Chrome on your Mac → go to your NeuronAI URL
2. Click the install icon in the address bar (or `⋮` → Install page as app)
3. It installs as a standalone app with its own Dock icon

---

## Supported Ticker Formats

| Type | Examples |
|------|---------|
| US Stocks | `AAPL`, `TSLA`, `MSFT`, `NVDA` |
| Indian NSE | `RELIANCE.NS`, `TCS.NS`, `INFY.NS` |
| Indian BSE | `RELIANCE.BO`, `TCS.BO` |
| Crypto | `BTC-USD`, `ETH-USD`, `SOL-USD` |
| Indices | `^NSEI` (Nifty 50), `^BSESN` (Sensex), `^GSPC` (S&P 500) |
| ETFs | `SPY`, `QQQ` |

---

## Switching Models in Chat

Open WebUI lets you switch models mid-conversation — the full chat history carries over.

- Click the **model name** at the top of any chat to switch
- Use **Groq** for complex reasoning and long analysis
- Use **Gemini Flash** for quick follow-up questions
- Use **local models** when you want zero API usage

---

## Repo Structure

```
neuronai-setup/
├── install.sh                    # One-click installer
├── Caddyfile                     # HTTPS reverse proxy config
├── continue_config.yaml          # VSCode Continue.dev AI config
├── docker-run.sh                 # Manual Docker start command
├── .env.example                  # API key template
├── tools/
│   └── market_analysis_tool.py   # Open WebUI market analysis tool
└── README.md
```

---

## Troubleshooting

**Open WebUI not loading?**
```bash
docker ps                          # check container is running
docker logs open-webui --tail 50   # check for errors
docker restart open-webui          # restart if needed
```

**Ollama models not showing in chat?**
```bash
ollama list                        # verify models are downloaded
systemctl status ollama            # check service is running
```

**Market Analysis Tool not working?**
```bash
docker exec open-webui pip install yfinance ta
docker restart open-webui
```

**Caddy SSL not working?**
```bash
sudo systemctl status caddy
sudo journalctl -u caddy --tail 30
# Make sure port 80 and 443 are open in your cloud firewall
```

---

## Security Notes

- Never commit your `.env` file (it's in `.gitignore`)
- The `continue_config.yaml` in this repo uses placeholders — fill in real keys only in your local copy
- Rotate your Groq/Gemini API keys periodically
- Consider restricting port 11434 (Ollama) to internal traffic only after setup

---

> This is a personal self-hosted setup. Not affiliated with Open WebUI, Ollama, Groq, or Google.
