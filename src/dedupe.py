from typing import List, Dict, Any


def dedupe_links(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for it in items:
        url = (it.get("url") or "").strip()
        if not url:
            continue
        key = url.split("#")[0]
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out
