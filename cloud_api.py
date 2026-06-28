"""
MAJOR.05 SMC - Cloud API Server with Web Dashboard
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
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
# 🔐 EXACT CREDENTIALS - DO NOT CHANGE
# ============================================
USERNAME = "SMCxx05"
PASSWORD = "TradeGold$9B"

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
# WEB DASHBOARD HTML
# ============================================
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MAJOR.05 SMC - Remote Control</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #fff;
            padding: 16px;
            padding-bottom: 80px;
        }
        .card {
            background: #2a2a2a;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            border: 1px solid #333;
        }
        .card-title {
            color: #00ff88;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
        }
        .label { color: #888; }
        .value { font-weight: bold; }
        .green { color: #00ff88; }
        .gold { color: #ffaa00; }
        .red { color: #ff4444; }
        .btn {
            background: #00ff88;
            color: #1a1a1a;
            border: none;
            padding: 14px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            width: 100%;
            cursor: pointer;
        }
        .btn-off { background: #ff4444; color: #fff; }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
        }
        .stat-box {
            background: #1a1a1a;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            border: 1px solid #333;
        }
        .stat-box .num { font-size: 22px; font-weight: bold; color: #00ff88; }
        .stat-box .lbl { font-size: 10px; color: #666; margin-top: 4px; }
        .trade-item {
            border-bottom: 1px solid #333;
            padding: 8px 0;
        }
        .trade-item:last-child { border-bottom: none; }
        .history-item {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #222;
        }
        .tab-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #2a2a2a;
            display: flex;
            border-top: 1px solid #333;
            padding: 8px 0;
        }
        .tab {
            flex: 1;
            text-align: center;
            padding: 6px 0;
            color: #666;
            font-size: 10px;
            cursor: pointer;
            border: none;
            background: transparent;
        }
        .tab.active { color: #00ff88; }
        .tab-icon { font-size: 22px; display: block; }
        .hidden { display: none !important; }
        .mt-8 { margin-top: 8px; }
        .text-center { text-align: center; }
    </style>
</head>
<body>

    <div class="card">
        <h2 style="color:#00ff88;">⚡ MAJOR.05 SMC</h2>
        <div class="row">
            <span class="label">📱 Remote Control</span>
            <span class="value green">ONLINE</span>
        </div>
        <div class="row">
            <span class="label">💰 Balance</span>
            <span class="value green" id="balance">$0.00</span>
        </div>
        <div class="row">
            <span class="label">📊 Equity</span>
            <span class="value gold" id="equity">$0.00</span>
        </div>
        <div class="row">
            <span class="label">🤖 Bot</span>
            <span class="value" id="botStatus">🔴 PAUSED</span>
        </div>
    </div>

    <div id="homeTab">
        <div class="stats">
            <div class="stat-box">
                <div class="num" id="dailyTrades">0</div>
                <div class="lbl">📊 Today</div>
            </div>
            <div class="stat-box">
                <div class="num" id="winRate">0%</div>
                <div class="lbl">🎯 Win Rate</div>
            </div>
            <div class="stat-box">
                <div class="num" id="lossStreak">0</div>
                <div class="lbl">📉 Loss Streak</div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">🤖 Bot Control</div>
            <button class="btn" id="toggleBtn" onclick="toggleBot()">TURN BOT ON</button>
            <p class="mt-8 text-center" style="color:#666;font-size:12px;" id="statusText">Bot is PAUSED</p>
        </div>

        <div class="card">
            <div class="card-title">🟢 Active Trades (<span id="activeCount">0</span>)</div>
            <div id="activeTrades"><p style="color:#666;text-align:center;padding:10px;">No active trades</p></div>
        </div>
    </div>

    <div id="historyTab" class="hidden">
        <div class="card">
            <div class="card-title">📋 Trade History</div>
            <div id="historyList"><p style="color:#666;text-align:center;padding:10px;">No trades yet</p></div>
        </div>
    </div>

    <div id="settingsTab" class="hidden">
        <div class="card">
            <div class="card-title">⚙️ Settings</div>
            <div class="row"><span class="label">Symbol</span><span class="value">XAUUSD_i</span></div>
            <div class="row"><span class="label">Min Score</span><span class="value" id="minScore">7</span></div>
            <div class="row"><span class="label">Daily Limit</span><span class="value" id="maxTrades">4</span></div>
            <div class="row"><span class="label">Server</span><span class="value" id="serverInfo">N/A</span></div>
        </div>
        <button class="btn" onclick="refreshData()">🔄 Refresh</button>
    </div>

    <div class="tab-bar">
        <button class="tab active" onclick="switchTab('home')"><span class="tab-icon">🏠</span>Home</button>
        <button class="tab" onclick="switchTab('history')"><span class="tab-icon">📋</span>History</button>
        <button class="tab" onclick="switchTab('settings')"><span class="tab-icon">⚙️</span>Settings</button>
    </div>

    <script>
        let botEnabled = false;
        let currentTab = 'home';

        async function apiCall(endpoint, method = 'GET', body = null) {
            try {
                const opts = { method, headers: { 'Content-Type': 'application/json' } };
                if (body) opts.body = JSON.stringify(body);
                const res = await fetch('/api' + endpoint, opts);
                return await res.json();
            } catch (e) { return { success: false, error: e.message }; }
        }

        async function refreshData() {
            try {
                const acc = await apiCall('/account');
                if (acc.success) {
                    document.getElementById('balance').textContent = '$' + acc.balance.toFixed(2);
                    document.getElementById('equity').textContent = '$' + acc.equity.toFixed(2);
                    document.getElementById('serverInfo').textContent = acc.server || 'Weltrade';
                }

                const bot = await apiCall('/bot/status');
                if (bot.success) {
                    botEnabled = bot.enabled;
                    document.getElementById('dailyTrades').textContent = bot.daily_trades || 0;
                    document.getElementById('lossStreak').textContent = bot.loss_streak || 0;
                    document.getElementById('minScore').textContent = bot.min_score || 7;
                    document.getElementById('maxTrades').textContent = bot.max_daily_trades || 4;

                    const statusEl = document.getElementById('botStatus');
                    const toggleBtn = document.getElementById('toggleBtn');
                    const statusText = document.getElementById('statusText');
                    if (bot.enabled) {
                        statusEl.textContent = '🟢 ACTIVE';
                        statusEl.style.color = '#00ff88';
                        toggleBtn.textContent = 'TURN BOT OFF';
                        toggleBtn.className = 'btn btn-off';
                        statusText.textContent = 'Bot is ACTIVE';
                    } else {
                        statusEl.textContent = '🔴 PAUSED';
                        statusEl.style.color = '#ff4444';
                        toggleBtn.textContent = 'TURN BOT ON';
                        toggleBtn.className = 'btn';
                        statusText.textContent = 'Bot is PAUSED';
                    }
                }

                const trades = await apiCall('/trades/active');
                if (trades.success) {
                    document.getElementById('activeCount').textContent = trades.count || 0;
                    const container = document.getElementById('activeTrades');
                    if (trades.count === 0) {
                        container.innerHTML = '<p style="color:#666;text-align:center;padding:10px;">No active trades</p>';
                    } else {
                        let html = '';
                        trades.trades.forEach(t => {
                            const color = t.profit >= 0 ? '#00ff88' : '#ff4444';
                            html += `
                                <div class="trade-item">
                                    <div style="display:flex;justify-content:space-between;">
                                        <span style="color:#00ff88;">#${t.ticket}</span>
                                        <span style="color:${t.type === 'BUY' ? '#00ff88' : '#ff4444'};">${t.type}</span>
                                        <span style="color:${color};">$${t.profit.toFixed(2)}</span>
                                    </div>
                                    <div style="display:flex;justify-content:space-between;font-size:12px;color:#888;margin-top:4px;">
                                        <span>Entry: $${t.entry.toFixed(2)}</span>
                                        <span>Current: $${t.current.toFixed(2)}</span>
                                        <span>Vol: ${t.volume}</span>
                                    </div>
                                </div>
                            `;
                        });
                        container.innerHTML = html;
                    }
                }

                const hist = await apiCall('/trades/history');
                if (hist.success) {
                    const container = document.getElementById('historyList');
                    if (hist.trades && hist.trades.length > 0) {
                        let html = '';
                        hist.trades.forEach(t => {
                            const color = t.profit >= 0 ? '#00ff88' : '#ff4444';
                            html += `<div class="history-item"><span>${t.signal}</span><span style="color:${color};">$${t.profit.toFixed(2)}</span></div>`;
                        });
                        container.innerHTML = html;
                    } else {
                        container.innerHTML = '<p style="color:#666;text-align:center;padding:10px;">No trades yet</p>';
                    }
                }

                if (hist.success && hist.total > 0) {
                    document.getElementById('winRate').textContent = hist.win_rate.toFixed(1) + '%';
                }

            } catch (e) { console.error(e); }
        }

        async function toggleBot() {
            const result = await apiCall('/bot/toggle', 'POST', { enabled: !botEnabled });
            if (result.success) { refreshData(); }
            else { alert('Error: ' + (result.error || 'Failed')); }
        }

        function switchTab(tab) {
            currentTab = tab;
            document.getElementById('homeTab').classList.toggle('hidden', tab !== 'home');
            document.getElementById('historyTab').classList.toggle('hidden', tab !== 'history');
            document.getElementById('settingsTab').classList.toggle('hidden', tab !== 'settings');
            document.querySelectorAll('.tab').forEach((el, i) => {
                el.classList.toggle('active', (tab === 'home' && i === 0) || (tab === 'history' && i === 1) || (tab === 'settings' && i === 2));
            });
        }

        refreshData();
        setInterval(refreshData, 10000);
    </script>
</body>
</html>
"""

# ============================================
# API ENDPOINTS
# ============================================

@app.get("/")
async def root(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    """Serve the web dashboard"""
    return HTMLResponse(content=HTML_PAGE)

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

# ============================================
# SECURITY INFO PAGE
# ============================================
@app.get("/security")
async def security_info():
    return {
        "message": "🔐 This API is password protected",
        "auth_method": "HTTP Basic Auth + API Key",
        "example_curl": """
curl -u SMCxx05:TradeGold$9B -H "api-key: MAJOR05_SECURE_KEY_2024" https://your-app.onrender.com/api/account
"""
    }

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     🔐 MAJOR.05 SMC - CLOUD API SERVER                   ║
    ║     📱 Secure access from anywhere!                      ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    print(f"👤 Username: SMCxx05")
    print(f"🔑 Password: TradeGold$9B")
    print("\n⚠️ Keep these credentials safe!")
    print("\nPress Ctrl+C to stop\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)