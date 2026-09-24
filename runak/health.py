"""Minimal HTTP server so Render sees a healthy web service, plus an optional self-ping
(KEEPALIVE=0 turns it off) to keep the free instance from idling out."""
import asyncio
import logging

import httpx

from . import config as cfg
from .branding import BRAND

log = logging.getLogger("runak.health")


async def _handle(reader, writer):
    try:
        request = await asyncio.wait_for(reader.read(2048), timeout=5)
        line = request.decode("latin-1", errors="replace").splitlines()[:1]
        path = line[0].split(" ")[1] if line and len(line[0].split(" ")) > 1 else "/"
        if path in ("/", "/healthz"):
            body, status = f'{{"status":"ok","service":"{BRAND}"}}'.encode("utf-8"), "200 OK"
        else:
            body, status = b'{"status":"not_found"}', "404 Not Found"
        writer.write(
            f"HTTP/1.1 {status}\r\nContent-Type: application/json; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode("ascii") + body
        )
        await writer.drain()
    except (asyncio.TimeoutError, ConnectionError, IndexError):
        pass
    finally:
        writer.close()


async def serve():
    server = await asyncio.start_server(_handle, "0.0.0.0", cfg.PORT)
    log.info("Health server on port %s", cfg.PORT)
    async with server:
        await server.serve_forever()


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
