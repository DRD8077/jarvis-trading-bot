"""
💻 JARVIS CODER — AI Programming Engine (Claude Opus 4 Powered)
═══════════════════════════════════════════════════════════════
JARVIS can write code, create files, install dependencies, push to GitHub.
When user says "program for me" / "code banao" / "app bana do" —
JARVIS asks what to build, writes production-grade code, tests it.

Powered by Claude Opus 4 (claude-opus-4-20250514) — the world's most
intelligent AI for code generation.

Author: David Crew AI (Boss: Deepak Kumar)
"""

import os
import json
import time
import logging
import subprocess
import tempfile
import requests
from typing import Optional, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger("jarvis_coder")

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("CLAUDE_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID", "5647898018"))

# Projects directory
PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "jarvis_projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Active coding sessions per user
_coding_sessions: Dict[int, dict] = {}


# ═══════════════════════════════════════════════════════════
#  CLAUDE OPUS 4 — Code Generation Engine
# ═══════════════════════════════════════════════════════════

CODER_SYSTEM_PROMPT = """You are JARVIS CODER — the world's most powerful AI programming assistant, 
built by David Crew for Boss Deepak Kumar.

You are powered by Claude Opus 4 — the most intelligent AI model in the world.

YOUR CAPABILITIES:
- Write production-grade code in ANY programming language
- Create complete project structures with all files  
- Write clean, documented, error-handled, tested code
- Design databases, APIs, UIs, mobile apps, smart contracts
- Debug ANY code and explain bugs clearly
- Optimize performance and security
- Create Docker/CI-CD configurations

RULES:
1. ALWAYS return code in proper JSON format with files array
2. Each file must have: "path" (relative), "content" (full code), "language" 
3. Include a "setup" field with commands to install dependencies
4. Include a "run" field with command to run the project
5. Code must be COMPLETE — no placeholders, no "TODO", no "..."
6. Add proper error handling, logging, comments
7. Use modern best practices for each language
8. Include a README.md with setup instructions
9. If asked in Hindi, explain in Hindi but write code in English
10. GENERATE the FULL implementation — user should be able to run it immediately

RESPONSE FORMAT (JSON):
{
    "project_name": "my_project",
    "description": "What this project does",
    "language": "python",
    "files": [
        {"path": "main.py", "content": "...", "language": "python"},
        {"path": "requirements.txt", "content": "...", "language": "text"},
        {"path": "README.md", "content": "...", "language": "markdown"}
    ],
    "setup": ["pip install -r requirements.txt"],
    "run": "python main.py",
    "explanation": "Hindi/English explanation of what was built"
}
"""


def generate_code(prompt: str, chat_id: int = 0, language: str = "auto") -> Dict:
    """Generate code using FREE AI providers (Groq → Gemini).
    
    Returns dict with: project_name, files[], setup[], run, explanation
    """
    # 100% FREE — always use Groq/Gemini (no paid Claude needed)
    return _fallback_code_gen(prompt, chat_id)
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        user_msg = f"""Generate a complete project for this request:

REQUEST: {prompt}

PREFERRED LANGUAGE: {language if language != 'auto' else 'Detect best language from request'}

Return ONLY a valid JSON object with the format specified in your instructions.
Make sure ALL code is complete and runnable. Include ALL necessary files."""

        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=16000,
            system=CODER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
            temperature=0.3,
        )
        
        if response.content and len(response.content) > 0:
            text = response.content[0].text
            # Extract JSON from response
            return _parse_code_response(text)
        
        return {"error": "No response from Claude"}
        
    except ImportError:
        logger.error("[CODER] anthropic package not installed")
        return _fallback_code_gen(prompt, chat_id)
    except Exception as e:
        logger.error(f"[CODER] Claude error: {e}")
        return _fallback_code_gen(prompt, chat_id)


def _fallback_code_gen(prompt: str, chat_id: int) -> Dict:
    """Fallback code generation using Groq → Gemini if Claude unavailable."""
    
    # ── Try Groq (fast, good for coding) ──
    try:
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            from groq import Groq
            client = Groq(api_key=groq_key, timeout=60.0)
            
            # Simplified prompt for Groq — better JSON compliance
            simplified_prompt = (
                f"Generate a complete project for this request:\n\n"
                f"REQUEST: {prompt}\n\n"
                f"Return ONLY a valid JSON object with this EXACT structure:\n"
                f'{{"project_name": "name", "description": "desc", "language": "python", '
                f'"files": [{{"path": "main.py", "content": "full code here", "language": "python"}}, '
                f'{{"path": "requirements.txt", "content": "deps", "language": "text"}}], '
                f'"setup": ["pip install -r requirements.txt"], '
                f'"run": "python main.py", '
                f'"explanation": "What this does"}}\n\n'
                f"IMPORTANT: Return ONLY the JSON. No markdown, no code blocks, no extra text."
            )
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": CODER_SYSTEM_PROMPT},
                    {"role": "user", "content": simplified_prompt}
                ],
                max_tokens=8000,
                temperature=0.2,
            )
            text = response.choices[0].message.content
            result = _parse_code_response(text)
            if "error" not in result:
                return result
            logger.warning(f"[CODER] Groq JSON parse failed, trying raw extraction")
    except Exception as e:
        logger.error(f"[CODER] Groq fallback error: {e}")
    
    # ── Try Gemini (free, good at coding) ──
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        if gemini_key:
            from google import genai
            gclient = genai.Client(api_key=gemini_key)
            
            gen_prompt = (
                f"{CODER_SYSTEM_PROMPT}\n\n"
                f"Generate a complete project for: {prompt}\n\n"
                f"Return ONLY valid JSON with files array. No markdown."
            )
            
            resp = gclient.models.generate_content(
                model="gemini-2.5-flash",
                contents=gen_prompt,
            )
            if resp.text:
                result = _parse_code_response(resp.text)
                if "error" not in result:
                    return result
    except Exception as e:
        logger.error(f"[CODER] Gemini fallback error: {e}")
    
    return {"error": "AI code generation failed. Please try a simpler request."}


def _parse_code_response(text: str) -> Dict:
    """Parse JSON code response from AI — robust extraction."""
    if not text:
        return {"error": "Empty response"}
    
    # Remove markdown code blocks if present
    import re
    text = re.sub(r'^```(?:json)?\s*\n?', '', text.strip(), flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text.strip(), flags=re.MULTILINE)
    
    try:
        # Try direct JSON parse
        result = json.loads(text.strip())
        if "files" in result:
            return result
    except json.JSONDecodeError:
        pass
    
    try:
        # Find JSON in response (between first { and last })
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = text[start:end]
            result = json.loads(json_str)
            if "files" in result:
                return result
    except json.JSONDecodeError:
        pass
    
    # Try to extract code blocks and create a project from them
    code_blocks = re.findall(r'```(\w+)?\n(.*?)```', text, re.DOTALL)
    if code_blocks:
        files = []
        for i, (lang, code) in enumerate(code_blocks):
            lang = lang or "python"
            ext = {"python": ".py", "javascript": ".js", "typescript": ".ts", 
                   "html": ".html", "css": ".css", "java": ".java",
                   "go": ".go", "rust": ".rs", "c": ".c", "cpp": ".cpp"}.get(lang, ".txt")
            path = f"main{ext}" if i == 0 else f"file_{i}{ext}"
            files.append({"path": path, "content": code.strip(), "language": lang})
        
        if files:
            return {
                "project_name": "jarvis_project",
                "description": "Generated code",
                "language": files[0].get("language", "python"),
                "files": files,
                "setup": [],
                "run": f"python main.py" if files[0].get("language") == "python" else "",
                "explanation": "Code extracted from AI response"
            }
    
    # If JSON parsing fails, wrap raw code
    return {
        "project_name": "jarvis_project",
        "description": "Generated code",
        "language": "python",
        "files": [
            {"path": "main.py", "content": text, "language": "python"}
        ],
        "setup": [],
        "run": "python main.py",
        "explanation": "Code generated (raw output — may need manual file separation)"
    }


def save_project(project: Dict, chat_id: int) -> str:
    """Save generated project files to disk.
    Returns the project directory path."""
    name = project.get("project_name", f"project_{int(time.time())}")
    name = "".join(c if c.isalnum() or c in "_-" else "_" for c in name)
    
    project_dir = os.path.join(PROJECTS_DIR, f"{chat_id}_{name}")
    os.makedirs(project_dir, exist_ok=True)
    
    files_created = []
    for f in project.get("files", []):
        path = f.get("path", "file.txt")
        content = f.get("content", "")
        
        # Create subdirectories if needed
        full_path = os.path.join(project_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w") as fh:
            fh.write(content)
        files_created.append(path)
    
    logger.info(f"[CODER] Saved {len(files_created)} files to {project_dir}")
    return project_dir


def install_dependencies(project: Dict, project_dir: str) -> Tuple[bool, str]:
    """Install project dependencies."""
    setup_cmds = project.get("setup", [])
    if not setup_cmds:
        return True, "No dependencies to install"
    
    results = []
    for cmd in setup_cmds:
        try:
            # Safety: only allow pip/npm/yarn/cargo
            allowed = ["pip ", "pip3 ", "npm ", "yarn ", "cargo ", "go mod"]
            if not any(cmd.strip().startswith(a) for a in allowed):
                results.append(f"⚠️ Skipped unsafe command: {cmd}")
                continue
            
            proc = subprocess.run(
                cmd, shell=True, cwd=project_dir,
                capture_output=True, text=True, timeout=120
            )
            if proc.returncode == 0:
                results.append(f"✅ {cmd}")
            else:
                results.append(f"❌ {cmd}: {proc.stderr[:100]}")
        except subprocess.TimeoutExpired:
            results.append(f"⏰ {cmd}: timed out")
        except Exception as e:
            results.append(f"❌ {cmd}: {e}")
    
    all_ok = all("✅" in r for r in results)
    return all_ok, "\n".join(results)


def push_to_github(project_dir: str, repo_name: str, description: str = "") -> Tuple[bool, str]:
    """Push project to GitHub using gh CLI."""
    try:
        # Check if gh is available
        proc = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            return False, "GitHub CLI not authenticated"
        
        # Init git repo
        cmds = [
            "git init",
            "git add .",
            'git commit -m "🚀 Initial commit by JARVIS AI Coder"',
        ]
        
        for cmd in cmds:
            subprocess.run(cmd, shell=True, cwd=project_dir, capture_output=True, timeout=30)
        
        # Create repo
        create_cmd = f'gh repo create {repo_name} --public --source=. --push'
        if description:
            create_cmd += f' --description "{description[:200]}"'
        
        proc = subprocess.run(
            create_cmd, shell=True, cwd=project_dir,
            capture_output=True, text=True, timeout=60
        )
        
        if proc.returncode == 0:
            # Extract repo URL
            url = f"https://github.com/DRD8077/{repo_name}"
            return True, url
        else:
            return False, f"GitHub push failed: {proc.stderr[:200]}"
    
    except Exception as e:
        return False, f"GitHub error: {e}"


def format_code_result(project: Dict, project_dir: str = "") -> str:
    """Format code generation result for Telegram."""
    if "error" in project:
        return f"❌ *Code Generation Failed*\n{project['error']}"
    
    name = project.get("project_name", "project")
    desc = project.get("description", "")
    lang = project.get("language", "?")
    files = project.get("files", [])
    explanation = project.get("explanation", "")
    run_cmd = project.get("run", "")
    
    msg = (
        f"💻 *JARVIS CODER — Project Ready!* 🚀\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 *Project:* {name}\n"
        f"💬 *Description:* {desc}\n"
        f"🔤 *Language:* {lang}\n"
        f"📄 *Files:* {len(files)}\n"
    )
    
    for f in files[:10]:
        path = f.get("path", "file")
        lines = f.get("content", "").count("\n") + 1
        msg += f"  📝 `{path}` ({lines} lines)\n"
    
    if len(files) > 10:
        msg += f"  ... +{len(files) - 10} more files\n"
    
    if run_cmd:
        msg += f"\n▶️ *Run:* `{run_cmd}`\n"
    
    if project_dir:
        msg += f"📂 *Saved at:* `{project_dir}`\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if explanation:
        msg += f"\n💡 *Explanation:*\n{explanation[:800]}\n"
    
    # Show first file's code (truncated)
    if files:
        first = files[0]
        code = first.get("content", "")[:1500]
        msg += f"\n📝 *{first['path']}:*\n```{first.get('language', '')}\n{code}\n```"
        if len(first.get("content", "")) > 1500:
            msg += "\n_(truncated — full code saved to disk)_"
    
    msg += f"\n\n🔧 *Commands:*\n"
    msg += "• `/code_github` — Push to GitHub\n"
    msg += "• `/code_install` — Install dependencies\n"
    msg += "• `/code_run` — Run the project\n"
    msg += "• `/code_show <file>` — Show full file\n"
    
    return msg


# ═══════════════════════════════════════════════════════════
#  CODING SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════

def start_coding_session(chat_id: int) -> str:
    """Start an interactive coding session."""
    _coding_sessions[chat_id] = {
        "state": "awaiting_prompt",
        "started": datetime.now().isoformat(),
        "project": None,
        "project_dir": None,
    }
    return (
        "💻🌸 *JARVIS CODER Activated!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Powered by *JARVIS FREE AI* 🧠⚡\n\n"
        "बताइए, *क्या बनाना है?* 🌸\n\n"
        "Examples:\n"
        "• _\"Python Flask API with user auth\"_\n"
        "• _\"React dashboard for stock market\"_\n"
        "• _\"Solana smart contract for token swap\"_\n"
        "• _\"Telegram bot jo weather bataye\"_\n"
        "• _\"Mobile app Flutter mein crypto tracker\"_\n"
        "• _\"Machine learning model for price prediction\"_\n\n"
        "💡 कोई भी language, कोई भी framework — \n"
        "बस बोलिए, main बना दूँगी! 🚀"
    )


def is_in_coding_session(chat_id: int) -> bool:
    """Check if user is in an active coding session."""
    return chat_id in _coding_sessions


def get_session(chat_id: int) -> Optional[dict]:
    """Get active coding session."""
    return _coding_sessions.get(chat_id)


def end_coding_session(chat_id: int):
    """End coding session."""
    _coding_sessions.pop(chat_id, None)


def process_coding_input(chat_id: int, text: str) -> Dict:
    """Process user input in coding session.
    
    Returns: {"message": str, "done": bool, "project": optional dict}
    """
    session = _coding_sessions.get(chat_id)
    if not session:
        return {"message": "No active coding session.", "done": True}
    
    state = session.get("state", "awaiting_prompt")
    
    if state == "awaiting_prompt":
        # User gave the coding prompt — generate code
        session["state"] = "generating"
        session["prompt"] = text
        
        # Generate code
        project = generate_code(text, chat_id)
        
        if "error" in project:
            return {
                "message": f"❌ Code generation failed: {project['error']}\n\nPlease try again with a different prompt.",
                "done": False,
                "project": None
            }
        
        # Save to disk
        project_dir = save_project(project, chat_id)
        session["project"] = project
        session["project_dir"] = project_dir
        session["state"] = "code_ready"
        
        msg = format_code_result(project, project_dir)
        msg += "\n\n*Kya karun?*\n"
        msg += "• Type `install` — Dependencies install karein\n"
        msg += "• Type `github` — GitHub par push karein\n"
        msg += "• Type `run` — Project run karein\n"
        msg += "• Type `done` — Session close karein\n"
        msg += "• Type `new` — Naya project banayein\n"
        
        return {"message": msg, "done": False, "project": project}
    
    elif state == "code_ready":
        cmd = text.lower().strip()
        project = session.get("project", {})
        project_dir = session.get("project_dir", "")
        
        if cmd in ("install", "dependencies", "deps"):
            ok, result = install_dependencies(project, project_dir)
            emoji = "✅" if ok else "⚠️"
            return {"message": f"{emoji} *Dependencies:*\n{result}", "done": False}
        
        elif cmd in ("github", "push", "git"):
            repo_name = project.get("project_name", f"jarvis-project-{int(time.time())}")
            desc = project.get("description", "Generated by JARVIS AI Coder")
            ok, result = push_to_github(project_dir, repo_name, desc)
            if ok:
                return {"message": f"✅ *GitHub Push Successful!*\n🔗 {result}", "done": False}
            else:
                return {"message": f"❌ GitHub push failed: {result}", "done": False}
        
        elif cmd in ("run", "execute", "chala"):
            run_cmd = project.get("run", "")
            if not run_cmd:
                return {"message": "⚠️ No run command defined for this project.", "done": False}
            try:
                proc = subprocess.run(
                    run_cmd, shell=True, cwd=project_dir,
                    capture_output=True, text=True, timeout=30
                )
                output = proc.stdout[:2000] or proc.stderr[:2000] or "(no output)"
                status = "✅" if proc.returncode == 0 else "❌"
                return {"message": f"{status} *Output:*\n```\n{output}\n```", "done": False}
            except subprocess.TimeoutExpired:
                return {"message": "⏰ Command timed out (30s limit)", "done": False}
            except Exception as e:
                return {"message": f"❌ Run error: {e}", "done": False}
        
        elif cmd in ("done", "exit", "close", "band"):
            end_coding_session(chat_id)
            return {"message": "✅ Coding session closed! 🌸", "done": True}
        
        elif cmd in ("new", "naya", "another"):
            session["state"] = "awaiting_prompt"
            session["project"] = None
            return {"message": "💻 Batao, ab *kya banana hai?* 🚀", "done": False}
        
        elif cmd.startswith("show "):
            filename = cmd.replace("show ", "").strip()
            for f in project.get("files", []):
                if f["path"] == filename or f["path"].endswith(filename):
                    code = f["content"][:3500]
                    return {"message": f"📝 *{f['path']}:*\n```{f.get('language','')}\n{code}\n```", "done": False}
            return {"message": f"❌ File `{filename}` not found in project.", "done": False}
        
        else:
            # Treat as a modification request
            return _modify_code(session, text, chat_id)
    
    return {"message": "💻 Type your coding request:", "done": False}


def _modify_code(session: dict, modification: str, chat_id: int) -> Dict:
    """Modify existing code based on user request."""
    project = session.get("project", {})
    if not project:
        return {"message": "No project to modify. Type `new` to start.", "done": False}
    
    # Use Claude to modify
    current_files = ""
    for f in project.get("files", [])[:5]:
        current_files += f"\n--- {f['path']} ---\n{f['content'][:2000]}\n"
    
    prompt = f"""CURRENT PROJECT:
{current_files}

MODIFICATION REQUEST: {modification}

Generate the UPDATED project with the modifications applied.
Return ONLY valid JSON in the same format as before."""
    
    new_project = generate_code(prompt, chat_id)
    if "error" not in new_project:
        project_dir = save_project(new_project, chat_id)
        session["project"] = new_project
        session["project_dir"] = project_dir
        session["state"] = "code_ready"
        
        msg = format_code_result(new_project, project_dir)
        msg += "\n✅ *Code updated as requested!*"
        return {"message": msg, "done": False, "project": new_project}
    
    return {"message": f"❌ Modification failed: {new_project.get('error', 'Unknown error')}", "done": False}


# ═══════════════════════════════════════════════════════════
#  MODULE STATUS
# ═══════════════════════════════════════════════════════════

CODER_AVAILABLE = True
CLAUDE_CONNECTED = False  # Removed — 100% FREE AI only (Groq/Gemini)
GITHUB_CONNECTED = bool(GITHUB_TOKEN) or os.path.exists(os.path.expanduser("~/.config/gh/hosts.yml"))

logger.info(
    f"[CODER] 💻 JARVIS Coder loaded: AI=Groq+Gemini(FREE) "
    f"GitHub={'✅' if GITHUB_CONNECTED else '❌'}"
)
