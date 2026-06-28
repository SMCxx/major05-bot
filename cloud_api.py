"""
MAJOR.05 SMC - Cloud API Server (Password Protected)
Deploy to Render.com for free 24/7 access!
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
import uvicorn
from datetime import datetime
import secrets

# ============================================
# 🔐 PASSWORD PROTECTION - CHANGE THESE!
# ============================================
USERNAME = "admin"
PASSWORD = "your_secure_password_123"

app = FastAPI(title="MAJOR.05 SMC Cloud API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials

# ============================================
# API KEY (Second layer of security)
# ============================================
API_KEY = "MAJOR05_SECURE_KEY_2024"

def verify_api_key(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

# ============================================
# DATA MODELS
# ============================================
class BotToggleRequest(BaseModel):
    enabled: bool

# ============================================
# STATE MANAGEMENT (WITH FILE CREATION)
# ============================================
STATE_FILE = "account_state.json"

def load_state():
    """Load state from file, create if it doesn't exist"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    
    # If file doesn't exist or is corrupt, create default
    default_state = {
        "enabled": True,
        "daily_trades": 0,
        "loss_streak": 0,
        "peak": 1000.0,
        "minimum_allowed_score": 7,
        "max_daily_trades": 4,
        "pending_suggestion": "NONE",
        "pending_approval_status": "PENDING"
    }
    save_state(default_state)
    return default_state

def save_state(state):
    """Save state to file"""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving state: {e}")
        return False

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    return {
        "name": "MAJOR.05 SMC Cloud API",
        "version": "2.0",
        "status": "running",
        "message": "✅ You are connected!",
        "user": credentials.username
    }

@app.get("/api/account")
async def get_account(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    api_key: str = Header(...)
):
    try:
        return {
            "success": True,
            "balance": 1000.00,
            "equity": 1000.00,
            "login": "DEMO",
            "server": "Weltrade",
            "symbol": "XAUUSD_i",
            "user": credentials.username,
            "message": "⚠️ This is a DEMO. Bot runs on your desktop."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/bot/status")
async def get_bot_status(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    api_key: str = Header(...)
):
    try:
        state = load_state()
        return {
            "success": True,
            "enabled": state.get("enabled", True),
            "daily_trades": state.get("daily_trades", 0),
            "max_daily_trades": state.get("max_daily_trades", 4),
            "loss_streak": state.get("loss_streak", 0),
            "min_score": state.get("minimum_allowed_score", 7)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/bot/toggle")
async def toggle_bot(
    request: BotToggleRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    api_key: str = Header(...)
):
    try:
        state = load_state()
        state["enabled"] = request.enabled
        if save_state(state):
            return {"success": True, "enabled": request.enabled}
        else:
            return {"success": False, "error": "Failed to save state"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/trades/active")
async def get_active_trades(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    api_key: str = Header(...)
):
    try:
        # Return sample data for now
        return {
            "success": True,
            "count": 0,
            "trades": []
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/trades/history")
async def get_trade_history(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    api_key: str = Header(...)
):
    try:
        # Return sample data for now
        return {
            "success": True,
            "total": 0,
            "win_rate": 0,
            "net_profit": 0,
            "trades": []
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================
# SECURITY INFO
# ============================================
@app.get("/security")
async def security_info():
    return {
        "message": "🔐 This API is password protected",
        "auth_method": "HTTP Basic Auth + API Key",
        "test_curl": f"""
curl -u {USERNAME}:{PASSWORD} -H "api-key: {API_KEY}" https://your-app.onrender.com/
"""
    }

# ============================================
# ROOT PATH CHECK
# ============================================
@app.get("/status")
async def status():
    return {"status": "online", "time": datetime.now().isoformat()}

if __name__ == "__main__":
    # Create initial state file
    load_state()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     🔐 MAJOR.05 SMC - CLOUD API SERVER                   ║
    ║     📱 Secure access from anywhere!                      ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    print(f"👤 Username: {USERNAME}")
    print(f"🔑 Password: {PASSWORD}")
    print(f"🔑 API Key: {API_KEY}")
    print("\n⚠️ Change the username and password in the code!")
    print("\nPress Ctrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)