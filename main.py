import os
import sys
import json
import time
import random
import argparse
import requests
from typing import Tuple, List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from banner_generator import create_saas_banner, upload_banner_to_web

# Ensure safe UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def load_dotenv():
    """Load key-value pairs from .env if present."""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.isfile(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val

load_dotenv()

# Configuration via environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")

WEBSITES = [
    {
        "name": "Wakit",
        "url": "https://wakit.progeni.live",
        "theme_color": (34, 197, 94),  # WhatsApp Emerald
        "headline_line1": "Split WhatsApp Videos",
        "headline_line2": "In Just 1-Click.",
        "tagline": "Browser-native WhatsApp utility suite • No login or install needed.",
        "features": [
            ("Exact 30-Second Status Splitting", "Perfect video cuts ready to upload seamlessly without manual trimming."),
            ("Direct Chat Without Saving Numbers", "Instantly open conversations without cluttering your phone contacts."),
            ("100% Client-Side & Secure", "Videos are processed in your browser. Nothing is ever sent to a server.")
        ],
        "default_hashtags": ["#WhatsAppStatus", "#Wakit", "#ProductivityHacks", "#VideoSplitter", "#WhatsAppTips", "#WebUtility", "#TechHacks"]
    },
    {
        "name": "Progeni Bench",
        "url": "https://bench.progeni.live",
        "theme_color": (99, 102, 241),  # Modern Indigo
        "headline_line1": "Developer Micro-Tools",
        "headline_line2": "Built For High Speed.",
        "tagline": "Instant developer & creator micro-tools • Zero setup required.",
        "features": [
            ("Browser-Native File Splitters", "Split, merge, and organize files securely in client-side memory."),
            ("Distraction-Free Safe Zones", "Secure workspace for code snippets, JSON, and sensitive workflows."),
            ("100% Free & Zero Tracking", "No accounts, no cookies, no tracking. Instant utility.")
        ],
        "default_hashtags": ["#WebDev", "#CodingTools", "#DeveloperLife", "#ProgeniBench", "#ProductivityTools", "#Programming", "#TechTools"]
    }
]

MARKETING_ANGLES = [
    "Problem & Solution: Highlight a frustrating daily problem and how this tool instantly solves it.",
    "Feature Spotlight: Focus on a standout capability (e.g. 30-sec status splitter, quick direct chat, or browser file splitting).",
    "Pro-Tip / Workflow Hack: Position the tool as an insider secret that saves 15+ minutes every day.",
    "Speed & Simplicity: Highlight that it's 100% web-based, instant, privacy-focused, and requires no complicated downloads."
]

class FeatureSchema(BaseModel):
    title: str = Field(description="Short feature title (3 to 5 words)")
    desc: str = Field(description="Crisp feature benefit or description (6 to 10 words)")

class MarketingPostSchema(BaseModel):
    headline_line1: str = Field(description="Massive bold headline line 1 (max 5 words, e.g. 'Split WhatsApp Videos')")
    headline_line2: str = Field(description="Massive bold headline line 2 (max 5 words, e.g. 'In Just 1-Click.')")
    tagline: str = Field(description="Crisp 1-line app summary under the headline")
    features: List[FeatureSchema] = Field(description="Exactly 3 key value propositions for the visual card")
    body: str = Field(description="2 engaging sentences for the Instagram caption body")
    call_to_action: str = Field(description="Clear CTA for the caption")
    hashtags: List[str] = Field(description="5 to 8 targeted Instagram hashtags starting with '#'")


def check_environment(dry_run: bool = False) -> bool:
    """Validate that required environment variables are set."""
    if not dry_run:
        missing = []
        if not GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not IG_ACCESS_TOKEN:
            missing.append("IG_ACCESS_TOKEN")
        if not IG_USER_ID:
            missing.append("IG_USER_ID")
        if missing:
            print(f"❌ Missing required environment variables: {', '.join(missing)}")
            print("💡 Tip: You can test the generation locally without Instagram credentials using: python main.py --dry-run")
            return False
    else:
        if not GEMINI_API_KEY:
            print("ℹ️ Note: GEMINI_API_KEY not set. Using curated high-converting SaaS card template for preview.")
    return True


def validate_instagram_token(access_token: str, user_id: str) -> bool:
    """Check Instagram Graph API access token validity before running jobs."""
    print("🔍 Validating Instagram access token and account ID...")
    url = f"https://graph.facebook.com/v18.0/{user_id}"
    params = {
        "fields": "id,name,username",
        "access_token": access_token
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if "error" in data:
            err = data["error"]
            print(f"❌ Instagram Authentication Error: {err.get('message')} (Code {err.get('code')})")
            print("💡 Ensure IG_ACCESS_TOKEN is a valid non-expired Token with 'instagram_content_publish' and 'instagram_basic' permissions.")
            print(f"💡 Ensure IG_USER_ID ({user_id}) is the Instagram Business Account ID, not a personal ID or Facebook Page ID.")
            return False
        
        username = data.get("username", data.get("name", user_id))
        print(f"✅ Authenticated as Instagram Account: @{username} (ID: {data.get('id')})")
        return True
    except Exception as e:
        print(f"⚠️ Could not verify Instagram credentials: {e}")
        return False


def generate_content(site: dict, angle: str) -> Tuple[str, dict]:
    """Generate marketing copy and card structure using Gemini API (with fallback)."""
    if not GEMINI_API_KEY:
        print("Using curated SaaS marketing template...")
        h1 = site.get("headline_line1", "Instant Web Utility")
        h2 = site.get("headline_line2", "Built For Speed.")
        tag = site.get("tagline", "Free browser-native utility.")
        feats = site.get("features", [])
        hashtags = site.get("default_hashtags", ["#Productivity", "#WebTools"])

        if "wakit" in site["name"].lower():
            body = "Tired of trimming 30-sec videos manually for WhatsApp status? Wakit splits any video in seconds with zero compression loss. Plus, chat directly without saving phone numbers!"
            cta = "Try it 100% free right now in your browser!"
        else:
            body = "Progeni Bench is your ultimate browser-native toolbox: client-side file splitters, quick developer utilities, and secure distraction-free safe zones with zero setup!"
            cta = "Supercharge your daily workflow today!"

        hashtag_str = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags])
        caption = f"{h1} {h2} ⚡\n\n{body}\n\n👉 {cta}\n🔗 Link in bio / visit: {site['url']}\n\n{hashtag_str}"

        card_data = {
            "headline_line1": h1,
            "headline_line2": h2,
            "tagline": tag,
            "features": feats
        }
        return caption, card_data

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
You are an elite SaaS growth marketer.
Create an Instagram marketing post and social media banner card copy for: {site['name']} ({site['url']}).
Angle for today: {angle}
Core Value: {site.get('tagline', '')}

Rules:
1. headline_line1: Punchy, scroll-stopping main benefit (max 5 words).
2. headline_line2: Punchline or speed indicator in vibrant color (max 4-5 words, e.g. 'In 1-Click.', 'With Zero Setup.').
3. tagline: 1 crisp line explaining what the tool is (under 12 words).
4. features: Exactly 3 high-impact features (each has a 3-4 word title and 6-8 word benefit).
5. body: 2 engaging sentences for the Instagram caption.
6. call_to_action: Strong, action-driven CTA.
7. hashtags: 5-8 relevant tags.
Return valid JSON adhering to the schema.
"""

    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    last_err = None

    for model_name in models:
        for attempt in range(1, 4):
            try:
                print(f"Generating content with {model_name} (attempt {attempt})...")
                res = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=MarketingPostSchema,
                        temperature=0.7
                    )
                )
                data = json.loads(res.text.strip())

                h1 = data.get("headline_line1", site.get("headline_line1", "Fast Web Utility"))
                h2 = data.get("headline_line2", site.get("headline_line2", "In 1-Click."))
                tag = data.get("tagline", site.get("tagline", ""))
                feats = [(f["title"], f["desc"]) for f in data.get("features", [])] or site.get("features", [])
                body = data.get("body", "").strip()
                cta = data.get("call_to_action", "").strip()
                hashtags = data.get("hashtags", site.get("default_hashtags", []))

                hashtag_str = " ".join([h if h.startswith("#") else f"#{h}" for h in hashtags])
                caption = f"{h1} {h2} ⚡\n\n{body}\n\n👉 {cta}\n🔗 Link in bio / visit: {site['url']}\n\n{hashtag_str}"

                card_data = {
                    "headline_line1": h1,
                    "headline_line2": h2,
                    "tagline": tag,
                    "features": feats
                }
                return caption, card_data

            except Exception as e:
                last_err = e
                print(f"Issue on attempt {attempt}: {e}")
                time.sleep(2)

    raise RuntimeError(f"Content generation failed across all models: {last_err}")


def post_to_instagram(image_url: str, caption: str, user_id: str, access_token: str):
    """Publish image container to Instagram Graph API with asynchronous status polling."""
    print("📤 Step 1/3: Creating Instagram media container...")
    container_url = f"https://graph.facebook.com/v18.0/{user_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    r = requests.post(container_url, data=payload, timeout=30)
    res = r.json()
    creation_id = res.get("id")

    if not creation_id:
        error_detail = res.get("error", {}).get("message", r.text)
        raise RuntimeError(f"Instagram container creation failed: {error_detail}")

    print(f"✅ Container created successfully. ID: {creation_id}")

    print("⏳ Step 2/3: Waiting for Instagram to process media...")
    status_url = f"https://graph.facebook.com/v18.0/{creation_id}"
    params = {
        "fields": "status_code,status",
        "access_token": access_token
    }

    max_retries = 15
    for attempt in range(1, max_retries + 1):
        time.sleep(4)
        check_r = requests.get(status_url, params=params, timeout=15)
        check_data = check_r.json()
        status = check_data.get("status_code")
        print(f"   [Checking status {attempt}/{max_retries}] Status: {status}")

        if status == "FINISHED":
            print("✅ Media container is ready for publishing.")
            break
        elif status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram media processing ended in state: {status} ({check_data})")
    else:
        print("⚠️ Status polling reached timeout, attempting to publish anyway...")

    print("🚀 Step 3/3: Publishing container to feed...")
    publish_url = f"https://graph.facebook.com/v18.0/{user_id}/media_publish"
    publish_payload = {
        "creation_id": creation_id,
        "access_token": access_token
    }
    pub_r = requests.post(publish_url, data=publish_payload, timeout=30)
    pub_res = pub_r.json()
    post_id = pub_res.get("id")

    if not post_id:
        error_detail = pub_res.get("error", {}).get("message", pub_r.text)
        raise RuntimeError(f"Instagram media publish failed: {error_detail}")

    print(f"🎉 Successfully published to Instagram! Post ID: {post_id}")
    return post_id


def main():
    parser = argparse.ArgumentParser(description="Automated Daily Instagram Marketing Bot")
    parser.add_argument("--dry-run", action="store_true", help="Generate graphics and copy without posting to Instagram")
    parser.add_argument("--validate", action="store_true", help="Only validate environment variables and Instagram credentials")
    parser.add_argument("--site", type=str, default=None, help="Filter to run for a specific site by name (e.g. Wakit)")
    parser.add_argument("--api-key", type=str, default=None, help="Gemini API Key (optional if in .env)")
    args = parser.parse_args()

    global GEMINI_API_KEY
    if args.api_key:
        GEMINI_API_KEY = args.api_key

    is_dry_run = args.dry_run or os.environ.get("DRY_RUN", "").lower() in ("true", "1", "yes")

    print("=" * 60)
    print("🚀 Professional SaaS Marketing Bot Starting")
    print(f"Mode: {'🧪 DRY-RUN (Local Preview)' if is_dry_run else '🌐 LIVE (Will post to Instagram)'}")
    print("=" * 60)

    if not check_environment(dry_run=is_dry_run):
        sys.exit(1)

    if not is_dry_run:
        is_valid = validate_instagram_token(IG_ACCESS_TOKEN, IG_USER_ID)
        if not is_valid:
            print("❌ Exiting due to invalid Instagram credentials.")
            sys.exit(1)

    if args.validate:
        print("✅ Environment and credentials are fully valid.")
        return

    targets = [s for s in WEBSITES if args.site.lower() in s["name"].lower()] if args.site else WEBSITES

    total_failures = 0
    for site in targets:
        print("\n" + "-" * 50)
        print(f"📱 Processing Campaign for: {site['name']}")
        print("-" * 50)

        angle = random.choice(MARKETING_ANGLES)
        print(f"💡 Strategy: {angle}")

        try:
            caption, card = generate_content(site, angle)
            print("\n📝 --- Generated Instagram Caption ---")
            print(caption)

            # Generate crisp 1080x1080 SaaS banner
            output_file = f"banner_{site['name'].lower().replace(' ', '_')}.jpg"
            print(f"\n🎨 Designing professional 1080x1080 SaaS banner: {output_file}...")
            banner_path = create_saas_banner(
                brand_name=site["name"],
                tagline=card["tagline"],
                headline_line1=card["headline_line1"],
                headline_line2=card["headline_line2"],
                url=site["url"],
                features=card["features"],
                theme_color=site.get("theme_color", (34, 197, 94)),
                output_path=output_file
            )
            print(f"✅ Banner created: {banner_path}")

            # Upload to public CDN for Instagram crawler (or preview)
            public_image_url = upload_banner_to_web(banner_path)
            print(f"🔗 Public Image URL: {public_image_url}")

            if is_dry_run:
                print("\n🧪 [DRY-RUN] Skipping actual Instagram post step.")
            else:
                post_to_instagram(public_image_url, caption, IG_USER_ID, IG_ACCESS_TOKEN)

        except Exception as e:
            print(f"❌ Error processing campaign for {site['name']}: {e}")
            total_failures += 1

        if site != targets[-1]:
            print("\n⏳ Short pause before next campaign...")
            time.sleep(5)

    print("\n" + "=" * 60)
    if total_failures > 0:
        print(f"⚠️ Completed with {total_failures} failure(s).")
        sys.exit(1)
    else:
        print("✨ All marketing campaigns completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
