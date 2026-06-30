#!/usr/bin/env python3
"""
Kush Trading Bot — local server
Reads .env credentials and serves them to bot.html at /api/config
"""
import os, json
from http.server import HTTPServer, SimpleHTTPRequestHandler

ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")

def load_env():
    config = {"key": "", "secret": "", "endpoint": "https://paper-api.alpaca.markets"}
    if not os.path.exists(ENV_FILE):
        return config
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k == "ALPACA_API_KEY":
                    config["key"] = v
                elif k == "ALPACA_SECRET_KEY":
                    config["secret"] = v
                elif k == "ALPACA_ENDPOINT":
                    config["endpoint"] = v
    return config

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/config":
            cfg = load_env()
            body = json.dumps(cfg).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        # Suppress normal request logs — only show startup message
        pass

if __name__ == "__main__":
    cfg = load_env()
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║       Kush Trading Bot — Running     ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"\n  Endpoint : {cfg['endpoint']}")
    print(f"  API Key  : {cfg['key'][:8]}{'*' * max(0, len(cfg['key'])-8) if cfg['key'] else '(not set)'}")
    print(f"  Secret   : {'*' * 8 if cfg['secret'] else '(not set)'}")
    if not cfg['key'] or cfg['key'] == "YOUR_API_KEY_HERE":
        print("\n  ⚠️  Open .env and paste your Alpaca keys first!")
    print(f"\n  Bot URL  : http://localhost:8080/bot.html")
    print("  Press Ctrl+C to stop.\n")
    server = HTTPServer(("localhost", 8080), Handler)
    server.serve_forever()
