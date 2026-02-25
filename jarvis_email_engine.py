"""
JARVIS Email Engine — Send, read, compose emails via SMTP/IMAP or Gmail API
"""
import os, json, logging, asyncio, aiohttp, smtplib, email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("jarvis.email")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
GMAIL_API_KEY = os.getenv("GMAIL_API_KEY", "")

DRAFTS_FILE = Path("jarvis_email_drafts.json")

def _load_drafts() -> list:
    if DRAFTS_FILE.exists():
        return json.loads(DRAFTS_FILE.read_text())
    return []

def _save_drafts(drafts: list):
    DRAFTS_FILE.write_text(json.dumps(drafts, indent=2, default=str))

async def send_email(to: str, subject: str, body: str, html: bool = False) -> dict:
    """Send an email via SMTP."""
    if not SMTP_USER or not SMTP_PASS:
        # Save as draft
        draft = {
            "id": f"draft_{int(datetime.now().timestamp())}",
            "to": to, "subject": subject, "body": body,
            "created": datetime.now().isoformat(), "status": "draft"
        }
        drafts = _load_drafts()
        drafts.append(draft)
        _save_drafts(drafts)
        return {
            "status": "draft_saved",
            "draft_id": draft["id"],
            "to": to, "subject": subject,
            "note": "Email saved as draft. Configure SMTP_USER and SMTP_PASS in .env to send.",
            "setup": {
                "gmail": "Use App Password: Google Account > Security > 2FA > App Passwords",
                "env": "SMTP_USER=your@gmail.com, SMTP_PASS=your_app_password"
            }
        }
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to
        
        if html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_smtp, msg)
        
        return {
            "status": "sent",
            "to": to, "subject": subject,
            "ts": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {"status": "error", "error": str(e)}

def _send_smtp(msg):
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

async def compose_professional_email(to: str, purpose: str, tone: str = "professional") -> dict:
    """AI-compose a professional email based on purpose."""
    templates = {
        "follow_up": {
            "subject": "Following Up — {purpose}",
            "body": """Dear Sir/Madam,

I hope this email finds you well. I am writing to follow up on our previous conversation regarding {purpose}.

I would appreciate the opportunity to discuss this further at your convenience.

Looking forward to hearing from you.

Best regards,
JARVIS AI Assistant"""
        },
        "introduction": {
            "subject": "Introduction — {purpose}",
            "body": """Dear Sir/Madam,

I hope this message finds you well. I am reaching out to introduce myself regarding {purpose}.

I believe there is great potential for collaboration, and I would love to discuss this further.

Please let me know a convenient time to connect.

Warm regards,
JARVIS AI Assistant"""
        },
        "thank_you": {
            "subject": "Thank You — {purpose}",
            "body": """Dear Sir/Madam,

Thank you so much for {purpose}. I really appreciate your time and effort.

Looking forward to continuing our association.

With gratitude,
JARVIS AI Assistant"""
        },
        "meeting": {
            "subject": "Meeting Request — {purpose}",
            "body": """Dear Sir/Madam,

I would like to request a meeting to discuss {purpose}.

Could you please share your availability for the upcoming week? I am flexible with timing.

Thank you for your consideration.

Best regards,
JARVIS AI Assistant"""
        }
    }
    
    # Auto-detect template
    purpose_lower = purpose.lower()
    template_key = "follow_up"
    if any(w in purpose_lower for w in ["introduce", "intro", "new"]):
        template_key = "introduction"
    elif any(w in purpose_lower for w in ["thank", "thanks", "grateful"]):
        template_key = "thank_you"
    elif any(w in purpose_lower for w in ["meet", "call", "schedule"]):
        template_key = "meeting"
    
    template = templates[template_key]
    return {
        "to": to,
        "subject": template["subject"].format(purpose=purpose),
        "body": template["body"].format(purpose=purpose),
        "tone": tone,
        "template_used": template_key,
        "ready_to_send": bool(SMTP_USER),
        "action": "Review and call /send-email to send"
    }

async def send_bulk_email(recipients: list, subject: str, body: str) -> dict:
    """Send email to multiple recipients."""
    results = []
    for to in recipients:
        r = await send_email(to, subject, body)
        results.append(r)
    sent = len([r for r in results if r.get("status") == "sent"])
    return {"sent": sent, "total": len(recipients), "results": results}

def get_drafts() -> list:
    """Get all saved email drafts."""
    return _load_drafts()

def delete_draft(draft_id: str) -> bool:
    """Delete an email draft."""
    drafts = _load_drafts()
    drafts = [d for d in drafts if d.get("id") != draft_id]
    _save_drafts(drafts)
    return True

def get_engine_status() -> dict:
    return {
        "engine": "email",
        "status": "online",
        "smtp_configured": bool(SMTP_USER and SMTP_PASS),
        "smtp_host": SMTP_HOST,
        "drafts_count": len(_load_drafts()),
        "features": ["send", "compose_ai", "bulk_send", "drafts", "templates"]
    }

logger.info("📧 Email engine loaded")
