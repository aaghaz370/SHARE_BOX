"""
Share-box by Univora - Callback Query Handlers
Handle inline button callbacks
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import config
from database import db
from handlers.user import (
    start_command, help_command, stats_command, 
    settings_command, referral_command, upgrade_command
)
from handlers.admin import (
    upload_command, mylinks_command
)

# ==================== CALLBACK HANDLERS ====================

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback query router"""
    
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Menu navigation
    # Menu navigation
    if data == "menu_start":
        # Redirect to start
        await start_command(update, context)
    
    elif data == "menu_help":
        await help_command(update, context)
    
    elif data == "menu_stats":
        await stats_command(update, context)
    
    elif data == "menu_settings":
        await settings_command(update, context)
    
    elif data == "menu_upload":
        await upload_command(update, context)
    
    elif data == "menu_mylinks":
        await mylinks_command(update, context)
    
    elif data == "menu_referral":
        await referral_command(update, context)
    
    elif data == "menu_upgrade":
        await upgrade_command(update, context)
    
    elif data.startswith("menu_edit_select") or data.startswith("edit_sel_page_"):
         from handlers.edit_panel import show_edit_selection_menu
         page = 1
         if "edit_sel_page_" in data:
             page = int(data.split("_")[-1])
         await show_edit_selection_menu(update, context, page)
         
    # Settings Handler
    elif data.startswith("set_"):
        await handle_settings_callback(update, context)
         
    # Link generation category selection
    elif data.startswith("gen_cat_"):
        await generate_link_category_callback(update, context)
        
    # QR Code generation
    elif data.startswith("qr_"):
        link_id = data.replace("qr_", "")
        from handlers.admin import send_qr_code
        await send_qr_code(update, context, link_id)

    # Premium Actions
    elif data.startswith("p_rename_"):
        link_id = data.replace("p_rename_", "")
        await query.answer("Use /setname COMMAND!")
        await query.message.reply_text(f"✏️ **Rename Link**\nUse: `/setname {link_id} NEW_NAME`", parse_mode="Markdown")
        
    elif data.startswith("p_pass_"):
        link_id = data.replace("p_pass_", "")
        await query.answer("Use /setpassword COMMAND!")
        await query.message.reply_text(f"🔒 **Set Password**\nUse: `/setpassword {link_id} PASSWORD`", parse_mode="Markdown")
        
    elif data.startswith("p_qrtoggle_"):
        link_id = data.replace("p_qrtoggle_", "")
        # Just generate QR now
        from handlers.admin import send_qr_code
        await send_qr_code(update, context, link_id)
    
    # Advanced Link Info
    elif data.startswith("linfo_"):
        link_id = data.replace("linfo_", "")
        link = db.get_link(link_id)
        
        if not link:
            await query.answer("❌ Link not found!")
            return
            
        # Comprehensive link details
        from utils.helpers import format_file_size, format_datetime, truncate_text
        
        files = link.get('files', [])
        file_count = len(files)
        total_size = link.get('total_size', 0)
        views = link.get('views', 0)
        downloads = link.get('downloads', 0)
        created = link.get('created_at')
        expiry = link.get('expiry_date')
        
        # Calculate stats
        avg_file_size = total_size / file_count if file_count > 0 else 0
        has_password = "🔒 Yes" if link.get('password') else "🔓 No"
        is_protected = "🛡️ On" if link.get('protect_content') else "🔓 Off"
        category = link.get('category', 'None')
        link_name = link.get('link_name', 'Untitled')
        
        # Build comprehensive info message - using HTML for better compatibility
        share_url = f"{config.WEBHOOK_URL or 'http://localhost:8000'}/share/{link_id}"
        
        info_text = f"""📋 <b>Link Information</b>

━━━━━━━━━━━━━━━━━━━━━
📌 <b>BASIC DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━

🏷️ <b>Name:</b> {link_name}
🆔 <b>ID:</b> <code>{link_id}</code>
🗂️ <b>Category:</b> {category}

━━━━━━━━━━━━━━━━━━━━━
📊 <b>STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━━

📁 <b>Files:</b> {file_count}
📦 <b>Total Size:</b> {format_file_size(total_size)}
📏 <b>Avg File Size:</b> {format_file_size(int(avg_file_size))}

👁️ <b>Views:</b> {views}
📥 <b>Downloads:</b> {downloads}
📈 <b>Engagement:</b> {downloads}/{views if views > 0 else 1} ratio

━━━━━━━━━━━━━━━━━━━━━
🔐 <b>SECURITY &amp; SETTINGS</b>
━━━━━━━━━━━━━━━━━━━━━

🔒 <b>Password:</b> {has_password}
🛡️ <b>Content Protection:</b> {is_protected}

━━━━━━━━━━━━━━━━━━━━━
⏰ <b>DATES</b>
━━━━━━━━━━━━━━━━━━━━━

📅 <b>Created:</b> {format_datetime(created) if created else 'Unknown'}
⏳ <b>Expires:</b> {format_datetime(expiry) if expiry else 'Never'}

━━━━━━━━━━━━━━━━━━━━━
🔗 <b>SHARE URL</b>
━━━━━━━━━━━━━━━━━━━━━

<code>{share_url}</code>
"""
        
        # Add top 5 files preview
        if files:
            info_text += "\n━━━━━━━━━━━━━━━━━━━━━\n📂 <b>TOP FILES</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            for idx, f in enumerate(files[:5], 1):
                fname = truncate_text(f.get('file_name', 'Unknown'), 25)
                fsize = format_file_size(f.get('file_size', 0))
                info_text += f"{idx}. {fname}\n   📦 {fsize}\n"
                
            if file_count > 5:
                info_text += f"\n... and {file_count - 5} more files"
        
        # Interactive buttons
        keyboard = [
            [
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_panel_{link_id}"),
                InlineKeyboardButton("📱 QR Code", callback_data=f"qr_{link_id}")
            ],
            [
                InlineKeyboardButton("🔗 Get Link", url=share_url),
                InlineKeyboardButton("📋 Copy ID", callback_data=f"copy_{link_id}")
            ],
            [
                InlineKeyboardButton("🗑️ Delete", callback_data=f"confirm_del_{link_id}"),
                InlineKeyboardButton("⬅️ Back", callback_data="menu_mylinks")
            ]
        ]
        
        await query.edit_message_text(
            info_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    
    # Delete Confirmation
    elif data.startswith("confirm_del_"):
        link_id = data.replace("confirm_del_", "")
        link = db.get_link(link_id)
        from utils.helpers import format_file_size
        
        if not link:
            await query.answer("❌ Link not found!")
            return
            
        confirm_text = f"""
⚠️ <b>Delete Confirmation</b>

Are you sure you want to delete this link?

🏷️ <b>Name:</b> {link.get('link_name', 'Untitled')}
📁 <b>Files:</b> {len(link.get('files', []))}
📦 <b>Size:</b> {format_file_size(link.get('total_size', 0))}

⚠️ <b>This action cannot be undone!</b>
"""
        
        keyboard = [
            [
                InlineKeyboardButton("❌ Cancel", callback_data="menu_mylinks"),
                InlineKeyboardButton("🗑️ YES, DELETE", callback_data=f"del_{link_id}")
            ]
        ]
        
        await query.edit_message_text(
            confirm_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    # Execute Deletion
    elif data.startswith("del_"):
        link_id = data.replace("del_", "")
        
        if db.delete_link(link_id):
            await query.answer("✅ Link deleted successfully!")
            await query.message.reply_text(
                "🗑️ **Link Deleted!**\n\nThe link and its files have been removed.",
                parse_mode="Markdown"
            )
            # Redirect to mylinks
            context.args = []
            await mylinks_command(update, context)
        else:
            await query.answer("❌ Error deleting link!")
            
    # Edit Panel
    elif data.startswith("edit_") or data.startswith("p_protect_toggle_"):
        from handlers.edit_panel import handle_edit_callbacks
        await handle_edit_callbacks(update, context)
    
    # Pagination
    elif data.startswith("links_page_"):
        # Handle mylinks pagination
        parts = data.split("_")
        page = int(parts[2])
        category = parts[3] if len(parts) > 3 and parts[3] != "all" else None
        
        context.args = []
        if category:
            context.args.extend(["category", category])
        context.args.append(str(page))
        
        await mylinks_command(update, context)
        
    # Copy Link ID
    elif data.startswith("copy_"):
        link_id = data.replace("copy_", "")
        from utils.helpers import generate_bot_link
        link_url = generate_bot_link(link_id)
        # Send raw text for easy copying
        await query.message.reply_text(f"📋 **Link:**\n`{link_url}`", parse_mode="Markdown")
        await query.answer("Link sent below!")

    # Add Files to Link
    elif data.startswith("add_files_"):
        link_id = data.replace("add_files_", "")
        from handlers.admin import pending_add_files
        
        # Init add mode
        pending_add_files[update.effective_user.id] = {
            "link_id": link_id,
            "files": []
        }
        
        await query.message.reply_text(
            f"➕ **Add Files Mode Activated!**\n\n"
            f"Send files to add to Link `{link_id}`.\n"
            f"Type /done when finished.",
            parse_mode="Markdown"
        )
        await query.answer("Send files now!")
    
    else:
        await query.message.reply_text(
            "⚠️ Unknown action!",
            parse_mode="Markdown"
        )

async def generate_link_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection for link generation"""
    
    query = update.callback_query
    user_id = query.from_user.id
    
    # Check if user has pending files
    from handlers.admin import pending_files
    
    if user_id not in pending_files:
        await query.message.reply_text(
            "❌ **No pending files!**\n\n"
            "Please start upload again with /upload",
            parse_mode="Markdown"
        )
        return
    
    files = pending_files[user_id]
    
    # Get selected category
    category = query.data.replace("gen_cat_", "")
    
    if category == "skip":
        category = "🗂️ Others"
    
    # Create link
    link_name = context.user_data.get('link_name')
    if not link_name:
        link_name = f"Link {datetime.now().strftime('%d %b %H:%M')}"
        
    link_id = db.create_link(
        admin_id=user_id,
        files_data=files,
        link_name=link_name,
        category=category
    )
    
    if link_id:
        from utils.helpers import generate_bot_link, calculate_total_size, format_file_size, format_expiry_date
        
        bot_link = generate_bot_link(link_id)
        total_size = calculate_total_size(files)
        
        link = db.get_link(link_id)
        
        message = config.LINK_GENERATED_SUCCESS.format(
            link=bot_link,
            file_count=len(files),
            total_size=format_file_size(total_size),
            category=category,
            created_at=datetime.now().strftime('%d %b %Y, %H:%M'),
            expires_at=format_expiry_date(link.get('expires_at'))
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={bot_link}"),
                InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_{link_id}")
            ],
            [
                InlineKeyboardButton("🔗 My Links", callback_data="menu_mylinks"),
                InlineKeyboardButton("➕ Add to Link", callback_data=f"add_files_{link_id}")
            ],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")]
        ]
        
        # Add Premium Actions
        if db.is_user_premium(user_id) or user_id in config.ADMIN_IDS:
             # Insert Premium options before Main Menu
             premium_row = [
                 InlineKeyboardButton("✏️ Rename", callback_data=f"p_rename_{link_id}"),
                 InlineKeyboardButton("🔒 Password", callback_data=f"p_pass_{link_id}"),
             ]
             keyboard.insert(2, premium_row)
             keyboard.insert(3, [InlineKeyboardButton("📱 Auto-QR: Toggle", callback_data=f"p_qrtoggle_{link_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        db.log_event("link_created", user_id=user_id, link_id=link_id, metadata={"files": len(files), "category": category})
        
        # Clean up
        del pending_files[user_id]
        if 'link_name' in context.user_data: del context.user_data['link_name']
    else:
        await query.message.reply_text(
            "❌ **Link Creation Failed!**\n\n"
            "You may have reached your limit or other error occurred.\n\n"
            "💡 Delete old links or upgrade to premium!",
            parse_mode="Markdown"
        )

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings toggles"""
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id
    
    user = db.get_user(user_id)
    settings = user.get("settings", {})
    
    if data == "set_toggle_notif":
        new_val = not settings.get("notifications", True)
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {"settings.notifications": new_val}}
        )
        await query.answer(f"Notifications {'Enabled' if new_val else 'Disabled'}!")
        
    elif data == "set_toggle_autodel":
        new_val = not settings.get("auto_delete_files", True)
        db.users.update_one(
            {"user_id": user_id},
            {"$set": {"settings.auto_delete_files": new_val}}
        )
        await query.answer(f"Auto-Delete {'Enabled' if new_val else 'Disabled'}!")
        
    # Refresh
    from handlers.user import settings_command
    await settings_command(update, context)
