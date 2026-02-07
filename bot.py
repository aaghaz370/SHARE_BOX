"""
Share-box by Univora - Main Bot File
Advanced Telegram File Sharing Bot with Free & Premium Tiers
"""

import logging
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask, jsonify, redirect, render_template, request
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

import config
from database import db

# Import handlers
from handlers.user import (
    start_command, help_command, getlink_command,
    detect_and_handle_link, unknown_command,
    stats_command, settings_command, referral_command,
    upgrade_command, skip_command, stop_command,
    checklink_command
)
from handlers.admin import (
    upload_command, handle_file_upload, done_command,
    cancel_command, mylinks_command, delete_link_command,
    linkinfo_command, add_files_command, qrcode_command,
    ban_command, unban_command, admin_stats_command,
    grant_premium_command, broadcast_command, handle_dynamic_qr
)
from handlers.premium import (
    setpassword_command, setname_command, protect_command, search_command
)
from handlers.callbacks import handle_callback_query
from handlers.edit_panel import edit_panel_command, edit_panel_callback
from handlers.importer import import_command

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== FLASK WEB SERVER ====================

app = Flask(__name__)

@app.route('/')
def home():
    """Home page"""
    return render_template('dashboard.html') if request.args.get('u') else """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Share Box Bot</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; background: #0f1115; color: white; text-align: center; padding: 50px; }
            .container { max-width: 600px; margin: 0 auto; }
            h1 { color: #6366f1; }
            .btn { display: inline-block; padding: 10px 20px; background: #6366f1; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📦 Share Box Bot</h1>
            <p>Advanced File Sharing & Management</p>
            <p>✅ Bot is Running 24/7</p>
            <a href="https://t.me/SHAREBOXBOT" class="btn">Open Bot</a>
        </div>
    </body>
    </html>
    """

@app.route('/dashboard')
def dashboard():
    """User Dashboard"""
    user_id = request.args.get('u')
    if not user_id:
        return "⚠️ Access Denied: Please open this link from the Telegram Bot."
    return render_template('dashboard.html')

@app.route('/api/links')
def api_get_links():
    try:
        user_id = request.args.get('u')
        if not user_id: return jsonify({"error": "Missing User ID"}), 400
        
        user_id = int(user_id)
        # Query for both user_id (legacy/imported) and admin_id (standard)
        query = {"$or": [{"user_id": user_id}, {"admin_id": user_id}]}
        
        links_cursor = db.links.find(query).sort("created_at", -1)
        links = []
        
        for link in links_cursor:
            # Serialization
            link_obj = {
                "link_id": link.get("link_id"),
                "name": link.get("name") or link.get("link_name", "Untitled"), # Handle both field names
                "views": link.get("views", 0),
                "downloads": link.get("downloads", 0),
                "created_at": link.get("created_at").isoformat() if link.get("created_at") else None,
                "file_count": len(link.get("files", [])),
                "category": link.get("category", "Uncategorized")
            }
            links.append(link_obj)
            
        return jsonify({"links": links})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def api_get_user_stats():
    try:
        user_id = request.args.get('u')
        if not user_id: return jsonify({"error": "Missing User ID"}), 400
        
        user_id = int(user_id)
        user = db.get_user(user_id) or {}
        
        # Aggregation
        query = {"$or": [{"user_id": user_id}, {"admin_id": user_id}]}
        pipeline = [
            {"$match": query},
            {"$group": {"_id": None, "total_views": {"$sum": "$views"}}}
        ]
        res = list(db.links.aggregate(pipeline))
        total_views = res[0]['total_views'] if res else 0
        total_links = db.links.count_documents(query)
        
        plan = db.get_plan_details(user_id)
        
        stats = {
            "username": user.get('first_name', 'User'),
            "plan": plan.get('name', 'Free').upper(),
            "total_links": total_links,
            "total_views": total_views,
            "joined_at": user.get('joined_at').isoformat() if user.get('joined_at') else None,
            "bot_username": config.BOT_USERNAME.replace('@', '') # Pass this for frontend
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "ok", "bot": config.BOT_NAME}), 200

@app.route('/share/<link_id>')
def share_redirect(link_id):
    return redirect(f"https://t.me/{config.BOT_USERNAME.replace('@', '')}?start={link_id}")

def run_flask():
    """Run Flask server in background"""
    app.run(host='0.0.0.0', port=config.PORT, debug=False)

# ==================== BOT ERROR HANDLER ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ **An error occurred!**\n\n"
                "Please try again or contact admin if problem persists.\n\n"
                f"Error: `{str(context.error)}`\n"
                f"Type: `{type(context.error).__name__}`",
                parse_mode="Markdown"
            )
        except:
            pass

# ==================== BOT MENU SETUP ====================

async def setup_bot_commands(application):
    """Setup bot command menu"""
    # Auto-detect username for accurate links
    try:
        bot_info = await application.bot.get_me()
        config.BOT_USERNAME = f"@{bot_info.username}"
        logger.info(f"✅ Bot Username Auto-detected: {config.BOT_USERNAME}")
    except Exception as e:
        logger.warning(f"⚠️ Could not detect bot username: {e}")

    logger.info("⚙️  Setting up bot commands...")
    
    # User commands (shown to everyone)
    user_commands = [
        BotCommand("start", "🏠 Start the bot"),
        BotCommand("help", "❓ Get help"),
        BotCommand("upload", "📤 Upload files"),
        BotCommand("mylinks", "🔗 View your links"),
        BotCommand("getlink", "📥 Download from link"),
        BotCommand("stats", "📊 Your statistics"),
        BotCommand("settings", "⚙️ Bot settings"),
        BotCommand("referral", "🎁 Referral program"),
        BotCommand("upgrade", "💎 Get premium"),
        BotCommand("qrcode", "📱 Generate QR Code"),
        BotCommand("search", "🔍 Search Links"),
        BotCommand("setname", "🏷️ Rename Link (Premium)"),
        BotCommand("protect", "🛡️ Protect Content (Premium)"),
        BotCommand("setpassword", "🔒 Set Password (Premium)"),
    ]
    
    # Set commands
    await application.bot.set_my_commands(user_commands)
    
    logger.info("✅ Bot commands configured!")

# ==================== MAIN FUNCTION ====================

def main():
    """Main function to run the bot"""
    
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"🚀 Starting {config.BOT_NAME}...")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Validate configuration
    try:
        config.validate_config()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        return
    
    # Start Flask web server
    logger.info(f"🌐 Starting web server on port {config.PORT}...")
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Web server started")
    
    # Create bot application
    logger.info("🤖 Initializing bot application...")
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # ==================== REGISTER HANDLERS ====================
    
    logger.info("📝 Registering command handlers...")
    
    # User commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("getlink", getlink_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("referral", referral_command))
    application.add_handler(CommandHandler("upgrade", upgrade_command))
    application.add_handler(CommandHandler("skip", skip_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("checklink", checklink_command))
    application.add_handler(CommandHandler("import", import_command))
    
    # Upload/Link management commands
    application.add_handler(CommandHandler("upload", upload_command))
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("mylinks", mylinks_command))
    application.add_handler(CommandHandler("delete", delete_link_command))
    application.add_handler(CommandHandler("linkinfo", linkinfo_command))
    application.add_handler(CommandHandler("add", add_files_command))
    application.add_handler(CommandHandler("qrcode", qrcode_command))
    
    # Admin commands
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("adminstats", admin_stats_command))
    application.add_handler(CommandHandler("grantpremium", grant_premium_command))
    application.add_handler(CommandHandler("grantpremium", grant_premium_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # Premium Commands
    application.add_handler(CommandHandler("setpassword", setpassword_command))
    application.add_handler(CommandHandler("setname", setname_command))
    application.add_handler(CommandHandler("protect", protect_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("edit", edit_panel_command))
    
    # File upload handler
    application.add_handler(
        MessageHandler(
            filters.Document.ALL | filters.VIDEO | filters.AUDIO | filters.PHOTO,
            handle_file_upload
        )
    )
    
    # Text message handler (for link detection)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            detect_and_handle_link
        )
    )

    # Dynamic QR handler
    application.add_handler(
        MessageHandler(
            filters.Regex(r'^/qrcode_'),
            handle_dynamic_qr
        )
    )
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Unknown command handler
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("✅ All handlers registered")
    
    # Setup bot commands menu
    application.post_init = setup_bot_commands
    
    # Start bot
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"✅ {config.BOT_NAME} is now ONLINE!")
    logger.info(f"🌐 Web server: http://localhost:{config.PORT}")
    logger.info(f"💬 Bot username: {config.BOT_USERNAME}")
    logger.info(f"👨‍💼 Admins: {len(config.ADMIN_IDS)}")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("Press Ctrl+C to stop")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Run bot with polling
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()
