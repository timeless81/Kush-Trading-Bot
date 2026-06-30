#!/usr/bin/env python3
"""
Kush Trading Bot — local server
- Reads .env for Alpaca credentials + bot password
- /api/login  : POST {password} → sets secure session cookie
- /api/config : GET  → returns Alpaca credentials (requires valid session)
- /api/logout : POST → clears session
- All other routes → static file serving
"""
import os, json, secrets, hashlib, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")

# In-memory session store: token -> expiry timestamp
SESSIONS = {}
SESSION_TTL = 12 * 3600  # 12 hours

def load_env():
    cfg = {
        "key": "", "secret": "",
        "endpoint": "https://paper-api.alpaca.markets",
        "password": "changeme123"
    }
    if not os.path.exists(ENV_FILE):
        return cfg
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k == "ALPACA_API_KEY":     cfg["key"]      = v
                elif k == "ALPACA_SECRET_KEY": cfg["secret"]   = v
                elif k == "ALPACA_ENDPOINT":   cfg["endpoint"] = v
                elif k == "BOT_PASSWORD":      cfg["password"] = v
    return cfg

def get_session_token(headers):
    """Extract session token from Cookie header."""
    cookie_hdr = headers.get("Cookie", "")
    for part in cookie_hdr.split(";"):
        part = part.strip()
        if part.startswith("bot_session="):
            return part[len("bot_session="):]
    return None

def is_authenticated(headers):
    token = get_session_token(headers)
    if not token:
        return False
    expiry = SESSIONS.get(token)
    if not expiry or time.time() > expiry:
        SESSIONS.pop(token, None)
        return False
    return True

def json_response(handler, status, data):
    body = json.dumps(data).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

class Handler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/api/config":
            if not is_authenticated(self.headers):
                json_response(self, 401, {"error": "Unauthorized"})
                return
            cfg = load_env()
            json_response(self, 200, {
                "key":      cfg["key"],
                "secret":   cfg["secret"],
                "endpoint": cfg["endpoint"]
            })

        elif self.path == "/api/check":
            # Let the frontend check if already logged in
            json_response(self, 200, {"authenticated": is_authenticated(self.headers)})

        else:
            super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length).decode()

        if self.path == "/api/login":
            try:
                data = json.loads(body)
            except Exception:
                json_response(self, 400, {"error": "Bad request"}); return

            cfg = load_env()
            if data.get("password") == cfg["password"]:
                token  = secrets.token_hex(32)
                SESSIONS[token] = time.time() + SESSION_TTL
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header(
                    "Set-Cookie",
                    f"bot_session={token}; HttpOnly; SameSite=Strict; Max-Age={SESSION_TTL}"
                )
                resp = json.dumps({"ok": True}).encode()
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
                print(f"  ✅  Login from {self.client_address[0]}")
            else:
                print(f"  ❌  Failed login attempt from {self.client_address[0]}")
                json_response(self, 401, {"error": "Wrong password"})

        elif self.path == "/api/logout":
            token = get_session_token(self.headers)
            SESSIONS.pop(token, None)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", "bot_session=; Max-Age=0")
            resp = json.dumps({"ok": True}).encode()
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            json_response(self, 404, {"error": "Not found"})

    def log_message(self, fmt, *args):
        pass  # Suppress noisy per-request logs

if __name__ == "__main__":
    cfg = load_env()
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║       Kush Trading Bot — Running     ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"\n  Endpoint : {cfg['endpoint']}")
    print(f"  API Key  : {cfg['key'][:6]}{'*'*max(0,len(cfg['key'])-6) if cfg['key'] else '(not set)'}")
    print(f"  Secret   : {'*'*8 if cfg['secret'] else '(not set)'}")
    print(f"  Password : {'set ✓' if cfg['password'] != 'changeme123' else '⚠️  still default — change BOT_PASSWORD in .env!'}")
    if not cfg['key'] or cfg['key'] == "YOUR_API_KEY_HERE":
        print("\n  ⚠️  Open .env and paste your Alpaca keys first!")
    print(f"\n  Local URL : http://localhost:8080/bot.html")
    print("  Press Ctrl+C to stop.\n")
    server = HTTPServer(("localhost", 8080), Handler)
    server.serve_forever()
