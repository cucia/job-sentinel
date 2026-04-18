#!/bin/sh
set -e

export DISPLAY="${DISPLAY:-:99}"
export VNC_PORT="${VNC_PORT:-5900}"
export NOVNC_PORT="${NOVNC_PORT:-6080}"

Xvfb "$DISPLAY" -screen 0 1440x960x24 -nolisten tcp &
fluxbox >/tmp/fluxbox.log 2>&1 &
x11vnc -display "$DISPLAY" -forever -shared -nopw -listen 0.0.0.0 -rfbport "$VNC_PORT" >/tmp/x11vnc.log 2>&1 &
websockify --web=/usr/share/novnc "$NOVNC_PORT" "localhost:$VNC_PORT" >/tmp/websockify.log 2>&1 &

exec "$@"
