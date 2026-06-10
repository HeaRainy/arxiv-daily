#!/usr/bin/env python3
"""
arxiv_fetcher.py - 从 arXiv API 检索论文
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 设置代理
proxy_server = "http://proxy.hk.hihonor.com:8080"  # 硬编码代理
if proxy_server:
    proxy_handler = urllib.request.ProxyHandler({'http': proxy_server, 'https': proxy_server})
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)


def search_arxiv(keywords: List[str], max_results: int = 50,
                 days_back: int = 1, categories: List[str] = None) -> List[Dict]:
    """
    搜索 arXiv 论文。

    Args:
        keywords: 关键词列表（OR 连接）
        max_results: 每个关键词最大返回数
        days_back: 回溯天数
        categories: 过滤分类（如 ["cs.CV", "cs.AI"]）

    Returns:
        论文列表，去重（按 arxiv_id）
    """
    all_papers = {}
    date_cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")

    for keyword in keywords:
        query_parts = [f'all:"{keyword}"']
        if categories:
            cat_filter = " OR ".join(f"cat:{c}" for c in categories)
            query_parts.append(f"({cat_filter})")

        query = " AND ".join(query_parts)
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        url = f"http://export.arxiv.org/api/query?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "arxiv-daily-bot/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml_data = resp.read().decode("utf-8")
        except Exception as e:
            print(f"  [WARN] 检索 '{keyword}' 失败: {e}", file=sys.stderr)
            continue

        root = ET.fromstring(xml_data)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        for entry in root.findall("atom:entry", ns):
            arxiv_id = entry.find("atom:id", ns).text.strip()
            # 提取纯 ID（去掉 URL 前缀）
            arxiv_id = arxiv_id.split("/abs/")[-1]

            if arxiv_id in all_papers:
                continue

            published = entry.find("atom:published", ns).text.strip()[:10].replace("-", "")
            if published < date_cutoff:
                continue

            title = " ".join(entry.find("atom:title", ns).text.strip().split())
            summary = " ".join(entry.find("atom:summary", ns).text.strip().split())

            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None:
                    authors.append(name.text.strip())

            # 分类
            cats = []
            for cat in entry.findall("atom:category", ns):
                cats.append(cat.get("term"))

            # PDF 链接
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href")
                    break

            all_papers[arxiv_id] = {
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors,
                "summary": summary,
                "published": published,
                "categories": cats,
                "pdf_url": pdf_url,
                "matched_keyword": keyword,
            }

        time.sleep(1)  # arXiv API 限速

    papers = sorted(all_papers.values(), key=lambda x: x["published"], reverse=True)
    return papers


def save_papers(papers: List[Dict], output_path: str):
    """保存论文列表为 JSON"""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"保存 {len(papers)} 篇论文 -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="arXiv 论文检索")
    parser.add_argument("--keywords", nargs="+", required=True, help="检索关键词")
    parser.add_argument("--max_results", type=int, default=50)
    parser.add_argument("--days_back", type=int, default=1)
    parser.add_argument("--categories", nargs="*", default=["cs.CV", "cs.AI", "cs.LG"])
    parser.add_argument("--output", default="data/papers.json", help="输出 JSON 路径")
    args = parser.parse_args()

    papers = search_arxiv(
        keywords=args.keywords,
        max_results=args.max_results,
        days_back=args.days_back,
        categories=args.categories,
    )
    save_papers(papers, args.output)
    print(f"检索完成，共 {len(papers)} 篇论文")


