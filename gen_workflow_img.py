import os
import sys
from PIL import Image, ImageDraw, ImageFont

def generate_workflow_image(output_path="simple_workflow_diagram.png"):
    width, height = 1400, 420
    # Create image with dark slate background
    img = Image.new('RGB', (width, height), color=(24, 28, 36))
    draw = ImageDraw.Draw(img)

    # Try loading fonts, fallback to default if not found
    try:
        font_title = ImageFont.truetype("arial.ttf", 20)
        font_subtitle = ImageFont.truetype("arialbd.ttf", 16)
        font_text = ImageFont.truetype("arial.ttf", 13)
        font_arrow = ImageFont.truetype("arialbd.ttf", 24)
    except Exception:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_arrow = ImageFont.load_default()

    boxes = [
        {
            "step": "STEP 1: USER INPUT",
            "subtitle": "Ingestion",
            "items": ["• Applicant Name & Contact", "• Requested Loan Amount", "• KYC, Bank & Income Proofs", "• Multipart HTTP Post"],
            "color": (30, 144, 255) # Blue accent
        },
        {
            "step": "STEP 2: PREPROCESSING",
            "subtitle": "Data Preparation",
            "items": ["• Save Raw Files (UUID)", "• PDF to Image Conversion", "• Base64 Data URI Encoding", "• Async Parallel Tasks"],
            "color": (0, 180, 216) # Cyan accent
        },
        {
            "step": "STEP 3: AI PROCESSING",
            "subtitle": "Extraction & Audit",
            "items": ["• AI Doc Classification", "• Field & PII Extraction", "• Rate Limit Fallback", "• Cross-Document Audit"],
            "color": (114, 9, 183) # Purple accent
        },
        {
            "step": "STEP 4: FINAL OUTPUT",
            "subtitle": "Decision & HITL",
            "items": ["• Underwriting Recommendation", "• Metrics & Red Flags", "• Human Verification Form", "• Save JSON Persistence"],
            "color": (46, 196, 182) # Teal accent
        }
    ]

    box_w, box_h = 280, 320
    start_y = 50
    spacing = 50
    start_x = 30

    for i, b in enumerate(boxes):
        x1 = start_x + i * (box_w + spacing)
        y1 = start_y
        x2 = x1 + box_w
        y2 = y1 + box_h

        # Draw box rounded rectangle outline and background
        draw.rectangle([x1, y1, x2, y2], fill=(36, 42, 54), outline=b["color"], width=3)
        
        # Header banner inside box
        draw.rectangle([x1, y1, x2, y1 + 45], fill=b["color"])
        
        # Header text
        draw.text((x1 + 15, y1 + 12), b["step"], fill=(255, 255, 255), font=font_subtitle)
        
        # Body items
        y_text = y1 + 65
        for item in b["items"]:
            draw.text((x1 + 15, y_text), item, fill=(220, 225, 235), font=font_text)
            y_text += 32

        # Draw arrow to next box if not last
        if i < len(boxes) - 1:
            arrow_x1 = x2 + 10
            arrow_y = y1 + box_h // 2
            arrow_x2 = arrow_x1 + 30
            draw.line([(arrow_x1, arrow_y), (arrow_x2, arrow_y)], fill=(30, 144, 255), width=4)
            # Arrow head
            draw.polygon([(arrow_x2, arrow_y - 8), (arrow_x2 + 10, arrow_y), (arrow_x2, arrow_y + 8)], fill=(30, 144, 255))

    img.save(output_path)
    print(f"Generated simple workflow image at: {output_path}")

if __name__ == "__main__":
    generate_workflow_image()
