"""
Share-box by Univora - Admin Command Handlers  
Advanced admin commands for file & link management
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import config
from database import db
from utils.helpers import (
    admin_only, user_check, format_file_size, format_datetime,
    get_file_info, generate_bot_link, calculate_total_size,
    get_file_emoji, create_pagination_data, truncate_text,
    format_expiry_date, check_upload_limit, check_link_creation_limit,
    sanitize_filename, premium_only
)
from utils.qr_generator import generate_qr_code, generate_fancy_qr_code

# Store pending files temporarily
pending_files = {}
pending_add_files = {}

# ==================== UPLOAD COMMAND ====================

@user_check
async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start file upload mode"""
    
    user_id = update.effective_user.id
    
    # Check if user can create new link
    limit_check = check_link_creation_limit(user_id)
    if not limit_check["allowed"]:
        await update.message.reply_text(
            f"🚫 **Upload Not Allowed!**\n\n"
            f"❌ {limit_check['reason']}",
            parse_mode="Markdown"
        )
        return
    
    # Initialize pending files
    pending_files[user_id] = []
    
    # Dynamic Upload Start Message
    plan = db.get_plan_details(user_id)
    plan_name = plan.get("name", "Free Tier").upper()
    is_premium = db.is_user_premium(user_id)
    
    max_size = format_file_size(plan.get("max_file_size_bytes", 2*1024*1024*1024))
    max_files = plan.get("max_files_per_link", 20)
    
    # Upsell Check
    upsell = ""
    if not is_premium:
        upsell = "\n💡 **Upgrade to Premium:**\n• 4GB Uploads 🚀\n• Unlimited Files ♾️\n• Password Protection 🔒\n• Custom Names ✏️\n"
    
    msg = f"""
📤 **UPLOAD MODE ACTIVATED!**
{upsell}
👤 **Plan Status:** `{plan_name}`
📦 **Your Limits:**
• Max Size: `{max_size}` per file
• Max Files: `{'Unlimited' if max_files > 9000 else max_files}` per link

🎯 **How to Start?**
1️⃣ **Send your Files** (Documents, Photos, Videos)
2️⃣ **Type /done** when finished to create link
3️⃣ **Type /cancel** to abort

✨ **Optional Features (After Upload):**
• Set Category (Create folders)
• {'✅' if is_premium else '🔒'} Set Password (Premium)
• {'✅' if is_premium else '🔒'} Auto-QR Code (Premium)

🚀 **Send your first file now!**
"""

    await update.effective_message.reply_text(msg, parse_mode="Markdown")
    
    db.log_event("upload_started", user_id=user_id)

# ==================== FILE UPLOAD HANDLER ====================

@user_check
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file uploads"""
    
    user_id = update.effective_user.id
    message = update.message
    
    # Check if user is in upload or add mode
    is_upload_mode = user_id in pending_files
    is_add_mode = user_id in pending_add_files
    
    if not is_upload_mode and not is_add_mode:
        # Not in any upload mode
        await message.reply_text(
            "📤 **Upload a file?**\n\n"
            "To upload files and create a link:\n"
            "1. Use /upload to start\n"
            "2. Send your files\n"
            "3. Use /done when finished\n\n"
            "💡 Or use /add to add files to existing link!",
            parse_mode="Markdown"
        )
        return
    
    # Get file info
    file_info = get_file_info(message)
    
    if not file_info["file_id"]:
        await message.reply_text(
            "❌ **Invalid File!**\n\n"
            "Please send a valid file (Document, Photo, Video, or Audio)."
        )
        return
    
    # Sanitize filename
    file_info["file_name"] = sanitize_filename(file_info["file_name"])
    
    # Check file size limit
    # Check file size limit
    is_premium = db.is_user_premium(user_id)
    current_count = len(pending_files.get(user_id, [])) + 1
    if is_add_mode:
        current_count += len(pending_add_files.get(user_id, {}).get("files", []))
        
    limit_check = check_upload_limit(user_id, current_count, file_info["file_size"])
    
    if not limit_check["allowed"]:
        await message.reply_text(
            f"🚫 **Upload Failed!**\n\n"
            f"❌ {limit_check['reason']}",
            parse_mode="Markdown"
        )
        return
    
    # Upload to channel (TRIPLE REDUNDANCY for data persistence!)
    try:
        # Send to all 3 storage channels
        channel_messages = []
        
        for channel_id in config.STORAGE_CHANNELS:
            if channel_id == 0:
                continue
            
            try:
                # Forward to channel
                forwarded = await message.copy(chat_id=channel_id)
                channel_messages.append({
                    "channel_id": channel_id,
                    "message_id": forwarded.message_id
                })
            except Exception as e:
                print(f"Warning: Failed to upload to channel {channel_id}: {e}")
        
        if not channel_messages:
            raise Exception("Failed to upload to any storage channel")
        
        # Use primary channel message ID
        primary_message_id = channel_messages[0]["message_id"]
        
        # Store file data  
        file_data = {
            "message_id": primary_message_id,
            "file_id": file_info["file_id"],
            "file_name": file_info["file_name"],
            "file_size": file_info["file_size"],
            "file_type": file_info["file_type"],
            "mime_type": file_info["mime_type"],
            "backup_messages": channel_messages  # Store all backups
        }
        
        # Add to pending files
        if is_upload_mode:
            pending_files[user_id].append(file_data)
            current_files = pending_files[user_id]
        else:  # add mode
            pending_add_files[user_id]["files"].append(file_data)
            current_files = pending_add_files[user_id]["files"]
        
        # Check file count limit
        plan = db.get_plan_details(user_id)
        max_files = plan.get("max_files_per_link", 20)
        
        # Success message with progress
        emoji = get_file_emoji(file_info["file_type"])
        total_size = calculate_total_size(current_files)
        
        status_message = f"""
✅ **File Added!**
`{truncate_text(file_info['file_name'], 45)}`
📦 **Size:** {format_file_size(file_info['file_size'])}

📊 **Session:** {len(current_files)} Files • {format_file_size(total_size)} Total

📤 _Send next file or use /done_
"""
        
        await message.reply_text(status_message, parse_mode="Markdown")
        
        db.log_event("file_uploaded", user_id=user_id, metadata={"file_type": file_info["file_type"], "file_size": file_info["file_size"]})
        
    except Exception as e:
        print(f"Upload error: {e}")
        await message.reply_text(
            f"❌ **Upload Failed!**\n\n"
            f"⚠️ Error: {str(e)}\n\n"
            f"💡 Please try again or contact admin.",
            parse_mode="Markdown"
        )

# ==================== DONE COMMAND ====================

@user_check
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish upload and generate link"""
    
    user_id = update.effective_user.id
    
    # Check upload mode
    if user_id in pending_files:
        await finish_upload(update, context)
    elif user_id in pending_add_files:
        await finish_add_files(update, context)
    else:
        await update.message.reply_text(
            "❌ **No Active Upload!**\n\n"
            "Start uploading with /upload first!",
            parse_mode="Markdown"
        )

async def finish_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish upload mode and ask for name"""
    user_id = update.effective_user.id
    files = pending_files.get(user_id, [])
    
    if not files:
        await update.message.reply_text(
            "❌ **No Files Uploaded!**\n\n"
            "Upload files before using /done.",
            parse_mode="Markdown"
        )
        return
    
    # Ask for Link Name
    context.user_data['awaiting_link_name'] = True
    
    await update.message.reply_text(
        f"✅ **Files Uploaded!**\n\n"
        f"✏️ **Name your Link:**\n"
        "Enter a custom name so users can identify it easily.\n"
        "Type /skip to use default name.",
        parse_mode="Markdown"
    )

async def ask_link_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for category generation"""
    user_id = update.effective_user.id
    files = pending_files.get(user_id, [])
    
    # Keyboard for categories
    keyboard = []
    row = []
    
    for idx, cat in enumerate(config.DEFAULT_CATEGORIES):
        row.append(InlineKeyboardButton(cat, callback_data=f"gen_cat_{cat}"))
        if len(row) == 2 or idx == len(config.DEFAULT_CATEGORIES) - 1:
            keyboard.append(row)
            row = []
            
    # Add skip option
    keyboard.append([InlineKeyboardButton("⏭️ Skip Category", callback_data="gen_cat_skip")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    total_size = calculate_total_size(files)
    
    await update.message.reply_text(
        f"📁 **Select Category**\n\n"
        f"You've uploaded **{len(files)} files** ({format_file_size(total_size)})\n\n"
        f"🗂️ **Choose a category for your link:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Store pending flag
    context.user_data['pending_generation'] = True

async def finish_add_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish adding files to existing link"""
    
    user_id = update.effective_user.id
    add_data = pending_add_files.get(user_id)
    
    if not add_data:
        return
    
    link_id = add_data["link_id"]
    files = add_data["files"]
    
    if not files:
        await update.message.reply_text(
            "❌ **No Files Uploaded!**\n\n"
            "Upload files before using /done.",
            parse_mode="Markdown"
        )
        return
    
    # Add files to link
    success = db.add_files_to_link(link_id, files)
    
    if success:
        link = db.get_link(link_id)
        total_files = len(link['files'])
        total_size = link.get('total_size', 0)
        bot_link = generate_bot_link(link_id)
        
        await update.message.reply_text(
            f"✅ **Files Added Successfully!**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔗 **Link:** `{bot_link}`\n\n"
            f"📁 **Total Files:** {total_files}\n"
            f"📦 **Total Size:** {format_file_size(total_size)}\n"
            f"➕ **Added:** {len(files)} new files\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )
        
        db.log_event("files_added", user_id=user_id, link_id=link_id, metadata={"files_added": len(files)})
    else:
        await update.message.reply_text(
            "❌ **Failed to Add Files!**\n\n"
            "Link may have been deleted.",
            parse_mode="Markdown"
        )
    
    # Clean up
    del pending_add_files[user_id]

# ==================== CANCEL COMMAND ====================

@user_check
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    
    user_id = update.effective_user.id
    
    was_active = False
    
    if user_id in pending_files:
        del pending_files[user_id]
        was_active = True
    
    if user_id in pending_add_files:
        del pending_add_files[user_id]
        was_active = True
    
    if 'pending_generation' in context.user_data:
        del context.user_data['pending_generation']
        was_active = True

    if 'awaiting_link_name' in context.user_data:
        del context.user_data['awaiting_link_name']
        was_active = True
        
    if 'link_name' in context.user_data:
        del context.user_data['link_name']
        was_active = True
    
    if was_active:
        await update.message.reply_text(
            "❌ **Operation Cancelled!**\n\n"
            "All pending files have been discarded.\n\n"
            "💡 Use /upload to start fresh!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "ℹ️ **No Active Operation**\n\n"
            "Nothing to cancel!",
            parse_mode="Markdown"
        )

# ==================== MY LINKS COMMAND ====================

@user_check  
async def mylinks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's links with pagination"""
    
    user_id = update.effective_user.id
    
    # Parse arguments
    category = None
    page = 1
    
    if context.args:
        for i, arg in enumerate(context.args):
            if arg.lower() == "category" and i + 1 < len(context.args):
                category = context.args[i + 1]
            elif arg.isdigit():
                page = int(arg)
    
    # Get links
    all_links = db.get_user_links(user_id, category=category, skip=0, limit=1000)
    
    if not all_links:
        message = "📭 **No Links Found!**\n\n"
        
        if category:
            message += f"You have no links in category: **{category}**\n\n"
        else:
            message += "You haven't created any links yet!\n\n"
        
        message += "💡 Use /upload to create your first link!"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        return
    
    # Paginate
    items_per_page = 5
    pagination = create_pagination_data(all_links, page, items_per_page)
    
    # Build message
    header = f"🔗 **Your Links**"
    if category:
        header += f" - {category}"
    
    header += f"\n\n📊 **Total:** {pagination['total_items']} links\n"
    header += f"📄 **Page:** {pagination['page']}/{pagination['total_pages']}\n"
    header += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Build message with inline buttons for each link
    header = f"🔗 **Your Links**"
    if category:
        header += f" - {category}"
    
    header += f"\n\n📊 **Total:** {pagination['total_items']} links\n"
    header += f"📄 **Page:** {pagination['page']}/{pagination['total_pages']}\n"
    header += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    message_text = header
    keyboard = []
    
    for idx, link in enumerate(pagination['items'], start=pagination['start_idx'] + 1):
        emoji = "💎" if link.get('is_premium_link') else "🔗"
        link_name = truncate_text(link.get('link_name', 'Untitled'), 30)
        file_count = len(link.get('files', []))
        total_size = format_file_size(link.get('total_size', 0))
        views = link.get('views', 0)
        
        # Link summary
        message_text += f"{emoji} **{idx}. {link_name}**\n"
        message_text += f"   📁 {file_count} files | 📦 {total_size} | 👁️ {views} views\n"
        
        # Direct action buttons for this link
        link_id = link['link_id']
        keyboard.append([
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_panel_{link_id}"),
            InlineKeyboardButton("ℹ️ Info", callback_data=f"linfo_{link_id}"),
            InlineKeyboardButton("📱 QR", callback_data=f"qr_{link_id}"),
            InlineKeyboardButton("🗑️", callback_data=f"confirm_del_{link_id}")
        ])
        message_text += "\n"
    
    # Navigation buttons
    nav_row = []
    if pagination['has_prev']:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"links_page_{page-1}_{category or 'all'}"))
    
    if pagination['has_next']:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"links_page_{page+1}_{category or 'all'}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Bottom menu
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Handle both command and callback query
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except Exception:
            await update.effective_message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# ==================== DELETE LINK COMMAND ====================

@user_check
async def delete_link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a link"""
    
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "🗑️ **Delete Link**\n\n"
            "**Usage:** `/delete LINK_ID`\n\n"
            "Example: `/delete AbC12XyZ`\n\n"
            "💡 Use /mylinks to see your link IDs",
            parse_mode="Markdown"
        )
        return
    
    link_id = context.args[0]
    link = db.get_link(link_id)
    
    if not link:
        await update.message.reply_text(
            "❌ **Link Not Found!**\n\n"
            "This link doesn't exist or was already deleted.",
            parse_mode="Markdown"
        )
        return
    
    # Check ownership
    if link['admin_id'] != user_id and user_id not in config.ADMIN_IDS:
        await update.message.reply_text(
            "🚫 **Access Denied!**\n\n"
            "You can only delete your own links!",
            parse_mode="Markdown"
        )
        return
    
    # Delete link
    success = db.delete_link(link_id)
    
    if success:
        await update.message.reply_text(
            f"✅ **Link Deleted Successfully!**\n\n"
            f"🗑️ **Deleted:** `{link_id}`\n"
            f"📁 **Files:** {len(link['files'])} files freed\n"
            f"💾 **Storage:** {format_file_size(link.get('total_size', 0))} freed\n\n"
            f"💡 View remaining links: /mylinks",
            parse_mode="Markdown"
        )
        
        db.log_event("link_deleted", user_id=user_id, link_id=link_id)
    else:
        await update.message.reply_text(
            "❌ **Delete Failed!**\n\n"
            "Unable to delete link. Please try again.",
            parse_mode="Markdown"
        )

# ==================== LINK INFO COMMAND ====================

@user_check
async def linkinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed link information"""
    
    if not context.args:
        await update.message.reply_text(
            "ℹ️ **Link Information**\n\n"
            "**Usage:** `/linkinfo LINK_ID`\n\n"
            "Example: `/linkinfo AbC12XyZ`",
            parse_mode="Markdown"
        )
        return
    
    link_id = context.args[0]
    link = db.get_link(link_id)
    
    if not link:
        await update.message.reply_text(
            "❌ **Link Not Found!**",
            parse_mode="Markdown"
        )
        return
    
    # Build file list
    files_text = ""
    for idx, file in enumerate(link['files'][:10], 1):  # Show first 10
        emoji = get_file_emoji(file['file_type'])
        files_text += f"{idx}. {emoji} `{truncate_text(file['file_name'], 30)}` - {format_file_size(file['file_size'])}\n"
    
    if len(link['files']) > 10:
        files_text += f"\n...and {len(link['files']) - 10} more files"
    
    bot_link = generate_bot_link(link_id)
    
    message = f"""
ℹ️ **Link Information**

━━━━━━━━━━━━━━━━━━━━━
🔗 **Link Details:**
━━━━━━━━━━━━━━━━━━━━━

🆔 **ID:** `{link_id}`
🏷️ **Name:** {link.get('link_name', 'Untitled')}
🗂️ **Category:** {link.get('category', 'Others')}
{'💎 **Type:** Premium Link' if link.get('is_premium_link') else '🆓 **Type:** Free Link'}
{'🔒 **Password:** Protected' if link.get('password') else '🔓 **Access:** Public'}

━━━━━━━━━━━━━━━━━━━━━
📊 **Statistics:**
━━━━━━━━━━━━━━━━━━━━━

📁 **Files:** {len(link['files'])}
📦 **Total Size:** {format_file_size(link.get('total_size', 0))}
📥 **Downloads:** {link.get('downloads', 0)}
👁️ **Views:** {link.get('views', 0)}

━━━━━━━━━━━━━━━━━━━━━
📅 **Dates:**
━━━━━━━━━━━━━━━━━━━━━

⏰ **Created:** {format_datetime(link.get('created_at'))}
📅 **Expires:** {format_expiry_date(link.get('expires_at'))}
👁️ **Last Accessed:** {format_datetime(link.get('last_accessed')) if link.get('last_accessed') else 'Never'}

━━━━━━━━━━━━━━━━━━━━━
📁 **Files:**
━━━━━━━━━━━━━━━━━━━━━

{files_text}

━━━━━━━━━━━━━━━━━━━━━
🔗 **Share Link:**
━━━━━━━━━━━━━━━━━━━━━

{bot_link}
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={bot_link}"),
            InlineKeyboardButton ("🗑️ Delete", callback_data=f"del_{link_id}")
        ],
        [InlineKeyboardButton("📱 QR Code", callback_data=f"qr_{link_id}")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ==================== ADD FILES COMMAND ====================

@user_check
async def add_files_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add files to existing link"""
    
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "➕ **Add Files to Link**\n\n"
            "**Usage:** `/add LINK_ID`\n\n"
            "Example: `/add AbC12XyZ`\n\n"
            "💡 Use /mylinks to see your link IDs",
            parse_mode="Markdown"
        )
        return
    
    link_id = context.args[0]
    link = db.get_link(link_id)
    
    if not link:
        await update.message.reply_text(
            "❌ **Link Not Found!**",
            parse_mode="Markdown"
        )
        return
    
    # Check ownership
    if link['admin_id'] != user_id and user_id not in config.ADMIN_IDS:
        await update.message.reply_text(
            "🚫 **Access Denied!**\n\n"
            "You can only modify your own links!",
            parse_mode="Markdown"
        )
        return
    
    # Initialize add mode
    pending_add_files[user_id] = {
        "link_id": link_id,
        "files": []
    }
    
    await update.message.reply_text(
        f"➕ **Add Files Mode**\n\n"
        f"🔗 **Link:** `{link_id}`\n"
        f"📁 **Current Files:** {len(link['files'])}\n"
        f"📦 **Current Size:** {format_file_size(link.get('total_size', 0))}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📤 **Send files to add them to this link!**\n\n"
        f"✅ **Finish:** /done\n"
        f"❌ **Cancel:** /cancel",
        parse_mode="Markdown"
    )

# ==================== QR CODE COMMAND ====================

@user_check
async def handle_dynamic_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /qrcode_LINKID commands"""
    text = update.message.text.strip()
    if "_" in text:
        link_id = text.split("_", 1)[1]
        await send_qr_code(update, context, link_id)
        
@user_check
async def qrcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate QR code for link (Premium feature)"""
    
    user_id = update.effective_user.id
    
    # Check premium or admin
    if user_id not in config.ADMIN_IDS and not db.is_user_premium(user_id):
        await update.message.reply_text(
            "💎 **Premium Feature!**\n\n"
            "QR code generation is only available for premium users.\n\n"
            "✨ **Premium benefits:**\n"
            "• Unlimited QR codes\n"
            "• Fancy branded QR codes\n"
            "• And much more!\n\n"
            "💡 Use /upgrade to get premium!",
            parse_mode="Markdown"
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "📥 **QR Code Generator**\n\n"
            "**Usage:** `/qrcode LINK_ID [fancy]`\n\n"
            "Examples:\n"
            "`/qrcode AbC12XyZ` - Basic QR\n"
            "`/qrcode AbC12XyZ fancy` - Branded QR\n\n"
            "💡 Use /mylinks to see your link IDs",
            parse_mode="Markdown"
        )
        return
    
    link_id = context.args[0]
    fancy = len(context.args) > 1 and context.args[1].lower() == "fancy"
    
    await send_qr_code(update, context, link_id, fancy)

async def send_qr_code(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: str, fancy: bool = False):
    """Generate and send QR code with caching"""
    link = db.get_link(link_id)
    if not link:
        if update.callback_query:
            await update.callback_query.answer("❌ Link Not Found!")
        else:
            await update.message.reply_text("❌ Link Not Found!")
        return

    # Check cache
    cache_key = "qr_file_id_fancy" if fancy else "qr_file_id"
    cached_id = link.get(cache_key)
    
    target_chat_id = update.effective_chat.id
    caption = f"📥 **QR Code Generated!**\n\n🔗 **Link:** `{link_id}`\n🏷️ **Name:** {link.get('link_name', 'Untitled')}\n📁 **Files:** {len(link['files'])}\n\n📱 Scan to access files instantly!"
    
    status_msg = None
    if not cached_id:
        if update.callback_query:
            await update.callback_query.answer("⏳ Generating QR...", show_alert=False)
            status_msg = await context.bot.send_message(target_chat_id, "⏳ **Generating QR Code...**", parse_mode="Markdown")
        else:
            status_msg = await update.message.reply_text("⏳ **Generating QR Code...**", parse_mode="Markdown")

    try:
        if cached_id:
            try:
                await context.bot.send_photo(
                    chat_id=target_chat_id,
                    photo=cached_id,
                    caption=caption,
                    parse_mode="Markdown"
                )
                if update.callback_query:
                    await update.callback_query.answer()
                return
            except Exception:
                # Cache invalid, regenerate
                pass

        # Generate
        bot_link = generate_bot_link(link_id)
        if fancy:
            qr_image = generate_fancy_qr_code(bot_link, link_id)
        else:
            qr_image = generate_qr_code(bot_link, link_id)
            
        msg = await context.bot.send_photo(
            chat_id=target_chat_id,
            photo=qr_image,
            caption=caption,
            parse_mode="Markdown"
        )
        
        # Cache ID
        if msg.photo:
            file_id = msg.photo[-1].file_id
            db.links.update_one({"link_id": link_id}, {"$set": {cache_key: file_id}})
        
        if status_msg:
            await status_msg.delete()
            
    except Exception as e:
        print(f"QR Error: {e}")
        error_text = "❌ QR Generation Failed!"
        if status_msg:
             await status_msg.edit_text(error_text)
        elif update.message:
            await update.message.reply_text(error_text)

# ==================== ADMIN ONLY COMMANDS ====================

@admin_only
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user"""
    
    if not context.args:
        await update.message.reply_text(
            "🚫 **Ban User**\n\n"
            "**Usage:** `/ban USER_ID`\n\n"
            "Example: `/ban 123456789`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text(
            "❌ Invalid user ID!",
            parse_mode="Markdown"
        )
        return
    
    # Don't ban admins
    if target_id in config.ADMIN_IDS:
        await update.message.reply_text(
            "❌ Cannot ban an admin!",
            parse_mode="Markdown"
        )
        return
    
    success = db.block_user(target_id)
    
    if success:
        await update.message.reply_text(
            f"✅ **User Banned!**\n\n"
            f"🆔 **User ID:** `{target_id}`\n\n"
            f"This user can no longer use the bot.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to ban user!",
            parse_mode="Markdown"
        )

@admin_only
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    
    if not context.args:
        await update.message.reply_text(
            "✅ **Unban User**\n\n"
            "**Usage:** `/unban USER_ID`\n\n"
            "Example: `/unban 123456789`",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_id = int(context.args[0])
    except:
        await update.message.reply_text(
            "❌ Invalid user ID!",
            parse_mode="Markdown"
        )
        return
    
    success = db.unblock_user(target_id)
    
    if success:
        await update.message.reply_text(
            f"✅ **User Unbanned!**\n\n"
            f"🆔 **User ID:** `{target_id}`\n\n"
            f"User can now use the bot again.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            "❌ Failed to unban user!",
            parse_mode="Markdown"
        )

@admin_only
async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin statistics"""
    
    stats = db.get_global_stats()
    
    # Calculate uptime (you can implement this properly)
    uptime = "24/7"
    
    # Get top users (placeholder)
    top_users = "1. User1 - 50 links\n2. User2 - 30 links\n3. User3 - 20 links"
    
    message = config.ADMIN_STATS_MESSAGE.format(
        total_users=stats['total_users'],
        free_users=stats['free_users'],
        premium_users=stats['premium_users'],
        total_links=stats['total_links'],
        total_files=stats['total_files'],
        total_storage=format_file_size(stats['total_storage']),
        total_downloads=stats['total_downloads'],
        total_views=stats['total_views'],
        new_users_today=0,  # Implement daily tracking later
        links_created_today=0,
        downloads_today=0,
        top_users=top_users,
        uptime=uptime
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh_stats"),
            InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics")
        ],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

@admin_only
async def grant_premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant premium (Deprecated)"""
    plans = ", ".join([f"`{k}`" for k in config.PLANS.keys()])
    await update.message.reply_text(
        f"⚠️ **Legacy Command Deprecated!**\n\n"
        f"Please use the new **Plan System**:\n"
        f"`/setplan USER_ID PLAN_NAME`\n\n"
        f"**Available Plans:**\n{plans}",
        parse_mode="Markdown"
    )

@admin_only
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    
    if not context.args:
        await update.message.reply_text(
            "📢 **Broadcast Message**\n\n"
            "**Usage:** `/broadcast MESSAGE`\n\n"
            "Example: `/broadcast Hello everyone!`\n\n"
            "⚠️ This will send message to ALL users!",
            parse_mode="Markdown"
        )
        return
    
    message = " ".join(context.args)
    users = db.get_all_users(include_blocked=False)
    
    sent = 0
    failed = 0
    
    status_msg = await update.message.reply_text(
        f"📢 **Broadcasting...**\n\n"
        f"👥 Total users: {len(users)}",
        parse_mode="Markdown"
    )
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 **Broadcast from {config.BOT_NAME}**\n\n{message}",
                parse_mode="Markdown"
            )
            sent += 1
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"📤 **Sent:** {sent}\n"
        f"❌ **Failed:** {failed}\n"
        f"👥 **Total:** {len(users)}",
        parse_mode="Markdown"
    )


# ==================== ADVANCED PREMIUM COMMANDS ====================

@user_check
@premium_only
async def setpassword_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set password for a link (Premium)"""
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "🔒 **Set Password**\n\n"
            "**Usage:** `/setpassword LINK_ID PASSWORD`\n"
            "**Remove:** `/setpassword LINK_ID off`\n\n"
            "Example: `/setpassword AbC12XyZ mysecurepass`",
            parse_mode="Markdown"
        )
        return
    
    link_id = context.args[0]
    password = context.args[1]
    
    link = db.get_link(link_id)
    if not link:
        await update.message.reply_text("❌ **Link Not Found!**", parse_mode="Markdown")
        return
    
    # Check ownership
    user_id = update.effective_user.id
    if link['admin_id'] != user_id and user_id not in config.ADMIN_IDS:
        await update.message.reply_text("🚫 **Access Denied!**", parse_mode="Markdown")
        return
    
    # Set password
    if password.lower() == "off":
        db.update_link(link_id, {"password": None})
        msg = "🔓 **Password Removed!**\nLink is now public."
    else:
        db.update_link(link_id, {"password": password})
        msg = f"🔒 **Password Set!**\n\n🔑 Password: `{password}`"
        
    await update.message.reply_text(
        f"✅ **Success!**\n\n{msg}",
        parse_mode="Markdown"
    )

@user_check
@premium_only
async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set custom name for a link (Premium)"""
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "🏷️ **Set Custom Name**\n\n"
            "**Usage:** `/setname LINK_ID New Name`\n\n"
            "Example: `/setname AbC12XyZ Holiday Photos 2024`",
            parse_mode="Markdown"
        )
        return
    
    link_id = context.args[0]
    new_name = " ".join(context.args[1:])
    
    link = db.get_link(link_id)
    if not link:
        await update.message.reply_text("❌ **Link Not Found!**", parse_mode="Markdown")
        return
        
    # Check ownership
    user_id = update.effective_user.id
    if link['admin_id'] != user_id and user_id not in config.ADMIN_IDS:
        await update.message.reply_text("🚫 **Access Denied!**", parse_mode="Markdown")
        return
        
    db.update_link(link_id, {"link_name": new_name})
    
    await update.message.reply_text(
        f"✅ **Name Updated!**\n\n"
        f"🔗 **Link:** `{link_id}`\n"
        f"🏷️ **New Name:** {new_name}",
        parse_mode="Markdown"
    )

@user_check
@premium_only
async def protect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle forward protection (Premium)"""
    
    if not context.args:
        await update.message.reply_text(
            "🛡️ **Content Protection**\n\n"
            "Prevent files from being forwarded/saved.\n\n"
            "**Usage:** `/protect LINK_ID [on/off]`\n\n"
            "Example: `/protect AbC12XyZ on`",
            parse_mode="Markdown"
        )
        return
    
    link_id = context.args[0]
    
    link = db.get_link(link_id)
    if not link:
        await update.message.reply_text("❌ **Link Not Found!**", parse_mode="Markdown")
        return
        
    # Check ownership
    user_id = update.effective_user.id
    if link['admin_id'] != user_id and user_id not in config.ADMIN_IDS:
        await update.message.reply_text("🚫 **Access Denied!**", parse_mode="Markdown")
        return
        
    if len(context.args) > 1:
        state = context.args[1].lower() == "on"
    else:
        # Toggle current state
        state = not link.get('protect_content', False)
        
    db.update_link(link_id, {"protect_content": state})
    
    status = "ON 🛡️" if state else "OFF 🔓"
    desc = "Files cannot be forwarded/saved." if state else "Files can be forwarded."
    
    await update.message.reply_text(
        f"✅ **Protection Updated!**\n\n"
        f"🔗 **Link:** `{link_id}`\n"
        f"🛡️ **Status:** {status}\n"
        f"ℹ️ {desc}",
        parse_mode="Markdown"
    )

# ==================== SEARCH COMMAND ====================

@user_check
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search user links"""
    
    if not context.args:
        await update.message.reply_text(
            "🔍 **Search Links**\n\n"
            "**Usage:** `/search QUERY`\n\n"
            "Example: `/search holiday`",
            parse_mode="Markdown"
        )
        return
        
    query = " ".join(context.args)
    user_id = update.effective_user.id
    
    # Search in DB
    # We need a db method for regex search or filter in python
    # db.get_user_links supports filter?
    # db.get_user_links(user_id, category=... skip=...)
    # I should add search method to db or fetch all and filter (inefficient but ok for now)
    
    # Let's assume fetching all (limit 1000) is okay for now
    all_links = db.get_user_links(user_id, limit=1000)
    
    results = []
    for link in all_links:
        if query.lower() in link.get('link_name', '').lower() or query.lower() in link.get('category', '').lower() or query in link['link_id']:
            results.append(link)
            
    if not results:
        if update.callback_query:
            await update.callback_query.answer("❌ No links found!")
        else:
            await update.effective_message.reply_text(
                "❌ **No Links Found!**\n\n"
                "You haven't created any links yet.\n"
                "Use /upload to start sharing files!",
                parse_mode="Markdown"
            )
        return
        
    # Show results (Top 10)
    message = f"🔍 **Search Results for:** `{query}`\n\n"
    
    for idx, link in enumerate(results[:10], 1):
        bot_link = generate_bot_link(link['link_id'])
        emoji = "💎" if link.get('is_premium_link') else "🔗"
        message += f"{emoji} **{idx}. {truncate_text(link.get('link_name', 'Untitled'), 30)}**\n"
        message += f"   🆔 `{link['link_id']}`\n"
        message += f"   🔗 {bot_link}\n\n"
        
    if len(results) > 10:
        message += f"...and {len(results) - 10} more results.\n"
        
    await update.message.reply_text(message, parse_mode="Markdown")

# ==================== PLAN MANAGEMENT ====================

@admin_only
async def set_plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user plan"""
    if not context.args or len(context.args) < 2:
        available_plans = ", ".join([f"`{k}`" for k in config.PLANS.keys()])
        await update.message.reply_text(
            f"❌ **Usage:** `/setplan USER_ID PLAN_NAME`\n\n"
            f"📋 **Available Plans:**\n{available_plans}",
            parse_mode="Markdown"
        )
        return

    try:
        target_id = int(context.args[0])
        plan_name = context.args[1].lower()
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID!")
        return

    if plan_name not in config.PLANS:
        available_plans = ", ".join([f"`{k}`" for k in config.PLANS.keys()])
        await update.message.reply_text(f"❌ **Invalid Plan!**\n\nAvailable: {available_plans}", parse_mode="Markdown")
        return

    plan_details = config.PLANS[plan_name]
    
    if db.set_user_plan(target_id, plan_name):
        notify_text = "✅ **Plan Updated!** (User notification failed)"
        try:
            # Try to notify user
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🎉 **Your Plan Has Been Updated!**\n\n"
                     f"💎 **New Plan:** {plan_details['name']}\n"
                     f"📅 **Duration:** {plan_details['duration_days']} days\n"
                     f"🚀 Enjoy enhanced limits!",
                parse_mode="Markdown"
            )
            notify_text = "✅ **Plan Updated & User Notified!**"
        except Exception:
            pass
            
        await update.message.reply_text(
            f"{notify_text}\n\n"
            f"👤 User: `{target_id}`\n"
            f"💎 Plan: `{plan_details['name']}`",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ Failed to update plan in database.")

