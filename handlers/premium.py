
from telegram import Update
from telegram.ext import ContextTypes
import config
from database import db
from utils.helpers import user_check, premium_only, generate_bot_link, truncate_text

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
        await update.message.reply_text(
            f"🔍 **No Results Found!**\n\n"
            f"Query: `{query}`\n"
            f"Try different keywords.",
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

