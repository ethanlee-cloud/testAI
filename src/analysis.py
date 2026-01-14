from typing import Dict, Any, List


def heuristic_priced_in(theme_sent: float, sig: Dict[str, Any], cfg) -> str:
    if "error" in sig:
        return "unknown (no market data)"

    r1m = sig.get("ret_1m")
    z = sig.get("last_move_z")
    dd = sig.get("drawdown_from_90d_high")

    s = cfg.market.signals

    if theme_sent > 0.35:
        if (r1m is not None and r1m > s.strong_move_1m) or (z is not None and z > s.z_threshold):
            return "likely priced in / crowded"
        if dd is not None and dd < s.drawdown_deep:
            return "possibly not priced in (market still skeptical)"
        return "partially priced in"

    if theme_sent < -0.35:
        if (r1m is not None and r1m < s.strong_drop_1m) or (z is not None and z < -s.z_threshold):
            return "negative priced in"
        return "risk not fully priced in"

    return "mixed/unclear"


def price_in_verdicts(llm, themes: List[Dict[str, Any]], cfg) -> List[Dict[str, Any]]:
    out = []
    for t in themes:
        theme_sent = float(t.get("theme_sentiment_score", 0.0))
        signals = t.get("etf_signals", [])

        # compute heuristic per ETF
        heuristic = []
        for sig in signals:
            heuristic.append({
                "ticker": sig.get("ticker"),
                "heuristic_verdict": heuristic_priced_in(theme_sent, sig, cfg),
                "signals": sig
            })

        # Ask LLM to produce a narrative verdict using theme + signals
        llm_input = {
            "theme": t.get("theme"),
            "description": t.get("description"),
            "theme_sentiment_score": theme_sent,
            "etf_signals": signals,
            "heuristic": heuristic,
        }
        try:
            llm_out = llm.priced_in_analysis(llm_input)
        except Exception:
            llm_out = {"verdict": "mixed/unclear", "reasoning_bullets": ["LLM analysis failed; using heuristic only."]}

        out.append({
            **t,
            "heuristic": heuristic,
            "llm_priced_in": llm_out,
        })
    return out
