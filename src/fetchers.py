from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from .dedupe import dedupe_links


def _http_get(url: str, user_agent: str, timeout: int = 30) -> str:
    r = requests.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=timeout
    )
    r.raise_for_status()
    return r.text


def _keyword_pass(title: str, url: str, cfg) -> bool:
    filters = cfg.filters if hasattr(cfg, "filters") else {}
    include = [k.lower() for k in filters.get("include_keywords", [])]
    exclude = [k.lower() for k in filters.get("exclude_keywords", [])]

    t = (title or "").lower()
    u = (url or "").lower()

    if exclude and any(k in t or k in u for k in exclude):
        return False

    if include:
        return any(k in t or k in u for k in include)

    return True


def _parse_rss_feed(feed_url: str, cfg) -> List[Dict[str, Any]]:
    xml = _http_get(feed_url, cfg.project.user_agent)
    soup = BeautifulSoup(xml, "xml")
    items = []

    for item in soup.find_all("item"):
        title = (item.title.text if item.title else "").strip()
        link = (item.link.text if item.link else "").strip()
        pub = (item.pubDate.text if item.pubDate else "").strip()

        if not link or not _keyword_pass(title, link, cfg):
            continue

        try:
            dt = dateparser.parse(pub) if pub else None
        except Exception:
            dt = None

        items.append({
            "title": title,
            "url": link,
            "published": dt.isoformat() if dt else None,
            "source": feed_url,
            "site_name": "RSS"
        })

    return items


def _scrape_news_index(index_url: str, site_name: str, cfg) -> List[Dict[str, Any]]:
    html = _http_get(index_url, cfg.project.user_agent)
    soup = BeautifulSoup(html, "lxml")
    items = []

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        title = a.get_text(" ", strip=True)

        if not href or len(title) < 8:
            continue

        if href.startswith("/"):
            from urllib.parse import urljoin
            href = urljoin(index_url, href)

        if not href.startswith("http"):
            continue

        if not _keyword_pass(title, href, cfg):
            continue

        items.append({
            "title": title,
            "url": href,
            "published": None,
            "source": index_url,
            "site_name": site_name
        })

    return items


def collect_latest_articles(cfg, cache) -> List[Dict[str, Any]]:
    all_items: List[Dict[str, Any]] = []

    # RSS first (fast & reliable)
    for feed in cfg.rss_feeds:
        try:
            all_items.extend(_parse_rss_feed(feed, cfg))
        except Exception:
            continue

    # Then scrape site index pages
    for site in cfg.websites:
        if not site.news_index:
            continue
        try:
            items = _scrape_news_index(site.news_index, site.name, cfg)
            all_items.extend(items)
        except Exception:
            continue

    # De-duplicate
    all_items = dedupe_links(all_items)

    # Date filtering (last N days)
    cutoff = datetime.utcnow() - timedelta(days=cfg.project.lookback_days)
    filtered = []

    for it in all_items:
        pub = it.get("published")
        if not pub:
            filtered.append(it)
            continue
        try:
            if dateparser.parse(pub) >= cutoff:
                filtered.append(it)
        except Exception:
            filtered.append(it)

    # Enforce per-site limits
    per_site = {}
    final = []

    for it in filtered:
        site = it.get("site_name", "unknown")
        per_site.setdefault(site, 0)

        if per_site[site] >= cfg.project.max_articles_per_site:
            continue

        per_site[site] += 1
        final.append(it)

        if len(final) >= cfg.project.max_total_articles:
            break

    return final
