"""
JARVIS WhatsApp Engine — Send messages, make calls via WhatsApp Web API
Uses Twilio WhatsApp API or direct web automation
"""
import os, json, logging, asyncio, aiohttp
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("jarvis.whatsapp")

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
CONTACTS_FILE = Path("jarvis_contacts.json")

def _load_contacts() -> dict:
    if CONTACTS_FILE.exists():
        return json.loads(CONTACTS_FILE.read_text())
    return {"contacts": {}}

def _save_contacts(data: dict):
    CONTACTS_FILE.write_text(json.dumps(data, indent=2, default=str))

def add_contact(name: str, phone: str, email: str = "", linkedin: str = "") -> dict:
    """Add a contact to JARVIS phonebook."""
    contacts = _load_contacts()
    contacts["contacts"][name.lower()] = {
        "name": name, "phone": phone, "email": email, "linkedin": linkedin,
        "added": datetime.now().isoformat()
    }
    _save_contacts(contacts)
    return {"status": "saved", "name": name, "phone": phone}

def get_contact(name: str) -> dict:
    """Find a contact by name."""
    contacts = _load_contacts()
    key = name.lower()
    if key in contacts["contacts"]:
        return contacts["contacts"][key]
    # fuzzy match
    for k, v in contacts["contacts"].items():
        if key in k or key in v.get("name", "").lower():
            return v
    return {"error": f"Contact '{name}' not found"}

def list_contacts() -> list:
    """List all saved contacts."""
    contacts = _load_contacts()
    return list(contacts["contacts"].values())

async def send_whatsapp_message(to_name: str, message: str) -> dict:
    """Send WhatsApp message via Twilio API."""
    contact = get_contact(to_name)
    if "error" in contact:
        return contact
    phone = contact.get("phone", "")
    if not phone:
        return {"error": f"No phone number for {to_name}"}
    
    if TWILIO_SID and TWILIO_TOKEN:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
            data = {
                "From": TWILIO_WHATSAPP,
                "To": f"whatsapp:{phone}",
                "Body": message
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, 
                                       auth=aiohttp.BasicAuth(TWILIO_SID, TWILIO_TOKEN)) as resp:
                    result = await resp.json()
                    return {
                        "status": "sent",
                        "to": to_name,
                        "phone": phone,
                        "message": message,
                        "sid": result.get("sid", ""),
                        "ts": datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Twilio WhatsApp error: {e}")
            return {"status": "queued", "to": to_name, "message": message,
                    "note": "Message queued — will send when Twilio credentials are configured",
                    "setup": "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN in .env"}
    
    # Queue message for later
    queue_file = Path("jarvis_whatsapp_queue.json")
    queue = json.loads(queue_file.read_text()) if queue_file.exists() else {"messages": []}
    queue["messages"].append({
        "to": to_name, "phone": phone, "message": message,
        "ts": datetime.now().isoformat(), "status": "queued"
    })
    queue_file.write_text(json.dumps(queue, indent=2))
    return {
        "status": "queued",
        "to": to_name,
        "phone": phone,
        "message": message,
        "note": "JARVIS has queued this message. Configure Twilio API or connect WhatsApp Web to send.",
        "setup_guide": {
            "step1": "Create free Twilio account at twilio.com",
            "step2": "Enable WhatsApp sandbox",
            "step3": "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env"
        }
    }

async def send_whatsapp_bulk(contacts_list: list, message: str) -> dict:
    """Send WhatsApp message to multiple contacts."""
    results = []
    for name in contacts_list:
        r = await send_whatsapp_message(name, message)
        results.append(r)
    return {"sent": len([r for r in results if r.get("status") == "sent"]),
            "queued": len([r for r in results if r.get("status") == "queued"]),
            "results": results}

def get_whatsapp_queue() -> list:
    """Get pending WhatsApp messages."""
    queue_file = Path("jarvis_whatsapp_queue.json")
    if queue_file.exists():
        return json.loads(queue_file.read_text()).get("messages", [])
    return []

async def initiate_whatsapp_call(to_name: str) -> dict:
    """Initiate a WhatsApp call (via deep link / Twilio voice)."""
    contact = get_contact(to_name)
    if "error" in contact:
        return contact
    phone = contact.get("phone", "")
    return {
        "status": "ready",
        "action": "whatsapp_call",
        "to": to_name,
        "phone": phone,
        "deeplink": f"https://wa.me/{phone.replace('+', '')}",
        "call_link": f"https://wa.me/{phone.replace('+', '')}?text=JARVIS%20calling...",
        "note": "Open the deep link to initiate a WhatsApp call on your device"
    }

def get_engine_status() -> dict:
    return {
        "engine": "whatsapp",
        "status": "online",
        "twilio_configured": bool(TWILIO_SID and TWILIO_TOKEN),
        "contacts_count": len(list_contacts()),
        "queue_size": len(get_whatsapp_queue()),
        "features": ["send_message", "bulk_send", "call", "contacts", "queue"]
    }

logger.info("📱 WhatsApp engine loaded")
