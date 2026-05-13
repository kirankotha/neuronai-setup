#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  NeuronAI — One-click AI chat agent installer
#  Installs: Docker, Ollama, Open WebUI, Caddy, Market Analysis Tool
#  Tested on: Ubuntu 20.04 / 22.04 / 24.04
#  Usage:
#    Basic:       bash install.sh
#    With domain: DOMAIN=myai.duckdns.org bash install.sh
#    Silent:      DOMAIN=myai.duckdns.org GROQ_API_KEY=xxx GEMINI_API_KEY=xxx bash install.sh
# ─────────────────────────────────────────────────────────────────
set -e

# ── Colors ────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
log()     { echo -e "${GREEN}[✔]${NC} $1"; }
info()    { echo -e "${CYAN}[→]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✘]${NC} $1"; exit 1; }
section() { echo -e "\n${CYAN}━━━ $1 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ── Banner ────────────────────────────────────────────────────────
echo -e "${CYAN}"
cat <<'EOF'
  _   _                           _    ___
 | \ | | ___ _   _ _ __ ___  _ __/ \  |_ _|
 |  \| |/ _ \ | | | '__/ _ \| '_ \_  \ | |
 | |\  |  __/ |_| | | | (_) | | | |/ | | |
 |_| \_|\___|\__,_|_|  \___/|_| |_/_/  |___|
  Self-hosted AI Chat Agent Installer
EOF
echo -e "${NC}"

# ── Config — override via env vars or interactive prompt ──────────
section "Configuration"

ask() {
    local var=$1 prompt=$2 default=$3
    if [ -z "${!var}" ]; then
        read -rp "$(echo -e "${CYAN}?${NC} $prompt [$default]: ")" input
        export "$var"="${input:-$default}"
    else
        log "$prompt: ${!var}"
    fi
}

ask WEBUI_NAME      "App name"                          "NeuronAI"
ask DOMAIN          "Domain (leave blank to use IP)"    ""
ask GROQ_API_KEY    "Groq API key (Enter to skip)"      ""
ask GEMINI_API_KEY  "Gemini API key (Enter to skip)"    ""
ask INSTALL_MODELS  "Ollama models (comma-separated)"   "qwen2.5-coder:7b,deepseek-coder:1.3b"

# ── 1. System Packages ────────────────────────────────────────────
section "System Packages"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    curl wget git ca-certificates gnupg lsb-release \
    apt-transport-https debian-keyring debian-archive-keyring \
    python3 python3-pip sqlite3
log "System packages ready"

# ── 2. Docker ─────────────────────────────────────────────────────
section "Docker"
if command -v docker &>/dev/null; then
    log "Docker already installed: $(docker --version)"
else
    info "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    log "Docker installed"
fi

# ── 3. Ollama ─────────────────────────────────────────────────────
section "Ollama"
if command -v ollama &>/dev/null; then
    log "Ollama already installed"
else
    info "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    log "Ollama installed"
fi

# Configure Ollama to listen on all interfaces
sudo mkdir -p /etc/systemd/system/ollama.service.d
cat <<EOF | sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
sudo systemctl daemon-reload
sudo systemctl enable ollama --quiet
sudo systemctl restart ollama
sleep 3
log "Ollama running on 0.0.0.0:11434"

# ── 4. Pull Models ────────────────────────────────────────────────
section "AI Models"
IFS=',' read -ra MODELS <<< "$INSTALL_MODELS"
for model in "${MODELS[@]}"; do
    model="$(echo "$model" | xargs)"
    info "Pulling $model..."
    ollama pull "$model" && log "$model ready" || warn "Failed to pull $model, skipping"
done

# ── 5. Open WebUI ─────────────────────────────────────────────────
section "Open WebUI"
if docker ps -a --format '{{.Names}}' | grep -q "^open-webui$"; then
    log "Open WebUI container already exists — skipping"
else
    info "Starting Open WebUI..."
    docker run -d \
        -v open-webui:/app/backend/data \
        -p 3000:8080 \
        -e OLLAMA_BASE_URL=http://172.17.0.1:11434 \
        -e BYPASS_MODEL_ACCESS_CONTROL=true \
        -e WEBUI_NAME="$WEBUI_NAME" \
        --name open-webui \
        --restart unless-stopped \
        ghcr.io/open-webui/open-webui:main
    info "Waiting for Open WebUI to start..."
    sleep 15
    log "Open WebUI running on port 3000"
fi

# ── 6. Market Analysis Tool Dependencies ─────────────────────────
section "Market Analysis Tool"
info "Installing yfinance and ta inside Open WebUI container..."
docker exec open-webui pip install yfinance ta -q && log "Python packages installed" || warn "Package install failed — you can retry later with: docker exec open-webui pip install yfinance ta"

# ── 7. Inject Market Analysis Tool into Open WebUI DB ─────────────
TOOL_FILE="$(dirname "$0")/tools/market_analysis_tool.py"
if [ -f "$TOOL_FILE" ]; then
    info "Injecting market analysis tool into Open WebUI..."
    TOOL_CONTENT=$(cat "$TOOL_FILE")
    docker exec open-webui python3 - <<PYEOF
import sqlite3, json, time

content = open('/dev/stdin').read() if False else """$TOOL_CONTENT"""

db = '/app/backend/data/webui.db'
conn = sqlite3.connect(db)

# Get admin user
user = conn.execute("SELECT id FROM user WHERE role='admin' LIMIT 1;").fetchone()
if not user:
    print("No admin user found, skipping tool injection")
    exit()

user_id = user[0]
tool_id = 'market-technical-analysis'
now = int(time.time())

specs = json.dumps([{
    'name': 'analyze_market',
    'description': 'Analyze a stock, crypto or index with live data and technical indicators.',
    'parameters': {
        'type': 'object',
        'properties': {
            'ticker':   {'type': 'string', 'description': 'e.g. AAPL, RELIANCE.NS, BTC-USD'},
            'period':   {'type': 'string', 'description': '1mo/3mo/6mo/1y/2y', 'default': '1y'},
            'interval': {'type': 'string', 'description': '1d or 1h', 'default': '1d'},
        },
        'required': ['ticker']
    }
}])
meta = json.dumps({'description': 'Live market data: RSI, MACD, Bollinger Bands, support/resistance.'})

conn.execute("DELETE FROM tool WHERE id=?", (tool_id,))
conn.execute(
    "INSERT INTO tool (id, user_id, name, content, specs, meta, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
    (tool_id, user_id, 'Market Technical Analysis', content, specs, meta, now, now)
)
conn.commit()
print("Market analysis tool injected successfully")
PYEOF
    log "Market analysis tool added to Open WebUI"
else
    warn "tools/market_analysis_tool.py not found — skipping tool injection"
fi

# ── 8. Add Groq / Gemini connections ─────────────────────────────
section "Cloud Model Connections"
if [ -n "$GROQ_API_KEY" ] || [ -n "$GEMINI_API_KEY" ]; then
    docker exec open-webui python3 - <<PYEOF
import sqlite3, json, time

db = '/app/backend/data/webui.db'
conn = sqlite3.connect(db)

connections = []

groq_key = "$GROQ_API_KEY"
gemini_key = "$GEMINI_API_KEY"

if groq_key:
    connections.append({
        "id":      "groq",
        "name":    "Groq",
        "url":     "https://api.groq.com/openai/v1",
        "key":     groq_key,
        "enabled": True
    })
    print("Groq connection queued")

if gemini_key:
    connections.append({
        "id":      "gemini",
        "name":    "Gemini",
        "url":     "https://generativelanguage.googleapis.com/v1beta/openai",
        "key":     gemini_key,
        "enabled": True
    })
    print("Gemini connection queued")

for c in connections:
    existing = conn.execute("SELECT id FROM config WHERE id=?", (c['id'],)).fetchone() if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='config';").fetchone() else None
    # Store in the openai_config / model config table if available
    # Open WebUI stores these in the 'config' key-value table
    try:
        val = json.dumps(c)
        conn.execute("INSERT OR REPLACE INTO config (id, data, created_at, updated_at) VALUES (?,?,?,?)",
                     (c['id'], val, int(time.time()), int(time.time())))
        conn.commit()
    except Exception as e:
        print(f"Note: Could not auto-add {c['name']} via DB ({e}) — add manually in Settings > Connections")

print("Done")
PYEOF
    log "Cloud connections configured"
else
    warn "No API keys provided — add Groq/Gemini later in Settings → Connections"
fi

# ── 9. Caddy ──────────────────────────────────────────────────────
section "Caddy (HTTPS)"
if ! command -v caddy &>/dev/null; then
    info "Installing Caddy..."
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
        | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
        | sudo tee /etc/apt/sources.list.d/caddy-stable.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install caddy -y -qq
    log "Caddy installed"
else
    log "Caddy already installed"
fi

if [ -n "$DOMAIN" ]; then
    info "Configuring Caddy for $DOMAIN..."
    sudo mkdir -p /var/www/html
    cat <<EOF | sudo tee /etc/caddy/Caddyfile > /dev/null
$DOMAIN {
    request_body {
        max_size 0
    }

    handle /continue_config.yaml {
        root * /var/www/html
        file_server
    }

    handle {
        reverse_proxy localhost:3000 {
            flush_interval -1
            transport http {
                response_header_timeout 300s
                dial_timeout 30s
            }
        }
    }
}

:80 {
    redir https://{host}{uri} permanent
}
EOF
    sudo systemctl enable caddy --quiet
    sudo systemctl restart caddy
    log "Caddy configured for https://$DOMAIN"
else
    warn "No domain set — Caddy not configured. Access via http://$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):3000"
fi

# ── 10. Firewall ──────────────────────────────────────────────────
section "Firewall"
for port in 22 80 443 3000 11434; do
    sudo ufw allow "$port/tcp" > /dev/null 2>&1 && info "Port $port open" || true
done
sudo ufw --force enable > /dev/null 2>&1 || true
log "Firewall configured"

# ── Done ──────────────────────────────────────────────────────────
section "Installation Complete"

VM_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo -e ""
echo -e "${GREEN}  ✅ NeuronAI is ready!${NC}"
echo -e ""
if [ -n "$DOMAIN" ]; then
echo -e "  ${CYAN}URL      :${NC} https://$DOMAIN"
else
echo -e "  ${CYAN}URL      :${NC} http://$VM_IP:3000"
fi
echo -e "  ${CYAN}Models   :${NC} $INSTALL_MODELS"
echo -e "  ${CYAN}Tool     :${NC} Market Technical Analysis (RSI, MACD, Support/Resistance)"
echo -e ""
echo -e "  Next steps:"
echo -e "  1. Open the URL and create your admin account"
echo -e "  2. Go to Workspace → Tools and enable Market Technical Analysis"
echo -e "  3. Install Mac PWA: open URL in Chrome → address bar install icon"
echo -e ""
