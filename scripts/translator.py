#!/usr/bin/env python3
"""
translator.py - 翻译英文摘要为中文，提取作者单位
支持两种后端：free（deep-translator）和 openai（OpenAI API）
"""

import argparse
import json
import os
import re
import sys
import time
from typing import Dict, List, Optional


def translate_free(text: str) -> str:
    """使用 deep-translator (Google Translate) 免费翻译"""
    try:
        from deep_translator import GoogleTranslator
        # 分段翻译（Google 单次有长度限制）
        chunks = _split_text(text, 4000)
        results = []
        for chunk in chunks:
            result = GoogleTranslator(source="en", target="zh-CN").translate(chunk)
            results.append(result)
            if len(chunks) > 1:
                time.sleep(0.5)
        return " ".join(results)
    except ImportError:
        print("[ERROR] deep-translator 未安装，请运行: pip install deep-translator", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"[WARN] 翻译失败: {e}", file=sys.stderr)
        return ""


def translate_openai(text: str, api_key: str, base_url: str,
                     model: str = "gpt-4o-mini") -> str:
    """使用 OpenAI API 翻译"""
    try:
        import urllib.request
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个学术论文翻译助手。请将以下英文摘要翻译成流畅专业的中文，保留技术术语的英文原文（如 ResNet、Diffusion Model 等）。仅输出翻译结果，不要添加任何解释。"},
                {"role": "user", "content": text},
            ],
            "temperature": 0.1,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        })
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[WARN] OpenAI 翻译失败: {e}", file=sys.stderr)
        return ""


def extract_affiliations(text: str) -> str:
    """
    从摘要中提取可能的作者单位/机构名。
    使用正则匹配常见的机构模式。
    """
    patterns = [
        r'(?:at|from|in)\s+(?:the\s+)?([A-Z][a-zA-Z\s&.,]+(?:University|Institute|College|Lab|Laboratory|Research|Inc|Ltd|Corp|Corporation|GmbH|S\.A\.|B\.V\.|K\.K\.|Labs?))',
        r'([A-Z][a-zA-Z\s&.,]+(?:University|Institute|College|Lab|Laboratory|Research))',
    ]
    affiliations = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            m = m.strip().rstrip(".,;")
            if len(m) > 5:
                affiliations.add(m)
    return "; ".join(sorted(affiliations)[:5])


def _split_text(text: str, max_len: int) -> List[str]:
    """按句子边界分段，每段不超过 max_len"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) + 1 > max_len and current:
            chunks.append(current)
            current = sent
        else:
            current = (current + " " + sent).strip()
    if current:
        chunks.append(current)
    return chunks


def process_papers(papers: List[Dict], translate_api: str = "free",
                   openai_key: str = "", openai_base: str = "",
                   openai_model: str = "gpt-4o-mini") -> List[Dict]:
    """对论文列表进行翻译和机构提取"""
    for i, paper in enumerate(papers):
        print(f"  处理 [{i+1}/{len(papers)}] {paper['arxiv_id']}: {paper['title'][:60]}...")

        # 翻译标题
        if translate_api == "openai" and openai_key:
            paper["title_zh"] = translate_openai(paper["title"], openai_key, openai_base, openai_model)
        else:
            paper["title_zh"] = translate_free(paper["title"])

        # 翻译摘要
        if translate_api == "openai" and openai_key:
            paper["summary_zh"] = translate_openai(paper["summary"], openai_key, openai_base, openai_model)
        else:
            paper["summary_zh"] = translate_free(paper["summary"])

        # 提取作者单位
        paper["affiliations"] = extract_affiliations(paper["summary"])

        if translate_api == "free":
            time.sleep(0.3)  # 免费 API 限速

    return papers


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="翻译论文摘要")
    parser.add_argument("--input", default="data/papers.json", help="输入 JSON")
    parser.add_argument("--output", default="data/papers_translated.json", help="输出 JSON")
    parser.add_argument("--api", default="free", choices=["free", "openai"])
    parser.add_argument("--openai_key", default="")
    parser.add_argument("--openai_base", default="https://api.openai.com/v1")
    parser.add_argument("--openai_model", default="gpt-4o-mini")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        papers = json.load(f)

    papers = process_papers(papers, args.api, args.openai_key, args.openai_base, args.openai_model)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"翻译完成 -> {args.output}")
