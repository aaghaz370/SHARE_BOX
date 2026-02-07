"""
Share-box by Univora - QR Code Generator
Generate QR codes for share links
"""

import qrcode
from qrcode.image.pil import PilImage
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import config

def generate_qr_code(link: str, link_id: str, add_label: bool = True) -> BytesIO:
    """
    Generate QR code for link
    
    Args:
    link: The shareable link
        link_id: The unique link ID
        add_label: Whether to add label below QR code
    
    Returns:
        BytesIO object containing the QR code image
    """
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    
    qr.add_data(link)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Extract PIL image if wrapper
    if hasattr(img, "_img"):
        img = img._img
    
    # Add label if requested
    if add_label:
        img = add_label_to_qr(img, link_id)
    
    # Convert to BytesIO
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    bio.name = f'qr_{link_id}.png'
    
    return bio

def add_label_to_qr(qr_img: Image, link_id: str) -> Image:
    """Add label below QR code"""
    
    # Original QR dimensions
    qr_width, qr_height = qr_img.size
    
    # Create new image with extra space for label
    label_height = 80
    new_height = qr_height + label_height
    
    new_img = Image.new('RGB', (qr_width, new_height), 'white')
    
    # Paste QR code
    new_img.paste(qr_img, (0, 0))
    
    # Draw label
    draw = ImageDraw.Draw(new_img)
    
    # Try to use a nice font, fallback to default
    try:
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_subtitle = ImageFont.truetype("arial.ttf", 16)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
    
    # Draw title
    title = config.BOT_NAME
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (qr_width - title_width) // 2
    title_y = qr_height + 10
    
    draw.text((title_x, title_y), title, fill='black', font=font_title)
    
    # Draw link ID
    subtitle = f"Link: {link_id}"
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (qr_width - subtitle_width) // 2
    subtitle_y = title_y + 35
    
    draw.text((subtitle_x, subtitle_y), subtitle, fill='gray', font=font_subtitle)
    
    return new_img

def generate_fancy_qr_code(link: str, link_id: str) -> BytesIO:
    """
    Generate fancy branded QR code
    """
    
    # Create QR code with higher error correction for logo
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    
    qr.add_data(link)
    qr.make(fit=True)
    
    # Create colorful QR code
    img = qr.make_image(fill_color="#6C63FF", back_color="white")

    # Extract PIL image if wrapper
    if hasattr(img, "_img"):
        img = img._img
    
    # Convert to RGB for further processing
    img = img.convert('RGB')
    
    # Add label
    img = add_label_to_qr(img, link_id)
    
    # Convert to BytesIO
    bio = BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    bio.name = f'qr_fancy_{link_id}.png'
    
    return bio
