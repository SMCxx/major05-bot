import MetaTrader5 as mt5
from data_engine import get_multi_tf
from smc_core import confluence
from execution_engine import execute, manage_open_positions
from performance_engine import analyze
from vix_filter import is_vix_elevated
from execution_filters import check_high_impact_news
from risk_engine import get_balance
from market_regime import detect_market_regime
from correlation_filter import get_correlation
from datetime import datetime
from data_engine import SYMBOL
from institutional_indicators import (
    get_order_book_imbalance,
    get_vwap_bands,
    get_value_area,
    detect_hidden_divergence,
    get_delta_imbalance
)

def main():
    print(r"""
    _  _ ____    _ ____ ____    ____ ___  
    |\/| |__|    | |  | |__/    |  |  __] 
    |  | |  | ___| |__| |  \ ___|__| [__  
    """)
    print(f"🏦 MAJOR.05 SMC: INSTITUTIONAL-GRADE ENGINE - {SYMBOL}")
    print("🧠 HIDDEN DIVERGENCE + ORDER BOOK + VWAP + VALUE AREA")
    print("📈 PARTIAL CLOSE: 50% at 2R | SL LOCK: 1:2 at 4R")
    print("🎯 INSTITUTIONAL SCORE REQUIREMENT: 7+")
    print("-" * 55)
    
    if not mt5.initialize():
        return

    try:
        balance = get_balance()
        print(f"💳 CURRENT BALANCE: ${balance:.2f}")
        
        print("\n📊 INSTITUTIONAL MARKET DATA:")
        
        vix = get_vix_equivalent()
        print(f"🌪️ VIX Equivalent: {vix:.1f}%" if vix else "🌪️ VIX: N/A")
        
        regime = detect_market_regime()
        print(f"📊 Market Regime: {regime}")
        
        ob_imbalance = get_order_book_imbalance()
        print(f"📚 Order Book Imbalance: {ob_imbalance:.1f}%")
        if abs(ob_imbalance) > 30:
            direction = "BUYING" if ob_imbalance > 0 else "SELLING"
            print(f"   🔥 {direction} PRESSURE DETECTED")
        
        tf = get_multi_tf()
        vwap = get_vwap_bands(tf["H1"])
        if vwap["vwap"] > 0:
            current_price = tf["M5"]["close"].iloc[-1]
            vwap_distance = ((current_price - vwap["vwap"]) / vwap["vwap"]) * 100
            print(f"📊 VWAP: ${vwap['vwap']:.2f} (Price: {vwap_distance:+.2f}% from VWAP)")
        
        value_area = get_value_area(tf["H1"])
        print(f"📊 Value Area: ${value_area['val']:.2f} - ${value_area['vah']:.2f}")
        print(f"   🎯 POC: ${value_area['poc']:.2f}")
        
        hidden_div = detect_hidden_divergence(tf["H1"])
        if hidden_div != "NONE":
            print(f"🔮 Hidden Divergence: {hidden_div} 🚀")
        
        delta = get_delta_imbalance(tf["M5"])
        print(f"📊 Delta Imbalance: {delta:.1f}%")
        
        correlation = get_correlation()
        if correlation is not None:
            print(f"📊 DXY Correlation: {correlation:.2f}")
        
        session_strength = get_session_strength()
        print(f"⏰ Session Strength: {session_strength}/3")
        
        print("-" * 55)
        
        if is_vix_elevated(threshold=25.0):
            print("🌪️ MARKET VOLATILITY TOO HIGH - TRADING PAUSED")
            return
            
        if not check_high_impact_news():
            print("📰 HIGH IMPACT NEWS BLOCKING TRADES")
            return
        
        manage_open_positions()
        
        signal, score, atr, target_tp_price = confluence(tf)
        print(f"🔄 Analysis -> Bias: {signal} | Institutional Score: {score} | TP: ${target_tp_price:.2f}")

        execute(signal, score, atr, target_tp_price)
        
        metrics = analyze()
        print("📊 Session Metrics:", metrics)
        print("-" * 55)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        mt5.shutdown()

def get_session_strength():
    h = datetime.utcnow().hour
    if 8 <= h <= 10 or 12 <= h <= 14:
        return 3
    elif 7 <= h < 8 or 10 <= h < 12 or 14 <= h <= 16:
        return 2
    elif 16 <= h <= 17:
        return 1
    else:
        return 0

def get_vix_equivalent():
    from vix_filter import get_vix_equivalent as gve
    return gve()

if __name__ == "__main__":
    main()