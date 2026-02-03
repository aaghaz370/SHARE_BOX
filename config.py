"""
Share-box by Univora - Configuration Module
Advanced configuration management with environment variables
"""

import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

# ===== BOT CONFIGURATION =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# ===== BRANDING =====
BOT_NAME = os.getenv("BOT_NAME", "Share-box by Univora")
BOT_USERNAME = os.getenv("BOT_USERNAME", "@ShareBoxBot")
BRAND_NAME = os.getenv("BRAND_NAME", "Univora 📦")

# ===== DATABASE =====
MONGO_URI = os.getenv("MONGO_URI", "")
DATABASE_NAME = "sharebox_univora"

# ===== STORAGE CHANNELS =====
PRIMARY_CHANNEL = int(os.getenv("PRIMARY_CHANNEL", "0"))
BACKUP_CHANNEL_1 = int(os.getenv("BACKUP_CHANNEL_1", "0"))
BACKUP_CHANNEL_2 = int(os.getenv("BACKUP_CHANNEL_2", "0"))

STORAGE_CHANNELS = [
    PRIMARY_CHANNEL,
    BACKUP_CHANNEL_1,
    BACKUP_CHANNEL_2
]

# ===== SERVER =====
PORT = int(os.getenv("PORT", "10000"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# ===== FEATURE FLAGS =====
ENABLE_PREMIUM_FEATURES = os.getenv("ENABLE_PREMIUM_FEATURES", "true").lower() == "true"
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
ENABLE_REFERRALS = os.getenv("ENABLE_REFERRALS", "true").lower() == "true"
ENABLE_QR_CODES = os.getenv("ENABLE_QR_CODES", "true").lower() == "true"

# ===== FREE TIER LIMITS =====
class FreeLimits:
    MAX_FILES_PER_LINK = int(os.getenv("FREE_MAX_FILES_PER_LINK", "20"))
    MAX_FILE_SIZE_GB = int(os.getenv("FREE_MAX_FILE_SIZE_GB", "2"))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_GB * 1024 * 1024 * 1024
    MAX_ACTIVE_LINKS = int(os.getenv("FREE_MAX_ACTIVE_LINKS", "10"))
    TOTAL_STORAGE_GB = int(os.getenv("FREE_TOTAL_STORAGE_GB", "50"))
    TOTAL_STORAGE_BYTES = TOTAL_STORAGE_GB * 1024 * 1024 * 1024
    LINK_EXPIRY_DAYS = int(os.getenv("FREE_LINK_EXPIRY_DAYS", "30"))

# ===== PREMIUM TIER LIMITS =====
class PremiumLimits:
    MAX_FILES_PER_LINK = int(os.getenv("PREMIUM_MAX_FILES_PER_LINK", "0"))  # 0 = unlimited
    MAX_FILE_SIZE_GB = int(os.getenv("PREMIUM_MAX_FILE_SIZE_GB", "4"))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_GB * 1024 * 1024 * 1024
    MAX_ACTIVE_LINKS = int(os.getenv("PREMIUM_MAX_ACTIVE_LINKS", "0"))  # 0 = unlimited
    TOTAL_STORAGE_GB = int(os.getenv("PREMIUM_TOTAL_STORAGE_GB", "500"))
    TOTAL_STORAGE_BYTES = TOTAL_STORAGE_GB * 1024 * 1024 * 1024
    LINK_EXPIRY_DAYS = int(os.getenv("PREMIUM_LINK_EXPIRY_DAYS", "0"))  # 0 = never

# ===== FILE SETTINGS =====
FILE_AUTO_DELETE_MINUTES = int(os.getenv("FILE_AUTO_DELETE_MINUTES", "20"))
FILE_AUTO_DELETE_SECONDS = FILE_AUTO_DELETE_MINUTES * 60
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", str(4 * 1024 * 1024 * 1024)))

# ===== SECURITY =====
RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", "20"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# ===== CATEGORIES =====
DEFAULT_CATEGORIES = [
    "🎬 Movies",
    "📄 Documents", 
    "📸 Photos",
    "🎵 Music",
    "🎮 Games",
    "📚 Books",
    "💾 Software",
    "📹 Videos",
    "🗂️ Others"
]

# ===== MESSAGES =====

WELCOME_MESSAGE = f"""
🎉 **Welcome to {BOT_NAME}!**

📦 **Share files securely with advanced features!**

━━━━━━━━━━━━━━━━━━━━━
🆓 **FREE TIER** - Everyone!
━━━━━━━━━━━━━━━━━━━━━
✅ Upload files & create links
✅ 20 files per link
✅ 10 active links
✅ 2GB max file size
✅ 50GB total storage
✅ Basic analytics
✅ Auto-delete protection

━━━━━━━━━━━━━━━━━━━━━
💎 **PREMIUM FEATURES** - Coming Soon!
━━━━━━━━━━━━━━━━━━━━━
🔒 Password protection
📊 Advanced analytics
♾️ Unlimited files & links
⏰ Link scheduling
👥 User whitelisting
📥 QR code generation
🎨 Custom categories
...and much more!

━━━━━━━━━━━━━━━━━━━━━
📱 **QUICK START:**
━━━━━━━━━━━━━━━━━━━━━

/upload - Upload files & create link
/mylinks - View your links
/help - Get help
/settings - Configure preferences

Made with ❤️ by {BRAND_NAME}
"""

HELP_MESSAGE = f"""
📚 **{BOT_NAME} - Help Guide**

━━━━━━━━━━━━━━━━━━━━━
📤 **FILE MANAGEMENT**
━━━━━━━━━━━━━━━━━━━━━

/upload - Start uploading files
  → Send files one by one
  → Use /done when finished
  → Or /cancel to abort

/mylinks - View all your links
  → See stats & details
  → Pagination support
  → Filter by category

/delete - Delete a link
  → Removes link permanently
  → Frees up storage space

━━━━━━━━━━━━━━━━━━━━━
🔗 **LINK OPERATIONS**
━━━━━━━━━━━━━━━━━━━━━

/getlink - Download files from link
  → Just send or type the link
  → Auto-detects Share-box links

/linkinfo - Get link details
  → File count & sizes
  → Download stats
  → Creation date

/add - Add files to existing link
  → Choose link to modify
  → Upload more files
  → Use /done to complete

━━━━━━━━━━━━━━━━━━━━━
⚙️ **SETTINGS & TOOLS**
━━━━━━━━━━━━━━━━━━━━━

/settings - Configure bot
  → Language preferences
  → Notification settings
  → Default categories

/stats - Your usage statistics
  → Storage used
  → Links created
  → Total downloads

/referral - Get referral link
  → Earn premium access
  → Share with friends

━━━━━━━━━━━━━━━━━━━━━
💎 **PREMIUM (Coming Soon)**
━━━━━━━━━━━━━━━━━━━━━

/qrcode - Generate QR codes
/schedule - Schedule links
/analytics - Advanced stats
/password - Set link password
/whitelist - Restrict access

━━━━━━━━━━━━━━━━━━━━━

Need support? Contact: {BRAND_NAME}
Bot Version: 1.0.0
"""

UPLOAD_START_MESSAGE = """
📤 **Upload Mode Activated!**

🎯 **How to upload:**

1️⃣ Send me your files (one by one)
   • Documents, Photos, Videos, Audio
   • Max 2GB per file (Free tier)
   • Up to 20 files per link

2️⃣ When done, use /done to create link

3️⃣ Or use /cancel to abort

━━━━━━━━━━━━━━━━━━━━━
📊 **Optional Settings:**

After /done, you can add:
• **Category** - Organize your files
• **Custom name** - Easy identification
• 💎 **Password** - Premium only
• 💎 **Expiry** - Premium only

━━━━━━━━━━━━━━━━━━━━━

✨ **Ready! Send your first file...**
"""

LINK_GENERATED_SUCCESS = """
✅ **Link Created Successfully!**

🔗 **Your Unique Link:**
`{link}`

━━━━━━━━━━━━━━━━━━━━━
📊 **Link Details:**
━━━━━━━━━━━━━━━━━━━━━

📁 Files: {file_count}
📦 Total Size: {total_size}
🏷️ Category: {category}
⏰ Created: {created_at}
📅 Expires: {expires_at}
📥 Downloads: 0

━━━━━━━━━━━━━━━━━━━━━

📤 **Share this link!**
Anyone can access files instantly!

💡 Manage: /mylinks
🗑️ Delete: /delete
"""

FILE_SENT_MESSAGE = """
📁 **File from {brand}**

━━━━━━━━━━━━━━━━━━━━━

📌 **Name:** `{filename}`
📦 **Size:** {filesize}
🏷️ **Category:** {category}

━━━━━━━━━━━━━━━━━━━━━
⚠️ **AUTO-DELETE WARNING**
━━━━━━━━━━━━━━━━━━━━━

⏰ This file will be deleted in {time_left}!
💾 Please save immediately!

━━━━━━━━━━━━━━━━━━━━━

Powered by {brand}
"""

STATS_MESSAGE = """
📊 **Your Statistics**

━━━━━━━━━━━━━━━━━━━━━
👤 **Account Info**
━━━━━━━━━━━━━━━━━━━━━

🎭 Username: @{username}
💳 Plan: {plan}
📅 Member Since: {joined_date}

━━━━━━━━━━━━━━━━━━━━━
📦 **Storage Usage**
━━━━━━━━━━━━━━━━━━━━━

💾 Used: {storage_used} / {storage_limit}
📊 Progress: {storage_percentage}%

{storage_bar}

━━━━━━━━━━━━━━━━━━━━━
🔗 **Links Statistics**
━━━━━━━━━━━━━━━━━━━━━

📌 Active Links: {active_links} / {max_links}
📥 Total Downloads: {total_downloads}
👁️ Total Views: {total_views}

━━━━━━━━━━━━━━━━━━━━━
🎯 **Popular Categories**
━━━━━━━━━━━━━━━━━━━━━

{popular_categories}

━━━━━━━━━━━━━━━━━━━━━

💡 Want more? Upgrade to Premium! 💎
"""

# ===== ADMIN MESSAGES =====

ADMIN_STATS_MESSAGE = """
👨‍💼 **Admin Dashboard**

━━━━━━━━━━━━━━━━━━━━━
📊 **Bot Statistics**
━━━━━━━━━━━━━━━━━━━━━

👥 Total Users: {total_users}
🆓 Free Users: {free_users}
💎 Premium Users: {premium_users}

🔗 Total Links: {total_links}
📁 Total Files: {total_files}
💾 Storage Used: {total_storage}

📥 Total Downloads: {total_downloads}
👁️ Total Views: {total_views}

━━━━━━━━━━━━━━━━━━━━━
📈 **Today's Activity**
━━━━━━━━━━━━━━━━━━━━━

🆕 New Users: {new_users_today}
📤 Links Created: {links_created_today}
📥 Downloads: {downloads_today}

━━━━━━━━━━━━━━━━━━━━━
🔥 **Top Users**
━━━━━━━━━━━━━━━━━━━━━

{top_users}

━━━━━━━━━━━━━━━━━━━━━

Version: 1.0.0 | Uptime: {uptime}
"""

# Validate configuration
def validate_config():
    """Validate required configuration"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is required")
    
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS is required")
    
    if not MONGO_URI:
        errors.append("MONGO_URI is required")
    
    if PRIMARY_CHANNEL == 0:
        errors.append("PRIMARY_CHANNEL is required")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True

if __name__ == "__main__":
    try:
        validate_config()
        print("✅ Configuration validated successfully!")
        print(f"Bot Name: {BOT_NAME}")
        print(f"Admins: {len(ADMIN_IDS)}")
        print(f"Storage Channels: {len([c for c in STORAGE_CHANNELS if c != 0])}")
    except ValueError as e:
        print(f"❌ {e}")
