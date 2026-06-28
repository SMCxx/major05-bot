"""
MAJOR.05 SMC - Cloud API Server (No MT5 Required)
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import json
import os
import uvicorn
from datetime import datetime
import secrets

app = FastAPI(title="MAJOR.05 SMC Cloud API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# 🔐 PASSWORD PROTECTION
# ============================================
USERNAME = "admin"
PASSWORD = "your_secure_password_123"

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

API_KEY = "MAJOR05_SECURE_KEY_2024"

def verify_api_key(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

class BotToggleRequest(BaseModel):
    enabled: bool

def load_state():
    if os.path.exists("account_state.json"):
        with open("account_state.json", "r") as f:
            return json.load(f)
    return {"enabled": True, "daily_trades": 0, "loss_streak": 0, "peak": 1000.0}

def save_state(state):
    with open("account_state.json", "w") as f:
        json.dump(state, f, indent=4)

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
    """Get account status"""
    try:
        state = load_state()
        return {
            "success": True,
            "balance": 1000.00,
            "equity": 1000.00,
            "login": "DEMO",
            "server": "Weltrade",
            "symbol": "XAUUSD_i",
            "user": credentials.username,
            "bot_enabled": state.get("enabled", True)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/bot/status")
async def get_bot_status(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    api_key: str = Header(...)
):
    """Get bot status"""
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
    """Turn bot ON/OFF"""
    try:
        state = load_state()
        state["enabled"] = request.enabled
        save_state(state)
        return {"success": True, "enabled": request.enabled}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/trades/active")
async def get_active_trades(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    api_key: str = Header(...)
):
    """Get active trades"""
    return {"success": True, "count": 0, "trades": []}

@app.get("/api/trades/history")
async def get_trade_history(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    api_key: str = Header(...),
    limit: int = 50
):
    """Get trade history"""
    if os.path.exists("trade_log.csv") and os.path.getsize("trade_log.csv") > 0:
        try:
            import pandas as pd
            df = pd.read_csv("trade_log.csv")
            if len(df) > 0:
                df_tail = df.tail(limit)
                trades = []
                for _, row in df_tail.iterrows():
                    trades.append({
                        "signal": row.get("signal", "TRADE"),
                        "score": int(row.get("score", 0)),
                        "profit": float(row.get("profit", 0))
                    })
                wins = len(df[df["profit"] > 0])
                total = len(df)
                return {
                    "success": True,
                    "total": total,
                    "win_rate": (wins / total * 100) if total > 0 else 0,
                    "net_profit": float(df["profit"].sum()),
                    "trades": trades
                }
        except:
            pass
    return {"success": True, "total": 0, "trades": []}

@app.get("/api/performance/monthly")
async def get_monthly_performance(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    api_key: str = Header(...)
):
    """Get monthly results"""
    return {"success": True, "total_trades": 0}

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     🔐 MAJOR.05 SMC - CLOUD API SERVER                   ║
    ║     📱 Secure access from anywhere!                      ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    print(f"👤 Username: {USERNAME}")
    print(f"🔑 Password: {PASSWORD}")
    print("\n⚠️ Change the username and password in the code!")
    print("\nPress Ctrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)