import os
from pathlib import Path

from src.config import load_config
from src.cache import Cache
from src.fetchers import collect_latest_articles
from src.extractors import extract_article
from src.llm_deepseek import DeepSeekClient
from src.themes import build_themes
from src.market import fetch_etf_signals_for_themes
from src.analysis import price_in_verdicts
from src.report import write_report


def main():
    # ===== Customize here =====
    CONFIG_PATH = os.getenv("INSIGHT_RADAR_CONFIG", "config.yaml")
    ETF_MAP_PATH = os.getenv("INSIGHT_RADAR_ETF_MAP", "etf_map.json")
    # ==========================

    cfg = load_config(CONFIG_PATH)
    cache = Cache(cfg.project.cache_dir)

    llm = DeepSeekClient(
        api_key=cfg.deepseek.api_key,
        base_url=cfg.deepseek.base_url,
        model=cfg.deepseek.model,
        timeout_sec=cfg.deepseek.timeout_sec,
    )

    Path(cfg.project.output_dir).mkdir(parents=True, exist_ok=True)

    # 1) Collect latest article links
    links = collect_latest_articles(cfg, cache)
    if not links:
        print("No links found. Try adding rss_feeds or a news_index for each site.")
        return

    # 2) Extract + summarize each article with citations
    articles = []
    for item in links:
        art = extract_article(item, cfg, cache)
        if not art.get("text"):
            continue

        summary = llm.summarize_article(art)
        art["summary"] = summary
        articles.append(art)

        if cfg.output.save_raw_articles:
            cache.save_json(
                f"raw_articles/{cache.safe_key(art['url'])}.json",
                art
            )

        if len(articles) >= cfg.project.max_total_articles:
            break

    if not articles:
        print("No articles extracted successfully.")
        return

    # 3) Cluster into themes + map to ETFs
    etf_map = cache.load_json_file(ETF_MAP_PATH, default={})
    themes = build_themes(llm, articles, etf_map)

    # 4) Fetch ETF market signals
    themes_with_signals = fetch_etf_signals_for_themes(cfg, themes)

    # 5) Priced-in verdicts using LLM + heuristics
    final_themes = price_in_verdicts(llm, themes_with_signals, cfg)

    # 6) Write report
    out_path = os.path.join(cfg.project.output_dir, cfg.output.report_filename)
    write_report(out_path, final_themes, articles, cfg)

    print(f"Report written to: {out_path}")
    print("Not financial advice.")


if __name__ == "__main__":
    main()
