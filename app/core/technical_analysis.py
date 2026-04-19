# app/core/technical_analysis.py
# Calcula indicadores tecnicos usando pandas-ta
import pandas as pd
import pandas_ta as ta

def get_technical_state(df: pd.DataFrame):
    """
    Calcula EMA, RSI y Bollinger Bands sobre el DataFrame.
    Devuelve (df_con_indicadores, dict_de_estado) o (df, None) si faltan datos.
    """
    if df is None or df.empty or len(df) < 50:
        return df, None

    # Calcular indicadores si no existen
    if "EMA_20"  not in df.columns: df.ta.ema(length=20,  append=True)
    if "EMA_9"   not in df.columns: df.ta.ema(length=9,   append=True)
    if "EMA_21"  not in df.columns: df.ta.ema(length=21,  append=True)
    if "RSI_14"  not in df.columns: df.ta.rsi(length=14,  append=True)
    if "EMA_200" not in df.columns: df.ta.ema(length=200, append=True)
    if not [c for c in df.columns if c.startswith("BBL")]:
        df.ta.bbands(length=20, std=2, append=True)
    if not [c for c in df.columns if c.startswith("ATRr")]:
        df.ta.atr(length=14, append=True)

    current_price = df["close"].iloc[-1]

    state = {
        "current_price":        current_price,
        "ema_val":              df["EMA_20"].iloc[-1]  if "EMA_20"  in df.columns else None,
        "ema_9":                df["EMA_9"].iloc[-1]   if "EMA_9"   in df.columns else None,
        "ema_21":               df["EMA_21"].iloc[-1]  if "EMA_21"  in df.columns else None,
        "ema_200_val":          df["EMA_200"].iloc[-1] if "EMA_200" in df.columns else None,
        "rsi_val":              df["RSI_14"].iloc[-1]  if "RSI_14"  in df.columns else None,
        "rsi_recuperandose":    False,
        "bollinger_baja":       None,
        "bollinger_alta":       None,
        "bollinger_toque_piso": False,
        "bollinger_toque_techo":False,
        "ema_alcista":          False,
        "patrones": {"doji": False, "engulfing_bull": False, "engulfing_bear": False, "hammer": False},
    }

    if state["ema_val"] is not None:
        state["ema_alcista"] = current_price > state["ema_val"]
    if state["rsi_val"] is not None and "RSI_14" in df.columns:
        state["rsi_recuperandose"] = df["RSI_14"].iloc[-1] > df["RSI_14"].iloc[-2]

    bbl = [c for c in df.columns if c.startswith("BBL")]
    bbu = [c for c in df.columns if c.startswith("BBU")]
    if bbl and bbu:
        bbl_val = df[bbl[0]].iloc[-1]
        bbu_val = df[bbu[0]].iloc[-1]
        state["bollinger_baja"] = bbl_val
        state["bollinger_alta"] = bbu_val
        if float(df["low"].iloc[-1]) <= bbl_val * 1.005:
            state["bollinger_toque_piso"] = True
        if float(df["high"].iloc[-1]) >= bbu_val * 0.995:
            state["bollinger_toque_techo"] = True

    return df, state
