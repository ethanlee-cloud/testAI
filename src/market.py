from typing import Dict, Any, List
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np


def _window_return(close, n: int):
    if len(close) < n + 1:
        return None
    return float(close[-1] / close[-(n + 1)] - 1.0)


def yahoo_etf_signals(ticker: str, history_days: int = 365) -> Dict[str, Any]:
    end = datetime.utcnow().date()
    start = end - timedelta(days=history_days * 2)

    df = yf.download(ticker, start=start.isoformat(), end=end.isoformat(), progress=False)
    if df is None or df.empty or "Close" not in df:
        return {"ticker": ticker, "error": "no data"}

    close = df["Close"].dropna()

    # If yfinance returns a DataFrame (happens sometimes), squeeze it
    if hasattr(close, "to_numpy"):
        close = close.to_numpy()
    
    # Make sure it's 1D
    close = np.asarray(close).squeeze()
    
    # If it's still not 1D, flatten as last resort
    if close.ndim != 1:
        close = close.reshape(-1)
    
    # Remove any non-finite values
    close = close[np.isfinite(close)]
    
    if close.size < 30:
        return {"ticker": ticker, "error": "insufficient data"}
    
    ret = np.diff(close) / close[:-1]


    r1 = _window_return(close, 1)
    r5 = _window_return(close, 5)
    r21 = _window_return(close, 21)
    r63 = _window_return(close, 63)

    # 60d vol if possible
    tail = ret[-60:] if len(ret) >= 60 else ret
    daily_vol = float(np.std(tail)) if len(tail) else None
    last_move = float(ret[-1]) if len(ret) else None
    z = (last_move / daily_vol) if daily_vol and daily_vol > 0 else None

    recent = close[-90:] if len(close) >= 90 else close
    dd = float(close[-1] / np.max(recent) - 1.0) if len(recent) else None

    return {
        "ticker": ticker,
        "last_close": float(close[-1]),
        "ret_1d": r1,
        "ret_5d": r5,
        "ret_1m": r21,
        "ret_3m": r63,
        "daily_vol_60d": daily_vol,
        "last_move_z": z,
        "drawdown_from_90d_high": dd,
    }


def fetch_etf_signals_for_themes(cfg, themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for t in themes:
        tickers = list(dict.fromkeys((t.get("etfs") or []) + (t.get("suggested_etfs") or [])))
        signals = []
        for tk in tickers:
            sig = yahoo_etf_signals(tk, history_days=cfg.market.history_days)
            signals.append(sig)
        t2 = {**t, "etf_signals": signals}
        out.append(t2)
    return out
