#!/usr/bin/env python3
"""Build viewer data from papers_translated.json (today) and papers_record.csv (history)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
JSON_PATH = BASE_DIR / "data" / "papers_translated.json"
CSV_PATH = BASE_DIR / "data" / "papers_record.csv"
OUTPUT_PATH = Path(__file__).resolve().parent / "papers_data.json"


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


def format_date(date_str: str) -> str:
    """Convert YYYYMMDD to YYYY-MM-DD"""
    if not date_str or len(date_str) != 8:
        return date_str
    return date_str[:4] + "-" + date_str[4:6] + "-" + date_str[6:8]


def load_from_json() -> list[dict]:
    """Load today's data from papers_translated.json"""
    if not JSON_PATH.exists():
        return []
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        papers = json.load(f)
    rows = []
    for p in papers:
        rows.append({
            "arxiv_id": normalize_text(p.get("arxiv_id", "")),
            "title": normalize_text(p.get("title", "")),
            "authors": normalize_text(p.get("authors", "")),
            "affiliations": normalize_text(p.get("affiliations", "")),
            "published_date": format_date(normalize_text(p.get("published", ""))),
            "categories": normalize_text(p.get("categories", "")),
            "abstract": normalize_text(p.get("summary", "")),
            "summary_cn": normalize_text(p.get("summary_zh", "")),
            "pdf_url": normalize_text(p.get("pdf_url", f"https://arxiv.org/pdf/{p.get('arxiv_id', '')}")),
            "pdf_filename": normalize_text(p.get("local_pdf", "")),
            "crawled_date": format_date(normalize_text(p.get("published", ""))),
        })
    return rows


def load_from_csv() -> list[dict]:
    """Load history data from papers_record.csv"""
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            arxiv_id = row.get("arxiv_id", "").strip()
            if not arxiv_id:
                continue
            rows.append({
                "arxiv_id": arxiv_id,
                "title": normalize_text(row.get("title", "")),
                "authors": normalize_text(row.get("authors", "")),
                "affiliations": normalize_text(row.get("affiliations", "")),
                "published_date": format_date(normalize_text(row.get("published", ""))),
                "categories": normalize_text(row.get("categories", "")),
                "abstract": normalize_text(row.get("summary", "")),
                "summary_cn": normalize_text(row.get("summary_zh", "")),
                "pdf_url": normalize_text(row.get("pdf_url", f"https://arxiv.org/pdf/{arxiv_id}")),
                "pdf_filename": normalize_text(row.get("local_pdf", "")),
                "crawled_date": format_date(normalize_text(row.get("crawled_date", ""))),
            })
    return rows


def main() -> None:
    # Load history data (CSV)
    papers_by_id = {}
    csv_papers = load_from_csv()
    for paper in csv_papers:
        papers_by_id[paper["arxiv_id"]] = paper
    
    # Load today's data (JSON), overwrite same ID papers from history
    json_papers = load_from_json()
    for paper in json_papers:
        papers_by_id[paper["arxiv_id"]] = paper
    
    papers = list(papers_by_id.values())

    if not papers:
        papers = []

    # Mark new papers (crawled today)
    json_ids = {p["arxiv_id"] for p in json_papers}
    for paper in papers:
        paper["is_new"] = paper["arxiv_id"] in json_ids

    papers.sort(key=lambda x: (x["crawled_date"], x["published_date"], x["arxiv_id"]), reverse=True)

    crawled_dates = sorted({p["crawled_date"] for p in papers if p["crawled_date"]})
    published_dates = sorted({p["published_date"] for p in papers if p["published_date"]})

    payload = {
        "count": len(papers),
        "new_count": sum(1 for p in papers if p.get("is_new")),
        "crawled_date_min": crawled_dates[0] if crawled_dates else "",
        "crawled_date_max": crawled_dates[-1] if crawled_dates else "",
        "published_date_min": published_dates[0] if published_dates else "",
        "published_date_max": published_dates[-1] if published_dates else "",
        "papers": papers,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Wrote {len(papers)} papers ({payload['new_count']} new) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()