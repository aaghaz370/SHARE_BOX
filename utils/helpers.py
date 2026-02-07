"""
Share-box by Univora - Helper Utilities
Advanced helper functions for the bot
"""

from functools import wraps
from telegram import Update
from telegram.helpers import escape_markdown
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

from telegram import BotCommand, BotCommandScopeChat

async def update_user_menu(bot, user_id):
    """Update command menu for specific user based on plan"""
    is_premium = db.is_user_premium(user_id)
    is_admin = user_id in config.ADMIN_IDS
    
    # Base commands
    commands = [
        BotCommand("start", "🏠 Start"),
        BotCommand("upload", "📤 Upload"),
        BotCommand("stop", "🛑 Stop"),
        BotCommand("checklink", "🔎 Check"),
        BotCommand("mylinks", "🔗 Links"),
        BotCommand("stats", "📊 Stats"),
        BotCommand("upgrade", "💎 Premium"),
        BotCommand("help", "❓ Help"),
        BotCommand("settings", "⚙️ Settings"),
        BotCommand("referral", "🎁 Refer"),
    ]
    
    # Premium
    if is_premium or is_admin:
        commands.extend([
            BotCommand("search", "🔍 Search"),
            BotCommand("qrcode", "📱 QR Code"),
            BotCommand("setname", "🏷️ Rename"),
            BotCommand("setpassword", "🔒 Password"),
            BotCommand("protect", "🛡️ Protect"),
        ])
        
    # Admin
    if is_admin:
        commands.extend([
            BotCommand("ban", "🚫 Ban"),
            BotCommand("unban", "✅ Unban"),
            BotCommand("broadcast", "📢 Broadcast"),
            BotCommand("adminstats", "📈 Admin Stats"),
            BotCommand("grantpremium", "👑 Grant"),
        ])
        
    try:
        await bot.set_my_commands(commands, scope=BotCommandScopeChat(user_id))
    except Exception as e:
        print(f"Error updating menu: {e}")

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
    # Use Web Redirect if available (Future Proof)
    if config.WEBHOOK_URL:
        # Ensure no trailing slash
        base_url = config.WEBHOOK_URL.rstrip("/")
        return f"{base_url}/share/{link_id}"
        
    # Fallback to direct telegram link
    bot_username = config.BOT_USERNAME.replace("@", "")
    return f"https://t.me/{bot_username}?start={link_id}"

def extract_link_id_from_text(text: str) -> Optional[str]:
    """Extract link ID from message text"""
    if not text:
        return None
    
    # Match t.me/bot?start=LINKID
    pattern_tg = r't\.me/[\w]+\?start=([A-Za-z0-9_-]+)'
    match = re.search(pattern_tg, text)
    if match: return match.group(1)
    
    # Match /share/LINKID (Webhook URL)
    pattern_share = r'/share/([A-Za-z0-9_-]+)'
    match = re.search(pattern_share, text)
    if match: return match.group(1)
    
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
    """Check if user can upload files based on their plan"""
    
    # Admins have no limits
    if user_id in config.ADMIN_IDS:
        return {"allowed": True}
        
    plan = db.get_plan_details(user_id)
    
    max_files = plan.get("max_files_per_link", 20)
    max_file_size = plan.get("max_file_size_bytes", 2 * 1024 * 1024 * 1024)
    storage_limit = plan.get("storage_bytes", 50 * 1024 * 1024 * 1024)
    
    # Check file count
    if max_files < 99999 and file_count > max_files:
        return {
            "allowed": False,
            "reason": f"File count limit! Your plan: {max_files} files per link."
        }
    
    # Check file size
    if file_size > max_file_size:
        return {
            "allowed": False,
            "reason": f"File too large! Your plan limit: {format_file_size(max_file_size)} per file."
        }
        
    # Check total storage
    current_storage = db.get_user_storage_used(user_id)
    if storage_limit < 999999999999 and (current_storage + file_size) > storage_limit:
        return {
            "allowed": False,
            "reason": f"Storage full! Your limit: {format_file_size(storage_limit)}."
        }
        
    return {"allowed": True}

def check_link_creation_limit(user_id: int) -> dict:
    """Check if user can create new links"""
    
    if user_id in config.ADMIN_IDS:
        return {"allowed": True}
        
    # Check monthly limit
    allowed = db.check_monthly_limit(user_id)
    
    if not allowed:
        plan = db.get_plan_details(user_id)
        limit = plan.get("max_active_links", 10)
        return {
            "allowed": False,
            "reason": f"Monthly link limit reached! ({limit}/month)"
        }
        
    return {"allowed": True}

# ==================== ANALYTICS HELPERS ====================

def format_user_stats(user_id: int) -> str:
    """Format user statistics message with detailed dashboard"""
    user = db.get_user(user_id)
    if not user:
        return "❌ User not found"
        
    plan = db.get_plan_details(user_id)
    stats = db.get_user_stats(user_id)
    
    plan_name = plan.get("name", "Free Tier").upper()
    expiry = user.get("premium_expiry")
    
    # 1. Storage
    storage_used = stats.get('storage_used', 0)
    storage_limit = plan.get("storage_bytes", 0)
    
    storage_pct = 0
    limit_text = "Unlimited"
    
    # Check if unlimited (arbitrary large number > 100TB)
    is_unlimited = storage_limit > 100 * 1024 * 1024 * 1024 * 1024
    
    if not is_unlimited:
         limit_text = format_file_size(storage_limit)
         if storage_limit > 0:
             storage_pct = int((storage_used / storage_limit) * 100)
             
    storage_bar = create_progress_bar(storage_used, storage_limit if not is_unlimited else storage_used * 2, 15)
    
    # 2. Expiry
    expiry_text = "NEVER"
    days_left_text = ""
    
    if expiry:
         if expiry.tzinfo is None: expiry = expiry.replace(tzinfo=pytz.UTC)
         expiry_text = expiry.strftime('%d %b %Y')
         days_left = (expiry - datetime.now(pytz.UTC)).days
         if days_left < 0: 
             expiry_text = "EXPIRED"
         else:
             days_left_text = f"({days_left} days left)"
    elif plan.get("price", 0) > 0:
         expiry_text = "EXPIRED"
         
    # 3. Monthly Links
    monthly_used = user.get("monthly_link_count", 0)
    monthly_limit = plan.get("max_active_links", 10)
    monthly_text = f"{monthly_used} / {monthly_limit if monthly_limit < 99999 else '∞'}"
    
    # 4. Global Stats
    total_links = stats.get('total_links', 0)
    total_files = stats.get('total_files', 0)
    total_views = stats.get("total_views", 0)
    total_downloads = stats.get("total_downloads", 0)

    message = f"""
👤 **ACCOUNT DASHBOARD**
━━━━━━━━━━━━━━━━━━━━━
**User:** {escape_markdown(user.get("first_name", "User"))}
**ID:** `{user_id}`

💎 **PLAN STATUS**
━━━━━━━━━━━━━━━━━━━━━
🏷️ **Current Plan:** `{plan_name}`
📅 **Expiry:** {expiry_text} {days_left_text}
🗓️ **Monthly Links:** `{monthly_text}`

📊 **USAGE OVERVIEW**
━━━━━━━━━━━━━━━━━━━━━
🔗 **Active Links:** `{total_links}`
📂 **Total Files:** `{total_files}`
👁️ **Total Views:** `{total_views}`
📥 **Total Downloads:** `{total_downloads}`

💾 **STORAGE (Used / Total)**
━━━━━━━━━━━━━━━━━━━━━
`{storage_bar}`
**{format_file_size(storage_used)} / {limit_text}** ({storage_pct}%)

💡 _Upgrade to Premium for more limits!_
"""
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
