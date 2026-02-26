"""JARVIS v13 Download Server"""
import http.server

PORT = 9090
DIR = "/workspaces/codespaces-blank"

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JARVIS AI v13 Download</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0e1a;color:#fff;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center}
.c{max-width:600px;padding:40px 20px;text-align:center}
h1{font-size:32px;background:linear-gradient(135deg,#8b5cf6,#3b82f6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.v{color:#64748b;font-size:14px;margin-bottom:32px}
.card{background:#1e293b;border-radius:16px;padding:24px;margin:16px 0;border:1px solid #334155}
.card h2{font-size:20px;margin-bottom:8px}
.card p{color:#94a3b8;font-size:13px;margin-bottom:16px}
.btn{display:inline-block;padding:12px 32px;border-radius:12px;text-decoration:none;font-weight:bold;font-size:16px}
.ba{background:linear-gradient(135deg,#10b981,#059669);color:#fff}
.bw{background:linear-gradient(135deg,#3b82f6,#2563eb);color:#fff}
.s{color:#64748b;font-size:12px;margin-top:8px}
.f{text-align:left;margin-top:32px;padding:20px;background:#1e293b;border-radius:16px;border:1px solid #334155}
.f h3{margin-bottom:12px;color:#8b5cf6}
.f li{color:#94a3b8;font-size:13px;margin:6px 0;list-style:none}
</style>
</head>
<body><div class="c">
<div style="font-size:64px;margin-bottom:16px">&#129302;</div>
<h1>JARVIS AI Trading</h1>
<div class="v">v13 Crash-Proof Edition | All Buttons Working</div>
<div class="card"><h2>&#128241; Android APK</h2><p>Voice, Gaming Coach, AI Trading</p>
<a href="/JARVIS-Trading-v13.apk" class="btn ba">Download APK</a><div class="s">~32 MB</div></div>
<div class="card"><h2>&#128187; Windows EXE</h2><p>Portable desktop app</p>
<a href="/JARVIS-Trading-v13.exe" class="btn bw">Download EXE</a><div class="s">~67 MB</div></div>
<div class="f"><h3>v13 Fixes</h3>
<li>&#9989; ALL buttons work - zero crashes</li>
<li>&#9989; Built-in AI keys - no setup needed</li>
<li>&#9989; Voice works on Android (native)</li>
<li>&#9989; Gaming Coach + BGMI launch</li>
<li>&#9989; 30+ services crash-proofed</li>
</div></div></body></html>"""

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.endswith((".apk", ".exe")):
            super().do_GET()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    s = http.server.HTTPServer(("0.0.0.0", PORT), H)
    print(f"JARVIS v13 Download Server on port {PORT}")
    s.serve_forever()
