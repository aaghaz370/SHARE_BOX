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

    def get_user_storage_used(self, user_id: int) -> int:
        """Get user storage used in bytes"""
        user = self.users.find_one({"user_id": user_id}, {"storage_used": 1})
        return user.get("storage_used", 0) if user else 0
    
    def update_user_storage(self, user_id: int, storage_delta: int) -> bool:
        """Update user storage (can be negative)"""
        result = self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"storage_used": storage_delta}}
        )
        return result.modified_count > 0
    
    def set_user_plan(self, user_id: int, plan_type: str) -> bool:
        """Set user plan"""
        plan_config = config.PLANS.get(plan_type)
        if not plan_config: return False
        
        duration = plan_config.get("duration_days", 30)
        expiry = datetime.now(pytz.UTC) + timedelta(days=duration)
        
        # Reset monthly count if upgrading
        update_data = {
            "plan_type": plan_type,
            "premium_expiry": expiry,
            "is_premium": plan_type != config.PlanTypes.FREE,
            "last_link_reset": datetime.now(pytz.UTC),
            "monthly_link_count": 0
        }
        
        result = self.users.update_one(
            {"user_id": user_id},
            {"$set": update_data},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    def get_user_plan_id(self, user_id: int) -> str:
        """Get user plan ID (handles expiry)"""
        # Admins are always lifetime
        if user_id in config.ADMIN_IDS:
            return config.PlanTypes.LIFETIME
            
        user = self.get_user(user_id)
        if not user:
            return config.PlanTypes.FREE
            
        plan_type = user.get("plan_type", config.PlanTypes.FREE)
        expiry = user.get("premium_expiry")
        
        # Check expiry if not FREE and not LIFETIME (though lifetime usually has far future expiry)
        if plan_type != config.PlanTypes.FREE and plan_type != config.PlanTypes.LIFETIME:
            if expiry:
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=pytz.UTC)
                if datetime.now(pytz.UTC) > expiry:
                    # Downgrade to free if expired
                    self.users.update_one(
                        {"user_id": user_id}, 
                        {"$set": {"plan_type": config.PlanTypes.FREE, "is_premium": False}}
                    )
                    return config.PlanTypes.FREE
                
        return plan_type

    def get_plan_details(self, user_id: int) -> dict:
        """Get full plan configuration dict"""
        plan_id = self.get_user_plan_id(user_id)
        return config.PLANS.get(plan_id, config.PLANS[config.PlanTypes.FREE])

    def increment_monthly_link_count(self, user_id: int) -> int:
        """Increment link count, resetting if month changed"""
        user = self.get_user(user_id)
        if not user: return 0
        
        now = datetime.now(pytz.UTC)
        
        last_reset = user.get("last_link_reset")
        if not last_reset:
             # First time
             self.users.update_one(
                {"user_id": user_id},
                {"$set": {"last_link_reset": now, "monthly_link_count": 1}}
             )
             return 1
             
        if last_reset.tzinfo is None:
             last_reset = last_reset.replace(tzinfo=pytz.UTC)
             
        # Check if month changed
        if now.month != last_reset.month or now.year != last_reset.year:
            # Reset
            self.users.update_one(
                {"user_id": user_id},
                {"$set": {"monthly_link_count": 1, "last_link_reset": now}}
            )
            return 1
        else:
            # Increment
            self.users.update_one(
                {"user_id": user_id},
                {"$inc": {"monthly_link_count": 1}}
            )
            return user.get("monthly_link_count", 0) + 1

    def check_monthly_limit(self, user_id: int) -> bool:
        """Check if user can create more links this month"""
        plan_id = self.get_user_plan_id(user_id)
        plan = config.PLANS.get(plan_id, config.PLANS[config.PlanTypes.FREE])
        limit = plan.get("max_active_links", 10)
        
        # Unlimited check
        if limit > 99999: return True
        
        user = self.get_user(user_id)
        if not user: return True
        
        # Check reset logic first (readonly check)
        now = datetime.now(pytz.UTC)
        last_reset = user.get("last_link_reset")
        current_count = user.get("monthly_link_count", 0)
        
        if last_reset:
             if last_reset.tzinfo is None: last_reset = last_reset.replace(tzinfo=pytz.UTC)
             if now.month != last_reset.month or now.year != last_reset.year:
                 current_count = 0 # Will be reset on next increment
        
        return current_count < limit

    def is_user_premium(self, user_id: int) -> bool:
        """Check if user has active premium (Legacy Compatibility)"""
        return self.get_user_plan_id(user_id) != config.PlanTypes.FREE

    def grant_premium(self, user_id: int, duration_days: int = None) -> bool:
        """Grant premium (Legacy - Maps to closest plan)"""
        if duration_days:
            if duration_days <= 1: 
                return self.set_user_plan(user_id, config.PlanTypes.DAILY)
            elif duration_days <= 31: 
                return self.set_user_plan(user_id, config.PlanTypes.MONTHLY)
            elif duration_days <= 62: 
                return self.set_user_plan(user_id, config.PlanTypes.BIMONTHLY)
            else: 
                return self.set_user_plan(user_id, config.PlanTypes.LIFETIME)
        else:
             return self.set_user_plan(user_id, config.PlanTypes.LIFETIME)
    
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
        """Create new link based on user plan"""
        
        user = self.get_user(admin_id)
        if not user: return None
        
        plan = self.get_plan_details(admin_id)
        plan_id = self.get_user_plan_id(admin_id)
        is_premium = plan_id != config.PlanTypes.FREE
        
        # Check Limits
        
        # 1. Active Links / Monthly Limit logic
        # Handled by check_link_creation_limit or checked here?
        # Let's re-verify monthly limit here just in case
        if not self.check_monthly_limit(admin_id) and admin_id not in config.ADMIN_IDS:
            return None
            
        # 2. Files per link
        max_files = plan.get("max_files_per_link", 20)
        if max_files < 99999 and len(files_data) > max_files and admin_id not in config.ADMIN_IDS:
            return None
            
        # 3. Password Check (Only premium features?)
        # User didn't specify free users can't use password, but usually they can't.
        # Assuming only premium for now as per previous logic.
        if password and not is_premium and admin_id not in config.ADMIN_IDS:
             return None
             
        # 4. Storage Check
        total_size = sum(f.get("file_size", 0) for f in files_data)
        storage_limit = plan.get("storage_bytes", 50 * 1024 * 1024 * 1024)
        
        if admin_id not in config.ADMIN_IDS:
            if storage_limit < 999999999999 and (user.get("storage_used", 0) + total_size) > storage_limit:
                return None

        # Generate link
        link_id = self.generate_link_id()
        
        # Calculate expiry
        # Plan expiry days
        plan_expiry_days = plan.get("link_expiry_days", 60)
        
        # If expires_in_days provided (e.g. custom), use it, otherwise plan default
        # But if plan has max limit, we should cap it? 
        # User requirements say specific expiry per plan.
        # "link expiry 6month" for daily plan.
        
        if expires_in_days:
            expiry_delta = expires_in_days
        else:
            expiry_delta = plan_expiry_days
            
        # Lifetime check
        if expiry_delta > 30000: # Approx 80 years
             expires_at = None
        else:
             expires_at = datetime.now(pytz.UTC) + timedelta(days=expiry_delta)
        
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
        
        # Increment Monthly Count
        if admin_id not in config.ADMIN_IDS:
             self.increment_monthly_link_count(admin_id)
        
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
        
    def update_link(self, link_id: str, updates: Dict) -> bool:
        """Update link fields"""
        result = self.links.update_one(
            {"link_id": link_id},
            {"$set": updates}
        )
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
            "status": "completed", # Auto-complete on join
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
            "completed_referrals": completed,
            "pending_referrals": total - completed
        }

    def check_referral_milestones(self, referrer_id: int) -> tuple[bool, str, int]:
        """Check and grant referral milestones (10, 30, 100)"""
        referrer = self.get_user(referrer_id)
        if not referrer: return False, "", 0
        
        total_refs = self.referrals.count_documents({"referrer_id": referrer_id, "status": "completed"})
        claimed = referrer.get("referral_milestones", [])
        if not isinstance(claimed, list): claimed = []
        
        milestones = [
            (10, config.PlanTypes.MONTHLY, "Monthly Starter", 30),
            (30, config.PlanTypes.BIMONTHLY, "Bi-Monthly Pro", 60),
            (100, config.PlanTypes.YEARLY, "Yearly Premium", 365) 
        ]
        
        for count, plan_type, display_name, days in milestones:
            if total_refs >= count and count not in claimed:
                self.set_user_plan(referrer_id, plan_type)
                
                self.users.update_one(
                    {"user_id": referrer_id},
                    {"$push": {"referral_milestones": count}}
                )
                
                return True, display_name, days
                
        return False, "", 0
    
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
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get comprehensive user statistics"""
        try:
            pipeline = [
                {"$match": {"admin_id": user_id, "is_active": True}},
                {
                    "$group": {
                        "_id": None,
                        "total_links": {"$sum": 1},
                        "total_files": {"$sum": {"$size": "$files"}},
                        "total_storage": {"$sum": "$total_size"},
                        "total_views": {"$sum": "$views"},
                        "total_downloads": {"$sum": "$downloads"}
                    }
                }
            ]
            
            result = list(self.links.aggregate(pipeline))
            stats = {
                "total_links": 0, "total_files": 0, "storage_used": 0,
                "total_views": 0, "total_downloads": 0,
                "category_breakdown": {}
            }
            
            if result:
                res = result[0]
                stats.update({
                    "total_links": res.get("total_links", 0),
                    "total_files": res.get("total_files", 0),
                    "storage_used": res.get("total_storage", 0),
                    "total_views": res.get("total_views", 0),
                    "total_downloads": res.get("total_downloads", 0)
                })

            # Category breakdown
            cat_pipeline = [
                {"$match": {"admin_id": user_id, "is_active": True}},
                {"$group": {"_id": "$category", "count": {"$sum": 1}}}
            ]
            cats = list(self.links.aggregate(cat_pipeline))
            stats["category_breakdown"] = {c["_id"]: c["count"] for c in cats}
            
            return stats
            
        except Exception as e:
            # print(f"Stats Error: {e}") # Silent error
            return {"total_links": 0, "total_files": 0, "storage_used": 0, "category_breakdown": {}}

    def get_user_analytics(self, user_id: int) -> dict:
        """Alias for get_user_stats"""
        return self.get_user_stats(user_id)

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

# Initialize database singleton
db = Database()
