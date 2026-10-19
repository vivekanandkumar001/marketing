import os
import sys
import requests
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def get_font(font_type="Bold", size=40):
    """Load standard system fonts across Windows and Linux or fallback."""
    candidate_paths = [
        # Windows standard fonts
        f"C:/Windows/Fonts/{'arialbd' if font_type == 'Bold' else 'arial'}.ttf",
        f"C:/Windows/Fonts/{'segoeuib' if font_type == 'Bold' else 'segoeui'}.ttf",
        # Linux / GitHub Actions standard fonts
        f"/usr/share/fonts/truetype/dejavu/{'DejaVuSans-Bold' if font_type == 'Bold' else 'DejaVuSans'}.ttf",
        f"/usr/share/fonts/truetype/liberation/{'LiberationSans-Bold' if font_type == 'Bold' else 'LiberationSans-Regular'}.ttf",
        f"/usr/share/fonts/truetype/freefont/{'FreeSansBold' if font_type == 'Bold' else 'FreeSans'}.ttf",
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_radial_gradient(draw, width, height, center_x, center_y, max_radius, color_start):
    """Draw a smooth ambient radial glow."""
    steps = 45
    for i in range(steps, 0, -1):
        ratio = i / steps
        r = int(max_radius * ratio)
        alpha = int(color_start[3] * (1 - ratio ** 1.6))
        color = (color_start[0], color_start[1], color_start[2], alpha)
        draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill=color)


def draw_checkmark_icon(draw, cx, cy, radius, theme_color):
    """Draw a crisp circular badge with a centered checkmark."""
    # Outer circle
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=(theme_color[0], theme_color[1], theme_color[2], 50),
        outline=theme_color,
        width=2
    )
    # Checkmark path
    p1 = (cx - 8, cy - 1)
    p2 = (cx - 2, cy + 6)
    p3 = (cx + 9, cy - 7)
    draw.line([p1, p2], fill=(255, 255, 255), width=3)
    draw.line([p2, p3], fill=(255, 255, 255), width=3)


def draw_lightning_bolt(draw, cx, cy, size, color):
    """Draw a sleek geometric bolt icon."""
    pts = [
        (cx + 2, cy - size),
        (cx - size // 2, cy),
        (cx, cy),
        (cx - 2, cy + size),
        (cx + size // 2, cy),
        (cx, cy)
    ]
    draw.polygon(pts, fill=color)


def create_saas_banner(
    brand_name: str,
    tagline: str,
    headline_line1: str,
    headline_line2: str,
    url: str,
    features: list,
    theme_color: tuple = (34, 197, 94),  # Vibrant Emerald green
    output_path: str = "banner.jpg"
) -> str:
    """Generate a high-converting, crystal-clear 1080x1080 SaaS promotional graphic."""
    width = 1080
    height = 1080

    # Base background (Midnight navy / dark slate)
    img = Image.new("RGBA", (width, height), (11, 15, 23, 255))
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    # Ambient radial lighting
    accent_glow = (theme_color[0], theme_color[1], theme_color[2], 65)
    draw_radial_gradient(draw_overlay, width, height, 920, 200, 520, accent_glow)
    draw_radial_gradient(draw_overlay, width, height, 160, 940, 420, accent_glow)

    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Main Card
    card_x0, card_y0 = 60, 60
    card_x1, card_y1 = 1020, 1020
    card_radius = 36

    draw.rounded_rectangle(
        [card_x0, card_y0, card_x1, card_y1],
        radius=card_radius,
        fill=(17, 24, 39, 245),
        outline=(51, 65, 85, 255),
        width=2
    )

    # Accent top highlight border
    draw.line(
        [card_x0 + 40, card_y0 + 2, card_x1 - 40, card_y0 + 2],
        fill=(theme_color[0], theme_color[1], theme_color[2], 220),
        width=3
    )

    # Top Brand Badge
    brand_box = [card_x0 + 45, card_y0 + 45, card_x0 + 270, card_y0 + 105]
    draw.rounded_rectangle(brand_box, radius=18, fill=(24, 33, 49, 255), outline=theme_color, width=2)
    draw_lightning_bolt(draw, brand_box[0] + 32, brand_box[1] + 30, 16, theme_color)
    font_brand = get_font("Bold", 28)
    draw.text((brand_box[0] + 55, brand_box[1] + 14), brand_name.upper(), fill=(255, 255, 255), font=font_brand)

    # Top Right Free Utility Badge
    free_box = [card_x1 - 320, card_y0 + 45, card_x1 - 45, card_y0 + 105]
    draw.rounded_rectangle(free_box, radius=18, fill=(24, 33, 49, 255), outline=(71, 85, 105), width=1)
    font_free = get_font("Bold", 22)
    draw.ellipse([free_box[0] + 25, free_box[1] + 24, free_box[0] + 37, free_box[1] + 36], fill=theme_color)
    draw.text((free_box[0] + 48, free_box[1] + 18), "FREE WEB UTILITY", fill=(203, 213, 225), font=font_free)

    # Hero Section Headline
    headline_y = card_y0 + 145
    font_h1 = get_font("Bold", 56)
    draw.text((card_x0 + 45, headline_y), headline_line1, fill=(255, 255, 255), font=font_h1)

    font_h2 = get_font("Bold", 56)
    draw.text((card_x0 + 45, headline_y + 75), headline_line2, fill=theme_color, font=font_h2)

    font_tag = get_font("Regular", 26)
    draw.text((card_x0 + 45, headline_y + 160), tagline, fill=(148, 163, 184), font=font_tag)

    # 3 Feature Rows
    feat_y_start = card_y0 + 430
    card_h = 100
    gap = 20

    font_feat_title = get_font("Bold", 27)
    font_feat_desc = get_font("Regular", 21)

    for i, (title, desc) in enumerate(features[:3]):
        fy0 = feat_y_start + i * (card_h + gap)
        fy1 = fy0 + card_h
        fbox = [card_x0 + 45, fy0, card_x1 - 45, fy1]
        
        draw.rounded_rectangle(fbox, radius=20, fill=(24, 33, 50, 240), outline=(45, 59, 80), width=1)
        
        icon_cx, icon_cy = fbox[0] + 48, fy0 + card_h // 2
        draw_checkmark_icon(draw, icon_cx, icon_cy, 22, theme_color)

        draw.text((fbox[0] + 92, fy0 + 19), title, fill=(248, 250, 252), font=font_feat_title)
        draw.text((fbox[0] + 92, fy0 + 55), desc, fill=(148, 163, 184), font=font_feat_desc)

    # Bottom CTA Bar
    cta_y0 = card_y1 - 150
    cta_y1 = card_y1 - 45
    cta_box = [card_x0 + 45, cta_y0, card_x1 - 45, cta_y1]

    draw.rounded_rectangle(cta_box, radius=24, fill=theme_color, outline=(255, 255, 255, 120), width=2)

    font_cta_main = get_font("Bold", 34)
    clean_domain = url.replace("https://", "").replace("http://", "")
    cta_text = f"Launch Free: {clean_domain}  \u2192"
    
    bbox = font_cta_main.getbbox(cta_text)
    text_w = bbox[2] - bbox[0]
    center_x = (card_x0 + 45 + card_x1 - 45 - text_w) // 2
    
    text_color = (11, 15, 23) if (theme_color[0] + theme_color[1] + theme_color[2]) > 380 else (255, 255, 255)
    draw.text((center_x, cta_y0 + 30), cta_text, fill=text_color, font=font_cta_main)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img_rgb = img.convert("RGB")
    img_rgb.save(output_path, "JPEG", quality=95)
    return output_path


def upload_banner_to_web(image_path: str) -> str:
    """Upload generated banner to Catbox (with Tmpfiles fallback) to obtain a direct HTTPS URL."""
    print(f"Uploading banner '{image_path}' to public CDN for Instagram crawlers...")
    
    # Try Catbox (Permanent direct HTTPS URL)
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": ("banner.jpg", f, "image/jpeg")},
                timeout=30
            )
        if r.status_code == 200 and r.text.strip().startswith("http"):
            url = r.text.strip()
            print(f"✅ Hosted on Catbox CDN: {url}")
            return url
    except Exception as e:
        print(f"⚠️ Catbox upload notice: {e}, attempting fallback...")

    # Fallback to Tmpfiles
    try:
        with open(image_path, "rb") as f:
            r = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": ("banner.jpg", f, "image/jpeg")},
                timeout=30
            )
        data = r.json()
        if r.status_code == 200 and data.get("status") == "success":
            raw_url = data["data"]["url"]
            # Convert tmpfiles page URL to direct image URL: tmpfiles.org/123/img.jpg -> tmpfiles.org/dl/123/img.jpg
            direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            print(f"✅ Hosted on Tmpfiles CDN: {direct_url}")
            return direct_url
    except Exception as e:
        print(f"⚠️ Tmpfiles fallback error: {e}")

    raise RuntimeError("Failed to host generated banner on public CDN.")


if __name__ == "__main__":
    banner = create_saas_banner(
        brand_name="Wakit",
        tagline="Browser-native WhatsApp utility suite • No login or install needed.",
        headline_line1="Split Long Videos For Status",
        headline_line2="In Just 1-Click.",
        url="https://wakit.progeni.live",
        features=[
            ("Exact 30-Second Status Splitting", "Perfect video cuts ready to upload seamlessly without manual trimming."),
            ("Direct Chat Without Saving Numbers", "Instantly open conversations without cluttering your phone contacts."),
            ("100% Client-Side & Secure", "Videos are processed in your browser. Nothing is ever sent to a server.")
        ],
        theme_color=(34, 197, 94),
        output_path="test_wakit_banner.jpg"
    )
    print(f"Generated: {banner}")
