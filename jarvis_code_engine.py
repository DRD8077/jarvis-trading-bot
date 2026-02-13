"""
⚡ JARVIS CODE ENGINE — Autonomous Code Generation + Execution
═══════════════════════════════════════════════════════════════
Nuclear-level AI Coder:
  • User says "code banao X" → JARVIS generates, installs, runs, returns OUTPUT
  • User says "github.com/x/y run karo" → JARVIS clones, installs, runs, returns OUTPUT
  • No manual steps needed — JARVIS does EVERYTHING autonomously
  • Supports: Python, Node.js, Go, Rust, C/C++, Java, Shell, HTML+CSS
  • Auto-dependency detection, sandboxed execution, timeout protection

Author: David Crew AI (Boss: Deepak Kumar)
"""

import os
import re
import json
import time
import shutil
import logging
import subprocess
import tempfile
import hashlib
from typing import Optional, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger("jarvis_code_engine")

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "5647898018"))

# Execution limits
MAX_EXECUTION_TIME = 30        # seconds
MAX_OUTPUT_SIZE = 4000         # chars for Telegram
MAX_FILE_SIZE = 50_000         # chars per file
SANDBOX_DIR = os.path.join(tempfile.gettempdir(), "jarvis_sandbox")
os.makedirs(SANDBOX_DIR, exist_ok=True)

# Language → file extension + run command
LANG_CONFIG = {
    "python":     {"ext": ".py",   "run": "python3 {file}",            "install": "pip3 install -q {deps}"},
    "javascript": {"ext": ".js",   "run": "node {file}",               "install": "npm install {deps}"},
    "typescript": {"ext": ".ts",   "run": "npx ts-node {file}",        "install": "npm install {deps} typescript ts-node"},
    "go":         {"ext": ".go",   "run": "go run {file}",             "install": "go get {deps}"},
    "rust":       {"ext": ".rs",   "run": "rustc {file} -o /tmp/rout && /tmp/rout", "install": ""},
    "c":          {"ext": ".c",    "run": "gcc {file} -o /tmp/cout -lm && /tmp/cout", "install": ""},
    "cpp":        {"ext": ".cpp",  "run": "g++ {file} -o /tmp/cppout -lm && /tmp/cppout", "install": ""},
    "java":       {"ext": ".java", "run": "javac {file} && java -cp {dir} Main", "install": ""},
    "bash":       {"ext": ".sh",   "run": "bash {file}",               "install": ""},
    "html":       {"ext": ".html", "run": "",                          "install": ""},
    "shell":      {"ext": ".sh",   "run": "bash {file}",               "install": ""},
}

# ═══════════════════════════════════════════════════════════
#  AI CODE GENERATION PROMPT — (NUCLEAR LEVEL)
# ═══════════════════════════════════════════════════════════

CODE_GEN_SYSTEM = """You are JARVIS CODE ENGINE — the world's most powerful autonomous code generator.

You write COMPLETE, RUNNABLE code that works FIRST TIME. No placeholders. No TODO. No "...".

RESPONSE FORMAT — STRICT JSON:
{
  "language": "python",
  "main_file": "main.py",
  "files": {
    "main.py": "complete code here",
    "requirements.txt": "package1\\npackage2"
  },
  "dependencies": ["requests", "beautifulsoup4"],
  "description": "What this does (in Hindi)",
  "run_command": "python3 main.py"
}

RULES:
1. Return ONLY the JSON. No markdown. No ```json blocks. JUST the raw JSON object.
2. code MUST be 100% complete and runnable — user will NEVER see the code, only OUTPUT
3. Handle ALL errors with try/except — print user-friendly messages
4. For web scrapers: use requests + beautifulsoup4 (NOT selenium)
5. For APIs: use requests (NOT httpx)
6. Print clear, beautiful output with emojis — this output goes to Telegram
7. ALL imports must be standard library OR in dependencies list
8. For Python: ALWAYS include a requirements.txt with ALL non-stdlib packages
9. Main logic MUST be in if __name__ == '__main__' block
10. Output formatting: use print() with beautiful formatting
11. NEVER use input() — this runs autonomously, no user interaction possible
12. NEVER use GUI libraries (tkinter, pygame) — this is headless server
13. For heavy computations: keep under 30 seconds
14. ALWAYS print something — the user expects to see output"""


# ═══════════════════════════════════════════════════════════
#  CORE: AI Code Generation
# ═══════════════════════════════════════════════════════════

def generate_autonomous_code(prompt: str) -> Dict:
    """Generate complete runnable code using FREE AI (Groq → Gemini).
    Returns: {language, main_file, files{}, dependencies[], description, run_command}
    """
    user_msg = (
        f"Generate a COMPLETE runnable project for this request:\n\n"
        f"REQUEST: {prompt}\n\n"
        f"Return ONLY valid JSON. No markdown. No code blocks. JUST the JSON object.\n"
        f"The code must print beautiful output — user will only see the printed output.\n"
        f"Include ALL dependencies in the dependencies array."
    )
    
    # ── Try Groq first (fastest) ──
    result = _try_groq(user_msg)
    if result:
        return result
    
    # ── Try Gemini (free tier) ──
    result = _try_gemini(user_msg)
    if result:
        return result
    
    return {"error": "❌ AI code generation failed. Thodi der mein try kariye!"}


def _try_groq(prompt: str) -> Optional[Dict]:
    """Generate via Groq (llama-3.3-70b)."""
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY, timeout=60.0)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": CODE_GEN_SYSTEM},
                {"role": "user", "content": prompt}
            ],
            max_tokens=8000,
            temperature=0.15,
        )
        text = resp.choices[0].message.content
        return _parse_code_json(text)
    except Exception as e:
        logger.error(f"[CODE-ENGINE] Groq error: {e}")
        return None


def _try_gemini(prompt: str) -> Optional[Dict]:
    """Generate via Gemini 2.5 Flash."""
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        full_prompt = f"{CODE_GEN_SYSTEM}\n\n{prompt}"
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )
        if resp.text:
            return _parse_code_json(resp.text)
    except Exception as e:
        logger.error(f"[CODE-ENGINE] Gemini error: {e}")
    return None


def _parse_code_json(text: str) -> Optional[Dict]:
    """Parse AI response into code JSON — robust extraction."""
    if not text:
        return None
    
    # Strip markdown wrappers
    text = re.sub(r'^```(?:json)?\s*\n?', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text.strip(), flags=re.MULTILINE)
    
    # Try direct parse
    for attempt in range(3):
        try:
            if attempt == 0:
                result = json.loads(text.strip())
            elif attempt == 1:
                start, end = text.find('{'), text.rfind('}') + 1
                if start >= 0 and end > start:
                    result = json.loads(text[start:end])
                else:
                    continue
            else:
                # Try to fix common JSON issues
                fixed = text.replace("'", '"').replace('\n', '\\n')
                start, end = fixed.find('{'), fixed.rfind('}') + 1
                if start >= 0 and end > start:
                    result = json.loads(fixed[start:end])
                else:
                    continue
            
            if "files" in result or "main_file" in result:
                # Normalize structure
                if isinstance(result.get("files"), list):
                    # Convert list format to dict
                    d = {}
                    for f in result["files"]:
                        if isinstance(f, dict):
                            d[f.get("path", f.get("name", "main.py"))] = f.get("content", "")
                    result["files"] = d
                
                if "language" not in result:
                    result["language"] = "python"
                if "main_file" not in result:
                    result["main_file"] = next(iter(result.get("files", {"main.py": ""})))
                if "dependencies" not in result:
                    result["dependencies"] = []
                if "run_command" not in result:
                    lang = result["language"]
                    mf = result["main_file"]
                    result["run_command"] = LANG_CONFIG.get(lang, {}).get("run", f"python3 {mf}").replace("{file}", mf)
                
                return result
        except (json.JSONDecodeError, ValueError):
            continue
    
    # Last resort: extract code blocks and wrap
    code_match = re.search(r'```(\w+)?\n(.*?)```', text, re.DOTALL)
    if code_match:
        lang = code_match.group(1) or "python"
        code = code_match.group(2).strip()
        ext = LANG_CONFIG.get(lang, {}).get("ext", ".py")
        mf = f"main{ext}"
        return {
            "language": lang,
            "main_file": mf,
            "files": {mf: code},
            "dependencies": _detect_python_deps(code) if lang == "python" else [],
            "description": "AI generated code",
            "run_command": LANG_CONFIG.get(lang, {}).get("run", f"python3 {mf}").replace("{file}", mf),
        }
    
    return None


# ═══════════════════════════════════════════════════════════
#  CORE: Autonomous Execution Pipeline
# ═══════════════════════════════════════════════════════════

def execute_code_autonomous(prompt: str, chat_id: int = 0) -> Dict:
    """
    FULL AUTONOMOUS PIPELINE:
    1. Generate code from prompt
    2. Save files to sandbox
    3. Install dependencies
    4. Execute
    5. Return output ONLY
    
    Returns: {success, output, description, language, execution_time, files_count}
    """
    start_time = time.time()
    
    # Step 1: Generate code
    logger.info(f"[CODE-ENGINE] Generating code for: {prompt[:80]}...")
    project = generate_autonomous_code(prompt)
    
    if not project or "error" in project:
        return {
            "success": False,
            "output": project.get("error", "❌ Code generation failed!"),
            "description": "",
            "language": "unknown",
            "execution_time": time.time() - start_time,
            "files_count": 0,
        }
    
    # Step 2: Create sandbox directory
    sandbox_id = hashlib.md5(f"{chat_id}_{time.time()}".encode()).hexdigest()[:12]
    sandbox_path = os.path.join(SANDBOX_DIR, f"project_{sandbox_id}")
    os.makedirs(sandbox_path, exist_ok=True)
    
    try:
        # Step 3: Save files
        files = project.get("files", {})
        for filename, content in files.items():
            filepath = os.path.join(sandbox_path, filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(content)
        
        logger.info(f"[CODE-ENGINE] Saved {len(files)} files to {sandbox_path}")
        
        # Step 4: Install dependencies
        deps = project.get("dependencies", [])
        lang = project.get("language", "python")
        dep_output = _install_deps(deps, lang, sandbox_path)
        
        # Also install from requirements.txt if exists
        req_file = os.path.join(sandbox_path, "requirements.txt")
        if os.path.exists(req_file):
            try:
                subprocess.run(
                    f"pip3 install -q -r {req_file}",
                    shell=True, cwd=sandbox_path,
                    capture_output=True, text=True, timeout=60
                )
            except Exception:
                pass
        
        # Also install from package.json if exists
        pkg_file = os.path.join(sandbox_path, "package.json")
        if os.path.exists(pkg_file):
            try:
                subprocess.run(
                    "npm install --quiet",
                    shell=True, cwd=sandbox_path,
                    capture_output=True, text=True, timeout=60
                )
            except Exception:
                pass
        
        # Step 5: Execute
        main_file = project.get("main_file", "main.py")
        run_cmd = project.get("run_command", "")
        
        if not run_cmd:
            run_cmd = LANG_CONFIG.get(lang, {}).get("run", f"python3 {main_file}")
            run_cmd = run_cmd.replace("{file}", main_file).replace("{dir}", sandbox_path)
        
        logger.info(f"[CODE-ENGINE] Running: {run_cmd}")
        
        proc = subprocess.run(
            run_cmd,
            shell=True,
            cwd=sandbox_path,
            capture_output=True,
            text=True,
            timeout=MAX_EXECUTION_TIME,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        
        output = proc.stdout.strip()
        errors = proc.stderr.strip()
        
        # Combine output
        if proc.returncode == 0:
            final_output = output if output else "(No output — code ran successfully)"
        else:
            # Try to auto-fix and re-run once
            fix_result = _auto_fix_and_rerun(project, errors, sandbox_path, chat_id)
            if fix_result:
                return fix_result
            final_output = f"{output}\n\n⚠️ Errors:\n{errors}" if errors else output or "(Code failed with no output)"
        
        execution_time = time.time() - start_time
        
        return {
            "success": proc.returncode == 0,
            "output": final_output[:MAX_OUTPUT_SIZE],
            "description": project.get("description", ""),
            "language": lang,
            "execution_time": execution_time,
            "files_count": len(files),
            "run_command": run_cmd,
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": f"⏰ Code execution timed out ({MAX_EXECUTION_TIME}s limit). Code bahut heavy hai!",
            "description": project.get("description", ""),
            "language": project.get("language", "unknown"),
            "execution_time": time.time() - start_time,
            "files_count": len(project.get("files", {})),
        }
    
    except Exception as e:
        logger.error(f"[CODE-ENGINE] Execution error: {e}")
        return {
            "success": False,
            "output": f"❌ Execution error: {str(e)[:200]}",
            "description": "",
            "language": "unknown",
            "execution_time": time.time() - start_time,
            "files_count": 0,
        }
    
    finally:
        # Cleanup sandbox after 5 minutes
        try:
            import threading
            def _cleanup():
                time.sleep(300)
                shutil.rmtree(sandbox_path, ignore_errors=True)
            threading.Thread(target=_cleanup, daemon=True).start()
        except Exception:
            pass


def _auto_fix_and_rerun(project: Dict, error: str, sandbox_path: str, chat_id: int) -> Optional[Dict]:
    """AI auto-fix: if code fails, send error to AI → get fixed code → re-run."""
    try:
        main_file = project.get("main_file", "main.py")
        main_path = os.path.join(sandbox_path, main_file)
        
        if not os.path.exists(main_path):
            return None
        
        with open(main_path) as f:
            original_code = f.read()
        
        fix_prompt = (
            f"This Python code has an error. Fix it and return ONLY the corrected code.\n"
            f"No explanation. No markdown. JUST the fixed Python code.\n\n"
            f"ERROR:\n{error[:500]}\n\n"
            f"ORIGINAL CODE:\n{original_code[:3000]}"
        )
        
        # Try Groq for quick fix
        fixed_code = None
        if GROQ_API_KEY:
            try:
                from groq import Groq
                client = Groq(api_key=GROQ_API_KEY, timeout=30.0)
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You fix Python code. Return ONLY the corrected code. No markdown. No explanation."},
                        {"role": "user", "content": fix_prompt}
                    ],
                    max_tokens=4000,
                    temperature=0.1,
                )
                fixed_code = resp.choices[0].message.content
            except Exception:
                pass
        
        if not fixed_code:
            return None
        
        # Remove markdown wrappers
        fixed_code = re.sub(r'^```(?:python)?\s*\n?', '', fixed_code.strip(), flags=re.MULTILINE)
        fixed_code = re.sub(r'\n?```\s*$', '', fixed_code.strip(), flags=re.MULTILINE)
        
        # Save fixed code
        with open(main_path, 'w') as f:
            f.write(fixed_code)
        
        # Re-install deps if import was missing
        if "ModuleNotFoundError" in error or "ImportError" in error:
            mod_match = re.search(r"No module named ['\"](\w+)['\"]", error)
            if mod_match:
                mod = mod_match.group(1)
                subprocess.run(f"pip3 install -q {mod}", shell=True, timeout=30,
                             capture_output=True)
        
        # Re-run
        run_cmd = project.get("run_command", f"python3 {main_file}")
        proc = subprocess.run(
            run_cmd, shell=True, cwd=sandbox_path,
            capture_output=True, text=True, timeout=MAX_EXECUTION_TIME,
        )
        
        if proc.returncode == 0:
            output = proc.stdout.strip() or "(Fixed & ran successfully — no output)"
            return {
                "success": True,
                "output": f"🔧 Auto-fixed & re-ran!\n\n{output[:MAX_OUTPUT_SIZE]}",
                "description": project.get("description", ""),
                "language": project.get("language", "python"),
                "execution_time": 0,
                "files_count": len(project.get("files", {})),
                "auto_fixed": True,
            }
    
    except Exception as e:
        logger.error(f"[CODE-ENGINE] Auto-fix failed: {e}")
    
    return None


# ═══════════════════════════════════════════════════════════
#  GITHUB CLONE & RUN ENGINE
# ═══════════════════════════════════════════════════════════

def clone_and_run_github(url: str, chat_id: int = 0, run_cmd: str = "") -> Dict:
    """
    Clone a GitHub repo, auto-detect project type, install deps, run it.
    
    Returns: {success, output, description, language, execution_time}
    """
    start_time = time.time()
    
    # Parse GitHub URL
    match = re.match(r'https?://github\.com/([^/]+)/([^/\s]+)', url)
    if not match:
        return {"success": False, "output": "❌ Invalid GitHub URL! Format: https://github.com/user/repo"}
    
    owner, repo = match.group(1), match.group(2).replace(".git", "")
    
    # Create sandbox
    sandbox_id = hashlib.md5(f"{owner}_{repo}_{time.time()}".encode()).hexdigest()[:12]
    sandbox_path = os.path.join(SANDBOX_DIR, f"gh_{sandbox_id}")
    
    try:
        # Step 1: Clone
        logger.info(f"[CODE-ENGINE] Cloning {owner}/{repo}...")
        proc = subprocess.run(
            f"git clone --depth 1 https://github.com/{owner}/{repo}.git {sandbox_path}",
            shell=True, capture_output=True, text=True, timeout=60,
        )
        
        if proc.returncode != 0:
            return {"success": False, "output": f"❌ Clone failed: {proc.stderr[:200]}"}
        
        # Step 2: Auto-detect project type
        project_type = _detect_project_type(sandbox_path)
        logger.info(f"[CODE-ENGINE] Detected: {project_type}")
        
        # Step 3: Auto-install dependencies
        install_output = _auto_install(sandbox_path, project_type)
        
        # Step 4: Auto-detect run command
        if not run_cmd:
            run_cmd = _auto_detect_run_cmd(sandbox_path, project_type)
        
        if not run_cmd:
            # List files and return project structure
            files = os.listdir(sandbox_path)[:20]
            return {
                "success": True,
                "output": (
                    f"✅ Repo cloned successfully!\n"
                    f"📁 {owner}/{repo}\n"
                    f"🔧 Type: {project_type}\n"
                    f"📄 Files: {', '.join(files)}\n\n"
                    f"⚠️ Auto-run command detect nahi hua.\n"
                    f"Bataiye kaise run karna hai?"
                ),
                "description": f"GitHub repo: {owner}/{repo}",
                "language": project_type,
                "execution_time": time.time() - start_time,
            }
        
        # Step 5: Execute
        logger.info(f"[CODE-ENGINE] Running: {run_cmd}")
        proc = subprocess.run(
            run_cmd, shell=True, cwd=sandbox_path,
            capture_output=True, text=True, timeout=MAX_EXECUTION_TIME,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        
        output = proc.stdout.strip()
        errors = proc.stderr.strip()
        
        if proc.returncode == 0:
            final_output = output or "(Ran successfully — no output)"
        else:
            final_output = f"{output}\n\n⚠️ Errors:\n{errors}" if errors else "(Run failed)"
        
        return {
            "success": proc.returncode == 0,
            "output": final_output[:MAX_OUTPUT_SIZE],
            "description": f"GitHub: {owner}/{repo}",
            "language": project_type,
            "execution_time": time.time() - start_time,
            "run_command": run_cmd,
        }
    
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": f"⏰ Execution timed out ({MAX_EXECUTION_TIME}s)!",
            "language": "unknown",
            "execution_time": time.time() - start_time,
        }
    except Exception as e:
        logger.error(f"[CODE-ENGINE] GitHub run error: {e}")
        return {
            "success": False,
            "output": f"❌ Error: {str(e)[:200]}",
            "language": "unknown",
            "execution_time": time.time() - start_time,
        }
    finally:
        try:
            import threading
            def _cleanup():
                time.sleep(300)
                shutil.rmtree(sandbox_path, ignore_errors=True)
            threading.Thread(target=_cleanup, daemon=True).start()
        except Exception:
            pass


def _detect_project_type(path: str) -> str:
    """Detect project type from files."""
    files = set(os.listdir(path))
    
    if "package.json" in files:
        return "node"
    if "requirements.txt" in files or "setup.py" in files or "pyproject.toml" in files:
        return "python"
    if "Cargo.toml" in files:
        return "rust"
    if "go.mod" in files:
        return "go"
    if "pom.xml" in files or "build.gradle" in files:
        return "java"
    if "Makefile" in files:
        return "make"
    if "Dockerfile" in files:
        return "docker"
    
    # Check for main files
    if any(f.endswith(".py") for f in files):
        return "python"
    if any(f.endswith(".js") for f in files):
        return "node"
    if any(f.endswith(".go") for f in files):
        return "go"
    
    return "unknown"


def _auto_install(path: str, project_type: str) -> str:
    """Auto-install dependencies based on project type."""
    results = []
    
    try:
        if project_type == "python":
            req = os.path.join(path, "requirements.txt")
            if os.path.exists(req):
                proc = subprocess.run(
                    f"pip3 install -q -r {req}",
                    shell=True, cwd=path,
                    capture_output=True, text=True, timeout=120,
                )
                results.append(f"pip: {'✅' if proc.returncode == 0 else '❌'}")
            
            setup = os.path.join(path, "setup.py")
            if os.path.exists(setup):
                proc = subprocess.run(
                    "pip3 install -q -e .",
                    shell=True, cwd=path,
                    capture_output=True, text=True, timeout=120,
                )
                results.append(f"setup.py: {'✅' if proc.returncode == 0 else '❌'}")
        
        elif project_type == "node":
            proc = subprocess.run(
                "npm install --quiet 2>/dev/null",
                shell=True, cwd=path,
                capture_output=True, text=True, timeout=120,
            )
            results.append(f"npm: {'✅' if proc.returncode == 0 else '❌'}")
        
        elif project_type == "go":
            proc = subprocess.run(
                "go mod download",
                shell=True, cwd=path,
                capture_output=True, text=True, timeout=60,
            )
            results.append(f"go: {'✅' if proc.returncode == 0 else '❌'}")
    
    except Exception as e:
        results.append(f"Install error: {e}")
    
    return " | ".join(results)


def _auto_detect_run_cmd(path: str, project_type: str) -> str:
    """Auto-detect the run command for a project."""
    
    # Check for common entry points
    if project_type == "python":
        for entry in ["main.py", "app.py", "run.py", "server.py", "bot.py", "manage.py", "index.py"]:
            if os.path.exists(os.path.join(path, entry)):
                return f"python3 {entry}"
        # Find any .py file with if __name__
        for f in os.listdir(path):
            if f.endswith(".py"):
                try:
                    with open(os.path.join(path, f)) as fh:
                        content = fh.read()
                    if "__name__" in content and "__main__" in content:
                        return f"python3 {f}"
                except Exception:
                    pass
    
    elif project_type == "node":
        pkg_path = os.path.join(path, "package.json")
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path) as f:
                    pkg = json.load(f)
                scripts = pkg.get("scripts", {})
                if "start" in scripts:
                    return "npm start"
                main = pkg.get("main", "")
                if main:
                    return f"node {main}"
            except Exception:
                pass
        for entry in ["index.js", "main.js", "app.js", "server.js"]:
            if os.path.exists(os.path.join(path, entry)):
                return f"node {entry}"
    
    elif project_type == "go":
        return "go run ."
    
    elif project_type == "make":
        return "make && make run 2>/dev/null || make"
    
    return ""


# ═══════════════════════════════════════════════════════════
#  QUICK CODE EXECUTION — Run raw code snippets
# ═══════════════════════════════════════════════════════════

def execute_raw_code(code: str, language: str = "python") -> Dict:
    """Execute a raw code snippet. Used when user pastes code directly."""
    config = LANG_CONFIG.get(language, LANG_CONFIG["python"])
    ext = config["ext"]
    
    sandbox_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]
    sandbox_path = os.path.join(SANDBOX_DIR, f"raw_{sandbox_id}")
    os.makedirs(sandbox_path, exist_ok=True)
    
    main_file = f"main{ext}"
    filepath = os.path.join(sandbox_path, main_file)
    
    try:
        with open(filepath, "w") as f:
            f.write(code)
        
        # Auto-install missing modules for Python
        if language == "python":
            deps = _detect_python_deps(code)
            if deps:
                subprocess.run(
                    f"pip3 install -q {' '.join(deps)}",
                    shell=True, timeout=60, capture_output=True,
                )
        
        run_cmd = config["run"].replace("{file}", main_file).replace("{dir}", sandbox_path)
        proc = subprocess.run(
            run_cmd, shell=True, cwd=sandbox_path,
            capture_output=True, text=True, timeout=MAX_EXECUTION_TIME,
        )
        
        output = proc.stdout.strip()
        errors = proc.stderr.strip()
        
        return {
            "success": proc.returncode == 0,
            "output": (output or errors or "(No output)")[:MAX_OUTPUT_SIZE],
            "language": language,
        }
    
    except subprocess.TimeoutExpired:
        return {"success": False, "output": f"⏰ Timeout ({MAX_EXECUTION_TIME}s)!"}
    except Exception as e:
        return {"success": False, "output": f"❌ Error: {e}"}
    finally:
        try:
            shutil.rmtree(sandbox_path, ignore_errors=True)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════

def _install_deps(deps: List[str], language: str, path: str) -> str:
    """Install dependencies for a specific language."""
    if not deps:
        return "No deps"
    
    try:
        if language in ("python",):
            cmd = f"pip3 install -q {' '.join(deps)}"
        elif language in ("javascript", "typescript", "node"):
            cmd = f"npm install --quiet {' '.join(deps)}"
        elif language == "go":
            cmd = f"go get {' '.join(deps)}"
        else:
            return "No installer"
        
        proc = subprocess.run(
            cmd, shell=True, cwd=path,
            capture_output=True, text=True, timeout=120,
        )
        return "✅ Deps installed" if proc.returncode == 0 else f"⚠️ Some deps failed: {proc.stderr[:100]}"
    except Exception as e:
        return f"❌ Install error: {e}"


def _detect_python_deps(code: str) -> List[str]:
    """Detect non-stdlib Python imports from code."""
    stdlib = {
        'os', 'sys', 'json', 'time', 'datetime', 'math', 'random', 're',
        'collections', 'itertools', 'functools', 'typing', 'abc', 'io',
        'pathlib', 'tempfile', 'shutil', 'subprocess', 'threading',
        'multiprocessing', 'logging', 'argparse', 'copy', 'hashlib',
        'base64', 'uuid', 'csv', 'sqlite3', 'urllib', 'html', 'xml',
        'email', 'http', 'socketserver', 'socket', 'ssl', 'select',
        'signal', 'string', 'textwrap', 'struct', 'codecs', 'unicodedata',
        'pprint', 'calendar', 'decimal', 'fractions', 'statistics',
        'enum', 'dataclasses', 'contextlib', 'ast', 'dis', 'inspect',
        'traceback', 'warnings', 'gc', 'weakref', 'array', 'heapq',
        'bisect', 'queue', 'sched', 'operator', 'pickle', 'shelve',
        'dbm', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile', 'glob',
        'fnmatch', 'stat', 'fileinput', 'filecmp', 'difflib', 'gettext',
        'locale', 'getpass', 'curses', 'platform', 'errno', 'ctypes',
        'unittest', 'doctest', 'pdb', 'profile', 'pstats', 'timeit',
        'cProfile', 'trace', 'venv', 'zipimport', 'pkgutil', 'importlib',
        'token', 'keyword', 'tokenize', 'tabnanny', 'site', 'code',
        'codeop', 'compile', 'compileall', 'py_compile', 'symtable',
    }
    
    deps = set()
    import_map = {
        'PIL': 'Pillow', 'cv2': 'opencv-python', 'sklearn': 'scikit-learn',
        'bs4': 'beautifulsoup4', 'yaml': 'pyyaml', 'dotenv': 'python-dotenv',
        'gi': 'PyGObject', 'wx': 'wxPython', 'serial': 'pyserial',
        'usb': 'pyusb', 'crypto': 'pycryptodome',
    }
    
    for line in code.split('\n'):
        line = line.strip()
        m = re.match(r'^(?:from\s+(\w+)|import\s+(\w+))', line)
        if m:
            mod = m.group(1) or m.group(2)
            if mod and mod not in stdlib:
                deps.add(import_map.get(mod, mod))
    
    return list(deps)


def extract_github_url(text: str) -> Optional[str]:
    """Extract GitHub URL from text."""
    m = re.search(r'https?://github\.com/[^\s)]+', text)
    return m.group(0) if m else None


def detect_code_request(text: str) -> str:
    """Detect if text is a code execution request.
    Returns: 'generate' | 'github' | 'raw_code' | 'none'
    """
    lower = text.lower().strip()
    
    # GitHub URL detection
    if re.search(r'https?://github\.com/', text):
        return 'github'
    
    # Raw code detection (user pasted code)
    code_indicators = [
        r'^\s*(import |from |def |class |#!|print\(|console\.log|function |const |let |var )',
        r'^\s*\{[\s\S]*\}\s*$',
    ]
    lines = text.split('\n')
    if len(lines) >= 2 and any(re.match(p, lines[0]) for p in code_indicators):
        return 'raw_code'
    
    # Also detect if it looks like a code block (indented, has keywords)
    code_keywords = ['import ', 'from ', 'def ', 'class ', 'print(', 'console.log', 'function ', 'return ']
    if len(lines) >= 2 and sum(1 for l in lines if any(kw in l for kw in code_keywords)) >= 2:
        return 'raw_code'
    
    # Code generation request — NUCLEAR: expanded Hindi + English triggers
    gen_triggers = [
        r'\b(code|program|script|app|project|bot|website|api|server|tool|game|calculator|converter)\s*(banao|bana\s*do|likho|likh\s*do|generate|create|make|build|write|develop)\b',
        r'\b(banao|bana\s*do|likho|likh\s*do)\s*(ek|mera|mujhe|koi)?\s*(code|program|script|app|project|bot|website|api|tool|game|calculator)\b',
        r'\b(generate|create|build|make|write|develop|code)\s*(a|an|the|me|mujhe)?\s*(code|program|script|app|project|bot|api|website|server|tool|game|calculator|converter|scraper|crawler)\b',
        r'\b(run|execute|chala|chalao|start|launch)\s*(this|ye|yeh|isko|code|program|script|karke)\b',
        r'\b(code|program|script|coding)\s*(karo|kar\s*do|chahiye|de\s*do|dedo|dikhao)\b',
        r'\b(github|repo|repository)\s*(se|from)?\s*(run|clone|download|chala|lekar)\b',
        r'\b(github|repo)\s*(se|ka)?\s*(code|project)\s*(run|chala|lekar|download)\b',
        r'\b(python|javascript|java|golang|rust|c\+\+)\s*(code|program|script|mein)\s*(banao|likho|karo)\b',
        r'\b(ek|mujhe|mera)\s*(python|javascript|java)?\s*(code|program|script|app)\s*(chahiye|do|dedo|banao|banana\s*hai)\b',
        r'\b(jarvis|tum|tu)\s*(code|coding|program)\s*(karo|kar\s*do|banao|likho)\b',
        r'\b(khud|apne\s*aap|autonomous)\s*(code|coding|program)\s*(karo|kar\s*do|banao|likho)\b',
        r'\b(code|coding)\s*(kar\s*ke|karke)\s*(dikha|batao|run|output|result)\b',
    ]
    
    for pattern in gen_triggers:
        if re.search(pattern, lower):
            return 'generate'
    
    return 'none'


# ═══════════════════════════════════════════════════════════
#  FORMAT OUTPUT FOR TELEGRAM
# ═══════════════════════════════════════════════════════════

def format_execution_result(result: Dict, prompt: str = "") -> str:
    """Format execution result beautifully for Telegram."""
    success = result.get("success", False)
    output = result.get("output", "")
    desc = result.get("description", "")
    lang = result.get("language", "unknown")
    exec_time = result.get("execution_time", 0)
    files_count = result.get("files_count", 0)
    auto_fixed = result.get("auto_fixed", False)
    
    status = "✅ SUCCESS" if success else "❌ FAILED"
    
    msg = (
        f"⚡ *JARVIS CODE ENGINE — {status}*\n"
        f"╔══════════════════════════════╗\n"
    )
    
    if prompt:
        msg += f"║ 📝 *Request:* _{prompt[:60]}{'...' if len(prompt) > 60 else ''}_\n"
    
    msg += (
        f"║ 🔤 *Language:* {lang.title()}\n"
        f"║ 📄 *Files:* {files_count}\n"
        f"║ ⏱️ *Time:* {exec_time:.1f}s\n"
    )
    
    if auto_fixed:
        msg += f"║ 🔧 *Auto-Fixed:* Yes (AI ne error fix kiya!)\n"
    
    msg += (
        f"╚══════════════════════════════╝\n\n"
        f"📤 *OUTPUT:*\n"
        f"```\n{output[:3500]}\n```"
    )
    
    if len(output) > 3500:
        msg += "\n_(Output truncated)_"
    
    if desc:
        msg += f"\n\n💡 _{desc[:200]}_"
    
    return msg


def format_github_result(result: Dict, url: str = "") -> str:
    """Format GitHub clone+run result for Telegram."""
    success = result.get("success", False)
    output = result.get("output", "")
    lang = result.get("language", "unknown")
    exec_time = result.get("execution_time", 0)
    
    status = "✅ SUCCESS" if success else "❌ FAILED"
    
    msg = (
        f"🐙 *JARVIS GITHUB RUNNER — {status}*\n"
        f"╔══════════════════════════════╗\n"
        f"║ 🔗 *Repo:* _{url[:50] if url else 'GitHub Repo'}_\n"
        f"║ 🔧 *Type:* {lang.title()}\n"
        f"║ ⏱️ *Time:* {exec_time:.1f}s\n"
        f"╚══════════════════════════════╝\n\n"
        f"📤 *OUTPUT:*\n"
        f"```\n{output[:3500]}\n```"
    )
    
    return msg


# ═══════════════════════════════════════════════════════════
#  MODULE STATUS
# ═══════════════════════════════════════════════════════════

CODE_ENGINE_AVAILABLE = True
logger.info("[CODE-ENGINE] ⚡ JARVIS Code Engine loaded — Autonomous Generate + Execute + GitHub Clone & Run")
