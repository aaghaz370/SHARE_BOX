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
    if data == "menu_start":
        # Redirect to start
        update.message = query.message
        await start_command(update, context)
    
    elif data == "menu_help":
        update.message = query.message
        await help_command(update, context)
    
    elif data == "menu_stats":
        update.message = query.message
        await stats_command(update, context)
    
    elif data == "menu_settings":
        update.message = query.message  
        await settings_command(update, context)
    
    elif data == "menu_upload":
        update.message = query.message
        await upload_command(update, context)
    
    elif data == "menu_mylinks":
        update.message = query.message
        await mylinks_command(update, context)
    
    elif data == "menu_referral":
        update.message = query.message
        await referral_command(update, context)
    
    elif data == "menu_upgrade":
        update.message = query.message
        await upgrade_command(update, context)
    
    # Link generation category selection
    elif data.startswith("gen_cat_"):
        await generate_link_category_callback(update, context)
    
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
        
        update.message = query.message
        await mylinks_command(update, context)
    
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
    link_id = db.create_link(
        admin_id=user_id,
        files_data=files,
        link_name=f"Link {datetime.now().strftime('%d %b %H:%M')}",
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
                InlineKeyboardButton("📤 Upload More", callback_data="menu_upload")
            ],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        db.log_event("link_created", user_id=user_id, link_id=link_id, metadata={"files": len(files), "category": category})
        
        # Clean up
        del pending_files[user_id]
    else:
        await query.message.reply_text(
            "❌ **Link Creation Failed!**\n\n"
            "You may have reached your limit or other error occurred.\n\n"
            "💡 Delete old links or upgrade to premium!",
            parse_mode="Markdown"
        )
