#!/usr/bin/env python3
"""
pdf_downloader.py - Download arXiv paper PDFs using requests.
"""

import argparse
import json
import os
import sys
import time
from typing import List, Dict

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def download_pdf(paper: dict, pdf_dir: str) -> bool:
    """Download a single paper PDF. Returns True on success."""
    pdf_url = paper.get("pdf_url", "")
    if not pdf_url:
        return False

    arxiv_id = paper["arxiv_id"].replace("/", "_")
    pdf_path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")

    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        paper["local_pdf"] = pdf_path
        return True

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        if HAS_REQUESTS:
            resp = requests.get(pdf_url, headers=headers, timeout=60, stream=True)
            resp.raise_for_status()
            with open(pdf_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            import urllib.request
            req = urllib.request.Request(pdf_url, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                with open(pdf_path, "wb") as f:
                    f.write(resp.read())

        if os.path.getsize(pdf_path) > 0:
            paper["local_pdf"] = pdf_path
            return True
        else:
            os.remove(pdf_path)
            return False

    except Exception as e:
        print(f"  [WARN] Download failed {arxiv_id}: {e}", file=sys.stderr)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        return False


def download_pdfs(papers: List[Dict], pdf_dir: str):
    """Download PDFs for all papers."""
    os.makedirs(pdf_dir, exist_ok=True)

    count = 0
    total = len(papers)
    for i, paper in enumerate(papers):
        pdf_url = paper.get("pdf_url", "")
        if not pdf_url:
            continue

        arxiv_id = paper["arxiv_id"].replace("/", "_")
        print(f"  [{i+1}/{total}] {arxiv_id} ...", end=" ")

        ok = download_pdf(paper, pdf_dir)
        if ok:
            count += 1
            print("OK")
        else:
            print("FAIL")

        time.sleep(1)  # Rate limit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download arXiv PDFs")
    parser.add_argument("--input", default="data/papers_translated.json")
    parser.add_argument("--output", default="data/papers_translated.json")
    parser.add_argument("--pdf_dir", default="pdfs")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        papers = json.load(f)

    download_pdfs(papers, args.pdf_dir)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"Done: {args.output}")
