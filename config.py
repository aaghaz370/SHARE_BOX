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
BOT_USERNAME = os.getenv("BOT_USERNAME", "@SHARE_BOX_BOT")
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
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL", "")

# ===== FEATURE FLAGS =====
ENABLE_PREMIUM_FEATURES = os.getenv("ENABLE_PREMIUM_FEATURES", "true").lower() == "true"
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
ENABLE_REFERRALS = os.getenv("ENABLE_REFERRALS", "true").lower() == "true"
ENABLE_QR_CODES = os.getenv("ENABLE_QR_CODES", "true").lower() == "true"

# ===== PLAN TYPES =====
class PlanTypes:
    FREE = "free"
    DAILY = "daily"
    MONTHLY = "monthly"
    BIMONTHLY = "bimonthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"

# ===== PLANS CONFIGURATION =====
PLANS = {
    PlanTypes.FREE: {
        "name": "Free Tier",
        "price": 0,
        "duration_days": 36500, # Forever
        "storage_gb": 200,
        "max_active_links": 10, # Per month
        "link_expiry_days": 60, # 2 months
        "max_files_per_link": 20,
        "max_file_size_gb": 2
    },
    PlanTypes.DAILY: {
        "name": "Daily Pass",
        "price": 40,
        "duration_days": 1,
        "storage_gb": 200,
        "max_active_links": 999999,
        "link_expiry_days": 180, # 6 months
        "max_files_per_link": 999999,
        "max_file_size_gb": 4
    },
    PlanTypes.MONTHLY: {
        "name": "Monthly Starter",
        "price": 299,
        "duration_days": 30,
        "storage_gb": 999999, 
        "max_active_links": 999999,
        "link_expiry_days": 240, # 8 months
        "max_files_per_link": 999999,
        "max_file_size_gb": 4
    },
    PlanTypes.BIMONTHLY: {
        "name": "Bi-Monthly Pro",
        "price": 499,
        "duration_days": 60,
        "storage_gb": 999999, 
        "max_active_links": 999999,
        "link_expiry_days": 365, # 1 Year
        "max_files_per_link": 999999,
        "max_file_size_gb": 4
    },
    PlanTypes.YEARLY: {
        "name": "Yearly Premium",
        "price": 999,
        "duration_days": 365,
        "storage_gb": 999999, 
        "max_active_links": 999999,
        "link_expiry_days": 365,
        "max_files_per_link": 999999,
        "max_file_size_gb": 4
    },
    PlanTypes.LIFETIME: {
        "name": "Lifetime Access",
        "price": 2999,
        "duration_days": 36500, # Forever
        "storage_gb": 999999, 
        "max_active_links": 999999,
        "link_expiry_days": 36500, # Forever
        "max_files_per_link": 999999,
        "max_file_size_gb": 4
    }
}

# Values in Bytes for easier calculation
for plan in PLANS.values():
    plan["storage_bytes"] = plan["storage_gb"] * 1024 * 1024 * 1024
    plan["max_file_size_bytes"] = plan["max_file_size_gb"] * 1024 * 1024 * 1024

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

/setpassword - Set link password
/protect - Prevent forwarding
/search - Search your links
/qrcode - Generate QR codes
/setname - Rename links
/settings - Auto-QR options

━━━━━━━━━━━━━━━━━━━━━

Need support? Contact: {BRAND_NAME}
Bot Version: 1.0.0
"""

UPLOAD_START_MESSAGE = """
📤 **Upload Mode Activated!**

🎯 **How to upload:**

1️⃣ Send me your files (one by one)
   • Documents, Photos, Videos, Audio
   • Max 2GB (Free) | 4GB (Premium)
   • Max 20 files (Free) | Unlimited (Premium)

2️⃣ When done, use /done to create link

3️⃣ Or use /cancel to abort

━━━━━━━━━━━━━━━━━━━━━
📊 **Optional Settings:**

After /done, you can add:
• **Category** - Organize your files
• **Custom name** - Easy identification (Premium)
• 💎 **Password** - Premium only
• 💎 **Auto-QR** - Premium only

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
