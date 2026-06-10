#!/usr/bin/env python3
"""
feishu_notifier.py - 推送论文日报到飞书群机器人
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import List, Dict

# 从本文件向上两层即为项目根目录，优先读取 viewer/papers_data.json
BASE_DIR = Path(__file__).resolve().parent.parent
VIEWER_DATA = BASE_DIR / "viewer" / "papers_data.json"
TRANSLATED_DATA = BASE_DIR / "data" / "papers_translated.json"


def load_papers(input_path: str) -> List[Dict]:
    """加载论文数据，自动从 papers_data.json 读取（包含 is_new 字段）"""
    path = Path(input_path) if input_path else None

    # 优先从 viewer/papers_data.json 读取，因为其中包含 is_new 字段
    if VIEWER_DATA.exists():
        path = VIEWER_DATA
    elif TRANSLATED_DATA.exists():
        path = TRANSLATED_DATA
    elif path is None or not path.exists():
        raise FileNotFoundError(f"找不到论文数据：{path or 'papers_data.json'}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 支持 {"papers": [...]} 格式
    if isinstance(data, dict) and "papers" in data:
        return data["papers"]
    # 支持 [...] 格式
    return data


def build_feishu_card(papers: List[Dict], web_url: str = "") -> dict:
    """
    构建飞书卡片消息。

    Args:
        papers: 论文列表
        web_url: Web 阅读页 URL（可选）

    Returns:
        飞书消息体 dict
    """
    elements = []

    # 统计新增论文数量
    new_count = sum(1 for p in papers if p.get("is_new"))

    # 标题
    title = f"**📄 arXiv 论文日报 — {len(papers)} 篇论文**"
    if new_count > 0:
        title += f" **{new_count} 篇新论文**"
    elements.append({
        "tag": "markdown",
        "content": title
    })

    if web_url:
        elements.append({
            "tag": "markdown",
            "content": f"[🌐 网页阅读]({web_url})"
        })

    elements.append({"tag": "hr"})

    # 每篇论文的卡片
    for i, paper in enumerate(papers[:20]):  # 最多 20 篇
        title_text = paper.get("title_zh", paper.get("title", ""))[:100]
        arxiv_id = paper["arxiv_id"]
        paper_url = f"https://arxiv.org/abs/{arxiv_id}"

        # NEW 标识
        is_new = paper.get("is_new", False)
        new_tag = " 🔴 **NEW**" if is_new else ""

        content = f"**{i+1}. [{title_text}]({paper_url})**{new_tag}\n"
        content += f"📎 arXiv: {arxiv_id}"

        authors = paper.get("authors", [])
        if authors:
            authors_str = authors if isinstance(authors, str) else ", ".join(authors[:3])
            content += f" | 作者: {authors_str}"
            if len(authors) > 3:
                content += " et al."

        affiliations = paper.get("affiliations", "")
        if affiliations:
            content += f"\n🏫 {affiliations[:150]}"

        elements.append({"tag": "markdown", "content": content})

    if len(papers) > 20:
        elements.append({
            "tag": "markdown",
            "content": f"... 还有 {len(papers) - 20} 篇，请查看 Web 页面"
        })

    elements.append({"tag": "hr"})
    elements.append({
        "tag": "markdown",
        "content": f"🤖 自动生成于 arXiv Daily Bot"
    })

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "arXiv 论文日报"},
                "template": "blue",
            },
            "elements": elements,
        }
    }
    return card


def send_feishu(webhook_url: str, message: dict):
    """发送消息到飞书"""
    payload = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                print("飞书推送成功")
            else:
                print(f"飞书推送失败: {result}", file=sys.stderr)
    except Exception as e:
        print(f"飞书推送异常: {e}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="推送论文日报到飞书")
    parser.add_argument("--input", default="", help="输入 JSON（默认自动定位）")
    parser.add_argument("--webhook", required=True, help="飞书 Webhook URL")
    parser.add_argument("--web_url", default="http://10.163.65.48:8765", help="Web 阅读页 URL")
    args = parser.parse_args()

    if not args.webhook or args.webhook == "your_webhook_url_here":
        print("[ERROR] 请设置 --webhook 参数", file=sys.stderr)
        sys.exit(1)

    papers = load_papers(args.input)
    message = build_feishu_card(papers, args.web_url)
    send_feishu(args.webhook, message)