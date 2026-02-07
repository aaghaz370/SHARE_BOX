"""
Share-box by Univora - User Command Handlers
Advanced user-facing commands with modern UI
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.helpers import escape_markdown
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import asyncio
import io
import qrcode
import config
from database import db
import asyncio
from utils.helpers import (
    user_check, format_file_size, format_datetime, format_expiry_date,
    extract_link_id_from_text, generate_bot_link, get_file_emoji,
    format_time_remaining, format_user_stats, update_user_menu
)

# ==================== START & HELP COMMANDS ====================

@user_check
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command and deep links"""
    
    user = update.effective_user
    user_id = user.id
    
    # Log event
    db.log_event("start_command", user_id=user_id)
    
    # Update command menu based on plan
    await update_user_menu(context.bot, user_id)
    
    # Check if there's a deep link parameter (link ID)
    if context.args:
        arg = context.args[0]
        
        # Check for referral
        if arg.startswith("ref_"):
            ref_code = arg.replace("ref_", "")
            if db.apply_referral(user_id, ref_code):
                # Check rewards for referrer
                referrer_user = db.users.find_one({"referral_code": ref_code})
                if referrer_user:
                    granted, plan_name, days = db.check_referral_milestones(referrer_user["user_id"])
                    if granted:
                        try:
                            await context.bot.send_message(
                                chat_id=referrer_user["user_id"],
                                text=f"🎉 **CONGRATULATIONS!**\n\nYou hit a Referral Milestone!\n💎 **Reward Unlocked:** {plan_name}\n\nYour premium plan has been activated automatically! 🚀",
                                parse_mode="Markdown"
                            )
                        except:
                            pass
            
            # Continue to welcome message
        
        else:
            # Assume it's a link ID
            link_id = arg
            
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
    
    await update.effective_message.reply_text(
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
    
    await update.effective_message.reply_text(
        config.HELP_MESSAGE,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== FILE REQUEST & DOWNLOAD ====================

async def handle_file_request(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: str):
    """Handle file download request from link"""
    
    user_id = update.effective_user.id
    
    # Get link from database (ASYNC)
    link = await asyncio.to_thread(db.get_link, link_id)
    
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

🏷️ **Name:** {escape_markdown(link.get('link_name', 'Untitled'), version=1)}
🗂️ **Category:** {escape_markdown(link.get('category', 'Others'), version=1)}
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
    # Reset stop flag
    if 'stop_sending' in context.user_data: del context.user_data['stop_sending']
    
    files = link.get('files', [])
    
    # Start background sending task
    asyncio.create_task(send_files_async(
        context, 
        update.effective_chat.id, 
        user_id, 
        link_id, 
        files, 
        link
    ))

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

async def send_files_async(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, link_id: str, files: list, link: dict):
    """Background task to send files"""
    sent_messages = []
    
    for idx, file_data in enumerate(files, 1):
        # Stop check
        if context.user_data.get('stop_sending'):
            await context.bot.send_message(chat_id=chat_id, text="🛑 **Stopped by user!**", parse_mode="Markdown")
            if 'stop_sending' in context.user_data: del context.user_data['stop_sending']
            return
            
        try:
            # Progress
            progress_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=f"📤 Sending file {idx}/{len(files)}...",
                parse_mode="Markdown"
            )
            
            # Send file (Redundant Channel Strategy)
            sent = False
            last_error = None
            
            # Prepare sources: Primary + Backups
            sources = [{"channel_id": config.PRIMARY_CHANNEL, "message_id": file_data["message_id"]}]
            if "backup_messages" in file_data:
                sources.extend([b for b in file_data["backup_messages"] if b["channel_id"] != config.PRIMARY_CHANNEL])
            
            file_message = None
            
            for source in sources:
                try:
                    file_message = await context.bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=source["channel_id"],
                        message_id=source["message_id"],
                        caption=config.FILE_SENT_MESSAGE.format(
                            brand=config.BRAND_NAME,
                            filename=escape_markdown(file_data['file_name'], version=1),
                            filesize=format_file_size(file_data['file_size']),
                            category=link.get('category', 'Others'),
                            time_left=format_time_remaining(config.FILE_AUTO_DELETE_SECONDS)
                        ),
                        parse_mode="Markdown",
                        protect_content=link.get('protect_content', False)
                    )
                    sent = True
                    break # Success!
                except Exception as e:
                    last_error = e
                    continue # Try next source
            
            if not sent:
                raise last_error or Exception("All channels failed")
            
            sent_messages.append(file_message.message_id)
            await progress_msg.delete()
            
        except Exception as e:
            print(f"Error sending file: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ **Error sending file {idx}**\n\n⚠️ Error: Content unavailable.\n💡 Contact owner.",
                parse_mode="Markdown"
            )

    # Success
    db.increment_link_downloads(link_id)
    db.log_event("files_downloaded", user_id=user_id, link_id=link_id, metadata={"file_count": len(files)})
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ **Download Complete!**\n\n"
             f"📥 **{len(files)} files sent successfully!**\n\n"
             f"⚠️ **AUTO-DELETE WARNING:**\n"
             f"Files will be deleted in **{config.FILE_AUTO_DELETE_MINUTES} minutes**!\n"
             f"💾 Please save them immediately!\n\n"
             f"━━━━━━━━━━━━━━━━━━━━━\n\n"
             f"Powered by Share Box\n"
             f"Create your own links: @SHARE_BOX_BOT",
        parse_mode="Markdown"
    )
    
    if sent_messages:
        asyncio.create_task(schedule_file_deletion(context, chat_id, sent_messages))

# ==================== LINK DETECTION ====================

@user_check
async def detect_and_handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-detect bot links in text messages + Handle password verification + Name Input"""
    
    text = update.message.text
    user_id = update.effective_user.id
    
    # 1. Check for Link Naming (Priority)
    if context.user_data.get('awaiting_link_name'):
        name = text.strip()
        
        # Handle skip
        if name == "/skip":
            name = None
        elif name.startswith("/"):
            return # Ignore other commands
            
        # Validation
        if name and len(name) > 50:
            await update.message.reply_text("❌ Name too long! Max 50 chars.\nTry again or /skip.")
            return
            
        context.user_data['link_name'] = name
        context.user_data['awaiting_link_name'] = False
        
        # Proceed to Category
        from handlers.admin import ask_link_category
        await ask_link_category(update, context)
        return
    
    # 2. Check if user is waiting to send password
    if 'password_pending_link' in context.user_data:
        link_id = context.user_data['password_pending_link']
        link = await asyncio.to_thread(db.get_link, link_id)
        
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
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            stats_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            stats_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# ==================== SETTINGS COMMAND ====================

@user_check
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show and manage user settings"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    settings = user.get('settings', {})
    
    # Defaults
    notif = settings.get('notifications', True)
    auto_del = settings.get('auto_delete_files', True)
    lang = settings.get('language', 'en')
    def_cat = settings.get('default_category', '🗂️ Others')
    
    # Symbols
    s_notif = "✅ ON" if notif else "❌ OFF"
    s_auto = "✅ ON" if auto_del else "❌ OFF"
    
    message = f"""
⚙️ **SETTINGS PANEL**

Manage your bot preferences here.

━━━━━━━━━━━━━━━━━━━━━
🔔 **Notifications:** {s_notif}
_Receive alerts about uploads/links._

🗑️ **Auto-Delete Files:** {s_auto}
_Automatically delete files after time limit to save space._

🗂️ **Default Category:** `{def_cat}`
_Category assigned to new links by default._

🌐 **Language:** `{lang.upper()}`
━━━━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = [
        [
            InlineKeyboardButton(f"🔔 Toggle Notifications", callback_data="set_toggle_notif"),
            InlineKeyboardButton(f"🗑️ Toggle Auto-Delete", callback_data="set_toggle_autodel")
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
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

Refer 10 Friends → **Monthly Starter** (1 Month) 💎
Refer 30 Friends → **Bi-Monthly Pro** (2 Months) 🌟
Refer 100 Friends → **Yearly Premium** (1 Year) 👑

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
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# ==================== UPGRADE COMMAND ====================

@user_check
async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium upgrade options"""
    
    # Get admin contact
    admin_id = config.ADMIN_IDS[0] if config.ADMIN_IDS else None
    
    message = f"""
💎 **PREMIUM UPGRADE PLANS**

Unlock the full power of {config.BOT_NAME}!

━━━━━━━━━━━━━━━━━━━━━
1️⃣ **DAILY PASS** - ₹40
⏳ **Validity:** 24 Hours
🔗 **Links:** Unlimited
📦 **User Storage:** 200 GB
🗓️ **Link Expiry:** 6 Months

2️⃣ **MONTHLY STARTER** - ₹299
⏳ **Validity:** 30 Days
🔗 **Links:** Unlimited
📦 **User Storage:** Unlimited
🗓️ **Link Expiry:** 8 Months

3️⃣ **BI-MONTHLY PRO** - ₹499
⏳ **Validity:** 60 Days
🔗 **Links:** Unlimited
📦 **User Storage:** Unlimited
🗓️ **Link Expiry:** 1 Year

━━━━━━━━━━━━━━━━━━━━━
👑 **LIFETIME PLAN**
Special access granted by Owner.
**Unlimited Everything. Never Expires.**

━━━━━━━━━━━━━━━━━━━━━
💳 **HOW TO BUY:**
Premium plans are activated manually by the Admin.
Click below to contact for payment details.
"""
    
    keyboard = [
        [
            InlineKeyboardButton("👤 Contact Admin to Buy", url=f"tg://user?id={admin_id}" if admin_id else "https://t.me/UnivoraSupport")
        ],
        [
            InlineKeyboardButton("🎁 Free Premium (Referral)", callback_data="menu_referral"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# ==================== UNKNOWN COMMAND ====================

@user_check
async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /skip command"""
    # Check naming state
    if context.user_data.get('awaiting_link_name'):
        context.user_data['link_name'] = None
        context.user_data['awaiting_link_name'] = False
        
        # Proceed
        from handlers.admin import ask_link_category
        await ask_link_category(update, context)
        return
        
    await update.message.reply_text("ℹ️ **Nothing to skip!**", parse_mode="Markdown")

@user_check
async def checklink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user to send link for checking"""
    await update.message.reply_text(
        "🔗 **Link Checker**\n\n"
        "Send your Share Box link or ID below to check status and access files!",
        parse_mode="Markdown"
    )

@user_check
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command"""
    context.user_data['stop_sending'] = True
    await update.message.reply_text("🛑 **Stop Requested!**\n\nStopping file delivery...", parse_mode="Markdown")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    
    await update.message.reply_text(
        "❓ **Unknown Command!**\n\n"
        "I don't understand this command.\n\n"
        "💡 Use /help to see all available commands.\n"
        "🏠 Or use /start to see main menu.",
        parse_mode="Markdown"
    )

# ==================== LINK NAMING ====================

@user_check
async def handle_link_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom link naming"""
    user_id = update.effective_user.id
    
    # Check if waiting for name
    if not context.user_data.get('awaiting_link_name'):
        return
        
    name = update.message.text
    
    # Handle /skip command via text filter logic
    if name == "/skip":
        name = None
    elif name.startswith("/"):
        return
        
    # Validation
    if name and len(name) > 50:
        await update.message.reply_text("❌ Name too long! Max 50 chars.\nTry again or /skip.")
        return
        
    # Save name
    context.user_data['link_name'] = name
    context.user_data['awaiting_link_name'] = False
    
    # Proceed to Category Selection
    from handlers.admin import ask_link_category
    await ask_link_category(update, context)
