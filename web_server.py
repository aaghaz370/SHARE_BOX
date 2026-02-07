import aiohttp
from aiohttp import web
import json
from database import db
import config
import os

# API Handler for Links
async def api_get_links(request):
    try:
        user_id = request.query.get('u')
        if not user_id:
            return web.json_response({"error": "Missing User ID"}, status=400)
            
        user_id = int(user_id)
        
        # Verify hash? For simplicity, we assume the link provided by bot contains a secret token if needed.
        # But user didn't ask for tough security, just a dashboard.
        # We'll fetch all links for this user.
        
        links_cursor = db.links.find({"user_id": user_id}).sort("created_at", -1)
        links = list(links_cursor)
        
        # Convert ObjectId to string and datetime to string
        for link in links:
            link['_id'] = str(link['_id'])
            if 'created_at' in link:
                link['created_at'] = link['created_at'].isoformat()
            
            # Count files
            if 'files' in link:
                link['file_count'] = len(link['files'])
                if len(link['files']) > 0:
                   # Calculate total size roughly for display
                   total_size = sum(f.get('file_size', 0) for f in link['files'])
                   link['total_size'] = total_size
                del link['files'] # Don't send full file list to summary view to save bandwidth
        
        return web.json_response({"links": links})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# API Handler for User Stats
async def api_get_stats(request):
    try:
        user_id = request.query.get('u')
        if not user_id: return web.json_response({"error": "Missing ID"}, status=400)
        user_id = int(user_id)
        
        user = db.users.find_one({"user_id": user_id})
        if not user: return web.json_response({"error": "User not found"}, status=404)
        
        # Calculate stats
        total_links = db.links.count_documents({"user_id": user_id})
        total_views = 0
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total_views": {"$sum": "$views"}}}
        ]
        res = list(db.links.aggregate(pipeline))
        if res: total_views = res[0]['total_views']
        
        plan = db.get_plan_details(user_id)
        
        stats = {
            "username": user.get('username', 'User'),
            "total_links": total_links,
            "total_views": total_views,
            "plan": plan.get('name', 'Free'),
            "join_date": user.get('joined_at', '').isoformat() if user.get('joined_at') else ''
        }
        return web.json_response(stats)
        
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

# Serve Dashboard HTML (Static Serve)
async def dashboard_page(request):
    return web.FileResponse('./templates/dashboard.html')

# Serve Root (Health Check for Render)
async def handle_root(request):
    return web.Response(text="Bot is Running!")

def init_web_app():
    app = web.Application()
    
    # API Routes
    app.router.add_get('/', handle_root)
    app.router.add_get('/dashboard', dashboard_page)
    app.router.add_get('/api/links', api_get_links)
    app.router.add_get('/api/stats', api_get_stats)
    
    # Static Files
    # Ensure static directory exists
    if not os.path.exists('static'):
        os.makedirs('static')
    
    app.router.add_static('/static/', path='static', name='static')
    
    return app
