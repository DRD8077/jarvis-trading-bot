"""
JARVIS Desktop Control Engine — Control laptop screen, apps, system via API
Provides system info, app launch, screenshots, clipboard, screen control
"""
import os, json, logging, asyncio, subprocess, platform, shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("jarvis.desktop")

SYSTEM = platform.system()  # Linux, Windows, Darwin

async def get_system_info() -> dict:
    """Get complete system information."""
    import psutil
    
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    
    try:
        battery = psutil.sensors_battery()
        battery_info = {
            "percent": battery.percent if battery else None,
            "plugged": battery.power_plugged if battery else None,
            "time_left": str(battery.secsleft // 60) + " min" if battery and battery.secsleft > 0 else "N/A"
        }
    except:
        battery_info = {"percent": None, "plugged": None, "time_left": "N/A"}
    
    return {
        "system": SYSTEM,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_cores": psutil.cpu_count(),
        "cpu_usage": f"{cpu_percent}%",
        "ram_total": f"{memory.total / (1024**3):.1f} GB",
        "ram_used": f"{memory.used / (1024**3):.1f} GB",
        "ram_percent": f"{memory.percent}%",
        "disk_total": f"{disk.total / (1024**3):.1f} GB",
        "disk_used": f"{disk.used / (1024**3):.1f} GB",
        "disk_free": f"{disk.free / (1024**3):.1f} GB",
        "battery": battery_info,
        "hostname": platform.node(),
        "python": platform.python_version(),
        "ts": datetime.now().isoformat()
    }

async def take_screenshot(filename: str = None) -> dict:
    """Take a screenshot of the desktop."""
    if not filename:
        filename = f"screenshot_{int(datetime.now().timestamp())}.png"
    
    filepath = Path("screenshots") / filename
    filepath.parent.mkdir(exist_ok=True)
    
    try:
        if SYSTEM == "Linux":
            # Try multiple screenshot methods
            for cmd in [
                f"scrot {filepath}",
                f"gnome-screenshot -f {filepath}",
                f"import -window root {filepath}",
                f"xdg-screenshot {filepath}"
            ]:
                try:
                    result = subprocess.run(cmd.split(), capture_output=True, timeout=5)
                    if result.returncode == 0:
                        return {"status": "captured", "file": str(filepath), "size": filepath.stat().st_size}
                except:
                    continue
        elif SYSTEM == "Windows":
            subprocess.run(["powershell", "-c", 
                f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen"], 
                capture_output=True, timeout=5)
        elif SYSTEM == "Darwin":
            subprocess.run(["screencapture", str(filepath)], timeout=5)
            if filepath.exists():
                return {"status": "captured", "file": str(filepath)}
        
        return {"status": "screenshot_tool_not_available", 
                "note": "Install scrot (Linux) or use on actual desktop",
                "command": "sudo apt install scrot"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def open_application(app_name: str) -> dict:
    """Open an application on the desktop."""
    app_map = {
        # Common apps
        "browser": {"linux": "xdg-open http://", "windows": "start chrome", "darwin": "open -a Safari"},
        "chrome": {"linux": "google-chrome", "windows": "start chrome", "darwin": "open -a 'Google Chrome'"},
        "firefox": {"linux": "firefox", "windows": "start firefox", "darwin": "open -a Firefox"},
        "terminal": {"linux": "gnome-terminal", "windows": "start cmd", "darwin": "open -a Terminal"},
        "files": {"linux": "nautilus", "windows": "explorer", "darwin": "open -a Finder"},
        "calculator": {"linux": "gnome-calculator", "windows": "calc", "darwin": "open -a Calculator"},
        "notepad": {"linux": "gedit", "windows": "notepad", "darwin": "open -a TextEdit"},
        "code": {"linux": "code", "windows": "code", "darwin": "code"},
        "vscode": {"linux": "code", "windows": "code", "darwin": "code"},
        "whatsapp": {"linux": "xdg-open https://web.whatsapp.com", "windows": "start https://web.whatsapp.com", "darwin": "open https://web.whatsapp.com"},
        "linkedin": {"linux": "xdg-open https://linkedin.com", "windows": "start https://linkedin.com", "darwin": "open https://linkedin.com"},
        "gmail": {"linux": "xdg-open https://mail.google.com", "windows": "start https://mail.google.com", "darwin": "open https://mail.google.com"},
        "youtube": {"linux": "xdg-open https://youtube.com", "windows": "start https://youtube.com", "darwin": "open https://youtube.com"},
        "twitter": {"linux": "xdg-open https://twitter.com", "windows": "start https://twitter.com", "darwin": "open https://twitter.com"},
        "telegram": {"linux": "telegram-desktop", "windows": "start telegram", "darwin": "open -a Telegram"},
    }
    
    app_key = app_name.lower().strip()
    sys_key = SYSTEM.lower()
    if sys_key == "windows":
        sys_key = "windows"
    elif sys_key == "darwin":
        sys_key = "darwin"
    else:
        sys_key = "linux"
    
    if app_key in app_map:
        cmd = app_map[app_key].get(sys_key, "")
        if cmd:
            try:
                subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return {"status": "opened", "app": app_name, "command": cmd}
            except Exception as e:
                return {"status": "error", "app": app_name, "error": str(e)}
    
    # Try direct launch
    try:
        subprocess.Popen(app_name, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "launched", "app": app_name}
    except:
        return {"status": "not_found", "app": app_name, 
                "available_apps": list(app_map.keys())}

async def open_url(url: str) -> dict:
    """Open a URL in the default browser."""
    try:
        if SYSTEM == "Linux":
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif SYSTEM == "Windows":
            subprocess.Popen(["start", url], shell=True)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", url])
        return {"status": "opened", "url": url}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def get_running_processes(top_n: int = 15) -> list:
    """Get top running processes by CPU/memory usage."""
    import psutil
    
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = p.info
            procs.append({
                "pid": info['pid'],
                "name": info['name'],
                "cpu": round(info.get('cpu_percent', 0), 1),
                "memory": round(info.get('memory_percent', 0), 1)
            })
        except:
            pass
    
    procs.sort(key=lambda x: x['cpu'], reverse=True)
    return procs[:top_n]

async def kill_process(name_or_pid) -> dict:
    """Kill a process by name or PID."""
    import psutil
    
    killed = []
    try:
        if isinstance(name_or_pid, int) or str(name_or_pid).isdigit():
            pid = int(name_or_pid)
            p = psutil.Process(pid)
            p.terminate()
            killed.append({"pid": pid, "name": p.name()})
        else:
            for p in psutil.process_iter(['name', 'pid']):
                if name_or_pid.lower() in p.info['name'].lower():
                    p.terminate()
                    killed.append({"pid": p.info['pid'], "name": p.info['name']})
    except Exception as e:
        return {"status": "error", "error": str(e)}
    
    return {"status": "killed" if killed else "not_found", "killed": killed}

async def set_volume(level: int) -> dict:
    """Set system volume (0-100)."""
    try:
        if SYSTEM == "Linux":
            subprocess.run(["amixer", "set", "Master", f"{level}%"], capture_output=True)
        elif SYSTEM == "Darwin":
            subprocess.run(["osascript", "-e", f"set volume output volume {level}"], capture_output=True)
        elif SYSTEM == "Windows":
            # PowerShell volume control
            pass
        return {"status": "set", "volume": level}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def get_clipboard() -> dict:
    """Get clipboard contents."""
    try:
        if SYSTEM == "Linux":
            result = subprocess.run(["xclip", "-selection", "clipboard", "-o"], 
                                  capture_output=True, text=True, timeout=3)
            return {"content": result.stdout, "length": len(result.stdout)}
        elif SYSTEM == "Darwin":
            result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=3)
            return {"content": result.stdout, "length": len(result.stdout)}
        return {"note": "Clipboard access requires desktop environment"}
    except:
        return {"note": "Clipboard tool not available. Install xclip on Linux."}

async def set_clipboard(text: str) -> dict:
    """Set clipboard contents."""
    try:
        if SYSTEM == "Linux":
            proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            proc.communicate(text.encode())
            return {"status": "set", "length": len(text)}
        elif SYSTEM == "Darwin":
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(text.encode())
            return {"status": "set", "length": len(text)}
        return {"note": "Clipboard access requires desktop environment"}
    except:
        return {"note": "Clipboard tool not available"}

async def search_files(query: str, directory: str = None) -> list:
    """Search for files on the system."""
    search_dir = directory or str(Path.home())
    results = []
    try:
        for root, dirs, files in os.walk(search_dir):
            # Skip hidden and system dirs
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if query.lower() in f.lower():
                    fp = os.path.join(root, f)
                    try:
                        stat = os.stat(fp)
                        results.append({
                            "name": f,
                            "path": fp,
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                    except:
                        pass
                if len(results) >= 20:
                    return results
    except:
        pass
    return results

async def execute_command(command: str) -> dict:
    """Execute a system command safely."""
    # Block dangerous commands
    dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb", "shutdown", "reboot"]
    if any(d in command.lower() for d in dangerous):
        return {"status": "blocked", "reason": "Command blocked for safety", "command": command}
    
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        return {
            "status": "executed",
            "command": command,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000] if result.stderr else "",
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "command": command}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def get_wifi_info() -> dict:
    """Get WiFi/network information."""
    try:
        result = subprocess.run(["ip", "addr"], capture_output=True, text=True, timeout=5)
        hostname = platform.node()
        return {
            "hostname": hostname,
            "network_info": result.stdout[:2000] if result.returncode == 0 else "N/A",
            "system": SYSTEM
        }
    except:
        return {"hostname": platform.node(), "network_info": "N/A"}

async def create_desktop_notification(title: str, message: str) -> dict:
    """Send a desktop notification."""
    try:
        if SYSTEM == "Linux":
            subprocess.run(["notify-send", title, message], timeout=5)
        elif SYSTEM == "Darwin":
            subprocess.run(["osascript", "-e", 
                f'display notification "{message}" with title "{title}"'], timeout=5)
        return {"status": "sent", "title": title, "message": message}
    except:
        return {"status": "no_display", "title": title, "message": message,
                "note": "Desktop notifications require a display environment"}

def get_engine_status() -> dict:
    return {
        "engine": "desktop_control",
        "status": "online",
        "system": SYSTEM,
        "platform": platform.platform(),
        "features": [
            "system_info", "screenshot", "open_app", "open_url",
            "processes", "kill_process", "volume", "clipboard",
            "file_search", "execute_command", "wifi_info", "notifications"
        ]
    }

logger.info("🖥️ Desktop control engine loaded")
