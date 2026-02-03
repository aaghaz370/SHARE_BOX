# 📁 Share-box by Univora - Project Structure

```
SHARE_BOX_BOT/
│
├── 📄 .env                          # Environment variables (NEVER commit!)
├── 📄 .gitignore                    # Git ignore rules
├── 📄 README.md                     # Main project documentation
├── 📄 DEPLOYMENT.md                 # Deployment guide
├── 📄 PROJECT_STRUCTURE.md          # This file
├── 📄 requirements.txt              # Python dependencies
├── 📄 Procfile                      # Render/Heroku deployment
├── 📄 render.yaml                   # Render configuration
├── 📄 start.sh                      # Startup script
│
├── 📄 bot.py                        # Main bot file (entry point)
├── 📄 config.py                     # Configuration module
├── 📄 database.py                   # MongoDB operations
│
├── 📁 handlers/                     # Command handlers
│   ├── __init__.py
│   ├── user.py                      # User commands
│   ├── admin.py                     # Admin & upload commands
│   └── callbacks.py                 # Inline button callbacks
│
├── 📁 utils/                        # Utility modules
│   ├── __init__.py
│   ├── helpers.py                   # Helper functions
│   └── qr_generator.py              # QR code generation
│
└── 📁 UNIVORA_FILES_BOT @UnivoraFilesBot/  # Reference bot (for learning)
    └── (reference files - will be deleted later)
```

---

## 📋 File Descriptions

### Core Files

#### `bot.py`
- **Purpose:** Main bot entry point
- **Features:**
  - Flask web server for health checks
  - Command handler registration
  - Error handling
  - Bot initialization
  - 24/7 availability

#### `config.py`
- **Purpose:** Configuration management
- **Contains:**
  - Environment variable loading
  - Bot settings
  - Free/Premium tier limits
  - Message templates
  - Feature flags

#### `database.py`
- **Purpose:** MongoDB database operations
- **Features:**
  - User management
  - Link/file operations
  - Analytics tracking
  - Referral system
  - Premium tier management

### Handler Modules

#### `handlers/user.py`
- **Commands:**
  - `/start` - Welcome message
  - `/help` - Help guide
  - `/getlink` - Download files
  - `/stats` - User statistics
  - `/settings` - User preferences
  - `/referral` - Referral program
  - `/upgrade` - Premium info
- **Features:**
  - File download with auto-delete
  - Password verification
  - Link detection
  - Statistics display

#### `handlers/admin.py`
- **Commands:**
  - `/upload` - Upload files
  - `/done` - Finish upload
  - `/cancel` - Cancel operation
  - `/mylinks` - View links
  - `/delete` - Delete link
  - `/linkinfo` - Link details
  - `/add` - Add files to link
  - `/qrcode` - Generate QR code (Premium)
  - `/ban` - Ban user (Admin)
  - `/unban` - Unban user (Admin)
  - `/adminstats` - Bot statistics (Admin)
  - `/grantpremium` - Grant premium (Admin)
  - `/broadcast` - Broadcast message (Admin)
- **Features:**
  - Triple backup file storage
  - Category selection
  - Pagination
  - Link management
  - User moderation

#### `handlers/callbacks.py`
- **Purpose:** Handle inline button clicks
- **Features:**
  - Menu navigation
  - Category selection
  - Link pagination
  - Quick actions

### Utility Modules

#### `utils/helpers.py`
- **Functions:**
  - Decorators (admin_only, user_check, premium_only)
  - File size formatting
  - Date/time formatting
  - Link generation
  - Pagination
  - Tier limit checking
  - Statistics formatting

#### `utils/qr_generator.py`
- **Functions:**
  - Basic QR code generation
  - Fancy branded QR codes
  - QR code customization

---

## 🔄 Data Flow

### File Upload Flow:
```
User sends /upload
  → Bot activates upload mode
  → User sends files
  → Files uploaded to 3 channels (TRIPLE BACKUP)
  → Message IDs stored in MongoDB
  → User sends /done
  → Category selection
  → Link generated in MongoDB
  → User gets shareable link
```

### File Download Flow:
```
User sends link
  → Bot extracts link_id
  → Check if password protected
  → (If yes) Ask for password
  → Verify password
  → Fetch files from primary channel
  → Send files to user
  → Schedule auto-delete (20 min)
  → Increment download counter
  → Log analytics
```

### Data Persistence:
```
Bot Deleted ❌
  ↓
Files in Channels ✅ (Safe)
Data in MongoDB ✅ (Safe)
  ↓
New Bot Created 🔄
  ↓
Same channels + database
  ↓
Everything Restored! 🎉
```

---

## 💾 Database Schema

### `users` Collection:
```javascript
{
  user_id: Number,              // Telegram user ID
  username: String,             // Telegram username
  first_name: String,           // User's first name
  is_premium: Boolean,          // Premium status
  premium_expiry: Date,         // Premium expiration
  subscription_tier: String,    // "free" or "premium"
  storage_used: Number,         // Bytes used
  referral_code: String,        // Unique referral code
  referred_by: Number,          // Who referred this user
  joined_at: Date,              // Registration date
  last_seen: Date,              // Last activity
  is_blocked: Boolean,          // Ban status
  total_links: Number,          // Links created
  total_downloads: Number,      // Total downloads
  total_views: Number,          // Total views
  settings: {
    language: String,
    notifications: Boolean,
    default_category: String,
    auto_delete_files: Boolean
  }
}
```

### `links` Collection:
```javascript
{
  link_id: String,              // Unique 8-char ID
  admin_id: Number,             // Creator's user ID
  files: [{
    message_id: Number,         // Channel message ID
    file_id: String,            // Telegram file ID
    file_name: String,          // Original filename
    file_size: Number,          // Size in bytes
    file_type: String,          // document/video/photo/audio
    mime_type: String,          // MIME type
    backup_messages: Array      // Backup channel IDs
  }],
  link_name: String,            // Custom link name
  password: String,             // Optional password
  category: String,             // File category
  created_at: Date,             // Creation timestamp
  expires_at: Date,             // Expiration date
  downloads: Number,            // Download count
  views: Number,                // View count
  last_accessed: Date,          // Last download time
  is_active: Boolean,           // Active/deleted status
  is_premium_link: Boolean,     // Created by premium user
  total_size: Number,           // Total files size
  whitelist_users: Array,       // Premium: restricted access
  max_downloads: Number,        // Premium: download limit
  forward_protection: Boolean,  // Premium: prevent forwarding
  scheduled_activation: Date,   // Premium: schedule link
  scheduled_deactivation: Date  // Premium: schedule expiry
}
```

### `analytics` Collection:
```javascript
{
  event_type: String,           // Event name
  user_id: Number,              // User who triggered
  link_id: String,              // Related link
  metadata: Object,             // Additional data
  timestamp: Date               // Event time
}
```

### `referrals` Collection:
```javascript
{
  referrer_id: Number,          // Who referred
  referred_id: Number,          // Who was referred
  status: String,               // "pending"/"completed"
  reward_given: Boolean,        // Reward status
  created_at: Date              // Referral date
}
```

---

## 🎯 Feature Checklist

### ✅ Implemented Features:

- [x] File upload & link generation
- [x] Triple backup storage (data persistence)
- [x] Free tier with limits
- [x] Premium tier tracking (no payment yet)
- [x] User authentication & blocking
- [x] Link management (create, view, delete)
- [x] File organization with categories
- [x] Download tracking & analytics
- [x] Auto-delete files (20 min)
- [x] Password protection (Premium)
- [x] QR code generation (Premium)
- [x] Referral system
- [x] Admin commands
- [x] Beautiful modern UI
- [x] Inline keyboards
- [x] Pagination
- [x] Web dashboard with health checks
- [x] Error handling
- [x] Logging system
- [x] 24/7 deployment ready

### 🔄 Future Features (Optional):

- [ ] Payment integration (Razorpay/Stripe/Telegram Stars)
- [ ] Link scheduling (activate/deactivate at specific times)
- [ ] Download limits per link
- [ ] User whitelist for restricted links
- [ ] Multi-language support
- [ ] Link templates
- [ ] Bulk operations
- [ ] Channel import feature
- [ ] Advanced analytics dashboard
- [ ] Export data (JSON/CSV)
- [ ] API access
- [ ] Web dashboard for users
- [ ] File preview
- [ ] Search functionality
- [ ] Collections (group multiple links)

---

## 🔧 Configuration Options

### Free Tier Limits:
```python
MAX_FILES_PER_LINK = 20
MAX_FILE_SIZE_GB = 2
MAX_ACTIVE_LINKS = 10
TOTAL_STORAGE_GB = 50
LINK_EXPIRY_DAYS = 30
```

### Premium Tier Limits:
```python
MAX_FILES_PER_LINK = 0 (unlimited)
MAX_FILE_SIZE_GB = 4
MAX_ACTIVE_LINKS = 0 (unlimited)
TOTAL_STORAGE_GB = 500
LINK_EXPIRY_DAYS = 0 (never expires)
```

### Feature Flags:
```python
ENABLE_PREMIUM_FEATURES = True
ENABLE_ANALYTICS = True
ENABLE_REFERRALS = True
ENABLE_QR_CODES = True
```

---

## 🚀 Quick Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env file
# (Edit .env with your credentials)

# Run bot locally
python bot.py

# Deploy to Render
git push origin main
# (Auto-deploy if enabled)
```

---

## 📊 Monitoring

### Health Check Endpoints:

- **Home:** `https://your-url.onrender.com/`
- **Health:** `https://your-url.onrender.com/health`
- **Stats:** `https://your-url.onrender.com/stats`

### Logs:

- **Render Dashboard:** Real-time logs
- **Bot Logs:** Console output with logging module

---

## 🔐 Security Features

1. **User blocking system**
2. **Admin-only commands**
3. **Environment variable protection**
4. **Password hashing for links** (coming soon)
5. **Rate limiting** (configurable)
6. **Input sanitization**
7. **Triple backup redundancy**

---

##  🎨 Customization

### Change Bot Name/Branding:
Edit `config.py`:
```python
BOT_NAME = "Your Custom Name"
BRAND_NAME = "Your Brand 📦"
```

### Modify Messages:
Edit message templates in `config.py`:
- `WELCOME_MESSAGE`
- `HELP_MESSAGE`
- `UPLOAD_START_MESSAGE`
- etc.

### Add Categories:
Edit `DEFAULT_CATEGORIES` in `config.py`

### Change Limits:
Edit `FreeLimits` and `PremiumLimits` classes in `config.py`

---

## 💡 Code Quality

- **Type Hints:** Used throughout
- **Docstrings:** All functions documented
- **Error Handling:** Comprehensive try-catch blocks
- **Logging:** Detailed logging for debugging
- **Modularity:** Separated concerns (handlers, utils, config)
- **DRY Principle:** Reusable helper functions
- **Async/Await:** Proper async implementation

---

## 📖 Documentation

- `README.md` - Main project overview
- `DEPLOYMENT.md` - Deployment guide
- `PROJECT_STRUCTURE.md` - This file
- Inline code comments
- Function docstrings

---

**Project Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** February 2026

Made with ❤️ by Univora Team
