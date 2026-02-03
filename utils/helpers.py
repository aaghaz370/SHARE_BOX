"""
Share-box by Univora - Helper Utilities
Advanced helper functions for the bot
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import re
from typing import Optional, List
import pytz
import config
from database import db

# ==================== DECORATORS ====================

def admin_only(func):
    """Decorator to restrict commands to admins only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        if user_id not in config.ADMIN_IDS:
            await update.message.reply_text(
                "🔒 **Access Denied!**\n\n"
                "This command is for administrators only.\n"
                "Contact bot owner if you need access."
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def user_check(func):
    """Decorator to check if user is blocked and create/update user"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        
        # Create or update user
        user_data = db.create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        # Check if blocked
        if user_data and user_data.get("is_blocked", False):
            await update.message.reply_text(
                "🚫 **You are blocked!**\n\n"
                "You cannot use this bot.\n"
                "Contact administrators for support."
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def premium_only(func):
    """Decorator to restrict commands to premium users"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Admins always have access
        if user_id in config.ADMIN_IDS:
            return await func(update, context, *args, **kwargs)
        
        if not db.is_user_premium(user_id):
            await update.message.reply_text(
                "💎 **Premium Feature!**\n\n"
                "This feature is only available for premium users.\n\n"
                "🎁 **Get Premium:**\n"
                "• Unlimited files & links\n"
                "• Password protection\n"
                "• Advanced analytics\n"
                "• QR codes & more!\n\n"
                "💡 Use /upgrade to get premium!"
            )
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper

# ==================== FORMATTING HELPERS ====================

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"

def format_datetime(dt: datetime, tz: str = "Asia/Kolkata") -> str:
    """Format datetime in readable format"""
    if not dt:
        return "Never"
    
    # Convert to timezone
    local_tz = pytz.timezone(tz)
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    local_dt = dt.astimezone(local_tz)
    
    return local_dt.strftime("%d %b %Y, %I:%M %p")

def format_time_remaining(seconds: int) -> str:
    """Format time remaining in readable format"""
    if seconds <= 0:
        return "Expired"
    
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 and days == 0:
        parts.append(f"{secs}s")
    
    return " ".join(parts) if parts else "0s"

def format_expiry_date(dt: Optional[datetime]) -> str:
    """Format expiry date"""
    if not dt:
        return "Never (Manual delete only)"
    
    now = datetime.now(pytz.UTC)
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    if dt <= now:
        return "Expired ❌"
    
    time_left = format_time_remaining(int((dt - now).total_seconds()))
    return f"{format_datetime(dt)} ({time_left} left)"

def create_progress_bar(current: int, total: int, length: int = 10) -> str:
    """Create a text progress bar"""
    if total == 0:
        return "▱" * length
    
    filled = int((current / total) * length)
    empty = length - filled
    
    return "▰" * filled + "▱" * empty

def truncate_text(text: str, max_length: int = 30) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

# ==================== FILE HELPERS ====================

def get_file_emoji(file_type: str) -> str:
    """Get emoji based on file type"""
    emoji_map = {
        "document": "📄",
        "video": "🎥",
        "audio": "🎵",
        "photo": "🖼️",
        "animation": "🎬",
        "voice": "🎤",
        "sticker": "🎨"
    }
    return emoji_map.get(file_type.lower(), "📎")

def get_file_info(message) -> dict:
    """Extract file information from message"""
    file_data = {
        "file_type": None,
        "file_id": None,
        "file_name": None,
        "file_size": 0,
        "mime_type": None
    }
    
    if message.document:
        file_data.update({
            "file_type": "document",
            "file_id": message.document.file_id,
            "file_name": message.document.file_name or "document",
            "file_size": message.document.file_size or 0,
            "mime_type": message.document.mime_type
        })
    elif message.video:
        file_data.update({
            "file_type": "video",
            "file_id": message.video.file_id,
            "file_name": message.video.file_name or f"video_{message.video.file_id[:8]}.mp4",
            "file_size": message.video.file_size or 0,
            "mime_type": message.video.mime_type
        })
    elif message.audio:
        file_data.update({
            "file_type": "audio",
            "file_id": message.audio.file_id,
            "file_name": message.audio.file_name or message.audio.title or "audio.mp3",
            "file_size": message.audio.file_size or 0,
            "mime_type": message.audio.mime_type
        })
    elif message.photo:
        photo = message.photo[-1]  # Get largest photo
        file_data.update({
            "file_type": "photo",
            "file_id": photo.file_id,
            "file_name": f"photo_{photo.file_id[:8]}.jpg",
            "file_size": photo.file_size or 0,
            "mime_type": "image/jpeg"
        })
    elif message.voice:
        file_data.update({
            "file_type": "voice",
            "file_id": message.voice.file_id,
            "file_name": f"voice_{message.voice.file_id[:8]}.ogg",
            "file_size": message.voice.file_size or 0,
            "mime_type": message.voice.mime_type
        })
    
    return file_data

def calculate_total_size(files: List[dict]) -> int:
    """Calculate total size of files"""
    return sum(f.get("file_size", 0) for f in files)

# ==================== LINK HELPERS ====================

def generate_bot_link(link_id: str) -> str:
    """Generate shareable bot link"""
    bot_username = config.BOT_USERNAME.replace("@", "")
    return f"https://t.me/{bot_username}?start={link_id}"

def extract_link_id_from_text(text: str) -> Optional[str]:
    """Extract link ID from message text"""
    if not text:
        return None
    
    # Match t.me/bot?start=LINKID
    pattern = r't\.me/[\w]+\?start=([A-Za-z0-9_-]+)'
    match = re.search(pattern, text)
    
    if match:
        return match.group(1)
    
    # Match direct link ID (8 characters)
    if re.match(r'^[A-Za-z0-9_-]{8}$', text.strip()):
        return text.strip()
    
    return None

def is_valid_password(password: str) -> bool:
    """Check if password is valid"""
    if not password:
        return False
    
    # Minimum 4 characters, maximum 32
    if len(password) < 4 or len(password) > 32:
        return False
    
    # Only alphanumeric and common special chars
    if not re.match(r'^[A-Za-z0-9@#$%^&*()_+=\-!.]+$', password):
        return False
    
    return True

# ==================== PAGINATION HELPERS ====================

def create_pagination_data(
    items: List,
    page: int,
    items_per_page: int
) -> dict:
    """Create pagination data"""
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    # Validate page number
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    page_items = items[start_idx:end_idx]
    
    return {
        "items": page_items,
        "page": page,
        "total_pages": total_pages,
        "total_items": total_items,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "start_idx": start_idx,
        "end_idx": end_idx
    }

# ==================== TIER CHECK HELPERS ====================

def check_upload_limit(user_id: int, file_count: int, file_size: int) -> dict:
    """Check if user can upload files"""
    user = db.get_user(user_id)
    is_premium = db.is_user_premium(user_id)
    
    # Get limits
    if is_premium:
        max_files = config.PremiumLimits.MAX_FILES_PER_LINK
        max_file_size = config.PremiumLimits.MAX_FILE_SIZE_BYTES
        max_storage = config.PremiumLimits.TOTAL_STORAGE_BYTES
    else:
        max_files = config.FreeLimits.MAX_FILES_PER_LINK
        max_file_size = config.FreeLimits.MAX_FILE_SIZE_BYTES
        max_storage = config.FreeLimits.TOTAL_STORAGE_BYTES
    
    # Check file count (0 = unlimited)
    if max_files > 0 and file_count > max_files:
        return {
            "allowed": False,
            "reason": f"File limit exceeded! Free tier: {max_files} files per link. Upgrade to premium for unlimited!"
        }
    
    # Check file size
    if file_size > max_file_size:
        max_gb = max_file_size / (1024**3)
        return {
            "allowed": False,
            "reason": f"File too large! Max size: {max_gb}GB. {'Upgrade to premium for 4GB!' if not is_premium else ''}"
        }
    
    # Check total storage
    storage_used = user.get("storage_used", 0)
    if storage_used + file_size > max_storage:
        return {
            "allowed": False,
            "reason": f"Storage limit reached! Used: {format_file_size(storage_used)}/{format_file_size(max_storage)}. {'Upgrade to premium for more!' if not is_premium else 'Delete old links to free space.'}"
        }
    
    return {"allowed": True}

def check_link_creation_limit(user_id: int) -> dict:
    """Check if user can create new link"""
    is_premium = db.is_user_premium(user_id)
    
    if is_premium:
        max_links = config.PremiumLimits.MAX_ACTIVE_LINKS
    else:
        max_links = config.FreeLimits.MAX_ACTIVE_LINKS
    
    # 0 = unlimited
    if max_links == 0:
        return {"allowed": True}
    
    active_links = db.get_user_active_links_count(user_id)
    
    if active_links >= max_links:
        return {
            "allowed": False,
            "reason": f"Link limit reached! You have {active_links}/{max_links} active links. {'Upgrade to premium for unlimited!' if not is_premium else 'Delete old links to create new ones.'}"
        }
    
    return {"allowed": True}

# ==================== ANALYTICS HELPERS ====================

def format_user_stats(user_id: int) -> str:
    """Format user statistics message"""
    user = db.get_user(user_id)
    if not user:
        return "❌ User not found"
    
    is_premium = db.is_user_premium(user_id)
    analytics = db.get_user_analytics(user_id)
    
    # Plan info
    plan = "💎 Premium" if is_premium else "🆓 Free"
    
    # Storage info
    storage_used = user.get("storage_used", 0)
    storage_limit = config.PremiumLimits.TOTAL_STORAGE_BYTES if is_premium else config.FreeLimits.TOTAL_STORAGE_BYTES
    storage_percentage = int((storage_used / storage_limit) * 100) if storage_limit > 0 else 0
    
    storage_bar = create_progress_bar(storage_used, storage_limit, 15)
    
    # Links info
    active_links = analytics.get("total_links", 0)
    max_links = config.PremiumLimits.MAX_ACTIVE_LINKS if is_premium else config.FreeLimits.MAX_ACTIVE_LINKS
    max_links_str = "Unlimited" if max_links == 0 else str(max_links)
    
    # Category breakdown
    categories = analytics.get("category_breakdown", {})
    top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
    category_list = "\n".join([f"• {cat}: {count} links" for cat, count in top_categories]) or "No links yet"
    
    # Format message
    message = config.STATS_MESSAGE.format(
        username=user.get("username") or "Unknown",
        plan=plan,
        joined_date=format_datetime(user.get("joined_at")),
        storage_used=format_file_size(storage_used),
        storage_limit=format_file_size(storage_limit),
        storage_percentage=storage_percentage,
        storage_bar=storage_bar,
        active_links=active_links,
        max_links=max_links_str,
        total_downloads=analytics.get("total_downloads", 0),
        total_views=analytics.get("total_views", 0),
        popular_categories=category_list
    )
    
    return message

# ==================== VALIDATION ====================

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS

def sanitize_filename(filename: str) -> str:
    """Sanitize filename"""
    # Remove path components
    filename = filename.replace("/", "_").replace("\\", "_")
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)
    
    # Truncate if too long
    if len(filename) > 100:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:95] + ("." + ext if ext else "")
    
    return filename or "file"
