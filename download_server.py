"""JARVIS AI v12.0.0 — Download Server"""
import http.server, os

DIST = '/workspaces/codespaces-blank/dist'

HTML = '''<!DOCTYPE html>
<html><head><title>JARVIS AI v12.0.0 Downloads</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0e1a;color:#fff;font-family:system-ui;padding:30px 20px;max-width:700px;margin:auto}
h1{background:linear-gradient(90deg,#3b82f6,#8b5cf6);-webkit-background-clip:text;color:transparent;font-size:1.8em;margin-bottom:4px}
.sub{color:#888;margin-bottom:24px;font-size:0.95em}
.card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:20px;margin:14px 0;transition:border-color 0.2s}
.card:hover{border-color:rgba(255,255,255,0.3)}
.card h3{margin-bottom:10px;font-size:1.1em}
a.dl{display:inline-block;padding:10px 20px;border-radius:10px;text-decoration:none;font-weight:bold;font-size:0.95em;transition:opacity 0.2s}
a.dl:hover{opacity:0.85}
.apk{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff}
.exe{background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff}
.size{color:#888;font-size:0.85em;margin-top:8px}
.badge{display:inline-block;padding:3px 8px;border-radius:6px;font-size:0.75em;margin-left:8px;vertical-align:middle}
.b-and{background:rgba(34,197,94,0.2);color:#4ade80;border:1px solid rgba(34,197,94,0.3)}
.b-win{background:rgba(59,130,246,0.2);color:#60a5fa;border:1px solid rgba(59,130,246,0.3)}
.fix{background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.2);border-radius:10px;padding:12px 16px;margin:16px 0;font-size:0.9em;color:#4ade80}
hr{border:none;border-top:1px solid rgba(255,255,255,0.08);margin:24px 0}
.foot{color:#555;font-size:0.8em;text-align:center}
</style></head><body>
<h1>JARVIS AI v12.0.0</h1>
<p class="sub">Crash-Proof Standalone AI — Gaming Coach + Full Device Control</p>
<div class="fix">v12.0.0: All 30+ services dynamically loaded with individual isolation. Zero startup crashes guaranteed.</div>
<div class="card">
<h3>📱 Android APK <span class="badge b-and">Android 8+</span></h3>
<a class="dl apk" href="/JARVIS-AI-v12.0.0-CrashProof-debug.apk">⬇️ Download APK (32 MB)</a>
<p class="size">Settings → Security → Enable "Unknown Sources" → Install APK → Open</p>
</div>
<div class="card">
<h3>🖥️ Windows Desktop <span class="badge b-win">Windows x64</span></h3>
<a class="dl exe" href="/JARVIS-AI-v12.0.0-Windows-x64.zip">⬇️ Download EXE (104 MB)</a>
<p class="size">Extract ZIP → Open win-unpacked → Run JARVIS AI.exe</p>
</div>
<hr>
<p class="foot">JARVIS AI v12 — Crash-Proof Architecture • 300+ Endpoints • Gaming Coach • No Telegram</p>
</body></html>'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIST, **kw)
    def do_GET(self):
        if self.path in ('/', '/downloads', '/download'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(HTML.encode())
        else:
            super().do_GET()
    def log_message(self, fmt, *args):
        pass  # Silent

if __name__ == '__main__':
    print('JARVIS Download Server on port 9090')
    http.server.HTTPServer(('0.0.0.0', 9090), Handler).serve_forever()
