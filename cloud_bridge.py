"""
MAJOR.05 SMC - Cloud Bridge
Connects your computer to the cloud
"""

import requests
import json
import time
import os
import MetaTrader5 as mt5

# ============================================
# 🔐 EXACT SAME CREDENTIALS - MATCHES CLOUD
# ============================================
CLOUD_URL = "https://major05-bot.onrender.com"
USERNAME = "SMCxx05"
PASSWORD = "TradeGold$9B"
API_KEY = "MAJOR05_SECURE_KEY_2024"

# ============================================
# START MT5
# ============================================
mt5.initialize()

def load_state():
    if os.path.exists("account_state.json"):
        with open("account_state.json", "r") as f:
            return json.load(f)
    return {"enabled": True}

def save_state(state):
    with open("account_state.json", "w") as f:
        json.dump(state, f, indent=4)

def sync_with_cloud():
    try:
        print("🔄 Checking cloud...")
        response = requests.get(
            f"{CLOUD_URL}/api/bot/status",
            headers={"api-key": API_KEY},
            auth=(USERNAME, PASSWORD),
            timeout=10
        )
        
        print(f"📡 Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                cloud_enabled = data.get("enabled", True)
                state = load_state()
                if state.get("enabled") != cloud_enabled:
                    state["enabled"] = cloud_enabled
                    save_state(state)
                    print(f"✅ Bot is now {'ACTIVE' if cloud_enabled else 'PAUSED'}")
        else:
            print(f"❌ Error: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def run_bridge():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     🌉 MAJOR.05 SMC - CLOUD BRIDGE                       ║
    ║     📱 Control your bot from ANYWHERE!                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    print(f"☁️ Cloud URL: {CLOUD_URL}")
    print(f"👤 Username: {USERNAME}")
    print("📱 Press Ctrl+C to stop\n")
    
    while True:
        sync_with_cloud()
        time.sleep(5)

if __name__ == "__main__":
    run_bridge()