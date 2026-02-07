import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import TelegramError
import config
from database import db
from utils.helpers import user_check, format_file_size

# Constants
FILTER_OPTS = {
    'all': 'All Content 📂',
    'video': 'Videos 🎥',
    'document': 'Documents 📄',
    'photo': 'Photos 📷',
    'audio': 'Audio 🎵'
}
LIMIT_OPTS = [10, 50, 100, 200, 500, 'all']

@user_check
async def import_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the import process"""
    # Reset state
    context.user_data['import_step'] = 'CHANNEL'
    context.user_data['import_filters'] = ['all']
    
    await update.message.reply_text(
        "📥 **Channel Importer**\n\n"
        "I can import files from any channel where I am an **Admin**.\n\n"
        "**Steps:**\n"
        "1. Add me to the target channel as Admin.\n"
        "2. Send the **Channel Link** or **Username** below.\n\n"
        "💡 _I will filter content and save it to your storage._",
        parse_mode="Markdown"
    )

async def handle_import_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for channel"""
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    try:
        # Check permissions
        chat = await context.bot.get_chat(text)
        member = await chat.get_member(context.bot.id)
        
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ **Error:** I must be an Admin in that channel to import files!")
            return
            
        # Save chat info
        context.user_data['import_source_id'] = chat.id
        context.user_data['import_source_title'] = chat.title
        context.user_data['import_step'] = 'FILTER'
        
        # Show Filter Menu
        await show_filter_menu(update, context)
        
    except Exception as e:
        await update.message.reply_text(f"❌ **Error:** Cannot access channel.\n`{str(e)}`")

async def show_filter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display filter selection menu"""
    current = context.user_data.get('import_filters', ['all'])
    
    keyboard = []
    row = []
    
    for key, label in FILTER_OPTS.items():
        # Checkbox style
        status = "✅" if key in current else "⬜"
        callback = f"imp_filter_{key}"
        
        row.append(InlineKeyboardButton(f"{status} {label}", callback_data=callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
            
    if row: keyboard.append(row)
    
    # Confirm actions
    keyboard.append([InlineKeyboardButton("➡️ Next Step", callback_data="imp_next_limit")])
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="imp_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "🔍 **Select Content Type**\n\n"
        "Choose what you want to import via buttons below.\n"
        "• 'All' selects everything.\n"
        "• selecting specific types deselects 'All'.\n\n"
        f"📂 **Source:** {context.user_data.get('import_source_title')}"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def show_limit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show limit selection menu"""
    keyboard = []
    row = []
    
    for limit in LIMIT_OPTS:
        label = f"{limit} Posts" if limit != 'all' else "All Posts (Slow)"
        callback = f"imp_limit_{limit}"
        row.append(InlineKeyboardButton(label, callback_data=callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="imp_back_filter")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "🔢 **How many posts to scan?**\n\n"
        "Select the number of latest posts to check for files.\n"
        "Scanning older posts takes longer.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def start_import_process(update: Update, context: ContextTypes.DEFAULT_TYPE, limit):
    """Initialize the background import task"""
    query = update.callback_query
    user_id = update.effective_user.id
    source_id = context.user_data['import_source_id']
    filters = context.user_data['import_filters']
    
    # Initial UI
    await query.edit_message_text(
        "⏳ **Starting Import...**\n\n"
        "Scanning channel for files...",
        parse_mode="Markdown"
    )
    
    # Run in background
    asyncio.create_task(run_import_task(
        context, 
        user_id, 
        query.message.chat_id, 
        query.message.message_id, 
        source_id, 
        filters, 
        limit
    ))

async def run_import_task(context, user_id, chat_id, message_id, source_id, filters, limit):
    """Background task logic"""
    try:
        imported_files = []
        scanned = 0
        found = 0
        
        # Determine scan strategy
        # Simplified strategy: We can't easily iterate history with Bot API.
        # Workaround: Send a dummy message to get ID, then work backwards.
        try:
            dummy = await context.bot.send_message(source_id, ".")
            last_id = dummy.message_id
            await dummy.delete()
        except:
            last_id = 100000 # Fallback high number
            
        start_id = last_id
        target = last_id - (limit if limit != 'all' else 5000) # Hard cap 5000 for 'all' safety
        if target < 1: target = 1
        
        # Progress Loop
        current_id = start_id
        while current_id > target and (limit == 'all' or scanned < int(limit) if limit != 'all' else True):
            current_id -= 1
            scanned += 1
            
            # Rate limiting
            if scanned % 20 == 0:
                await asyncio.sleep(1) # Be nice
                # Update UI
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"🔄 **Importing...**\n\n"
                             f"📂 Scanned: {scanned}\n"
                             f"✅ Found: {found}\n"
                             f"📉 ID: {current_id}",
                        parse_mode="Markdown"
                    )
                except: pass

            try:
                # Try to copy message to STORAGE CHANNEL directly
                # We copy to primary storage first to validate content
                # Filter check
                # Note: We can't check type without copying or forwarding first because we can't 'get' message.
                # So we try copy to Storage. If fails (empty/deleted), ignore.
                
                # Copy to Primary Storage
                msg = await context.bot.copy_message(
                    chat_id=config.PRIMARY_CHANNEL,
                    from_chat_id=source_id,
                    message_id=current_id
                )
                
                # Check Filter
                is_valid = False
                if 'all' in filters:
                    is_valid = bool(msg.document or msg.video or msg.audio or msg.photo)
                else:
                    if 'video' in filters and msg.video: is_valid = True
                    elif 'document' in filters and msg.document: is_valid = True
                    elif 'audio' in filters and msg.audio: is_valid = True
                    elif 'photo' in filters and msg.photo: is_valid = True
                
                if is_valid:
                    # Keep it and Store metadata
                    # Backup redundancy logic (Optional for import speed? Let's do async redundancy later? No, do it now)
                    # For speed, we skip backup copies during bulk import, or launch async tasks.
                    # We store basic info.
                    
                    # Extract file info
                    f_id = None
                    f_name = "Imported File"
                    f_size = 0
                    
                    if msg.document:
                        f_id = msg.document.file_id
                        f_name = msg.document.file_name or "Document"
                        f_size = msg.document.file_size
                    elif msg.video:
                        f_id = msg.video.file_id
                        f_name = msg.video.file_name or "Video"
                        f_size = msg.video.file_size
                    elif msg.audio:
                        f_id = msg.audio.file_id
                        f_name = msg.audio.file_name or "Audio"
                        f_size = msg.audio.file_size
                    elif msg.photo:
                        f_id = msg.photo[-1].file_id
                        f_name = "Photo.jpg"
                        f_size = msg.photo[-1].file_size
                    
                    imported_files.append({
                        "message_id": msg.message_id, # Primary
                        "file_id": f_id,
                        "file_name": f_name,
                        "file_size": f_size,
                        # "backup_messages": [] # Skip backups for bulk import speed, or implement queue
                    })
                    found += 1
                else:
                    # Delete if not matching filter or text-only
                    await msg.delete()
                    
            except Exception:
                continue # Message deleted or inaccessible
                
        # Finish
        if not imported_files:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ **Import Failed**\nNo matching files found in the scanned range.",
                parse_mode="Markdown"
            )
            return

        # Generate Link
        from handlers.admin import create_share_link
        # We need to simulate the 'link' object creation manually or use helper
        # Logic:
        # Create link entry in DB
        import secrets
        from datetime import datetime
        link_id = secrets.token_urlsafe(6)
        
        link_data = {
            "link_id": link_id,
            "user_id": user_id,
            "name": f"Imported {context.user_data.get('import_source_title')}",
            "files": imported_files, # List of file objects
            "created_at": datetime.now(),
            "views": 0,
            "downloads": 0
        }
        
        # Insert to DB
        # db.links.insert_one(link_data) -> Need db access
        await asyncio.to_thread(db.links.insert_one, link_data)
        
        # Update User stats
        # await asyncio.to_thread(db.users.update_one, ...)
        
        # Send Success
        base_url = f"https://t.me/{config.BOT_USERNAME.replace('@', '')}?start={link_id}"
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ **Import Complete!**\n\n"
                 f"📂 Scanned: {scanned}\n"
                 f"📦 Imported: {found}\n\n"
                 f"🔗 **Your Link:**\n{base_url}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"Import Error: {e}")
        try:
            await context.bot.send_message(chat_id, f"⚠️ Import Error: {e}")
        except: pass

async def handle_import_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback dispatcher for import"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("imp_filter_"):
        flt = data.split("_")[2]
        current = context.user_data.get('import_filters', ['all'])
        
        # Logic: Toggle
        if flt == 'all':
            # Create fresh list if selecting 'all'
            current = ['all']
        else:
            # If selecting specific, remove 'all' first
            if 'all' in current: 
                current.remove('all')
            
            # Toggle item
            if flt in current: current.remove(flt)
            else: current.append(flt)
            
        # Fallback to 'all' if empty
        if not current: current = ['all']
        
        context.user_data['import_filters'] = current
        await show_filter_menu(update, context)
        
    elif data == "imp_next_limit":
        context.user_data['import_step'] = 'LIMIT'
        await show_limit_menu(update, context)
        
    elif data.startswith("imp_limit_"):
        limit = data.split("_")[2]
        # Start
        await start_import_process(update, context, limit)
        
    elif data == "imp_cancel":
        context.user_data['import_step'] = None
        await query.message.delete()
        await query.message.reply_text("❌ Import Cancelled.")
    elif data == "imp_back_filter":
        context.user_data['import_step'] = 'FILTER'
        await show_filter_menu(update, context)
