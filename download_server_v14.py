#!/usr/bin/env python3
"""JARVIS v14 Download Server — Serves APK + EXE builds"""
import http.server
import os

PORT = 9090
BASE = "/workspaces/codespaces-blank"

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>JARVIS v14 — Download</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a1a;color:#fff;font-family:'Segoe UI',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}
.container{text-align:center;padding:40px}
h1{font-size:2.5rem;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.ver{color:#94a3b8;font-size:14px;margin-bottom:40px}
.cards{display:flex;gap:24px;flex-wrap:wrap;justify-content:center}
.card{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:20px;padding:32px;width:280px;transition:all .3s}
.card:hover{transform:translateY(-4px);border-color:rgba(96,165,250,.4);box-shadow:0 20px 40px rgba(96,165,250,.1)}
.icon{font-size:48px;margin-bottom:16px}
.card h3{font-size:18px;margin-bottom:8px}
.card p{color:#94a3b8;font-size:13px;margin-bottom:20px}
.btn{display:inline-block;padding:12px 32px;border-radius:12px;font-weight:600;text-decoration:none;transition:all .3s}
.btn-apk{background:linear-gradient(135deg,#10b981,#059669);color:#fff}
.btn-exe{background:linear-gradient(135deg,#3b82f6,#6366f1);color:#fff}
.btn:hover{transform:scale(1.05);box-shadow:0 8px 24px rgba(0,0,0,.3)}
.size{color:#64748b;font-size:11px;margin-top:8px}
.features{margin-top:40px;text-align:left;max-width:600px;margin-left:auto;margin-right:auto}
.features h3{color:#a78bfa;margin-bottom:12px;font-size:16px}
.features ul{list-style:none;columns:2;gap:8px}
.features li{color:#94a3b8;font-size:12px;padding:4px 0}
.features li::before{content:"✅ ";color:#10b981}
</style></head><body>
<div class="container">
<h1>⚡ JARVIS AI Trading Bot</h1>
<p class="ver">Version 14 — All Buttons Fixed • Real-Time Live • AI Fallback • Voice Ready</p>
<div class="cards">
<div class="card">
<div class="icon">📱</div>
<h3>Android APK</h3>
<p>Install directly on your Android phone. No Play Store needed.</p>
<a href="/download/apk" class="btn btn-apk">Download APK</a>
<p class="size">~32 MB</p>
</div>
<div class="card">
<div class="icon">💻</div>
<h3>Windows EXE</h3>
<p>Portable desktop app. No installation required — just run.</p>
<a href="/download/exe" class="btn btn-exe">Download EXE</a>
<p class="size">~67 MB</p>
</div>
</div>
<div class="features">
<h3>🚀 v14 Highlights</h3>
<ul>
<li>All buttons verified working</li>
<li>Real-time WebSocket prices</li>
<li>AI Chat with offline fallback</li>
<li>Hindi Voice Assistant (native)</li>
<li>BGMI Gaming Coach</li>
<li>Auto-refresh on all screens</li>
<li>Crash-proof error boundaries</li>
<li>Trading buy/sell wired to API</li>
<li>Wallet auto-refresh (15s)</li>
<li>Embedded AI keys (no setup)</li>
<li>50+ components lazy-loaded</li>
<li>23 services crash-protected</li>
</ul>
</div>
</div></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/download/apk':
            self._serve_file(f"{BASE}/JARVIS-Trading-v14.apk", "JARVIS-Trading-v14.apk", "application/vnd.android.package-archive")
        elif self.path == '/download/exe':
            self._serve_file(f"{BASE}/JARVIS-Trading-v14.exe", "JARVIS-Trading-v14.exe", "application/octet-stream")
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML.encode())

    def _serve_file(self, path, name, ctype):
        if not os.path.exists(path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"File not found")
            return
        size = os.path.getsize(path)
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Disposition", f'attachment; filename="{name}"')
        self.send_header("Content-Length", str(size))
        self.end_headers()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                self.wfile.write(chunk)

    def log_message(self, fmt, *args):
        print(f"[JARVIS Download] {args[0]}")

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"🚀 JARVIS v14 Download Server running on port {PORT}")
    print(f"   APK: {os.path.getsize(f'{BASE}/JARVIS-Trading-v14.apk') // 1024 // 1024}MB")
    print(f"   EXE: {os.path.getsize(f'{BASE}/JARVIS-Trading-v14.exe') // 1024 // 1024}MB")
    server.serve_forever()
