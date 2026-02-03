"""
Share-box by Univora - Main Bot File
Advanced Telegram File Sharing Bot with Free & Premium Tiers
"""

import logging
import asyncio
from datetime import datetime
from threading import Thread
from flask import Flask, jsonify
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
    upgrade_command
)
from handlers.admin import (
    upload_command, handle_file_upload, done_command,
    cancel_command, mylinks_command, delete_link_command,
    linkinfo_command, add_files_command, qrcode_command,
    ban_command, unban_command, admin_stats_command,
    grant_premium_command, broadcast_command
)
from handlers.callbacks import handle_callback_query

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
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{config.BOT_NAME}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
 <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                padding: 50px 20px;
                margin: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                backdrop-filter: blur(4px);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }}
            h1 {{ font-size: 3em; margin: 0; }}
            .status {{ color: #4ade80; font-size: 1.5em; margin: 20px 0; }}
            .features {{ text-align: left; margin: 30px 0; }}
            .feature {{ margin: 15px 0; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 10px; }}
            .btn {{
                display: inline-block;
                padding: 15px 30px;
                background: white;
                color: #667eea;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
                margin: 10px;
                transition: transform 0.3s;
            }}
            .btn:hover {{ transform: scale(1.05); }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin: 30px 0;
            }}
            .stat {{
                background: rgba(255,255,255,0.2);
                padding: 20px;
                border-radius: 10px;
            }}
            .stat-value {{ font-size: 2em; font-weight: bold; }}
            .stat-label {{ font-size: 0.9em; opacity: 0.9; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📦 {config.BOT_NAME}</h1>
            <div class="status">✅ Bot is Running!</div>
            
            <p style="font-size: 1.2em; margin: 20px 0;">
                Share files securely with advanced features!
            </p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">FREE</div>
                    <div class="stat-label">20 Files/Link</div>
                </div>
                <div class="stat">
                    <div class="stat-value">💎</div>
                    <div class="stat-label">Premium Available</div>
                </div>
                <div class="stat">
                    <div class="stat-value">24/7</div>
                    <div class="stat-label">Always Online</div>
                </div>
            </div>
            
            <div class="features">
                <div class="feature">📤 Upload files & create shareable links</div>
                <div class="feature">🔒 Password protection (Premium)</div>
                <div class="feature">📊 Advanced analytics & statistics</div>
                <div class="feature">📥 QR code generation (Premium)</div>
                <div class="feature">♾️ Unlimited storage (Premium)</div>
                <div class="feature">🔄 Triple backup redundancy</div>
            </div>
            
            <a href="https://t.me/{config.BOT_USERNAME.replace('@', '')}" class="btn">
                🚀 Start Bot
            </a>
            <a href="/health" class="btn">
                💚 Health Check
            </a>
            
            <p style="margin-top: 40px; font-size: 0.9em; opacity: 0.8;">
                Made with ❤️ by {config.BRAND_NAME}<br>
                Version 1.0.0 | © 2026
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check database connection
        stats = db.get_global_stats()
        
        return jsonify({
            "status": "healthy",
            "bot": config.BOT_NAME,
            "uptime": "24/7",
            "database": "connected",
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "total_users": stats.get('total_users', 0),
                "total_links": stats.get('total_links', 0),
                "total_files": stats.get('total_files', 0)
            }
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/stats')
def stats_endpoint():
    """Public stats endpoint"""
    try:
        stats = db.get_global_stats()
        
        return jsonify({
            "bot_name": config.BOT_NAME,
            "total_users": stats.get('total_users', 0),
            "premium_users": stats.get('premium_users', 0),
            "total_links": stats.get('total_links', 0),
            "total_downloads": stats.get('total_downloads', 0),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_flask():
    """Run Flask  server in background"""
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
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    
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
