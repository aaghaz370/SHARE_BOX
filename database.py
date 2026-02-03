"""
Share-box by Univora - Advanced Database Module
MongoDB operations with async support and advanced features
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import secrets
import pytz
import config

class Database:
    """Advanced database manager with singleton pattern"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialize MongoDB connection
        self.client = MongoClient(
            config.MONGO_URI,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True
        )
        
        self.db = self.client[config.DATABASE_NAME]
        
        # Collections
        self.users = self.db.users
        self.links = self.db.links
        self.analytics = self.db.analytics
        self.referrals = self.db.referrals
        self.settings = self.db.settings
        
        # Create indexes
        self._create_indexes()
        
        self._initialized = True
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Users indexes
            self.users.create_index([("user_id", ASCENDING)], unique=True)
            self.users.create_index([("username", ASCENDING)])
            self.users.create_index([("is_premium", ASCENDING)])
            self.users.create_index([("referral_code", ASCENDING)], unique=True, sparse=True)
            
            # Links indexes
            self.links.create_index([("link_id", ASCENDING)], unique=True)
            self.links.create_index([("admin_id", ASCENDING)])
            self.links.create_index([("is_active", ASCENDING)])
            self.links.create_index([("category", ASCENDING)])
            self.links.create_index([("created_at", DESCENDING)])
            self.links.create_index([("expires_at", ASCENDING)])
            
            # Analytics indexes
            self.analytics.create_index([("link_id", ASCENDING)])
            self.analytics.create_index([("user_id", ASCENDING)])
            self.analytics.create_index([("timestamp", DESCENDING)])
            self.analytics.create_index([("event_type", ASCENDING)])
            
            # Referrals indexes
            self.referrals.create_index([("referrer_id", ASCENDING)])
            self.referrals.create_index([("referred_id", ASCENDING)])
            
        except Exception as e:
            print(f"⚠️  Index creation warning: {e}")
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, user_id: int, username: str = None, first_name: str = None) -> Dict:
        """Create or update user"""
        
        # Generate unique referral code
        referral_code = self._generate_referral_code()
        
        user_data = {
            "user_id": user_id,
            "is_premium": False,
            "premium_expiry": None,
            "subscription_tier": "free",
            "storage_used": 0,
            "referral_code": referral_code,
            "referred_by": None,
            "joined_at": datetime.now(pytz.UTC),
            "is_blocked": False,
            "total_links": 0,
            "total_downloads": 0,
            "total_views": 0,
            "settings": {
                "language": "en",
                "notifications": True,
                "default_category": "🗂️ Others",
                "auto_delete_files": True
            }
        }
        
        result = self.users.update_one(
            {"user_id": user_id},
            {
                "$setOnInsert": user_data,
                "$set": {
                    "username": username,
                    "first_name": first_name,
                    "last_seen": datetime.now(pytz.UTC)
                }
            },
            upsert=True
        )
        
        return self.get_user(user_id)
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return self.users.find_one({"user_id": user_id})
    
    def update_user_storage(self, user_id: int, storage_delta: int) -> bool:
        """Update user storage (can be negative)"""
        result = self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"storage_used": storage_delta}}
        )
        return result.modified_count > 0
    
    def is_user_premium(self, user_id: int) -> bool:
        """Check if user has active premium"""
        user = self.get_user(user_id)
        if not user or not user.get("is_premium"):
            return False
        
        expiry = user.get("premium_expiry")
        if not expiry:
            return True  # Lifetime premium
        
        # Ensure timezone aware
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=pytz.UTC)
        
        return datetime.now(pytz.UTC) < expiry
    
    def grant_premium(self, user_id: int, duration_days: int = None) -> bool:
        """Grant premium to user (None = lifetime)"""
        update_data = {
            "is_premium": True,
            "subscription_tier": "premium"
        }
        
        if duration_days:
            expiry = datetime.now(pytz.UTC) + timedelta(days=duration_days)
            update_data["premium_expiry"] = expiry
        else:
            update_data["premium_expiry"] = None  # Lifetime
        
        result = self.users.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def revoke_premium(self, user_id: int) -> bool:
        """Revoke premium from user"""
        result = self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "is_premium": False,
                    "subscription_tier": "free",
                    "premium_expiry": None
                }
            }
        )
        return result.modified_count > 0
    
    def block_user(self, user_id: int) -> bool:
        """Block user"""
        result = self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_blocked": True}}
        )
        return result.modified_count > 0
    
    def unblock_user(self, user_id: int) -> bool:
        """Unblock user"""
        result = self.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_blocked": False}}
        )
        return result.modified_count > 0
    
    def get_all_users(self, include_blocked: bool = False) -> List[Dict]:
        """Get all users"""
        query = {} if include_blocked else {"is_blocked": False}
        return list(self.users.find(query))
    
    def get_blocked_users(self) -> List[Dict]:
        """Get blocked users"""
        return list(self.users.find({"is_blocked": True}))
    
    def update_user_settings(self, user_id: int, settings: Dict) -> bool:
        """Update user settings"""
        result = self.users.update_one(
            {"user_id": user_id},
            {"$set": {f"settings.{k}": v for k, v in settings.items()}}
        )
        return result.modified_count > 0
    
    # ==================== LINK OPERATIONS ====================
    
    def generate_link_id(self) -> str:
        """Generate unique link ID"""
        while True:
            link_id = secrets.token_urlsafe(6)[:8]
            if not self.links.find_one({"link_id": link_id}):
                return link_id
    
    def create_link(
        self,
        admin_id: int,
        files_data: List[Dict],
        link_name: str = "",
        password: str = None,
        category: str = "🗂️ Others",
        expires_in_days: int = None
    ) -> Optional[str]:
        """Create new link"""
        
        user = self.get_user(admin_id)
        if not user:
            return None
        
        is_premium = self.is_user_premium(admin_id)
        
        # Check limits
        if not is_premium:
            # Free tier checks
            active_links = self.get_user_active_links_count(admin_id)
            if active_links >= config.FreeLimits.MAX_ACTIVE_LINKS:
                return None
            
            if len(files_data) > config.FreeLimits.MAX_FILES_PER_LINK:
                return None
            
            # No password for free users
            if password:
                return None
        
        # Calculate total size
        total_size = sum(f.get("file_size", 0) for f in files_data)
        
        # Check storage limit
        max_storage = config.PremiumLimits.TOTAL_STORAGE_BYTES if is_premium else config.FreeLimits.TOTAL_STORAGE_BYTES
        if user.get("storage_used", 0) + total_size > max_storage:
            return None
        
        # Generate link
        link_id = self.generate_link_id()
        
        # Calculate expiry
        if is_premium:
            expires_at = None if not expires_in_days else datetime.now(pytz.UTC) + timedelta(days=expires_in_days)
        else:
            expires_at = datetime.now(pytz.UTC) + timedelta(days=config.FreeLimits.LINK_EXPIRY_DAYS)
        
        link_doc = {
            "link_id": link_id,
            "admin_id": admin_id,
            "files": files_data,
            "link_name": link_name or f"Link {link_id}",
            "password": password,
            "category": category,
            "created_at": datetime.now(pytz.UTC),
            "expires_at": expires_at,
            "downloads": 0,
            "views": 0,
            "last_accessed": None,
            "is_active": True,
            "is_premium_link": is_premium,
            "total_size": total_size,
            "whitelist_users": [],
            "max_downloads": None,
            "forward_protection": False,
            "scheduled_activation": None,
            "scheduled_deactivation": None
        }
        
        self.links.insert_one(link_doc)
        
        # Update user stats
        self.users.update_one(
            {"user_id": admin_id},
            {
                "$inc": {
                    "storage_used": total_size,
                    "total_links": 1
                }
            }
        )
        
        return link_id
    
    def get_link(self, link_id: str) -> Optional[Dict]:
        """Get link by ID"""
        link = self.links.find_one({"link_id": link_id, "is_active": True})
        
        # Check if expired
        if link and link.get("expires_at"):
            expires_at = link["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=pytz.UTC)
                
            if datetime.now(pytz.UTC) > expires_at:
                self.delete_link(link_id)
                return None
        
        return link
    
    def get_user_links(
        self,
        admin_id: int,
        category: str = None,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict]:
        """Get user's links with pagination"""
        query = {"admin_id": admin_id, "is_active": True}
        
        if category:
            query["category"] = category
        
        return list(
            self.links.find(query)
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
    
    def get_user_active_links_count(self, admin_id: int) -> int:
        """Count user's active links"""
        return self.links.count_documents({"admin_id": admin_id, "is_active": True})
    
    def add_files_to_link(self, link_id: str, files_data: List[Dict]) -> bool:
        """Add files to existing link"""
        link = self.get_link(link_id)
        if not link:
            return False
        
        # Calculate new total size
        additional_size = sum(f.get("file_size", 0) for f in files_data)
        
        result = self.links.update_one(
            {"link_id": link_id},
            {
                "$push": {"files": {"$each": files_data}},
                "$inc": {"total_size": additional_size}
            }
        )
        
        # Update user storage
        if result.modified_count > 0:
            self.update_user_storage(link["admin_id"], additional_size)
        
        return result.modified_count > 0
    
    def remove_file_from_link(self, link_id: str, file_index: int) -> bool:
        """Remove specific file from link"""
        link = self.get_link(link_id)
        if not link or file_index >= len(link["files"]):
            return False
        
        removed_file = link["files"][file_index]
        removed_size = removed_file.get("file_size", 0)
        
        link["files"].pop(file_index)
        
        if len(link["files"]) == 0:
            return self.delete_link(link_id)
        
        result = self.links.update_one(
            {"link_id": link_id},
            {
                "$set": {"files": link["files"]},
                "$inc": {"total_size": -removed_size}
            }
        )
        
        # Update user storage
        if result.modified_count > 0:
            self.update_user_storage(link["admin_id"], -removed_size)
        
        return result.modified_count > 0
    
    def delete_link(self, link_id: str) -> bool:
        """Soft delete link and free storage"""
        link = self.links.find_one({"link_id": link_id})
        if not link:
            return False
        
        result = self.links.update_one(
            {"link_id": link_id},
            {"$set": {"is_active": False}}
        )
        
        # Free up storage
        if result.modified_count > 0:
            total_size = link.get("total_size", 0)
            self.update_user_storage(link["admin_id"], -total_size)
        
        return result.modified_count > 0
    
    def increment_link_downloads(self, link_id: str) -> bool:
        """Increment download counter"""
        result = self.links.update_one(
            {"link_id": link_id},
            {
                "$inc": {"downloads": 1},
                "$set": {"last_accessed": datetime.now(pytz.UTC)}
            }
        )
        
        # Update user stats
        link = self.get_link(link_id)
        if link:
            self.users.update_one(
                {"user_id": link["admin_id"]},
                {"$inc": {"total_downloads": 1}}
            )
        
        return result.modified_count > 0
    
    def increment_link_views(self, link_id: str) -> bool:
        """Increment view counter"""
        result = self.links.update_one(
            {"link_id": link_id},
            {"$inc": {"views": 1}}
        )
        
        # Update user stats
        link = self.get_link(link_id)
        if link:
            self.users.update_one(
                {"user_id": link["admin_id"]},
                {"$inc": {"total_views": 1}}
            )
        
        return result.modified_count > 0
    
    # ==================== ANALYTICS ====================
    
    def log_event(
        self,
        event_type: str,
        user_id: int = None,
        link_id: str = None,
        metadata: Dict = None
    ):
        """Log analytics event"""
        if not config.ENABLE_ANALYTICS:
            return
        
        event = {
            "event_type": event_type,
            "user_id": user_id,
            "link_id": link_id,
            "metadata": metadata or {},
            "timestamp": datetime.now(pytz.UTC)
        }
        
        self.analytics.insert_one(event)
    
    def get_user_analytics(self, user_id: int) -> Dict:
        """Get user analytics"""
        links = list(self.links.find({"admin_id": user_id, "is_active": True}))
        
        total_downloads = sum(l.get("downloads", 0) for l in links)
        total_views = sum(l.get("views", 0) for l in links)
        
        # Category breakdown
        category_stats = {}
        for link in links:
            cat = link.get("category", "Others")
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        return {
            "total_links": len(links),
            "total_downloads": total_downloads,
            "total_views": total_views,
            "category_breakdown": category_stats
        }
    
    # ==================== REFERRAL SYSTEM ====================
    
    def _generate_referral_code(self) -> str:
        """Generate unique referral code"""
        while True:
            code = secrets.token_urlsafe(8)[:10].upper()
            if not self.users.find_one({"referral_code": code}):
                return code
    
    def apply_referral(self, referred_id: int, referral_code: str) -> bool:
        """Apply referral code to new user"""
        if not config.ENABLE_REFERRALS:
            return False
        
        # Find referrer
        referrer = self.users.find_one({"referral_code": referral_code})
        if not referrer:
            return False
        
        # Don't allow self-referral
        if referrer["user_id"] == referred_id:
            return False
        
        # Update referred user
        self.users.update_one(
            {"user_id": referred_id},
            {"$set": {"referred_by": referrer["user_id"]}}
        )
        
        # Log referral
        self.referrals.insert_one({
            "referrer_id": referrer["user_id"],
            "referred_id": referred_id,
            "status": "pending",
            "reward_given": False,
            "created_at": datetime.now(pytz.UTC)
        })
        
        return True
    
    def get_referral_stats(self, user_id: int) -> Dict:
        """Get referral statistics"""
        total = self.referrals.count_documents({"referrer_id": user_id})
        completed = self.referrals.count_documents({"referrer_id": user_id, "status": "completed"})
        
        return {
            "total_referrals": total,
            "completed_referrals": completed,
            "pending_referrals": total - completed
        }
    
    # ==================== ADMIN STATS ====================
    
    def get_global_stats(self) -> Dict:
        """Get global bot statistics"""
        total_users = self.users.count_documents({})
        free_users = self.users.count_documents({"is_premium": False})
        premium_users = self.users.count_documents({"is_premium": True})
        
        total_links = self.links.count_documents({"is_active": True})
        total_files = sum(
            len(link.get("files", []))
            for link in self.links.find({"is_active": True})
        )
        
        # Calculate total storage
        total_storage = sum(
            link.get("total_size", 0)
            for link in self.links.find({"is_active": True})
        )
        
        # Calculate total downloads/views
        total_downloads = sum(
            link.get("downloads", 0)
            for link in self.links.find({"is_active": True})
        )
        
        total_views = sum(
            link.get("views", 0)
            for link in self.links.find({"is_active": True})
        )
        
        return {
            "total_users": total_users,
            "free_users": free_users,
            "premium_users": premium_users,
            "total_links": total_links,
            "total_files": total_files,
            "total_storage": total_storage,
            "total_downloads": total_downloads,
            "total_views": total_views
        }
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

# Initialize database singleton
db = Database()
