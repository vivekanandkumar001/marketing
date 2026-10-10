import os
import requests
from google import genai

# Configuration via GitHub Environment Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")

websites = [
    {"name": "Wakit", "url": "https://wakit.progeni.live", "focus": "WhatsApp utilities, status splitters, and direct chat."},
    {"name": "Progeni Bench", "url": "https://bench.progeni.live", "focus": "Developer and creator micro-tools, file splitters, and safe zones."}
]

def generate_content_with_gemini(site):
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
    Create an engaging Instagram marketing caption and an AI image generation prompt for a web utility platform called {site['name']} ({site['url']}).
    Focus: {site['focus']}
    
    Format your response strictly as:
    CAPTION: [Write a catchy hook, short description, emojis, and include the link {site['url']}]
    IMAGE_PROMPT: [Write a concise, high-quality visual prompt for an AI image generator representing this tool]
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    text = response.text.strip()
    
    # Parse output
    lines = text.split("\n")
    caption = ""
    image_prompt = ""
    for line in lines:
        if line.startswith("CAPTION:"):
            caption = line.replace("CAPTION:", "").strip()
        elif line.startswith("IMAGE_PROMPT:"):
            image_prompt = line.replace("IMAGE_PROMPT:", "").strip()
            
    return caption, image_prompt

def generate_image(prompt):
    # Using Pollinations.ai free public text-to-image endpoint
    encoded_prompt = requests.utils.quote(prompt)
    image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1080&height=1080&nologo=true"
    return image_url

def post_to_instagram(image_url, caption):
    # Step 1: Create Container
    container_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': IG_ACCESS_TOKEN
    }
    r = requests.post(container_url, data=payload)
    creation_id = r.json().get('id')
    
    if not creation_id:
        print(f"Error creating container: {r.text}")
        return

    # Step 2: Publish Container
    publish_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish"
    publish_payload = {
        'creation_id': creation_id,
        'access_token': IG_ACCESS_TOKEN
    }
    pub_r = requests.post(publish_url, data=publish_payload)
    print(f"Published successfully: {pub_r.json()}")

if __name__ == "__main__":
    for site in websites:
        print(f"Processing {site['name']}...")
        caption, img_prompt = generate_content_with_gemini(site)
        print(f"Generated Caption: {caption}")
        
        image_url = generate_image(img_prompt)
        print(f"Generated Image URL: {image_url}")
        
        post_to_instagram(image_url, caption)
