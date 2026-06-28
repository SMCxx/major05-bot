import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime
from market_regime import detect_market_regime, get_regime_score
from institutional_indicators import (
    get_institutional_score, 
    get_fake_breakout_score,
    get_vwap_bands,
    get_value_area,
    detect_hidden_divergence,
    get_order_book_imbalance
)

try:
    from data_engine import SYMBOL
except ImportError:
    SYMBOL = "XAUUSD_i"

def get_swings(df):
    if len(df) < 5:
        return pd.Series(dtype=float), pd.Series(dtype=float)
        
    swing_highs = (df["high"] > df["high"].shift(1)) & \
                  (df["high"] > df["high"].shift(2)) & \
                  (df["high"] > df["high"].shift(-1)) & \
                  (df["high"] > df["high"].shift(-2))
                  
    swing_lows = (df["low"] < df["low"].shift(1)) & \
                 (df["low"] < df["low"].shift(2)) & \
                 (df["low"] < df["low"].shift(-1)) & \
                 (df["low"] < df["low"].shift(-2))
                 
    return df["high"][swing_highs], df["low"][swing_lows]

def get_pricing_zone(df, current_price):
    highs, lows = get_swings(df)
    if highs.empty or lows.empty:
        return "EQUILIBRIUM"
    
    recent_high = highs.iloc[-1]
    recent_low = lows.iloc[-1]
    range_size = recent_high - recent_low
    
    if range_size <= 0:
        return "EQUILIBRIUM"
        
    equilibrium = recent_low + (range_size * 0.50)
    
    if current_price < (recent_low + (range_size * 0.40)):
        return "DEEP_DISCOUNT"  
    elif current_price > (recent_high - (range_size * 0.40)):
        return "DEEP_PREMIUM"   
    elif current_price < equilibrium:
        return "DISCOUNT"
    else:
        return "PREMIUM"

def get_m15_atr(df):
    if len(df) < 20:
        return 3.00  
    high_low = df["high"] - df["low"]
    high_cp = abs(df["high"] - df["close"].shift(1))
    low_cp = abs(df["low"] - df["close"].shift(1))
    tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    return float(tr.rolling(14).mean().iloc[-1])

def validate_volume_ob(df, index_idx):
    if "tick_volume" not in df.columns or len(df) < 15:
        return True 
    target_volume = df["tick_volume"].iloc[index_idx]
    avg_volume_short = df["tick_volume"].iloc[max(0, index_idx-10):index_idx].mean()
    avg_volume_long = df["tick_volume"].iloc[max(0, index_idx-20):index_idx].mean()
    return target_volume > (avg_volume_short * 1.5) or target_volume > (avg_volume_long * 2.0)

def get_order_flow_imbalance(df):
    """Detect if aggressive market orders are dominating"""
    if len(df) < 10: 
        return "BALANCED"
    
    bullish_candles = df[df["close"] > df["open"]]
    bearish_candles = df[df["close"] < df["open"]]
    
    if len(bullish_candles) > len(bearish_candles) * 1.5:
        return "BULLISH_DOMINANT"
    elif len(bearish_candles) > len(bullish_candles) * 1.5:
        return "BEARISH_DOMINANT"
    else:
        return "BALANCED"

def structure(df):
    if df.empty or len(df) < 15:
        return "RANGE"
    highs, lows = get_swings(df)
    if highs.empty or lows.empty:
        return "RANGE"
    try:
        last_swing_high = highs.iloc[-1]
        last_swing_low = lows.iloc[-1]
        current_close = df["close"].iloc[-1]
        order_flow = get_order_flow_imbalance(df)

        if current_close > last_swing_high:
            if validate_volume_ob(df, -1) or order_flow == "BULLISH_DOMINANT": 
                return "BULLISH_BOS"
        if current_close < last_swing_low:
            if validate_volume_ob(df, -1) or order_flow == "BEARISH_DOMINANT": 
                return "BEARISH_BOS"
    except IndexError:
        return "RANGE"
    return "RANGE"

def find_valid_poi(df):
    highs, lows = get_swings(df)
    if highs.empty or lows.empty:
        return None, None
    if validate_volume_ob(df, -2):
        return float(df["low"].iloc[-2]), float(df["high"].iloc[-2])
    return float(lows.iloc[-1]), float(highs.iloc[-1])

def liquidity_sweep_catalyst(m5_df, poi_low, poi_high, bias):
    if poi_low is None or poi_high is None or len(m5_df) < 3:
        return False
        
    current_low = m5_df["low"].iloc[-1]
    current_high = m5_df["high"].iloc[-1]
    current_close = m5_df["close"].iloc[-1]
    
    if bias == "BUY":
        return current_low < poi_low and current_close > poi_low
    elif bias == "SELL":
        return current_high > poi_high and current_close < poi_high
    return False

def get_session_strength():
    """Calculate session strength based on time of day"""
    h = datetime.utcnow().hour
    current_day = datetime.utcnow().weekday()
    
    if current_day >= 5:
        return -2
    
    if 8 <= h <= 10 or 12 <= h <= 14:
        return 3
    elif 7 <= h < 8 or 10 <= h < 12 or 14 <= h <= 16:
        return 2
    elif 16 <= h <= 17:
        return 1
    elif 17 <= h <= 22:
        return 0
    else:
        return -1

def get_structural_tp(df, bias):
    if df.empty:
        return 0.0
    
    highs, lows = get_swings(df)
    if highs.empty or lows.empty:
        return 0.0
    
    if bias == "BUY":
        if len(highs) >= 2:
            return float(highs.iloc[-2])
        return float(highs.iloc[-1])
    
    elif bias == "SELL":
        if len(lows) >= 2:
            return float(lows.iloc[-2])
        return float(lows.iloc[-1])
    
    return 0.0

def confluence(tf):
    h4, h1, m15, m5 = tf["H4"], tf["H1"], tf["M15"], tf["M5"]
    if h4.empty or h1.empty or m15.empty or m5.empty:
        return "NONE", 0, 3.00, 0.0

    current_price = m5["close"].iloc[-1]
    atr = get_m15_atr(m15)
    
    m15_highs, m15_lows = get_swings(m15)
    
    h4_trend = structure(h4)
    h1_struct = structure(h1)
    order_flow = get_order_flow_imbalance(m5)
    
    # Market Regime Detection
    regime = detect_market_regime()
    regime_score = get_regime_score(regime)
    print(f"📊 Market Regime: {regime} (Score: {regime_score})")
    
    # Session Strength
    session_score = get_session_strength()
    print(f"⏰ Session Strength: {session_score}")
    
    # Institutional Indicators
    hidden_div = detect_hidden_divergence(h1)
    ob_imbalance = get_order_book_imbalance()
    vwap_bands = get_vwap_bands(h1)
    value_area = get_value_area(h1)
    
    print(f"🏦 Hidden Divergence: {hidden_div}")
    print(f"📚 Order Book Imbalance: {ob_imbalance:.1f}%")
    print(f"📊 VWAP: ${vwap_bands['vwap']:.2f}")
    print(f"📊 Value Area: ${value_area['val']:.2f} - ${value_area['vah']:.2f}")
    
    bias = "NONE"
    target_tp_price = 0.0

    if h1_struct == "BULLISH_BOS" and h4_trend != "BEARISH_BOS":
        if order_flow != "BEARISH_DOMINANT":
            bias = "BUY"
            target_tp_price = get_structural_tp(h1, "BUY")
            if target_tp_price == 0.0:
                target_tp_price = float(m15_highs.iloc[-1]) if not m15_highs.empty else 0.0
                
    elif h1_struct == "BEARISH_BOS" and h4_trend != "BULLISH_BOS":
        if order_flow != "BULLISH_DOMINANT":
            bias = "SELL"
            target_tp_price = get_structural_tp(h1, "SELL")
            if target_tp_price == 0.0:
                target_tp_price = float(m15_lows.iloc[-1]) if not m15_lows.empty else 0.0
        
    if bias == "NONE" or target_tp_price == 0.0:
        return "NONE", 0, atr, 0.0

    if bias == "BUY" and target_tp_price <= current_price:
        target_tp_price = current_price + (atr * 2.0)
    if bias == "SELL" and target_tp_price >= current_price:
        target_tp_price = current_price - (atr * 2.0)

    price_zone = get_pricing_zone(h1, current_price)
    if bias == "BUY" and price_zone not in ["DISCOUNT", "DEEP_DISCOUNT"]:
        return "NONE", 0, atr, 0.0
    if bias == "SELL" and price_zone not in ["PREMIUM", "DEEP_PREMIUM"]:
        return "NONE", 0, atr, 0.0

    # --- INSTITUTIONAL SCORING SYSTEM ---
    score = 2  # Base score lowered - need more confirmation
    
    # SMC Confirmations
    if price_zone in ["DEEP_DISCOUNT", "DEEP_PREMIUM"]:
        score += 1
        print("✅ Deep Discount/Premium +1")
    
    if order_flow != "BALANCED" and bias in ["BUY", "SELL"]:
        if (bias == "BUY" and order_flow == "BULLISH_DOMINANT") or \
           (bias == "SELL" and order_flow == "BEARISH_DOMINANT"):
            score += 1
            print("✅ Order Flow matches bias +1")
    
    # Liquidity Sweep
    poi_low, poi_high = find_valid_poi(m15)
    if liquidity_sweep_catalyst(m5, poi_low, poi_high, bias):
        score += 2  
        print("✅ Liquidity Sweep Confirmed +2")
    else:
        return "NONE", 0, atr, 0.0
    
    # Market Regime
    if regime in ["STRONG_UPTREND", "UPTREND"] and bias == "BUY":
        score += 1
        print("✅ Uptrend Regime +1")
    elif regime in ["STRONG_DOWNTREND", "DOWNTREND"] and bias == "SELL":
        score += 1
        print("✅ Downtrend Regime +1")
    elif regime == "RANGING":
        score -= 1
        print("⚠️ Ranging Market -1")
    
    # Session Strength
    if session_score >= 2:
        score += 1
        print("✅ Strong Session +1")
    elif session_score <= -1:
        score -= 1
        print("⚠️ Weak Session -1")
    
    # --- INSTITUTIONAL INDICATOR SCORING ---
    
    # 1. Hidden Divergence (Institutional Edge)
    if hidden_div == "HIDDEN_BULLISH" and bias == "BUY":
        score += 3
        print("🏦 Hidden Bullish Divergence +3")
    elif hidden_div == "HIDDEN_BEARISH" and bias == "SELL":
        score += 3
        print("🏦 Hidden Bearish Divergence +3")
    
    # 2. Order Book Imbalance
    if abs(ob_imbalance) > 30:
        if (bias == "BUY" and ob_imbalance > 0) or (bias == "SELL" and ob_imbalance < 0):
            score += 2
            print(f"🏦 Order Book Imbalance {ob_imbalance:.1f}% +2")
    
    # 3. VWAP Position
    if vwap_bands["vwap"] > 0:
        vwap_distance = (current_price - vwap_bands["vwap"]) / vwap_bands["vwap"]
        if bias == "BUY" and vwap_distance < -0.005:
            score += 1
            print("🏦 Below VWAP +1")
        elif bias == "SELL" and vwap_distance > 0.005:
            score += 1
            print("🏦 Above VWAP +1")
    
    # 4. Value Area
    if bias == "BUY" and current_price < value_area["val"]:
        score += 1
        print("🏦 Below Value Area +1")
    elif bias == "SELL" and current_price > value_area["vah"]:
        score += 1
        print("🏦 Above Value Area +1")
    
    # 5. Institutional Score (Combined)
    inst_score, details = get_institutional_score(m5, bias, current_price)
    score += inst_score
    for detail in details:
        print(f"🏦 {detail}")
    
    # 6. Fake Breakout Detection (Penalty)
    fake_score = get_fake_breakout_score(m5, bias, poi_low if bias == "BUY" else poi_high)
    score += fake_score
    if fake_score < 0:
        print("🚨 Fake Breakout Detected -2")
    
    # Session time check
    if not session_ok():
        score -= 2
        print("⚠️ Off-Hours Trading -2")
    
    # Correlation filter
    from correlation_filter import is_correlation_valid, get_correlation_score
    if not is_correlation_valid(bias):
        print("❌ Correlation filter blocked trade")
        return "NONE", 0, atr, 0.0
    
    corr_score = get_correlation_score(bias)
    score += corr_score
    if corr_score > 0:
        print(f"✅ Correlation Bonus +{corr_score}")
    elif corr_score < 0:
        print(f"⚠️ Correlation Penalty {corr_score}")

    # FINAL SCORE CHECK - Institutional Grade (Minimum 7)
    min_score = 7  # Raised from 5 to 7 for institutional quality
    
    if regime == "RANGING" and score < 8:
        print(f"📊 Ranging market requires minimum score 8 (current: {score})")
        return "NONE", score, atr, 0.0
    
    if score >= min_score:
        print(f"🏆 INSTITUTIONAL SCORE: {score} (Regime: {regime}, Session: {session_score})")
        print(f"📊 Hidden Divergence: {hidden_div}, Order Book: {ob_imbalance:.1f}%")
        return bias, score, atr, target_tp_price
    else:
        print(f"❌ Score {score} below minimum {min_score} - No Trade")

    return "NONE", score, atr, 0.0

def session_ok():
    h = datetime.utcnow().hour
    return 7 <= h <= 17