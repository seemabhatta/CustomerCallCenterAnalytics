#!/bin/bash
# Launch ngrok tunnels for all MCP apps (ports 8001-8005)
#
# Usage: ./start_ngrok_apps.sh
# Optional: set NGROK_REGION or NGROK_API_ADDR env vars before running.

set -euo pipefail

if ! command -v ngrok >/dev/null 2>&1; then
    echo "❌ ngrok CLI not found. Install ngrok and ensure it is on your PATH." >&2
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    echo "❌ curl is required to query ngrok's local API." >&2
    exit 1
fi

if ! ngrok config check >/dev/null 2>&1; then
    echo "❌ ngrok is not authenticated. Run 'ngrok config add-authtoken <YOUR_TOKEN>' first." >&2
    echo "ℹ️  Get your token at https://dashboard.ngrok.com/get-started/your-authtoken" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs"
CONFIG_FILE="${LOG_DIR}/ngrok_mcp.yml"
REGION="${NGROK_REGION:-us}"
API_ADDR="${NGROK_API_ADDR:-127.0.0.1:4040}"
API_URL="http://${API_ADDR}/api/tunnels"

mkdir -p "${LOG_DIR}"

cat > "${CONFIG_FILE}" <<EOF
version: "2"
region: ${REGION}
tunnels:
  universal:
    addr: 8001
    proto: http
  advisor_borrower:
    addr: 8002
    proto: http
  advisor_performance:
    addr: 8003
    proto: http
  leadership_portfolio:
    addr: 8004
    proto: http
  leadership_strategy:
    addr: 8005
    proto: http
EOF

CONFIG_ARGS=()

add_config() {
    local cfg="$1"
    if [[ -f "$cfg" ]]; then
        CONFIG_ARGS+=(--config "$cfg")
    fi
}

if [[ -n "${NGROK_CONFIG:-}" ]]; then
    IFS=':' read -r -a NGROK_CONFIG_PATHS <<< "${NGROK_CONFIG}"
    for cfg in "${NGROK_CONFIG_PATHS[@]}"; do
        add_config "$cfg"
    done
fi

add_config "${HOME}/.config/ngrok/ngrok.yml"
add_config "${HOME}/.ngrok2/ngrok.yml"

shopt -s nullglob
for cfg in "${HOME}"/snap/ngrok/*/.config/ngrok/ngrok.yml; do
    add_config "$cfg"
done
shopt -u nullglob

CONFIG_ARGS+=(--config "${CONFIG_FILE}")

NGROK_PID=""
cleanup() {
    echo ""
    echo "🛑 Stopping ngrok tunnels..."
    if [[ -n "${NGROK_PID}" ]] && kill -0 "${NGROK_PID}" 2>/dev/null; then
        kill "${NGROK_PID}" 2>/dev/null || true
        wait "${NGROK_PID}" 2>/dev/null || true
    fi
    rm -f "${CONFIG_FILE}"
}

trap cleanup EXIT
trap 'exit 0' INT TERM

NGROK_CMD=(ngrok start --all)
NGROK_CMD+=("${CONFIG_ARGS[@]}")
NGROK_CMD+=(--log "${LOG_DIR}/ngrok.log" --log-format=json)

echo "🚀 Starting ngrok tunnels for MCP apps (region: ${REGION})..."
"${NGROK_CMD[@]}" > "${LOG_DIR}/ngrok_stdout.log" 2>&1 &
NGROK_PID=$!

sleep 1

echo "Waiting for tunnel endpoints (log: ${LOG_DIR}/ngrok.log)..."

EXPECTED_TUNNELS=(universal advisor_borrower advisor_performance leadership_portfolio leadership_strategy)
declare -A PORT_MAP=(
    [universal]=8001
    [advisor_borrower]=8002
    [advisor_performance]=8003
    [leadership_portfolio]=8004
    [leadership_strategy]=8005
)

TUNNEL_LINES=""
EXPECTED_JOINED=$(IFS=,; echo "${EXPECTED_TUNNELS[*]}")
for attempt in {1..30}; do
    if ! kill -0 "${NGROK_PID}" 2>/dev/null; then
        echo "❌ ngrok terminated early. Check ${LOG_DIR}/ngrok_stdout.log for details." >&2
        exit 1
    fi
    TUNNEL_LINES=$(LOG_PATH="${LOG_DIR}/ngrok.log" EXPECTED_TUNNELS="${EXPECTED_JOINED}" python3 <<'PY'
import json
import sys
from pathlib import Path
import os

log_path = Path(os.environ.get("LOG_PATH", ""))
expected_raw = os.environ.get("EXPECTED_TUNNELS", "")
expected = [name for name in expected_raw.split(",") if name]
found = {}

if log_path.exists():
    try:
        with log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("msg") == "started tunnel":
                    name = entry.get("name")
                    url = entry.get("url")
                    if name in expected and url:
                        found[name] = url
    except Exception:
        pass

if len(found) == len(expected):
    for name in expected:
        print(f"{name}={found[name]}")
    sys.exit(0)

sys.exit(1)
PY
)
    status=$?
    if [[ ${status} -eq 0 ]] && [[ -n "${TUNNEL_LINES}" ]]; then
        break
    fi
    sleep 1
    if [[ ${attempt} -eq 30 ]]; then
        echo "❌ Timed out waiting for ngrok tunnels to start. Check ${LOG_DIR}/ngrok.log." >&2
        exit 1
    fi
done

printf "\n🌐 MCP ngrok tunnels (https endpoints):\n"
if [[ -z "${TUNNEL_LINES}" ]]; then
    echo "  (no tunnels detected yet; see ${LOG_DIR}/ngrok.log for details)"
else
    while IFS='=' read -r name url; do
        port="${PORT_MAP[$name]:-unknown}"
        printf "  - %s (port %s): %s\n" "$name" "$port" "$url"
    done <<< "${TUNNEL_LINES}"
fi

cat <<EOF

🗒️ Notes:
- Full ngrok logs: ${LOG_DIR}/ngrok_stdout.log (agent) and ${LOG_DIR}/ngrok.log (JSON).
- Use the URLs above when registering MCP apps inside ChatGPT.
- Press Ctrl+C to stop all tunnels.
EOF

wait "${NGROK_PID}"
