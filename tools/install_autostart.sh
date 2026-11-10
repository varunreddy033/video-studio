#!/usr/bin/env bash
# Start Video Studio + the Tailscale tunnel automatically whenever you log in to this Mac,
# restart them if they crash, and keep the Mac awake while they run (plugged in).
#
#   bash ~/youtube-pipeline/tools/install_autostart.sh            install / update
#   bash ~/youtube-pipeline/tools/install_autostart.sh remove     stop and remove
#
# Logs: ~/youtube-pipeline/output/server.log and ~/Library/Application Support/vs-tailscale/tailscaled.log
set -euo pipefail
P="$HOME/youtube-pipeline"
TS="$HOME/Library/Application Support/vs-tailscale"
LA="$HOME/Library/LaunchAgents"
UIDN="$(id -u)"
SERVER=com.videostudio.server
TUNNEL=com.videostudio.tailscale
mkdir -p "$LA" "$TS" "$P/output"
chmod 700 "$TS"

unload() {
  for label in "$SERVER" "$TUNNEL"; do
    launchctl bootout "gui/$UIDN/$label" 2>/dev/null || true
  done
}

if [ "${1:-}" = "remove" ]; then
  unload
  rm -f "$LA/$SERVER.plist" "$LA/$TUNNEL.plist"
  echo "Removed. Video Studio and the tunnel no longer start on their own."
  exit 0
fi

TAILSCALED="$(command -v tailscaled || echo /opt/homebrew/bin/tailscaled)"
[ -x "$P/bin/python" ] || { echo "ERROR: $P/bin/python not found. Run setup.sh first."; exit 1; }
[ -x "$TAILSCALED" ] || { echo "ERROR: tailscaled not found. Run: brew install tailscale"; exit 1; }

cat > "$LA/$SERVER.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$SERVER</string>
  <key>ProgramArguments</key><array>
    <string>/usr/bin/caffeinate</string><string>-is</string>
    <string>$P/bin/python</string><string>$P/render_server.py</string>
  </array>
  <key>WorkingDirectory</key><string>$P</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>PYTHONUNBUFFERED</key><string>1</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>10</integer>
  <key>StandardOutPath</key><string>$P/output/server.log</string>
  <key>StandardErrorPath</key><string>$P/output/server.log</string>
</dict></plist>
EOF

cat > "$LA/$TUNNEL.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$TUNNEL</string>
  <key>ProgramArguments</key><array>
    <string>$TAILSCALED</string>
    <string>--tun=userspace-networking</string>
    <string>--statedir=$TS</string>
    <string>--socket=$TS/tailscaled.sock</string>
    <string>--port=0</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>10</integer>
  <key>StandardOutPath</key><string>$TS/tailscaled.log</string>
  <key>StandardErrorPath</key><string>$TS/tailscaled.log</string>
</dict></plist>
EOF

unload
# stop copies that were started by hand, so the background services own the ports
pkill -f "render_server.py" 2>/dev/null || true
lsof -ti "tcp:${PORT:-8765}" -sTCP:LISTEN 2>/dev/null | xargs kill 2>/dev/null || true
pkill -f "tailscaled.*vs-tailscale" 2>/dev/null || true
sleep 2
launchctl bootstrap "gui/$UIDN" "$LA/$TUNNEL.plist"
launchctl bootstrap "gui/$UIDN" "$LA/$SERVER.plist"
sleep 8
ok=1
# check the background service itself owns the port (not an old copy started by hand)
if launchctl print "gui/$UIDN/$SERVER" 2>/dev/null | grep -q "state = running" \
   && curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT:-8765}/login" | grep -qE "200|302"; then
  echo "ok: Video Studio is running as a background service (http://localhost:${PORT:-8765})"
else
  echo "WARNING: the Video Studio service is not running; see output/server.log"; ok=0
fi
tailscale --socket="$TS/tailscaled.sock" status >/dev/null 2>&1 && echo "ok: Tailscale tunnel service is running" || { echo "WARNING: tunnel not running yet; see $TS/tailscaled.log"; ok=0; }
echo "Both now start by themselves when you log in to this Mac. Keep it plugged in with the lid open."
[ $ok -eq 1 ]
