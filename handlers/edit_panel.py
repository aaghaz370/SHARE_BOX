
"""
Share-box by Univora - Edit Panel Handler
Advanced link editing features
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from database import db
from utils.helpers import user_check, truncate_text, format_file_size

@user_check
async def edit_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show Master Edit Panel for a link"""
    
    # Get Link ID
    if not context.args:
        await update.message.reply_text("❌ Usage: `/edit LINK_ID`", parse_mode="Markdown")
        return
        
    link_id = context.args[0]
    await show_edit_panel(update, context, link_id)

async def show_edit_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: str):
    """Render the edit panel"""
    link = db.get_link(link_id)
    if not link:
        if update.callback_query:
            await update.callback_query.answer("❌ Link Not Found!")
        else:
            await update.message.reply_text("❌ Link Not Found!")
        return
    
    # Check ownership
    user_id = update.effective_user.id
    if link['admin_id'] != user_id and user_id not in config.ADMIN_IDS:
        if update.callback_query:
            await update.callback_query.answer("🚫 Access Denied!")
        else:
            await update.message.reply_text("🚫 Access Denied!")
        return
        
    # Stats
    files_count = len(link['files'])
    total_size = link.get('total_size', 0)
    views = link.get('views', 0)
    downloads = link.get('downloads', 0)
    
    # Status Icons
    is_protected = "🛡️ On" if link.get('protect_content') else "🔓 Off"
    has_pass = "🔒 Yes" if link.get('password') else "🔓 No"
    
    text = f"""
🛠️ <b>Link Editor: {link.get('link_name', 'Untitled')}</b>

🆔 <b>ID:</b> <code>{link_id}</code>
📁 <b>Files:</b> {files_count} | 📦 {format_file_size(total_size)}
🗂️ <b>Category:</b> {link.get('category', 'None')}

📊 <b>Stats:</b> 👁️ {views} | 📥 {downloads}
🛡️ <b>Protection:</b> {is_protected}
🔒 <b>Password:</b> {has_pass}

👇 <b>Choose Action:</b>
"""

    # Password Button Logic
    pass_btn_text = "🔒 Set Password"
    pass_cb = f"p_pass_{link_id}"
    
    if link.get('password'):
        pass_btn_text = "🔓 Remove Pass"
        pass_cb = f"p_pass_remove_{link_id}"

    keyboard = [
        [
            InlineKeyboardButton("➕ Add Files", callback_data=f"edit_add_{link_id}"),
            InlineKeyboardButton("❌ Remove Files", callback_data=f"edit_rm_{link_id}")
        ],
        [
            InlineKeyboardButton("✏️ Rename", callback_data=f"p_rename_{link_id}"),
            InlineKeyboardButton(pass_btn_text, callback_data=pass_cb)
        ],
        [
            InlineKeyboardButton("🛡️ Protection", callback_data=f"p_protect_toggle_{link_id}"), 
            InlineKeyboardButton("📱 QR Code", callback_data=f"p_qrtoggle_{link_id}")
        ],
        [
            InlineKeyboardButton("👁️ View Content", callback_data=f"edit_view_{link_id}"),
            InlineKeyboardButton("🗑️ Delete Link", callback_data=f"confirm_del_{link_id}")
        ],
        [InlineKeyboardButton("⬅️ Back to Links", callback_data="menu_mylinks")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        # Edit
        try:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except Exception:
             await update.callback_query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

# Callback Handlers
async def handle_edit_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith("edit_panel_"):
        link_id = data.replace("edit_panel_", "")
        await show_edit_panel(update, context, link_id)
        
    elif data.startswith("edit_add_"):
        link_id = data.replace("edit_add_", "")
        # Logic to enter Add Mode (Similar to /add)
        # We can simulate /add command or set state
        from handlers.admin import pending_add_files
        user_id = update.effective_user.id
        
        pending_add_files[user_id] = {"link_id": link_id, "files": []}
        
        await query.message.reply_text(
            f"📤 **Add Files to:** `{link_id}`\n\n"
            "Send files now. Use /done when finished.",
            parse_mode="Markdown"
        )
        await query.answer("Upload mode started!")
        
    elif data.startswith("edit_rm_page_"):
         parts = data.replace("edit_rm_page_", "").split("_")
         link_id = parts[0]
         page = int(parts[1])
         await show_file_delete_menu(update, context, link_id, page)
         
    elif data.startswith("edit_rm_"):
         link_id = data.replace("edit_rm_", "")
         await show_file_delete_menu(update, context, link_id, 0)
         
    elif data.startswith("edit_del_file_"):
        parts = data.replace("edit_del_file_", "").split("_")
        link_id = parts[0]
        file_idx = int(parts[1])
        page = int(parts[2])
        
        if db.remove_file_from_link(link_id, file_idx):
             await query.answer("File deleted!")
             await show_file_delete_menu(update, context, link_id, page)
        else:
             await query.answer("Error deleting file!")

    elif data.startswith("p_protect_toggle_"):
        link_id = data.replace("p_protect_toggle_", "")
        link = db.get_link(link_id)
        if link:
            new_state = not link.get("protect_content", False)
            db.update_link(link_id, {"protect_content": new_state})
            await query.answer(f"Protection {'Enabled' if new_state else 'Disabled'}")
            await show_edit_panel(update, context, link_id)
            
    elif data.startswith("p_pass_remove_"):
        link_id = data.replace("p_pass_remove_", "")
        db.links.update_one({"link_id": link_id}, {"$unset": {"password": ""}})
        await query.answer("Password Removed!")
        await show_edit_panel(update, context, link_id)
            
    elif data.startswith("edit_view_"):
         # Show file list text
         link_id = data.replace("edit_view_", "")
         link = db.get_link(link_id)
         user_id = update.effective_user.id
         
         if not link: return
         
         text = f"📂 <b>Files in {link.get('link_name', 'Link')}:</b>\n\n"
         files = link.get('files', [])
         if not files:
             text += "No files."
         else:
             for i, f in enumerate(files, 1):
                 # Escape HTML characters in filename
                 safe_name = f['file_name'].replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
                 text += f"{i}. {truncate_text(safe_name)} ({format_file_size(f['file_size'])})\n"
         
         text += f"\n🔗 <code>{link_id}</code>"
         
         # Back button
         keyboard = [[InlineKeyboardButton("⬅️ Back to Edit", callback_data=f"edit_panel_{link_id}")]]
         await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_file_delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, link_id: str, page: int):
    link = db.get_link(link_id)
    if not link: return
    
    files = link.get('files', [])
    total_files = len(files)
    
    ACTIONS_PER_PAGE = 5
    start = page * ACTIONS_PER_PAGE
    end = start + ACTIONS_PER_PAGE
    current_files = files[start:end]
    
    text = f"❌ **Delete Files** (Page {page+1})\nTap to delete:\n"
    
    keyboard = []
    for idx, f in enumerate(current_files):
        real_idx = start + idx
        btn_text = f"❌ {truncate_text(f['file_name'], 20)}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"edit_del_file_{link_id}_{real_idx}_{page}")])
        
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"edit_rm_page_{link_id}_{page-1}"))
        
    if end < total_files:
         nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"edit_rm_page_{link_id}_{page+1}"))
         
    if nav: keyboard.append(nav)
    
    keyboard.append([InlineKeyboardButton("⬅️ Back to Editor", callback_data=f"edit_panel_{link_id}")])
    
    markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    except:
        pass

async def show_edit_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    """Show list of links to select for editing"""
    user_id = update.effective_user.id
    
    # Get user links
    all_links = sorted(db.get_user_links(user_id, limit=100), key=lambda x: x['created_at'], reverse=True)
    
    if not all_links:
         if update.callback_query:
            await update.callback_query.answer("❌ No links found!")
         return
         
    # Pagination
    ITEMS_PER_PAGE = 5
    total_items = len(all_links)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    if page < 1: page = 1
    if page > total_pages: page = total_pages
    
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_items = all_links[start:end]
    
    text = f"🛠️ **Select Link to Edit** (Page {page}/{total_pages})\nChoose a link below:"
    
    keyboard = []
    for link in current_items:
        name = truncate_text(link.get('link_name', 'Untitled'), 25)
        keyboard.append([InlineKeyboardButton(f"📝 {name}", callback_data=f"edit_panel_{link['link_id']}")])
        
    # Navigation
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"edit_sel_page_{page-1}"))
    if page < total_pages:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"edit_sel_page_{page+1}"))
        
    if nav: keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("⬅️ Back to Links", callback_data="menu_mylinks")])
    
    markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
