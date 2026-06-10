#!/usr/bin/env python3
"""excel_manager.py - Maintain local Excel records with deduplication"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Dict


def load_excel(path: str) -> List[Dict]:
    """Load existing Excel/CSV"""
    if not os.path.exists(path):
        return []

    import csv
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def merge_papers(existing: List[Dict], new_papers: List[Dict]) -> List[Dict]:
    """Merge new and old papers, deduplicate by arxiv_id, new papers first"""
    seen_ids = set()
    merged = []
    
    # Get today's date as crawled_date
    today = datetime.now().strftime("%Y%m%d")

    for paper in new_papers:
        aid = paper.get("arxiv_id", "")
        if aid not in seen_ids:
            seen_ids.add(aid)
            # Add crawled_date if not exists
            if "crawled_date" not in paper or not paper["crawled_date"]:
                paper["crawled_date"] = today
            merged.append(paper)

    for paper in existing:
        aid = paper.get("arxiv_id", "")
        if aid not in seen_ids:
            seen_ids.add(aid)
            merged.append(paper)

    return merged


def save_to_csv(papers: List[Dict], path: str):
    """Save as CSV"""
    if not papers:
        print("No data, skip saving")
        return

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    fieldnames = [
        "arxiv_id", "title", "title_zh", "authors", "summary", "summary_zh",
        "affiliations", "published", "categories", "pdf_url",
        "local_pdf", "matched_keyword", "crawled_date",
    ]
    import csv
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for p in papers:
            row = {}
            for k in fieldnames:
                v = p.get(k, "")
                if isinstance(v, list):
                    v = "; ".join(v)
                row[k] = v
            writer.writerow(row)
    print(f"Saved {len(papers)} records -> {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Maintain local Excel/CSV")
    parser.add_argument("--input", default="data/papers_translated.json")
    parser.add_argument("--excel", default="data/papers_record.csv")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        new_papers = json.load(f)

    existing = load_excel(args.excel)
    merged = merge_papers(existing, new_papers)
    save_to_csv(merged, args.excel)
