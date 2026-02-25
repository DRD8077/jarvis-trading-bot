"""
JARVIS LinkedIn Engine — Profile management, messaging, job search, post creation
Uses LinkedIn API or web automation patterns
"""
import os, json, logging, asyncio, aiohttp
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("jarvis.linkedin")

LINKEDIN_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PROFILE_FILE = Path("jarvis_linkedin_profile.json")
POSTS_FILE = Path("jarvis_linkedin_posts.json")

def _load_profile() -> dict:
    if LINKEDIN_PROFILE_FILE.exists():
        return json.loads(LINKEDIN_PROFILE_FILE.read_text())
    return {}

def _save_profile(data: dict):
    LINKEDIN_PROFILE_FILE.write_text(json.dumps(data, indent=2, default=str))

def save_linkedin_profile(name: str, headline: str, about: str, 
                          experience: list = None, skills: list = None) -> dict:
    """Save LinkedIn profile data for JARVIS to manage."""
    profile = {
        "name": name, "headline": headline, "about": about,
        "experience": experience or [], "skills": skills or [],
        "updated": datetime.now().isoformat()
    }
    _save_profile(profile)
    return {"status": "saved", "profile": profile}

def get_linkedin_profile() -> dict:
    """Get saved LinkedIn profile."""
    return _load_profile() or {"note": "No profile saved. Use save_linkedin_profile to add your data."}

async def generate_linkedin_post(topic: str, tone: str = "professional", 
                                  include_hashtags: bool = True) -> dict:
    """Generate a LinkedIn post on any topic."""
    post_templates = {
        "professional": f"""🚀 {topic}

In today's rapidly evolving landscape, staying ahead means embracing change and innovation.

Here are my key insights:

1️⃣ Continuous learning is non-negotiable
2️⃣ Building genuine connections matters more than ever
3️⃣ Execution beats perfection every time

What are your thoughts on {topic}? I'd love to hear your perspective in the comments below.

#Leadership #Innovation #Growth #Professional""",
        
        "motivational": f"""💪 {topic}

Every setback is a setup for a comeback. The journey to success is never linear — it's the persistence that matters.

Remember:
✨ Your potential is unlimited
✨ Small steps lead to big results  
✨ Consistency beats talent when talent doesn't work hard

Let's connect and grow together! 🌟

#Motivation #Success #Mindset #NeverGiveUp""",
        
        "tech": f"""🔥 {topic}

The tech landscape is moving at lightning speed. Here's what I think everyone should know:

💡 AI is transforming every industry
💡 Data-driven decisions are the new normal
💡 The future belongs to those who adapt

What's your take? Drop your thoughts below 👇

#Technology #AI #Innovation #TechTrends #FutureOfWork""",
        
        "career": f"""📈 {topic}

Career growth isn't just about climbing the ladder — it's about creating value at every step.

My advice:
🎯 Focus on impact, not just activity
🎯 Build your personal brand consistently
🎯 Network with intent and authenticity

Share your career journey below — let's inspire each other! 💼

#CareerGrowth #Networking #PersonalBrand #JobSearch"""
    }
    
    tone_key = "professional"
    topic_lower = topic.lower()
    if any(w in topic_lower for w in ["motivat", "inspire", "success"]):
        tone_key = "motivational"
    elif any(w in topic_lower for w in ["tech", "ai", "code", "software", "data"]):
        tone_key = "tech"
    elif any(w in topic_lower for w in ["career", "job", "work", "hire"]):
        tone_key = "career"
    if tone.lower() in post_templates:
        tone_key = tone.lower()
    
    post = post_templates.get(tone_key, post_templates["professional"])
    
    # Save post
    posts_data = json.loads(POSTS_FILE.read_text()) if POSTS_FILE.exists() else {"posts": []}
    posts_data["posts"].append({
        "id": f"post_{int(datetime.now().timestamp())}",
        "topic": topic, "tone": tone_key, "content": post,
        "created": datetime.now().isoformat(), "status": "draft"
    })
    POSTS_FILE.write_text(json.dumps(posts_data, indent=2))
    
    return {
        "post": post,
        "topic": topic,
        "tone": tone_key,
        "char_count": len(post),
        "status": "draft — ready to post",
        "action": "Copy and share on LinkedIn, or configure LinkedIn API to auto-post"
    }

async def publish_linkedin_post(post_content: str) -> dict:
    """Publish a post to LinkedIn via API."""
    if not LINKEDIN_TOKEN:
        return {
            "status": "draft_saved",
            "content": post_content,
            "note": "LinkedIn API not configured. Post saved as draft.",
            "setup": {
                "step1": "Go to LinkedIn Developer Portal (developer.linkedin.com)",
                "step2": "Create an app and get Access Token",
                "step3": "Set LINKEDIN_ACCESS_TOKEN in .env"
            }
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {LINKEDIN_TOKEN}",
            "Content-Type": "application/json"
        }
        # Get profile URN
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.linkedin.com/v2/me", headers=headers) as resp:
                profile = await resp.json()
                urn = profile.get("id", "")
            
            payload = {
                "author": f"urn:li:person:{urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": post_content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            
            async with session.post("https://api.linkedin.com/v2/ugcPosts", 
                                   headers=headers, json=payload) as resp:
                result = await resp.json()
                return {"status": "published", "post_id": result.get("id", ""), 
                        "ts": datetime.now().isoformat()}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def search_linkedin_jobs(keywords: str, location: str = "India") -> dict:
    """Search for jobs (uses public job search or LinkedIn API)."""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}"
            # Return search guidance since direct scraping requires auth
            return {
                "search_url": url,
                "keywords": keywords,
                "location": location,
                "tips": [
                    f"Search on LinkedIn: {keywords} jobs in {location}",
                    "Set up job alerts for instant notifications",
                    "Use JARVIS to generate tailored cover letters",
                    "Optimize your profile headline for recruiters"
                ],
                "action": "JARVIS can help you prepare resume, cover letter, and interview prep"
            }
    except Exception as e:
        return {"error": str(e)}

async def generate_connection_message(person_name: str, reason: str) -> dict:
    """Generate a personalized LinkedIn connection request message."""
    messages = {
        "networking": f"Hi {person_name}, I came across your profile and was impressed by your work. I'd love to connect and learn from your experience. Looking forward to exchanging ideas!",
        "job": f"Hi {person_name}, I noticed your company is doing amazing work. I'm interested in opportunities and would love to connect. I believe my skills could be a great fit for your team.",
        "mentorship": f"Hi {person_name}, I truly admire your journey and expertise. I'm looking to grow in this field and would be grateful for the opportunity to connect and learn from you.",
        "collaboration": f"Hi {person_name}, I see great potential for collaboration between our areas of expertise. I'd love to connect and explore how we can create value together."
    }
    
    reason_lower = reason.lower()
    msg_type = "networking"
    if any(w in reason_lower for w in ["job", "hire", "work", "opportunity"]):
        msg_type = "job"
    elif any(w in reason_lower for w in ["mentor", "learn", "guide"]):
        msg_type = "mentorship"
    elif any(w in reason_lower for w in ["collab", "partner", "project"]):
        msg_type = "collaboration"
    
    return {
        "message": messages[msg_type],
        "person": person_name,
        "type": msg_type,
        "char_count": len(messages[msg_type]),
        "note": "LinkedIn connection notes are limited to 300 characters"
    }

def get_saved_posts() -> list:
    """Get all saved LinkedIn post drafts."""
    if POSTS_FILE.exists():
        return json.loads(POSTS_FILE.read_text()).get("posts", [])
    return []

def get_engine_status() -> dict:
    return {
        "engine": "linkedin",
        "status": "online",
        "api_configured": bool(LINKEDIN_TOKEN),
        "profile_saved": LINKEDIN_PROFILE_FILE.exists(),
        "drafts_count": len(get_saved_posts()),
        "features": ["post_generation", "job_search", "connection_messages", 
                     "profile_management", "auto_publish"]
    }

logger.info("💼 LinkedIn engine loaded")
