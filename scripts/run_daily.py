#!/usr/bin/env python3
"""
run_daily.py - 每日运行入口：检索 -> 翻译 -> 下载 PDF -> 更新 CSV -> 构建 Viewer -> 推送飞书
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime


SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)
VIEWER_DIR = os.path.join(SKILL_DIR, "viewer")


def run_step(step_name: str, args: list):
    print(f"\n{'='*60}")
    print(f"  [{step_name}]")
    print(f"{'='*60}")
    cmd = [sys.executable] + args
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"[ERROR] {step_name} failed (exit={result.returncode})", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="arXiv daily paper monitor")
    parser.add_argument("--config", default=os.path.join(SCRIPTS_DIR, "config.yaml"))
    parser.add_argument("--keywords", nargs="+", help="Search keywords")
    parser.add_argument("--max_results", type=int, default=50)
    parser.add_argument("--days_back", type=int, default=1)
    parser.add_argument("--webhook", default="", help="Feishu webhook URL")
    parser.add_argument("--web_port", type=int, default=8765, help="Viewer port")
    parser.add_argument("--web_url", type=str, default="", help="Viewer port")
    parser.add_argument("--data_dir", default=os.path.join(SKILL_DIR, "data"))
    parser.add_argument("--pdf_dir", default=os.path.join(SKILL_DIR, "pdfs"))
    parser.add_argument("--translate_api", default="free", choices=["free", "openai"])
    parser.add_argument("--openai_key", default="")
    parser.add_argument("--openai_base", default="https://api.openai.com/v1")
    parser.add_argument("--openai_model", default="gpt-4o-mini")
    parser.add_argument("--skip_translate", action="store_true")
    parser.add_argument("--skip_download", action="store_true")
    parser.add_argument("--skip_notify", action="store_true")
    parser.add_argument("--serve", action="store_true", help="Start viewer after processing")
    args = parser.parse_args()

    # Load YAML config
    config = {}
    if os.path.exists(args.config):
        try:
            import yaml
            with open(args.config, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except ImportError:
            pass

    arxiv_cfg = config.get("arxiv", {})
    feishu_cfg = config.get("feishu", {})
    local_cfg = config.get("local", {})
    trans_cfg = config.get("translate", {})
    
    


    keywords = args.keywords or arxiv_cfg.get("keywords", ["image generation", "diffusion model"])
    max_results = args.max_results if args.max_results != 50 else arxiv_cfg.get("max_results_per_keyword", 50)
    days_back = args.days_back if args.days_back != 1 else arxiv_cfg.get("days_back", 1)
    webhook = args.webhook or feishu_cfg.get("webhook_url", "")
    web_url = args.web_url or feishu_cfg.get("web_url", "")
    data_dir = args.data_dir or local_cfg.get("data_dir", os.path.join(SKILL_DIR, "data"))
    pdf_dir = args.pdf_dir or local_cfg.get("pdf_dir", os.path.join(SKILL_DIR, "pdfs"))
    translate_api = args.translate_api or trans_cfg.get("api", "free")
    openai_key = args.openai_key or trans_cfg.get("openai_api_key", "")
    openai_base = args.openai_base or trans_cfg.get("openai_base_url", "https://api.openai.com/v1")
    openai_model = args.openai_model or trans_cfg.get("openai_model", "gpt-4o-mini")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)

    papers_json = os.path.join(data_dir, "papers.json")
    translated_json = os.path.join(data_dir, "papers_translated.json")
    excel_path = os.path.join(data_dir, "papers_record.csv")

    # Step 1: Search arXiv
    if not run_step("1. arXiv Search", [
        os.path.join(SCRIPTS_DIR, "arxiv_fetcher.py"),
        "--keywords", *keywords,
        "--max_results", str(max_results),
        "--days_back", str(days_back),
        "--output", papers_json,
    ]):
        sys.exit(1)

    # Step 2: Translate
    if not args.skip_translate:
        trans_args = [
            os.path.join(SCRIPTS_DIR, "translator.py"),
            "--input", papers_json,
            "--output", translated_json,
            "--api", translate_api,
        ]
        if translate_api == "openai":
            trans_args += ["--openai_key", openai_key, "--openai_base", openai_base, "--openai_model", openai_model]
        run_step("2. Translate + Extract Affiliations", trans_args)
    else:
        translated_json = papers_json

    # Step 3: Download PDFs
    if not args.skip_download:
        run_step("3. Download PDFs", [
            os.path.join(SCRIPTS_DIR, "pdf_downloader.py"),
            "--input", translated_json,
            "--pdf_dir", pdf_dir,
        ])

    # Step 5: Build viewer data
    run_step("5. Build Viewer Data", [
        os.path.join(VIEWER_DIR, "build_data.py"),
    ])

    # Step 4: Update CSV
    run_step("4. Update CSV Record", [
        os.path.join(SCRIPTS_DIR, "excel_manager.py"),
        "--input", translated_json,
        "--excel", excel_path,
    ])

    # Step 6: Push to Feishu
    if not args.skip_notify and webhook:
        weburl = f"http://{web_url}:{args.web_port}"
        run_step("6. Push to Feishu", [
            os.path.join(SCRIPTS_DIR, "feishu_notifier.py"),
            "--input", translated_json,
            "--webhook", webhook,
            "--web_url", weburl,
        ])
    elif not webhook:
        print("[SKIP] No Feishu webhook configured")

    # Step 7: Serve viewer
    if args.serve:
        print(f"\nStarting viewer: http://{web_url}:{args.web_port}")
        subprocess.run([
            sys.executable,
            os.path.join(VIEWER_DIR, "run_viewer.py"),
            "--port", str(args.web_port),
            "--host", str({args.web_url}),
        ])

    print(f"\n{'='*60}")
    print(f"  All done!")
    print(f"  Data: {os.path.abspath(data_dir)}")
    print(f"  CSV:  {excel_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
