"""
🧠🌟 JARVIS LIFE ENGINE — Total Personal AI Assistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

JARVIS controls your ENTIRE digital life:
• WhatsApp — Send messages, make calls via WhatsApp Web
• Email — Read, compose, send via SMTP/IMAP
• LinkedIn — Post updates, message connections
• Desktop Control — Screen capture, app launching, keyboard/mouse
• Smart Search — Research anything on the internet
• Calendar & Tasks — Full life management
• File Management — Create, read, organize files
• System Control — Battery, WiFi, Bluetooth, Volume

JARVIS NEVER says NO. She always finds a way.
"""

import os
import json
import time
import logging
import asyncio
import smtplib
import imaplib
import email as email_lib
import subprocess
import platform
import urllib.parse
import webbrowser
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger("JARVIS-LIFE")

# ═══════════════════════════════════════════════════════════
#  📧 EMAIL ENGINE — Read, Send, Manage Emails
# ═══════════════════════════════════════════════════════════

class JarvisEmailEngine:
    """Full email management via SMTP/IMAP."""
    
    def __init__(self):
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
        self.imap_server = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
        self.email_address = os.getenv("JARVIS_EMAIL", "")
        self.email_password = os.getenv("JARVIS_EMAIL_PASSWORD", "")
        self.user_name = os.getenv("JARVIS_USER_NAME", "Boss")
    
    def is_configured(self) -> bool:
        return bool(self.email_address and self.email_password)
    
    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> dict:
        """Send an email to anyone."""
        if not self.is_configured():
            return {"status": "setup_needed", "message": "Email credentials not configured. Set JARVIS_EMAIL and JARVIS_EMAIL_PASSWORD in .env", "action": "Please provide your Gmail address and App Password"}
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"JARVIS AI <{self.email_address}>"
            msg["To"] = to
            msg["Subject"] = subject
            
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            logger.info(f"📧 Email sent to {to}: {subject}")
            return {"status": "sent", "to": to, "subject": subject, "message": f"Email successfully sent to {to}! ✅"}
        except Exception as e:
            return {"status": "error", "message": str(e), "help": "For Gmail: Enable 2FA, create App Password at myaccount.google.com/apppasswords"}
    
    def read_inbox(self, count: int = 10, folder: str = "INBOX") -> dict:
        """Read recent emails from inbox."""
        if not self.is_configured():
            return {"status": "setup_needed", "message": "Email not configured"}
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.email_password)
            mail.select(folder)
            
            _, data = mail.search(None, "ALL")
            email_ids = data[0].split()
            recent_ids = email_ids[-count:] if len(email_ids) >= count else email_ids
            recent_ids.reverse()
            
            emails = []
            for eid in recent_ids:
                _, msg_data = mail.fetch(eid, "(RFC822)")
                msg = email_lib.message_from_bytes(msg_data[0][1])
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")[:500]
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")[:500]
                
                emails.append({
                    "from": msg.get("From", "Unknown"),
                    "subject": msg.get("Subject", "No Subject"),
                    "date": msg.get("Date", ""),
                    "preview": body[:200],
                    "id": eid.decode()
                })
            
            mail.logout()
            return {"status": "ok", "count": len(emails), "emails": emails}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def search_emails(self, query: str, count: int = 10) -> dict:
        """Search emails by subject or sender."""
        if not self.is_configured():
            return {"status": "setup_needed", "message": "Email not configured"}
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.email_password)
            mail.select("INBOX")
            
            _, data = mail.search(None, f'(OR SUBJECT "{query}" FROM "{query}")')
            email_ids = data[0].split()
            recent_ids = email_ids[-count:] if len(email_ids) >= count else email_ids
            recent_ids.reverse()
            
            emails = []
            for eid in recent_ids:
                _, msg_data = mail.fetch(eid, "(RFC822)")
                msg = email_lib.message_from_bytes(msg_data[0][1])
                emails.append({
                    "from": msg.get("From", "Unknown"),
                    "subject": msg.get("Subject", "No Subject"),
                    "date": msg.get("Date", ""),
                })
            
            mail.logout()
            return {"status": "ok", "query": query, "results": len(emails), "emails": emails}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def compose_smart_reply(self, original_subject: str, original_body: str, intent: str = "reply") -> dict:
        """AI drafts a smart email reply."""
        return {
            "status": "draft_ready",
            "subject": f"Re: {original_subject}",
            "body_suggestion": f"Based on the original email about '{original_subject[:50]}', here's a suggested {intent}...",
            "action": "Review and send with /email send"
        }


# ═══════════════════════════════════════════════════════════
#  💬 WHATSAPP ENGINE — Messages & Calls
# ═══════════════════════════════════════════════════════════

class JarvisWhatsAppEngine:
    """WhatsApp integration via wa.me deep links and web API."""
    
    def __init__(self):
        self.user_contacts = self._load_contacts()
    
    def _load_contacts(self) -> dict:
        try:
            p = Path("jarvis_contacts.json")
            if p.exists():
                return json.loads(p.read_text())
        except:
            pass
        return {}
    
    def _save_contacts(self):
        Path("jarvis_contacts.json").write_text(json.dumps(self.user_contacts, indent=2, ensure_ascii=False))
    
    def add_contact(self, name: str, phone: str) -> dict:
        """Save a contact for quick messaging."""
        phone = phone.replace("+", "").replace(" ", "").replace("-", "")
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone
        self.user_contacts[name.lower()] = {"name": name, "phone": phone, "added": datetime.now().isoformat()}
        self._save_contacts()
        return {"status": "saved", "name": name, "phone": phone, "message": f"Contact '{name}' saved! ✅"}
    
    def get_contacts(self) -> dict:
        """List all saved contacts."""
        return {"contacts": self.user_contacts, "count": len(self.user_contacts)}
    
    def send_message(self, to: str, message: str) -> dict:
        """Send WhatsApp message via wa.me deep link or API."""
        phone = to.replace("+", "").replace(" ", "").replace("-", "")
        
        # Check saved contacts
        if to.lower() in self.user_contacts:
            phone = self.user_contacts[to.lower()]["phone"]
        elif not phone.isdigit():
            return {"status": "need_number", "message": f"Contact '{to}' not found. Please provide phone number or save contact first."}
        
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone
        
        encoded_msg = urllib.parse.quote(message)
        wa_link = f"https://wa.me/{phone}?text={encoded_msg}"
        api_link = f"https://api.whatsapp.com/send?phone={phone}&text={encoded_msg}"
        
        return {
            "status": "ready",
            "phone": phone,
            "message": message,
            "wa_link": wa_link,
            "api_link": api_link,
            "action": f"Click to send: {wa_link}",
            "instructions": "Open this link to send WhatsApp message instantly! JARVIS has prepared everything for you."
        }
    
    def make_call(self, to: str) -> dict:
        """Initiate WhatsApp call via deep link."""
        phone = to.replace("+", "").replace(" ", "").replace("-", "")
        if to.lower() in self.user_contacts:
            phone = self.user_contacts[to.lower()]["phone"]
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone
        
        return {
            "status": "ready",
            "phone": phone,
            "call_link": f"https://wa.me/{phone}",
            "video_call_link": f"https://wa.me/{phone}?video=true",
            "action": "WhatsApp call link ready! Click to call.",
            "instructions": "Open the link to start WhatsApp voice/video call"
        }
    
    def send_bulk(self, contacts: list, message: str) -> dict:
        """Send WhatsApp to multiple contacts."""
        results = []
        for contact in contacts:
            r = self.send_message(contact, message)
            results.append({"contact": contact, **r})
        return {"status": "bulk_ready", "count": len(results), "results": results}


# ═══════════════════════════════════════════════════════════
#  💼 LINKEDIN ENGINE — Professional Networking
# ═══════════════════════════════════════════════════════════

class JarvisLinkedInEngine:
    """LinkedIn integration — post updates, network management."""
    
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.profile = self._load_profile()
    
    def _load_profile(self) -> dict:
        try:
            p = Path("jarvis_linkedin_profile.json")
            if p.exists():
                return json.loads(p.read_text())
        except:
            pass
        return {}
    
    def is_configured(self) -> bool:
        return bool(self.access_token)
    
    def create_post(self, content: str) -> dict:
        """Create a LinkedIn post."""
        if not self.is_configured():
            share_url = f"https://www.linkedin.com/sharing/share-offsite/?url=&text={urllib.parse.quote(content[:700])}"
            return {
                "status": "share_ready",
                "content": content,
                "share_link": share_url,
                "action": f"Click to post on LinkedIn: {share_url}",
                "instructions": "Open this link to share your post on LinkedIn! JARVIS prepared the content."
            }
        
        import requests
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        body = {
            "author": f"urn:li:person:{self.profile.get('id', '')}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        try:
            r = requests.post("https://api.linkedin.com/v2/ugcPosts", json=body, headers=headers, timeout=10)
            if r.status_code in [200, 201]:
                return {"status": "posted", "content": content[:100], "message": "LinkedIn post published! ✅"}
            return {"status": "error", "code": r.status_code, "detail": r.text[:200]}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def generate_post_idea(self, topic: str = "AI trading") -> dict:
        """AI generates LinkedIn post ideas."""
        ideas = [
            f"🚀 How AI is revolutionizing {topic} — 5 insights from my JARVIS AI agent that changed my trading game!",
            f"📊 I let AI manage my {topic} portfolio for 30 days. Here's what happened... (Thread 🧵)",
            f"💡 The future of {topic} is here. My AI assistant JARVIS just did something incredible...",
            f"🔥 Hot take: {topic} will never be the same after 2026. Here's why smart money is paying attention.",
            f"📈 From ₹0 to consistent profits: How I used AI-powered {topic} to change my financial life.",
        ]
        return {"status": "ideas_ready", "topic": topic, "ideas": ideas, "count": len(ideas)}
    
    def generate_profile_headline(self, skills: list = None) -> dict:
        """Generate compelling LinkedIn headlines."""
        if not skills:
            skills = ["AI Trading", "Machine Learning", "FinTech"]
        headlines = [
            f"{'|'.join(skills[:3])} Enthusiast | Building the Future with AI",
            f"Passionate about {skills[0]} | {skills[1]} | Helping others grow 📈",
            f"AI-First Trader & {skills[0]} Expert | 10x Your Portfolio with Smart Tech",
        ]
        return {"status": "ok", "headlines": headlines}


# ═══════════════════════════════════════════════════════════
#  🖥️ DESKTOP CONTROL ENGINE — Screen, Apps, System
# ═══════════════════════════════════════════════════════════

class JarvisDesktopEngine:
    """Control your desktop — apps, screen, files, system."""
    
    def __init__(self):
        self.os_type = platform.system()
        self.screen_available = self._check_screen()
    
    def _check_screen(self) -> bool:
        try:
            import pyautogui
            return True
        except:
            return False
    
    def get_system_info(self) -> dict:
        """Get complete system information."""
        import shutil
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "hostname": platform.node(),
        }
        
        try:
            import psutil
            info["cpu_percent"] = psutil.cpu_percent(interval=1)
            info["ram_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
            info["ram_used_gb"] = round(psutil.virtual_memory().used / (1024**3), 2)
            info["ram_percent"] = psutil.virtual_memory().percent
            info["disk_total_gb"] = round(shutil.disk_usage("/").total / (1024**3), 2)
            info["disk_free_gb"] = round(shutil.disk_usage("/").free / (1024**3), 2)
            battery = psutil.sensors_battery()
            if battery:
                info["battery_percent"] = battery.percent
                info["battery_plugged"] = battery.power_plugged
                info["battery_time_left"] = str(timedelta(seconds=battery.secsleft)) if battery.secsleft > 0 else "Charging"
        except:
            pass
        
        return {"status": "ok", "system": info}
    
    def take_screenshot(self, filename: str = None) -> dict:
        """Take a screenshot of the current screen."""
        if not filename:
            filename = f"jarvis_screenshot_{int(time.time())}.png"
        
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            filepath = str(Path("screenshots") / filename)
            Path("screenshots").mkdir(exist_ok=True)
            screenshot.save(filepath)
            return {"status": "ok", "file": filepath, "message": f"Screenshot saved: {filepath}"}
        except ImportError:
            # Fallback to system command
            filepath = f"screenshots/{filename}"
            Path("screenshots").mkdir(exist_ok=True)
            if self.os_type == "Linux":
                try:
                    subprocess.run(["scrot", filepath], capture_output=True, timeout=5)
                    if Path(filepath).exists():
                        return {"status": "ok", "file": filepath}
                except:
                    pass
            return {"status": "unavailable", "message": "Screenshot requires display. On server, use remote desktop.", 
                    "tip": "On your laptop/phone, JARVIS APK/EXE has full screenshot support!"}
    
    def open_app(self, app_name: str) -> dict:
        """Open any application on the system."""
        app_map = {
            "chrome": {"Windows": "start chrome", "Darwin": "open -a 'Google Chrome'", "Linux": "google-chrome"},
            "firefox": {"Windows": "start firefox", "Darwin": "open -a Firefox", "Linux": "firefox"},
            "notepad": {"Windows": "start notepad", "Darwin": "open -a TextEdit", "Linux": "gedit"},
            "terminal": {"Windows": "start cmd", "Darwin": "open -a Terminal", "Linux": "gnome-terminal"},
            "calculator": {"Windows": "start calc", "Darwin": "open -a Calculator", "Linux": "gnome-calculator"},
            "whatsapp": {"Windows": "start whatsapp:", "Darwin": "open -a WhatsApp", "Linux": "xdg-open https://web.whatsapp.com"},
            "linkedin": {"all": "xdg-open https://www.linkedin.com || open https://www.linkedin.com || start https://www.linkedin.com"},
            "gmail": {"all": "xdg-open https://mail.google.com || open https://mail.google.com || start https://mail.google.com"},
        }
        
        app_lower = app_name.lower()
        if app_lower in app_map:
            cmd_map = app_map[app_lower]
            if "all" in cmd_map:
                cmd = cmd_map["all"]
            else:
                cmd = cmd_map.get(self.os_type, f"xdg-open {app_lower}")
        else:
            cmd = f"start {app_name}" if self.os_type == "Windows" else f"xdg-open {app_name}" if self.os_type == "Linux" else f"open -a '{app_name}'"
        
        try:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"status": "opened", "app": app_name, "command": cmd, "message": f"Opening {app_name}... ✅"}
        except Exception as e:
            return {"status": "error", "app": app_name, "message": str(e)}
    
    def open_url(self, url: str) -> dict:
        """Open any URL in the default browser."""
        try:
            webbrowser.open(url)
            return {"status": "opened", "url": url, "message": f"Opening {url} in browser... ✅"}
        except Exception as e:
            return {"status": "error", "url": url, "message": str(e)}
    
    def type_text(self, text: str) -> dict:
        """Type text using keyboard automation."""
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.02)
            return {"status": "typed", "text": text[:50], "message": "Text typed successfully!"}
        except ImportError:
            return {"status": "unavailable", "message": "Keyboard control requires pyautogui + display. Available in desktop app."}
    
    def hotkey(self, *keys) -> dict:
        """Press keyboard shortcut."""
        try:
            import pyautogui
            pyautogui.hotkey(*keys)
            return {"status": "ok", "keys": list(keys), "message": f"Pressed {'+'.join(keys)}"}
        except ImportError:
            return {"status": "unavailable", "message": "Keyboard control requires desktop app."}
    
    def list_files(self, path: str = ".", pattern: str = "*") -> dict:
        """List files in a directory."""
        try:
            p = Path(path)
            files = list(p.glob(pattern))[:50]
            return {
                "status": "ok",
                "path": str(p.resolve()),
                "count": len(files),
                "files": [{"name": f.name, "size": f.stat().st_size if f.is_file() else 0, 
                           "type": "file" if f.is_file() else "dir", 
                           "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()} for f in files]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def create_file(self, filepath: str, content: str) -> dict:
        """Create a file with content."""
        try:
            p = Path(filepath)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return {"status": "created", "file": str(p), "size": len(content), "message": f"File created: {filepath} ✅"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def read_file_content(self, filepath: str) -> dict:
        """Read a file's content."""
        try:
            p = Path(filepath)
            content = p.read_text()[:10000]
            return {"status": "ok", "file": str(p), "content": content, "size": p.stat().st_size}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def run_command(self, command: str) -> dict:
        """Execute a system command safely."""
        dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb"]
        for d in dangerous:
            if d in command.lower():
                return {"status": "blocked", "message": "This command could be dangerous. JARVIS protects your system! 🛡️"}
        
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {
                "status": "ok",
                "command": command,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "message": "Command took too long (>30s)"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_running_processes(self, count: int = 20) -> dict:
        """List running processes."""
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                procs.append(p.info)
            procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            return {"status": "ok", "count": len(procs[:count]), "processes": procs[:count]}
        except:
            result = subprocess.run("ps aux --sort=-%cpu | head -20", shell=True, capture_output=True, text=True, timeout=5)
            return {"status": "ok", "raw": result.stdout}
    
    def get_network_info(self) -> dict:
        """Get network information."""
        try:
            import psutil
            addrs = psutil.net_if_addrs()
            stats = psutil.net_io_counters()
            return {
                "status": "ok",
                "interfaces": {k: [{"address": a.address, "family": str(a.family)} for a in v] for k, v in addrs.items()},
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
            }
        except:
            return {"status": "basic", "hostname": platform.node()}
    
    def set_volume(self, level: int) -> dict:
        """Set system volume (0-100)."""
        level = max(0, min(100, level))
        if self.os_type == "Linux":
            try:
                subprocess.run(f"amixer set Master {level}%", shell=True, capture_output=True, timeout=5)
                return {"status": "ok", "volume": level}
            except:
                pass
        elif self.os_type == "Darwin":
            try:
                subprocess.run(f"osascript -e 'set volume output volume {level}'", shell=True, capture_output=True, timeout=5)
                return {"status": "ok", "volume": level}
            except:
                pass
        return {"status": "unavailable", "message": f"Volume control: Use your system settings to set volume to {level}%"}


# ═══════════════════════════════════════════════════════════
#  🌐 SMART WEB SEARCH ENGINE
# ═══════════════════════════════════════════════════════════

class JarvisWebSearch:
    """Search the internet for anything."""
    
    def search(self, query: str, count: int = 5) -> dict:
        """Search the web using DuckDuckGo."""
        try:
            import requests
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                timeout=10
            )
            data = r.json()
            results = []
            
            if data.get("Abstract"):
                results.append({"title": data.get("Heading", ""), "snippet": data["Abstract"], "url": data.get("AbstractURL", ""), "source": data.get("AbstractSource", "")})
            
            for item in data.get("RelatedTopics", [])[:count]:
                if "Text" in item:
                    results.append({"title": item.get("FirstURL", "").split("/")[-1], "snippet": item["Text"], "url": item.get("FirstURL", "")})
            
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            
            return {"status": "ok", "query": query, "results": results, "count": len(results), "google_link": google_url}
        except Exception as e:
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            return {"status": "fallback", "query": query, "google_link": google_url, "message": f"Open Google: {google_url}"}
    
    def get_news(self, topic: str = "India stock market") -> dict:
        """Get latest news on any topic."""
        try:
            import requests
            r = requests.get(
                f"https://newsdata.io/api/1/news",
                params={"apikey": os.getenv("NEWSDATA_API_KEY", ""), "q": topic, "language": "en", "size": 5},
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                return {"status": "ok", "topic": topic, "articles": data.get("results", [])[:5]}
        except:
            pass
        
        return {
            "status": "ok",
            "topic": topic,
            "search_url": f"https://news.google.com/search?q={urllib.parse.quote(topic)}",
            "message": f"Latest news on '{topic}' available at the search link"
        }


# ═══════════════════════════════════════════════════════════
#  📅 CALENDAR & LIFE MANAGEMENT
# ═══════════════════════════════════════════════════════════

class JarvisLifeManager:
    """Manage your life — calendar, goals, habits, budget."""
    
    LIFE_FILE = Path("jarvis_life_data.json")
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> dict:
        try:
            if self.LIFE_FILE.exists():
                return json.loads(self.LIFE_FILE.read_text())
        except:
            pass
        return {"events": [], "goals": [], "habits": [], "budget": {}, "journal": []}
    
    def _save(self):
        self.LIFE_FILE.write_text(json.dumps(self.data, indent=2, ensure_ascii=False, default=str))
    
    def add_event(self, title: str, date: str, time_str: str = "09:00", description: str = "") -> dict:
        event = {
            "id": f"E{int(time.time())}",
            "title": title,
            "date": date,
            "time": time_str,
            "description": description,
            "created": datetime.now().isoformat()
        }
        self.data["events"].append(event)
        self._save()
        return {"status": "added", "event": event, "message": f"Event '{title}' added for {date} at {time_str} ✅"}
    
    def get_today_events(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        events = [e for e in self.data["events"] if e.get("date") == today]
        return {"status": "ok", "date": today, "events": events, "count": len(events)}
    
    def get_upcoming_events(self, days: int = 7) -> dict:
        now = datetime.now()
        end = now + timedelta(days=days)
        events = []
        for e in self.data["events"]:
            try:
                edate = datetime.strptime(e["date"], "%Y-%m-%d")
                if now.date() <= edate.date() <= end.date():
                    events.append(e)
            except:
                pass
        events.sort(key=lambda x: x.get("date", ""))
        return {"status": "ok", "days": days, "events": events, "count": len(events)}
    
    def set_goal(self, goal: str, deadline: str = "", category: str = "general") -> dict:
        g = {
            "id": f"G{int(time.time())}",
            "goal": goal,
            "deadline": deadline,
            "category": category,
            "progress": 0,
            "status": "active",
            "created": datetime.now().isoformat()
        }
        self.data["goals"].append(g)
        self._save()
        return {"status": "added", "goal": g, "message": f"Goal set: '{goal}' 🎯"}
    
    def get_goals(self) -> dict:
        active = [g for g in self.data["goals"] if g.get("status") == "active"]
        return {"status": "ok", "goals": active, "count": len(active)}
    
    def update_goal_progress(self, goal_id: str, progress: int) -> dict:
        for g in self.data["goals"]:
            if g["id"] == goal_id:
                g["progress"] = min(100, progress)
                if progress >= 100:
                    g["status"] = "completed"
                self._save()
                return {"status": "updated", "goal": g}
        return {"status": "not_found"}
    
    def add_journal_entry(self, entry: str, mood: str = "neutral") -> dict:
        j = {
            "id": f"J{int(time.time())}",
            "entry": entry,
            "mood": mood,
            "date": datetime.now().isoformat()
        }
        self.data["journal"].append(j)
        self._save()
        return {"status": "added", "entry": j, "message": "Journal entry saved 📝"}
    
    def get_journal(self, count: int = 10) -> dict:
        entries = self.data["journal"][-count:]
        entries.reverse()
        return {"status": "ok", "entries": entries, "count": len(entries)}
    
    def set_budget(self, category: str, amount: float) -> dict:
        if "budget" not in self.data:
            self.data["budget"] = {}
        self.data["budget"][category] = {"amount": amount, "spent": 0, "updated": datetime.now().isoformat()}
        self._save()
        return {"status": "set", "category": category, "budget": amount, "message": f"Budget for '{category}': ₹{amount:,.0f}"}
    
    def log_expense(self, category: str, amount: float, description: str = "") -> dict:
        if category in self.data.get("budget", {}):
            self.data["budget"][category]["spent"] = self.data["budget"][category].get("spent", 0) + amount
        if "expenses" not in self.data:
            self.data["expenses"] = []
        self.data["expenses"].append({
            "category": category, "amount": amount, "description": description,
            "date": datetime.now().isoformat()
        })
        self._save()
        remaining = self.data.get("budget", {}).get(category, {}).get("amount", 0) - self.data.get("budget", {}).get(category, {}).get("spent", 0)
        return {"status": "logged", "category": category, "amount": amount, "remaining": remaining}
    
    def get_budget_summary(self) -> dict:
        return {"status": "ok", "budget": self.data.get("budget", {}), "expenses": self.data.get("expenses", [])[-20:]}


# ═══════════════════════════════════════════════════════════
#  🔊 GLOBAL INSTANCES 
# ═══════════════════════════════════════════════════════════

email_engine = JarvisEmailEngine()
whatsapp_engine = JarvisWhatsAppEngine()
linkedin_engine = JarvisLinkedInEngine()
desktop_engine = JarvisDesktopEngine()
web_search = JarvisWebSearch()
life_manager = JarvisLifeManager()


# ═══════════════════════════════════════════════════════════
#  🎯 MASTER COMMAND PROCESSOR
# ═══════════════════════════════════════════════════════════

def process_life_command(command: str, user_id: str = "default", **kwargs) -> dict:
    """
    Universal command processor — JARVIS understands natural language.
    She NEVER says no. She ALWAYS finds a way.
    """
    cmd = command.lower().strip()
    
    # WhatsApp commands
    if any(w in cmd for w in ["whatsapp", "wa ", "message send", "msg bhej", "call kar"]):
        if "call" in cmd:
            phone = kwargs.get("phone", "")
            return whatsapp_engine.make_call(phone)
        elif "send" in cmd or "bhej" in cmd:
            phone = kwargs.get("phone", kwargs.get("to", ""))
            msg = kwargs.get("message", "")
            return whatsapp_engine.send_message(phone, msg)
        elif "contact" in cmd:
            return whatsapp_engine.get_contacts()
    
    # Email commands
    if any(w in cmd for w in ["email", "mail", "inbox", "gmail"]):
        if "send" in cmd or "bhej" in cmd:
            return email_engine.send_email(kwargs.get("to", ""), kwargs.get("subject", ""), kwargs.get("body", ""))
        elif "read" in cmd or "inbox" in cmd or "padh" in cmd:
            return email_engine.read_inbox(kwargs.get("count", 10))
        elif "search" in cmd or "dhundh" in cmd:
            return email_engine.search_emails(kwargs.get("query", cmd))
    
    # LinkedIn commands
    if any(w in cmd for w in ["linkedin", "li post", "professional"]):
        if "post" in cmd:
            return linkedin_engine.create_post(kwargs.get("content", cmd))
        elif "idea" in cmd:
            return linkedin_engine.generate_post_idea(kwargs.get("topic", "AI"))
    
    # Desktop commands
    if any(w in cmd for w in ["screenshot", "screen", "capture"]):
        return desktop_engine.take_screenshot()
    if any(w in cmd for w in ["open", "launch", "start", "kholो"]):
        app = kwargs.get("app", cmd.split()[-1])
        return desktop_engine.open_app(app)
    if any(w in cmd for w in ["system info", "laptop info", "computer info", "battery"]):
        return desktop_engine.get_system_info()
    if any(w in cmd for w in ["volume"]):
        level = kwargs.get("level", 50)
        return desktop_engine.set_volume(level)
    
    # Life management
    if any(w in cmd for w in ["event", "calendar", "schedule"]):
        return life_manager.add_event(kwargs.get("title", cmd), kwargs.get("date", datetime.now().strftime("%Y-%m-%d")))
    if any(w in cmd for w in ["goal", "target", "aim"]):
        return life_manager.set_goal(kwargs.get("goal", cmd))
    if any(w in cmd for w in ["journal", "diary", "feeling"]):
        return life_manager.add_journal_entry(kwargs.get("entry", cmd), kwargs.get("mood", "neutral"))
    if any(w in cmd for w in ["budget", "kharcha", "expense"]):
        if "log" in cmd or "add" in cmd:
            return life_manager.log_expense(kwargs.get("category", "general"), kwargs.get("amount", 0), kwargs.get("description", ""))
        return life_manager.get_budget_summary()
    
    # Web search
    if any(w in cmd for w in ["search", "find", "google", "dhundh", "kya hai"]):
        return web_search.search(kwargs.get("query", cmd))
    
    # Files
    if "list files" in cmd or "files dikha" in cmd:
        return desktop_engine.list_files(kwargs.get("path", "."))
    
    # Default — search the web
    return web_search.search(cmd)


def get_life_engine_status() -> dict:
    """Get status of all life engines."""
    return {
        "status": "JARVIS Life Engine v2.0 — ALL SYSTEMS ONLINE",
        "engines": {
            "email": {"online": True, "configured": email_engine.is_configured()},
            "whatsapp": {"online": True, "configured": True},
            "linkedin": {"online": True, "configured": linkedin_engine.is_configured()},
            "desktop": {"online": True, "screen_control": desktop_engine.screen_available},
            "web_search": {"online": True},
            "life_manager": {"online": True},
            "calendar": {"online": True},
            "file_manager": {"online": True},
        },
        "capabilities": [
            "📧 Email — Send, Read, Search emails",
            "💬 WhatsApp — Send messages, Make calls",
            "💼 LinkedIn — Post updates, Generate content",
            "🖥️ Desktop — Screenshots, Open apps, System control",
            "🌐 Web Search — Research anything",
            "📅 Calendar — Events, goals, journal",
            "📁 Files — Create, read, list files",
            "🔊 System — Volume, battery, network, processes",
        ],
        "personality": "JARVIS NEVER says NO. She ALWAYS finds a way to help. 🌟"
    }
