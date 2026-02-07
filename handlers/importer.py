import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from telegram.helpers import escape_markdown
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
    raw_text = update.message.text.strip()
    text = raw_text # Working copy
    
    # Logic to handle Links (t.me/xyz)
    if "t.me/" in text or "telegram.me/" in text:
        # 1. Private Channel Post Link (t.me/c/123456789/100)
        if "/c/" in text:
            try:
                # Extract ID part
                parts = text.split("/c/")[1].split("/")
                if parts[0].isdigit():
                    # Telegram Private Channels use -100 prefix
                    text = int(f"-100{parts[0]}")
                    
                # Extract Message ID (Start Point)
                if len(parts) > 1 and parts[1].isdigit():
                    context.user_data['import_start_msg_id'] = int(parts[1])
            except:
                pass # Failed to parse, try original
        
        # 2. Invite Links (Cannot be used directly)
        elif "/+" in text or "joinchat" in text:
             await update.message.reply_text(
                 "❌ **Private Invite Link Detected**\n\n"
                 "I cannot use invite links. Please send a **Post Link** from the channel instead (e.g. `t.me/c/1234/56`).\n\n"
                 "Or send the **Channel ID** directly (`-100xxxx`).",
                 parse_mode="Markdown"
             )
             return
             
        # 3. Public Links (t.me/username/123)
        else:
            try:
                parts = text.rstrip("/").split("/")
                # Check for MsgID (last part digits)
                if parts[-1].isdigit():
                    context.user_data['import_start_msg_id'] = int(parts.pop())
                    
                username = parts[-1].split("?")[0]
                if not username.startswith("@") and not username.startswith("-"):
                     text = f"@{username}"
            except: pass
            
    # Try integer conversion if it looks like ID (manual input)
    try:
        if isinstance(text, str):
            chat_id = int(text)
            text = chat_id
    except ValueError:
        pass

    try:
        # Check permissions
        chat = await context.bot.get_chat(text)
        
        # Verify Bot is Admin
        try:
            member = await chat.get_member(context.bot.id)
            if member.status not in ['administrator', 'creator']:
                await update.message.reply_text("❌ **Error:** I am NOT an Admin in that channel!\n\nPlease promote me to Admin with 'Post Messages' permission.")
                return
        except Exception as e:
            # If bot is not in chat (and it's private), get_member fails.
            if "/c/" in str(update.message.text):
                await update.message.reply_text("❌ **Access Denied:** I am not in that private channel.\n\nPlease add me as **Admin** first, then try again.")
                return
            await update.message.reply_text(f"❌ **Access Error:** Cannot verify admin status.\nReason: {e}")
            return
            
        # Save chat info
        context.user_data['import_source_id'] = chat.id
        context.user_data['import_source_title'] = chat.title
        context.user_data['import_step'] = 'FILTER'
        
        # Show Filter Menu
        await show_filter_menu(update, context)
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ **Error:** Cannot access channel.\n`{str(e)}`\n\n"
            "**Possible Reasons:**\n"
            "1. Bot is not Admin in the channel.\n"
            "2. Link format is invalid.\n"
            "3. If Private, use a Post Link (t.me/c/...) or ID.",
            parse_mode="Markdown"
        )

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
    
    safe_title = escape_markdown(context.user_data.get('import_source_title', 'Unknown'), version=1)
    
    text = (
        "🔍 **Select Content Type**\n\n"
        "Choose what you want to import via buttons below.\n"
        "• 'All' selects everything.\n"
        "• selecting specific types deselects 'All'.\n\n"
        f"📂 **Source:** {safe_title}"
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
    
    keyboard.append([InlineKeyboardButton("✏️ Custom Number", callback_data="imp_limit_custom")])
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="imp_back_filter")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "🔢 **How many posts to scan?**\n\n"
        "Select an option or choose Custom.\n"
        "Scanning older posts takes longer.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def start_import_process(update: Update, context: ContextTypes.DEFAULT_TYPE, limit):
    """Initialize the background import task"""
    query = update.callback_query
    if not query:
        # Called from text input usually
        chat_id = update.effective_chat.id
        message_id = None # New message
    else:
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        
    user_id = update.effective_user.id
    source_id = context.user_data['import_source_id']
    filters = context.user_data['import_filters']
    
    # Cast limit
    if limit != 'all':
        try:
            limit = int(limit)
        except:
            limit = 100 # Fallback
    
    # Initial UI
    msg_text = "⏳ **Starting Import...**\n\nScanning channel for files..."
    
    if query:
        await query.edit_message_text(msg_text, parse_mode="Markdown")
    else:
        # Send new message if text input
        msg = await context.bot.send_message(chat_id, msg_text, parse_mode="Markdown")
        message_id = msg.message_id
    
    # Run in background
    asyncio.create_task(run_import_task(
        context, 
        user_id, 
        chat_id, 
        message_id, 
        source_id, 
        filters, 
        limit
    ))

async def handle_import_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom limit number"""
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Please enter a valid number (e.g. 50).")
        return
        
    limit = int(text)
    if limit < 1: limit = 1
    if limit > 10000: limit = 10000 # Safety cap
    
    await start_import_process(update, context, limit)
    
# ... run_import_task is below ...

async def run_import_task(context, user_id, chat_id, message_id, source_id, filters, limit):
    """Background task logic"""
    try:
        imported_files = []
        scanned = 0
        found = 0
        
        # Determine scan start point
        start_id = context.user_data.get('import_start_msg_id')
        
        if not start_id:
            # Default: Latest message
            try:
                dummy = await context.bot.send_message(source_id, ".")
                start_id = dummy.message_id
                await dummy.delete()
            except:
                start_id = 100000 # Fallback
                
        # Limit arithmetic
        limit_val = int(limit) if limit != 'all' else 5000
        
        target = start_id - limit_val
        if target < 1: target = 1
        
        # Progress Loop
        current_id = start_id
        while current_id > target and (limit == 'all' or scanned < limit_val):
            # Scan Strategy: Downwards
            process_id = current_id 
            
            # Rate limiting & UI Update
            # Update every 5% or at least every 5 messages
            update_step = max(5, int(limit_val / 20))
            
            if scanned > 0 and (scanned % update_step == 0 or scanned == limit_val):
                try:
                    percent = 0
                    if limit != 'all':
                        percent = int((scanned / limit_val) * 100)
                    
                    # Bar: [██████░░░░]
                    filled = int(percent / 10)
                    bar = "▓" * filled + "░" * (10 - filled)
                    
                    status_text = (
                        f"📥 **Importing Files...**\n"
                        f"`[{bar}] {percent}%`\n\n"
                        f"📂 **Scanned:** {scanned}/{limit_val}\n"
                        f"✅ **Found:** {found}\n"
                        f"📉 **Current ID:** `{process_id}`"
                    )
                    
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=status_text,
                        parse_mode="Markdown"
                    )
                    # Small yield to prevent blocking event loop, but not slow down opacity
                    await asyncio.sleep(0.1)
                except Exception as e:
                    # Ignore "Message not modified" or Rate Limits
                    await asyncio.sleep(1) # Backoff slightly on error
                    pass

            try:
                # 1. Forward first to inspect content (returns full Message object)
                # We use forward because copy_message returns MessageId object (no data)
                temp_msg = await context.bot.forward_message(
                    chat_id=config.PRIMARY_CHANNEL,
                    from_chat_id=source_id,
                    message_id=process_id
                )
                
                # Inspect content
                file_type = None
                if temp_msg.document: file_type = 'document'
                elif temp_msg.video: file_type = 'video'
                elif temp_msg.audio: file_type = 'audio'
                elif temp_msg.photo: file_type = 'photo'
                
                is_valid = False
                if 'all' in filters:
                    is_valid = bool(file_type)
                elif file_type and file_type in filters:
                    is_valid = True
                
                if is_valid:
                    # 2. Valid! Create CLEAN COPY (no forward tag)
                    clean_msg_id = await context.bot.copy_message(
                        chat_id=config.PRIMARY_CHANNEL,
                        from_chat_id=source_id,
                        message_id=process_id
                    )
                    # copy_message returns MessageId object
                    final_mid = clean_msg_id.message_id
                    
                    # Extract info from temp_msg (it has the data)
                    f_id, f_name, f_size = None, "Imported", 0
                    
                    if temp_msg.document:
                        f_id = temp_msg.document.file_id
                        f_name = temp_msg.document.file_name or "Document"
                        f_size = temp_msg.document.file_size
                    elif temp_msg.video:
                        f_id = temp_msg.video.file_id
                        f_name = temp_msg.video.file_name or "Video"
                        f_size = temp_msg.video.file_size
                    elif temp_msg.audio:
                        f_id = temp_msg.audio.file_id
                        f_name = temp_msg.audio.file_name or "Audio"
                        f_size = temp_msg.audio.file_size
                    elif temp_msg.photo:
                        f_id = temp_msg.photo[-1].file_id
                        f_name = "Photo.jpg"
                        f_size = temp_msg.photo[-1].file_size
                    
                    imported_files.append({
                        "message_id": final_mid, # stored info
                        "file_id": f_id,
                        "file_name": f_name,
                        "file_size": f_size,
                        "file_type": file_type
                    })
                    found += 1
                
                # 3. Cleanup temp forward
                await temp_msg.delete()
                    
            except Exception as e:
                # print(f"Skip: {e}")
                pass
            
            # Decrement loop - MUST BE OUTSIDE TRY/EXCEPT
            current_id -= 1
            scanned += 1
                 
                
        # Finish
        if not imported_files:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ **Import Failed**\nNo matching files found in the scanned range.",
                parse_mode="Markdown"
            )
            return

        # Hand over to Manual Flow (Standard Generation)
        from handlers.admin import pending_files
        pending_files[user_id] = imported_files
        
        # Set state for naming
        context.user_data['awaiting_link_name'] = True
        
        # We can suggest a name based on channel title
        suggested_name = context.user_data.get('import_source_title', 'Imported Files')
        context.user_data['default_link_name'] = f"Imported: {suggested_name}"
        
        from telegram.helpers import escape_markdown
        safe_name = escape_markdown(suggested_name, version=1)
        
        success_text = (
            f"✅ **Import Complete!**\n\n"
            f"📦 **{found} Files Ready.**\n\n"
            f"✏️ **Name your Link:**\n"
            f"Enter a name for this collection.\n\n"
            f"Type /skip to use default:\n`Imported: {safe_name}`"
        )
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=success_text,
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
        limit_str = data.split("_")[2]
        
        if limit_str == "custom":
             context.user_data['import_step'] = 'LIMIT_INPUT'
             await query.message.edit_text(
                 "🔢 **Custom Limit**\n\n"
                 "Send the number of posts you want me to scan (e.g. `250`).", 
                 parse_mode="Markdown"
             )
             return
             
        # Start
        await start_import_process(update, context, limit_str)
        
    elif data == "imp_cancel":
        context.user_data['import_step'] = None
        await query.message.delete()
        await query.message.reply_text("❌ Import Cancelled.")
    elif data == "imp_back_filter":
        context.user_data['import_step'] = 'FILTER'
        await show_filter_menu(update, context)
