"""
Share-box by Univora - User Command Handlers
Advanced user-facing commands with modern UI
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import asyncio
import config
from database import db
from utils.helpers import (
    user_check, format_file_size, format_datetime, format_expiry_date,
    extract_link_id_from_text, generate_bot_link, get_file_emoji,
    format_time_remaining, format_user_stats
)

# ==================== START & HELP COMMANDS ====================

@user_check
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and deep links"""
    
    user = update.effective_user
    user_id = user.id
    
    # Log event
    db.log_event("start_command", user_id=user_id)
    
    # Check if there's a deep link parameter (link ID)
    if context.args:
        link_id = context.args[0]
        
        # Save link_id for password verification
        context.user_data['pending_link_id'] = link_id
        
        # Let handle_file_request process it
        await handle_file_request(update, context, link_id)
        return
    
    # Welcome message
    keyboard = [
        [
            InlineKeyboardButton("📤 Upload Files", callback_data="menu_upload"),
            InlineKeyboardButton("🔗 My Links", callback_data="menu_mylinks")
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="menu_stats"),
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
        ],
        [
            InlineKeyboardButton("💎 Upgrade Premium", callback_data="menu_upgrade"),
            InlineKeyboardButton("❓ Help", callback_data="menu_help")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        config.WELCOME_MESSAGE,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

@user_check  
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    
    keyboard = [
        [
            InlineKeyboardButton("📤 Start Upload", callback_data="menu_upload"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        config.HELP_MESSAGE,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== FILE REQUEST & DOWNLOAD ====================

async def handle_file_request(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: str):
    """Handle file download request from link"""
    
    user_id = update.effective_user.id
    
    # Get link from database
    link = db.get_link(link_id)
    
    if not link:
        await update.message.reply_text(
            "❌ **Link Not Found!**\n\n"
            "This link doesn't exist or has been deleted.\n\n"
            "🔍 Possible reasons:\n"
            "• Link was deleted by owner\n"
            "• Link has expired\n"
            "• Invalid link ID\n\n"
            "💡 Contact link creator for help."
        )
        return
    
    # Increment views
    db.increment_link_views(link_id)
    db.log_event("link_viewed", user_id=user_id, link_id=link_id)
    
    # Check password protection
    if link.get("password"):
        # Check if password already verified
        if context.user_data.get(f'password_verified_{link_id}'):
            # Password already verified, proceed to download
            pass
        else:
            # Ask for password
            await update.message.reply_text(
                "🔒 **Password Protected Link!**\n\n"
                f"🏷️ **Link:** `{link.get('link_name', link_id)}`\n"
                f"📁 **Files:** {len(link['files'])}\n"
                f"📦 **Size:** {format_file_size(link.get('total_size', 0))}\n\n"
                "🔑 **Please send the password to access files:**",
                parse_mode="Markdown"
            )
            
            # Store pending link ID for password verification
            context.user_data['password_pending_link'] = link_id
            return
    
    # Send link info first
    info_message = f"""
📦 **Link Information**

━━━━━━━━━━━━━━━━━━━━━
🔗 **Link Details:**
━━━━━━━━━━━━━━━━━━━━━

🏷️ **Name:** {link.get('link_name', 'Untitled')}
🗂️ **Category:** {link.get('category', 'Others')}
📁 **Files:** {len(link['files'])}
📦 **Total Size:** {format_file_size(link.get('total_size', 0))}
{"🔒 **Password:** Protected" if link.get('password') else "🔓 **Access:** Public"}

━━━━━━━━━━━━━━━━━━━━━
📊 **Statistics:**
━━━━━━━━━━━━━━━━━━━━━

📥 **Downloads:** {link.get('downloads', 0)}
👁️ **Views:** {link.get('views', 0)}
⏰ **Created:** {format_datetime(link.get('created_at'))}
📅 **Expires:** {format_expiry_date(link.get('expires_at'))}

━━━━━━━━━━━━━━━━━━━━━

⬇️ **Downloading files...**
"""
    
    await update.message.reply_text(info_message, parse_mode="Markdown")
    
    # Send files
    files = link.get('files', [])
    sent_messages = []
    
    for idx, file_data in enumerate(files, 1):
        try:
            # Progress indicator
            progress_msg = await update.message.reply_text(
                f"📤 Sending file {idx}/{len(files)}...",
                parse_mode="Markdown"
            )
            
            # Send file from channel
            file_message = await context.bot.copy_message(
                chat_id=update.effective_chat.id,
                from_chat_id=config.PRIMARY_CHANNEL,
                message_id=file_data['message_id'],
                caption=config.FILE_SENT_MESSAGE.format(
                    brand=config.BRAND_NAME,
                    filename=file_data['file_name'],
                    filesize=format_file_size(file_data['file_size']),
                    category=link.get('category', 'Others'),
                    time_left=format_time_remaining(config.FILE_AUTO_DELETE_SECONDS)
                ),
                parse_mode="Markdown"
            )
            
            sent_messages.append(file_message.message_id)
            
            # Delete progress message
            await progress_msg.delete()
            
        except Exception as e:
            print(f"Error sending file: {e}")
            await update.message.reply_text(
                f"❌ **Error sending file {idx}**\n\n"
                f"📁 **File:** `{file_data['file_name']}`\n"
                f"⚠️ **Error:** File may have been deleted from storage.\n\n"
                f"💡 Contact link owner: @{link.get('admin_username', 'unknown')}"
            )
    
    # Increment download counter
    db.increment_link_downloads(link_id)
    db.log_event("files_downloaded", user_id=user_id, link_id=link_id, metadata={"file_count": len(files)})
    
    # Success message
    await update.message.reply_text(
        f"✅ **Download Complete!**\n\n"
        f"📥 **{len(files)} files sent successfully!**\n\n"
        f"⚠️ **AUTO-DELETE WARNING:**\n"
        f"Files will be deleted in **{config.FILE_AUTO_DELETE_MINUTES} minutes**!\n"
        f"💾 Please save them immediately!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Powered by {config.BRAND_NAME}\n"
        f"Create your own links: {config.BOT_USERNAME}",
        parse_mode="Markdown"
    )
    
    # Schedule auto-deletion
    if sent_messages:
        await schedule_file_deletion(context, update.effective_chat.id, sent_messages)

async def schedule_file_deletion(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_ids: list):
    """Schedule auto-deletion of files - SILENT deletion"""
    
    # Wait for configured time
    await asyncio.sleep(config.FILE_AUTO_DELETE_SECONDS)
    
    # Delete messages silently
    for msg_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            print(f"Failed to delete message {msg_id}: {e}")

# ==================== LINK DETECTION ====================

@user_check
async def detect_and_handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-detect bot links in text messages + Handle password verification"""
    
    text = update.message.text
    user_id = update.effective_user.id
    
    # Check if user is waiting to send password
    if 'password_pending_link' in context.user_data:
        link_id = context.user_data['password_pending_link']
        link = db.get_link(link_id)
        
        if link and link.get('password'):
            # Verify password
            if text.strip() == link['password']:
                # Password correct
                context.user_data[f'password_verified_{link_id}'] = True
                del context.user_data['password_pending_link']
                
                await update.message.reply_text(
                    "✅ **Password Correct!**\n\n"
                    "🔓 Access granted. Downloading files...",
                    parse_mode="Markdown"
                )
                
                # Proceed with file download
                await handle_file_request(update, context, link_id)
            else:
                # Wrong password
                await update.message.reply_text(
                    "❌ **Wrong Password!**\n\n"
                    "🔑 Please try again or contact link owner.",
                    parse_mode="Markdown"
                )
        
        return
    
    # Try to extract link ID from text
    link_id = extract_link_id_from_text(text)
    
    if link_id:
        # Store for potential password verification
        context.user_data['pending_link_id'] = link_id
        
        await handle_file_request(update, context, link_id)

# ==================== GET LINK COMMAND ====================

@user_check
async def getlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /getlink command"""
    
    await update.message.reply_text(
        "🔗 **Get Files from Link**\n\n"
        "Send me a Share-box link to download files!\n\n"
        "📤 **Supported formats:**\n"
        "• Full link: `https://t.me/bot?start=LINKID`\n"
        "• Link ID: `LINKID`\n\n"
        "Just send the link in your next message!",
        parse_mode="Markdown"
    )

# ==================== STATISTICS COMMAND ====================

@user_check
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics"""
    
    user_id = update.effective_user.id
    
    # Get formatted stats
    stats_message = format_user_stats(user_id)
    
    keyboard = [
        [
            InlineKeyboardButton("🔗 My Links", callback_data="menu_mylinks"),
            InlineKeyboardButton("💎 Upgrade", callback_data="menu_upgrade")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        stats_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== SETTINGS COMMAND ====================

@user_check
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user settings"""
    
    user = db.get_user(update.effective_user.id)
    settings = user.get('settings', {})
    
    message = f"""
⚙️ **Your Settings**

━━━━━━━━━━━━━━━━━━━━━
📱 **Preferences:**
━━━━━━━━━━━━━━━━━━━━━

🌐 **Language:** {settings.get('language', 'en').upper()}
🔔 **Notifications:** {'✅ Enabled' if settings.get('notifications', True) else '❌ Disabled'}
🗂️ **Default Category:** {settings.get('default_category', '🗂️ Others')}
🗑️ **Auto-delete Files:** {'✅ Yes' if settings.get('auto_delete_files', True) else '❌ No'}

━━━━━━━━━━━━━━━━━━━━━

💡 More settings coming soon!
"""
    
    keyboard = [
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== REFERRAL COMMAND ====================

@user_check
async def referral_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral info"""
    
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    referral_code = user.get('referral_code', 'N/A')
    referral_stats = db.get_referral_stats(user_id)
    
    bot_username = config.BOT_USERNAME.replace('@', '')
    referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}"
    
    message = f"""
🎁 **Referral Program**

━━━━━━━━━━━━━━━━━━━━━
🔗 **Your Referral Link:**
━━━━━━━━━━━━━━━━━━━━━

`{referral_link}`

━━━━━━━━━━━━━━━━━━━━━
📊 **Your Referral Stats:**
━━━━━━━━━━━━━━━━━━━━━

👥 **Total Referrals:** {referral_stats.get('total_referrals', 0)}
✅ **Completed:** {referral_stats.get('completed_referrals', 0)}
⏳ **Pending:** {referral_stats.get('pending_referrals', 0)}

━━━━━━━━━━━━━━━━━━━━━
🎁 **Rewards:**
━━━━━━━━━━━━━━━━━━━━━

Refer 5 friends → 1 month premium FREE! 💎
Refer 10 friends → 3 months premium FREE! 🎖️
Refer 25 friends → 1 year premium FREE! 👑

━━━━━━━━━━━━━━━━━━━━━

📤 Share your link and earn rewards!
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={referral_link}&text=Join Share-box - Best file sharing bot!")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== UPGRADE COMMAND ====================

@user_check
async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium upgrade options"""
    
    message = """
💎 **Upgrade to Premium**

━━━━━━━━━━━━━━━━━━━━━
🆓 **FREE vs 💎 PREMIUM**
━━━━━━━━━━━━━━━━━━━━━

**Files per Link:**
🆓 Max 20 → 💎 Unlimited

**File Size:**
🆓 2GB → 💎 4GB

**Active Links:**
🆓 Max 10 → 💎 Unlimited

**Storage:**
🆓 50GB → 💎 500GB

**Link Expiry:**
🆓 30 days → 💎 Never

━━━━━━━━━━━━━━━━━━━━━
✨ **Premium Exclusive Features:**
━━━━━━━━━━━━━━━━━━━━━

🔒 Password protection
📊 Advanced analytics
📥 QR code generation
⏰ Link scheduling
👥 User whitelisting
🎨 Custom categories
🚀 Priority downloads
💾 Bulk operations
📈 Detailed insights
...and much more!

━━━━━━━━━━━━━━━━━━━━━
💰 **Pricing:**
━━━━━━━━━━━━━━━━━━━━━

📅 Monthly: $4.99/month
🎖️ Yearly: $49.99/year (Save 17%!)
👑 Lifetime: $199.99 (One-time)

━━━━━━━━━━━━━━━━━━━━━

⚠️ **Payment integration coming soon!**
Stay tuned for launch! 🎉
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🎁 Get Free Premium", callback_data="menu_referral"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== UNKNOWN COMMAND ====================

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    
    await update.message.reply_text(
        "❓ **Unknown Command!**\n\n"
        "I don't understand this command.\n\n"
        "💡 Use /help to see all available commands.\n"
        "🏠 Or use /start to see main menu.",
        parse_mode="Markdown"
    )
