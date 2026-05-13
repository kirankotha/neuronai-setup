# NeuronAI — Self-Hosted AI Platform

Private ChatGPT-style AI assistant running on Oracle Cloud (OCI) Ubuntu VM.

## Stack
- **Open WebUI** (ForgeAI fork) — ChatGPT-like interface
- **Ollama** — local model runner
- **Caddy** — HTTPS reverse proxy
- **Continue.dev** — VSCode AI coding assistant

## Models
- Gemini 2.5 Pro / Flash (Google)
- Groq Llama 3.3 70B
- Qwen 2.5 Coder 7B (local)
- DeepSeek Coder 1.3B (local, tab autocomplete)

## Tools
- `tools/market_analysis_tool.py` — live stock/crypto technical analysis (RSI, MACD, Bollinger Bands, support/resistance)

## Setup

### 1. Copy environment variables
```bash
cp .env.example .env
# Fill in your actual API keys in .env
```

### 2. Start Open WebUI
```bash
chmod +x docker-run.sh
./docker-run.sh
```

### 3. Set up Caddy
```bash
sudo cp Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

### 4. Set up Continue.dev
Copy `continue_config.yaml` to your VM's `/var/www/html/` after substituting real API keys.

## Mac App
Installed Open WebUI as a PWA via Chrome — appears as a native app in the Dock.
