"""Minimal HTTP server using Flask so Render sees a healthy web service, plus an optional self-ping
(KEEPALIVE=0 turns it off) to keep the free instance from idling out."""
import asyncio
import logging
import os
import threading
from flask import Flask
import httpx

from . import config as cfg
from .branding import BRAND

log = logging.getLogger("runak.health")

app = Flask(__name__)

@app.route("/")
@app.route("/healthz")
def health_check():
    return f'{{"status":"ok","service":"{BRAND}"}}', 200, {"Content-Type": "application/json; charset=utf-8"}

def run_health_server():
    port = int(os.environ.get("PORT", getattr(cfg, "PORT", 8080)))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_health_check_thread():
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    log.info("Flask health check thread started on port %s", int(os.environ.get("PORT", getattr(cfg, "PORT", 8080))))

# Backwards compatibility wrapper for Runak's async serve() expected by main.py
async def serve():
    start_health_check_thread()
    # Keep the async task alive so background loop doesn't exit immediately
    while True:
        await asyncio.sleep(3600)


async def keepalive():
    """Ping our own public URL every 10 minutes (Render idles after 15)."""
    if not cfg.EXTERNAL_URL or not cfg.KEEPALIVE:
        return
    url = cfg.EXTERNAL_URL.rstrip("/") + "/healthz"
    async with httpx.AsyncClient(timeout=20) as http:
        while True:
            await asyncio.sleep(600)
            try:
                await http.get(url)
            except Exception:
                log.debug("keepalive ping failed")
