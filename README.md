# 📦 Share-box by Univora

> **Advanced Telegram File Sharing Bot with Free & Premium Tiers**

An enterprise-level Telegram bot that converts files into secure, shareable links with advanced features like password protection, QR codes, analytics, and a comprehensive Free/Premium subscription model.

---

## 🎯 Project Overview

**Share-box** is designed for **all audiences** - from casual users sharing a few files to power users managing large file collections. The bot implements a **freemium model** to sustain operations while providing excellent value to free users.

### 🎨 Bot Identity
- **Name:** Share-box by Univora
- **Tagline:** "Share Smart, Share Secure 📦"
- **Target Audience:** Students, Content Creators, Businesses, Communities
- **Business Model:** Free + Premium Subscriptions

---

## 📊 FEATURE ANALYSIS FROM REFERENCE BOT

### ✅ Core Features Found in Reference Bot

#### 1. **File Management** 📁
- Upload files (Documents, Videos, Audio, Photos)
- Support for files up to 4GB
- Multiple files → Single shareable link
- Add files to existing links
- Remove specific files from links
- Auto-backup to 3 channels (triple redundancy)

#### 2. **Link System** 🔗
- Unique 8-character link IDs
- Password protection option
- Category/Tag organization (Movies, Documents, Photos, Music, Others)
- Custom link names
- Download tracking
- Link info display
- QR code generation for links

#### 3. **User Experience** 👥
- Auto-detect links in messages
- Password verification flow
- 20-minute auto-delete timer for downloaded files
- Pagination for link lists
- Bulk delete operations
- Channel import feature (import files from Telegram channels)

#### 4. **Admin Features** 👨‍💼
- User ban/unban system
- Blocked users list
- Broadcast messaging
- Statistics dashboard
- Complete admin panel

#### 5. **Technical Features** ⚙️
- MongoDB database
- Flask web server for health checks
- 24/7 uptime (Render deployment)
- Singleton database pattern
- Error handling
- Rate limiting setup
- Command menu system

---

## 🆓 FREE vs 💎 PREMIUM - Feature Distribution

### 🆓 FREE TIER (For Everyone)

#### **Core Access** ✅
- ✅ File upload & link generation
- ✅ Basic file types (Documents, Photos, Audio, Video)
- ✅ Download tracking
- ✅ Auto-delete after 20 minutes
- ✅ Basic categories (5 options)
- ✅ Link management (/mylinks, /delete)
- ✅ Bot commands access
- ✅ 24/7 availability

#### **Limits & Restrictions** 🚧

| Feature | Free Limit |
|---------|-----------|
| **Files per Link** | Max 20 files |
| **Max File Size** | 2GB per file |
| **Total Storage** | 50GB lifetime |
| **Active Links** | Max 10 links at a time |
| **Link Expiry** | Auto-delete after 30 days |
| **Password Protection** | ❌ Not available |
| **QR Code Generation** | ❌ Not available |
| **Custom Link Names** | ❌ Not available |
| **Analytics** | Basic (download count only) |
| **Bulk Operations** | ❌ Not available |
| **Channel Import** | ❌ Not available |
| **Priority Support** | ❌ Not available |
| **Custom Categories** | ❌ Not available |
| **Download Speed** | Standard |
| **Batch Upload** | ❌ Not available |
| **Forward Protection** | ❌ Not available |

---

### 💎 PREMIUM TIER ($4.99/month or $49.99/year)

#### **All Free Features +** 🎁

| Feature | Premium Access |
|---------|---------------|
| **Files per Link** | ✅ Unlimited files |
| **Max File Size** | ✅ 4GB per file (2x free) |
| **Total Storage** | ✅ 500GB lifetime (10x free) |
| **Active Links** | ✅ Unlimited links |
| **Link Expiry** | ✅ Never expires (manual control) |
| **Password Protection** | ✅ Full access with custom passwords |
| **QR Code Generation** | ✅ Unlimited QR codes |
| **Custom Link Names** | ✅ Full customization |
| **Analytics** | ✅ Advanced (downloads, views, timestamps, user data) |
| **Bulk Operations** | ✅ Delete, Export, Modify multiple links |
| **Channel Import** | ✅ Import from any accessible channel |
| **Priority Support** | ✅ 24h response time |
| **Custom Categories** | ✅ Create unlimited categories |
| **Download Speed** | ✅ Priority fast downloads |
| **Batch Upload** | ✅ Upload multiple files at once |
| **Forward Protection** | ✅ Prevent message forwarding |
| **Link Scheduling** | ✅ Schedule link activation/deactivation |
| **Download Limits** | ✅ Set max downloads per link |
| **User Whitelist** | ✅ Restrict link access to specific users |
| **Branding Removal** | ✅ Remove "Share-box" watermark |
| **API Access** | ✅ RESTful API for integrations |
| **Export Data** | ✅ Export all data as JSON/CSV |

---

## 🚀 ADVANCED FEATURES TO ADD

### 1. **Premium Subscription System** 💳
- Payment integration (Razorpay/Stripe/Telegram Stars)
- Subscription management
- Free trial (7 days)
- Referral program (earn 1 month free for 5 referrals)
- Usage quota tracking

### 2. **Advanced Link Management** 🔗
```
- Link scheduling (activate/deactivate at specific times)
- Download limits per link
- Link access whitelist (only specific users)
- Link expiry countdown
- Custom short URLs (share-box.com/abc123)
- Link templates (preset configurations)
- Link cloning (duplicate link settings)
```

### 3. **Enhanced Security** 🔐
```
- Two-factor authentication for sensitive links
- IP-based access control
- Automatic file encryption
- Forward protection (prevent Telegram forwarding)
- Screenshot detection & watermarking
- User verification (email/phone)
```

### 4. **Rich Analytics Dashboard** 📈
```
FREE:
- Total downloads
- Last accessed time

PREMIUM:
- Download timeline graphs
- Top downloaded files
- Geographic data (country-wise downloads)
- User engagement metrics
- Download heatmaps (hourly/daily patterns)
- Export reports (PDF/CSV)
```

### 5. **User Experience Enhancements** ✨
```
- Web dashboard (share-box.com)
- Dark/Light theme for bot messages
- Multi-language support (English, Hindi, Spanish, etc.)
- File preview (images, videos without download)
- Search functionality (search your links)
- Favorites/Bookmarks
- Collections (group multiple links)
- Share to other platforms (WhatsApp, Email)
```

### 6. **File Management Pro** 📂
```
FREE:
- Basic upload
- Single file selection

PREMIUM:
- Drag-and-drop batch upload
- Folder upload (entire folder → 1 link)
- File compression (reduce size)
- Format conversion (video to audio, etc.)
- Video thumbnail customization
- File sorting (by name, size, date)
- Duplicate file detection
```

### 7. **Collaboration Features** 👥
```
PREMIUM ONLY:
- Shared links (multiple admins)
- Comment sections on links
- User roles (owner, editor, viewer)
- Activity logs (who accessed what)
- Team workspaces
```

### 8. **Integration & Automation** 🤖
```
PREMIUM ONLY:
- Webhook support (notify on downloads)
- Telegram channel auto-posting
- RSS feed generation
- Zapier/IFTTT integration
- API access (create/manage links programmatically)
- Chrome/Firefox extension
```

### 9. **Content Delivery Network (CDN)** 🌐
```
FREE: Standard speed
PREMIUM: 
- Priority CDN (faster downloads globally)
- Edge caching
- Parallel downloads
- Resume support
```

### 10. **Monetization for Users** 💰
```
PREMIUM SELLERS:
- Paid links (charge users for access)
- Subscription links (recurring payments)
- Affiliate tracking
- Payment gateway integration
```

---

## 🎨 USER INTERFACE IMPROVEMENTS

### 1. **Welcome Screen**
```
🎉 Welcome to Share-box by Univora!

📦 Share files, not worries.

🆓 FREE TIER:
• 20 files per link
• 10 active links
• 2GB per file
• Basic features

💎 PREMIUM TIER:
• Unlimited everything
• Password protection
• QR codes & more
• $4.99/month

👉 Get Started: /upload
💎 Go Premium: /upgrade
❓ Need Help: /help
```

### 2. **Modern Button Layouts**
- Inline keyboards with emojis
- Quick actions (✏️ Edit, 🗑️ Delete, 📊 Stats)
- Swipe navigation
- Context menus

### 3. **Rich Message Formatting**
- Progress bars for uploads
- File previews (thumbnails)
- Color-coded categories
- Status badges (🟢 Active, 🔴 Expired, 💎 Premium)

---

## 🏗️ TECHNICAL ARCHITECTURE

### **Database Schema Updates**

```javascript
// Users Collection
{
  user_id: Number,
  username: String,
  first_name: String,
  is_premium: Boolean,              // NEW
  premium_expiry: Date,             // NEW
  subscription_tier: String,        // NEW: "free", "premium", "lifetime"
  storage_used: Number,             // NEW: Track usage
  referral_code: String,            // NEW
  referred_by: Number,              // NEW
  joined_at: Date,
  last_seen: Date,
  is_blocked: Boolean,
  settings: {                       // NEW
    language: String,
    theme: String,
    notifications: Boolean
  }
}

// Links Collection
{
  link_id: String,
  admin_id: Number,
  files: Array,
  link_name: String,
  password: String,
  category: String,
  custom_categories: Array,         // NEW: User-defined categories
  created_at: Date,
  expires_at: Date,                 // NEW: Link expiration
  downloads: Number,
  max_downloads: Number,            // NEW: Download limit
  last_accessed: Date,
  is_active: Boolean,
  is_premium_link: Boolean,         // NEW: Flag premium links
  whitelist_users: Array,           // NEW: Access control
  forward_protection: Boolean,      // NEW
  scheduled_activation: Date,       // NEW
  scheduled_deactivation: Date,     // NEW
  analytics: {                      // NEW: Detailed analytics
    views: Number,
    unique_visitors: Array,
    download_history: Array
  }
}

// Subscriptions Collection (NEW)
{
  user_id: Number,
  plan: String,                     // "free", "premium_monthly", "premium_yearly"
  status: String,                   // "active", "expired", "cancelled"
  started_at: Date,
  expires_at: Date,
  payment_method: String,
  transaction_id: String,
  auto_renew: Boolean
}

// Referrals Collection (NEW)
{
  referrer_id: Number,
  referred_id: Number,
  status: String,                   // "pending", "completed"
  reward_given: Boolean,
  created_at: Date
}
```

### **Tech Stack**

```yaml
Backend:
  - Python 3.11+
  - python-telegram-bot 20.x
  - Flask (API & health checks)
  - MongoDB (database)
  - Redis (caching & rate limiting)

File Storage:
  - Telegram Channels (primary)
  - AWS S3 / Google Cloud Storage (backup for premium)

Payments:
  - Razorpay (India)
  - Stripe (Global)
  - Telegram Stars (in-app)

Analytics:
  - Custom MongoDB aggregations
  - Google Analytics (web dashboard)

Hosting:
  - Render (bot server)
  - Vercel (web dashboard)
  - MongoDB Atlas (database)
  - Redis Cloud (caching)
```

---

## 📱 COMMAND STRUCTURE

### **All Users**
```
/start - Start the bot
/help - Get help and commands
/mylinks - View your links (with pagination)
/upload - Upload files & create link
/delete - Delete a link
/linkinfo - Get link details
/getlink - Download files from link
/settings - Configure bot preferences
/upgrade - Upgrade to Premium 💎
/referral - Get referral link & rewards
```

### **Premium Users Only**
```
/generate - Advanced link creation with options
/qrcode - Generate QR code for link
/add - Add files to existing link
/bulkdelete - Delete multiple links
/import - Import from channels
/analytics - View detailed analytics
/schedule - Schedule link activation
/whitelist - Manage link access
/export - Export all data
```

### **Admin Only**
```
/ban - Ban a user
/unban - Unban a user
/blocklist - View blocked users
/stats - Bot statistics
/broadcast - Send message to all users
/grantpremium - Give premium to user
```

---

## 🎯 IMPLEMENTATION PHASES

### **Phase 1: Core Migration (Week 1-2)** ✅
- [ ] Set up new project structure in root folder
- [ ] Migrate database schema with new premium fields
- [ ] Implement free tier limits
- [ ] Basic bot commands working
- [ ] File upload/download functional

### **Phase 2: Premium System (Week 3-4)** 💎
- [ ] User subscription tracking
- [ ] Payment integration (Razorpay/Stripe)
- [ ] Premium feature restrictions
- [ ] Referral system
- [ ] Usage quota tracking

### **Phase 3: Advanced Features (Week 5-6)** 🚀
- [ ] Password protection for links
- [ ] QR code generation
- [ ] Custom link names
- [ ] Link scheduling
- [ ] Download limits
- [ ] User whitelisting

### **Phase 4: Analytics & Dashboard (Week 7-8)** 📊
- [ ] Basic analytics for free users
- [ ] Advanced analytics for premium
- [ ] Web dashboard (share-box.com)
- [ ] API endpoints
- [ ] Export functionality

### **Phase 5: UI/UX Polish (Week 9-10)** ✨
- [ ] Modern message designs
- [ ] Inline keyboards optimization
- [ ] Multi-language support
- [ ] Dark/Light themes
- [ ] File previews

### **Phase 6: Testing & Launch (Week 11-12)** 🎉
- [ ] Beta testing with selected users
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation completion
- [ ] Public launch

---

## 💰 PRICING STRATEGY

### **Free Tier** 🆓
- **Price:** $0
- **Target:** Casual users, students, trial users
- **Retention Strategy:** Limit features but provide strong value

### **Premium Monthly** 💎
- **Price:** $4.99/month
- **Target:** Regular users, content creators
- **Value Prop:** Unlimited storage, advanced features

### **Premium Yearly** 🎖️
- **Price:** $49.99/year (Save 17%)
- **Target:** Power users, businesses
- **Value Prop:** Best value, priority support

### **Lifetime** 👑
- **Price:** $199.99 (one-time)
- **Target:** Ultra loyal users, early adopters
- **Value Prop:** Never pay again

---

## 🎁 FREEMIUM CONVERSION TACTICS

1. **Smart Limits:**
   - Free users get good value (20 files/link is reasonable)
   - But power users will hit limits quickly

2. **Feature Teasing:**
   - Show lock icons 🔒 on premium features
   - "Upgrade to use passwords" prompts

3. **Time-based Trials:**
   - 7-day premium trial for new users
   - Seasonal promotions (50% off)

4. **Referral Rewards:**
   - Free users earn 1 month premium for 5 referrals
   - Premium users get discounts

5. **Usage Notifications:**
   - "You've used 8/10 links. Upgrade for unlimited"
   - "2GB limit reached. Premium users get 4GB"

---

## 🔐 SECURITY MEASURES

1. **Data Protection:**
   - End-to-end encryption for premium files
   - Secure password hashing (bcrypt)
   - Regular backups

2. **Access Control:**
   - IP-based rate limiting
   - User verification
   - Whitelist/Blacklist system

3. **Payment Security:**
   - PCI-compliant payment gateways
   - No credit card storage
   - Webhooks validation

4. **Abuse Prevention:**
   - CAPTCHA for suspicious activity
   - File scanning (malware detection)
   - DMCA compliance system

---

## 📈 SUCCESS METRICS

### **User Engagement**
- Daily Active Users (DAU)
- Monthly Active Users (MAU)
- Average files uploaded per user
- Link sharing rate

### **Conversion Metrics**
- Free → Premium conversion rate (Target: 5%)
- Trial → Paid conversion (Target: 20%)
- Churn rate (Target: <10% monthly)

### **Revenue Metrics**
- Monthly Recurring Revenue (MRR)
- Average Revenue Per User (ARPU)
- Customer Lifetime Value (CLV)

---

## 🌟 COMPETITIVE ADVANTAGES

1. **Telegram-Native:**
   - No app downloads needed
   - Instant access
   - Familiar interface

2. **Generous Free Tier:**
   - Better than competitors (10 files vs our 20)
   - No ads in free tier

3. **Advanced Features:**
   - QR codes, analytics, scheduling
   - Not available in similar bots

4. **Affordable Premium:**
   - $4.99/month vs competitors' $9.99
   - Yearly discount attractive

5. **Indian Market Focus:**
   - Razorpay for easy payments
   - Hindi language support
   - Competitive pricing for Indian users

---

## 📞 SUPPORT CHANNELS

- **Telegram Support:** @ShareBoxSupport
- **Email:** support@sharebox-univora.com
- **Documentation:** docs.sharebox.com
- **Community:** t.me/ShareBoxCommunity
- **Status Page:** status.sharebox.com

---

## 📝 LICENSE & CREDITS

**Developed by:** Univora Team  
**License:** Proprietary (All Rights Reserved)  
**Version:** 1.0.0  
**Last Updated:** February 2026  

---

## 🎯 NEXT STEPS

1. ✅ **Read this README completely**
2. 📋 **Review feature priorities**
3. 💬 **Discuss implementation approach**
4. 🚀 **Begin Phase 1 development**

---

**Ready to build Share-box?** 🚀  
**Let's create the best file-sharing bot on Telegram!** 📦✨
