# 🚀 Share-box by Univora - Deployment Guide

Complete guide to deploy your advanced file-sharing bot **100% FREE**!

---

## 📋 Prerequisites

Before starting, make sure you have:

1. ✅ **Telegram Bot Token** - Get from [@BotFather](https://t.me/BotFather)
2. ✅ **MongoDB Atlas Account** - [Free 512MB cluster](https://www.mongodb.com/cloud/atlas/register)
3. ✅ **3 Telegram Channels** - Create private channels for file storage
4. ✅ **Render Account** - [Free hosting](https://render.com)
5. ✅ **Your Telegram ID** - Get from [@userinfobot](https://t.me/userinfobot)

---

## 🤖 Step 1: Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Choose a name: `Share-box by Univora`
4. Choose a username: `YourUsername_sharebox_bot`
5. Copy the **Bot Token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. Send `/setcommands` to BotFather
7. Select your bot
8. Send this command list:

```
start - 🏠 Start the bot
help - ❓ Get help
upload - 📤 Upload files
mylinks - 🔗 View your links
getlink - 📥 Download from link
stats - 📊 Your statistics
settings - ⚙️ Bot settings
referral - 🎁 Referral program
upgrade - 💎 Get premium
```

---

## 📦 Step 2: Create Storage Channels

You need 3 private channels for **file persistence** (files stay even if bot is deleted):

### Creating Each Channel:

1. Open Telegram
2. Click "New Channel"
3. Name: `Share-box Storage 1` (or 2, 3)
4. Type: **Private Channel**
5. Click "Create"
6. Add your bot as **Administrator** with:
   - ✅ Post messages
   - ✅ Edit messages
   - ✅ Delete messages

### Get Channel IDs:

1. Forward any message from channel to [@userinfobot](https://t.me/userinfobot)
2. Copy the channel ID (looks like: `-1001234567890`)
3. Repeat for all 3 channels

---

## 💾 Step 3: Setup MongoDB Atlas (FREE)

### Create Cluster:

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Click "Build a Database"
3. Choose **M0 FREE** tier
4. Select closest region
5. Name cluster: `sharebox-cluster`
6. Click "Create"

### Create Database User:

1. Click "Database Access" (left sidebar)
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Username: `sharebox_admin`
5. Password: Generate secure password (save it!)
6. Database User Privileges: "Read and write to any database"
7. Click "Add User"

### Whitelist IP:

1. Click "Network Access" (left sidebar)
2. Click "Add IP Address"
3. Click "Allow Access from Anywhere" (0.0.0.0/0)
4. Click "Confirm"

### Get Connection String:

1. Click "Database" (left sidebar)
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Copy the connection string (looks like: `mongodb+srv://sharebox_admin:<password>@sharebox-cluster.xxxxx.mongodb.net/`)
5. Replace `<password>` with your database password
6. **Save this connection string!**

---

## 🔧 Step 4: Configure Environment Variables

Open the `.env` file and fill in your values:

```env
# Bot Configuration
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=your_telegram_id_here

# MongoDB Configuration
MONGO_URI=mongodb+srv://sharebox_admin:YOUR_PASSWORD@sharebox-cluster.xxxxx.mongodb.net/

# Storage Channels (Your 3 channel IDs)
PRIMARY_CHANNEL=-1001234567890
BACKUP_CHANNEL_1=-1001234567891
BACKUP_CHANNEL_2=-1001234567892

# Server Configuration (Will get from Render later)
PORT=10000
WEBHOOK_URL=

# Bot Settings
BOT_NAME=Share-box by Univora
BOT_USERNAME=@YourBotUsername
BRAND_NAME=Univora 📦
```

---

## 🌐 Step 5: Deploy to Render (FREE 24/7 Hosting)

### Create Render Account:

1. Go to [Render.com](https://render.com)
2. Sign up with GitHub
3. Verify email

### Deploy Bot:

#### Option A: Deploy from GitHub (Recommended)

1. **Push code to GitHub:**
   ```bash
   cd "c:/ALL FINAL PROJECTS/BOTS/SHARE_BOX_BOT"
   git init
   git add .
   git commit -m "Initial commit - Share-box bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/sharebox-bot.git
   git push -u origin main
   ```

2. **Create Web Service on Render:**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Name: `sharebox-bot`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
   - Plan: **Free**

3. **Add Environment Variables:**
   - In Render dashboard, go to "Environment"
   - Add all variables from your `.env` file
   - Click "Save Changes"

4. **Deploy:**
   - Click "Create Web Service"
   - Wait for deployment (2-3 minutes)
   - Copy your Render URL (like: `https://sharebox-bot.onrender.com`)

5. **Update WEBHOOK_URL:**
   - Go back to Environment variables
   - Set `WEBHOOK_URL=https://sharebox-bot.onrender.com`
   - Save changes

#### Option B: Deploy with render.yaml

1. Make sure `render.yaml` is in your repository
2. Go to Render Dashboard
3. Click "New +" → "Blueprint"
4. Connect repository
5. Render will auto-detect `render.yaml`
6. Add environment variables
7. Click "Apply"

---

## 🔄 Step 6: Keep Bot Alive 24/7 (FREE)

Render free tier sleeps after 15 minutes of inactivity. Use **UptimeRobot** to keep it awake:

1. Go to [UptimeRobot.com](https://uptimerobot.com)
2. Sign up (free)
3. Click "Add New Monitor"
4. Monitor Type: **HTTP(s)**
5. Friendly Name: `Share-box Bot`
6. URL: `https://your-render-url.onrender.com/health`
7. Monitoring Interval: **5 minutes**
8. Click "Create Monitor"

✅ Your bot is now **100% online 24/7** for FREE!

---

## ✅ Step 7: Verify Everything Works

### Test Bot:

1. Open Telegram
2. Search for your bot: `@YourBotUsername``
3. Send `/start`
4. You should see the welcome message! 🎉

### Test File Upload:

1. Send `/upload`
2. Send a test file
3. Send `/done`
4. Select category
5. You should get a shareable link!

### Test Link Access:

1. Copy the generated link
2. Open in new chat or send to friend
3. Click the link
4. Files should be downloaded!

### Check Web Interface:

1. Open: `https://your-render-url.onrender.com`
2. You should see the beautiful web dashboard!

### Check Health:

1. Open: `https://your-render-url.onrender.com/health`
2. Should return: `{"status": "healthy", ...}`

---

## 🎯 Step 8: Admin Commands

As admin, you have special powers:

```bash
# User Management
/ban USER_ID - Ban a user
/unban USER_ID - Unban a user

# Premium Management
/grantpremium USER_ID - Grant lifetime premium
/grantpremium USER_ID 30 - Grant 30 days premium

# Statistics
/adminstats - View bot statistics

# Communication
/broadcast MESSAGE - Send message to all users
```

---

## 🔐 Security Best Practices

1. **Never share your `.env` file**
2. **Never commit `.env` to GitHub** (already in `.gitignore`)
3. **Keep bot token secret**
4. **Use strong MongoDB password**
5. **Regularly backup MongoDB database**

---

## 🛠️ Troubleshooting

### Bot Not Responding:

1. Check Render logs for errors
2. Verify all environment variables are set
3. Check MongoDB connection string
4. Ensure bot is admin in all 3 channels

### Files Not Uploading:

1. Verify channel IDs are correct (include the `-100` prefix)
2. Check bot has admin rights in channels
3. Check file size limits

### Database Errors:

1. Verify MongoDB URI is correct
2. Check network access allows all IPs (0.0.0.0/0)
3. Verify database user has read/write permissions

### Bot Sleeping:

1. Ensure UptimeRobot monitor is active
2. Check monitor interval is 5 minutes
3. Verify health endpoint works

---

## 📊 Monitoring & Logs

### View Logs:

1. Go to Render Dashboard
2. Click on your service
3. Click "Logs" tab
4. See real-time logs

### Monitor Statistics:

1. Use `/adminstats` command
2. Check web dashboard: `https://your-url.onrender.com/stats`

---

## 🔄 Updates & Maintenance

### Update Bot Code:

1. Make changes to code
2. Commit to GitHub:
   ```bash
   git add .
   git commit -m "Update: description"
   git push
   ```
3. Render auto-deploys! (if auto-deploy enabled)

### Manual Deploy:

1. Go to Render Dashboard
2. Click "Manual Deploy" → "Deploy latest commit"

### Backup Database:

1. Go to MongoDB Atlas
2. Click "..." on cluster
3. Choose "Take Snapshot"

---

## 💡 Tips for Success

1. **Test thoroughly** before sharing with users
2. **Monitor logs** regularly for errors
3. **Backup database** weekly
4. **Keep dependencies updated**
5. **Engage with users** - use broadcast feature
6. **Track analytics** - use /adminstats

---

## 🎉 You're All Set!

Your advanced Share-box bot is now:

✅ **Live 24/7** on Render  
✅ **Data persistent** in MongoDB  
✅ **Files safe** in 3 backup channels  
✅ **Modern UI** with inline keyboards  
✅ **Analytics enabled**  
✅ **Free & Premium** tiers ready  
✅ **100% FREE** to run!

---

## 📞 Need Help?

- Check logs in Render dashboard
- Review MongoDB connection
- Verify all environment variables
- Re-read this guide carefully

---

## 🚀 Next Steps

1. **Share your bot** with friends
2. **Customize messages** in `config.py`
3. **Add more features** as needed
4. **Consider premium payment** integration later
5. **Keep improving** based on user feedback!

---

**Enjoy your advanced file-sharing bot!** 📦✨

Made with ❤️ by Univora Team
