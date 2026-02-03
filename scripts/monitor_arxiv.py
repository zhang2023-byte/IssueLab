#!/usr/bin/env python3
"""
arXiv 论文监控脚本

定期扫描 arXiv 新论文，返回指定时间范围内的新论文列表。

Usage:
    python scripts/monitor_arxiv.py \
        --categories "cs.AI,cs.LG,cs.CL" \
        --last-scan "2026-01-01T00:00:00Z" \
        --max-papers 10 \
        --output /tmp/papers.json
"""

import argparse
import json
import re
import sys
import urllib.parse
from datetime import datetime
from typing import Any

import feedparser


def parse_arxiv_date(date_str: str) -> str:
    """解析 arXiv 日期格式为 ISO 格式"""
    try:
        # arXiv 日期格式: "2026-01-15T20:00:00Z"
        dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str[:10] if date_str else "Unknown"


def clean_text(text: str) -> str:
    """清理文本中的多余空白"""
    # 移除多余空白
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate_text(text: str, max_length: int = 1500) -> str:
    """截断文本，保留摘要可用"""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(".", 1)[0] +..."


def fetch_arxiv_papers(
    categories: list[str],
    last_scan: str,
    max_papers: int = 10,
) -> list[dict[str, Any]]:
    """
    获取指定分类下的新论文

    Args:
        categories: arXiv 分类列表
        last_scan: 上次扫描时间 (ISO 格式)
        max_papers: 最大返回数量

    Returns:
        新论文列表
    """
    # 解析 last_scan 时间
    try:
        last_scan_dt = datetime.strptime(last_scan[:19], "%Y-%m-%dT%H:%M:%S")
        last_scan_timestamp = last_scan_dt.timestamp()
    except (ValueError, TypeError):
        last_scan_timestamp = 0

    all_papers = []

    for category in categories:
        print(f"📥 获取 {category} 分类论文...")

        # arXiv API 查询 URL
        base_url = "http://export.arxiv.org/api/query"
        query = f"cat:{category}"
        params = {
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_papers * 3,  # 多取一些，因为有些可能过期
        }

        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        print(f"   URL: {url}")

        try:
            response = feedparser.parse(url)

            if response.bozo:
                print(f"   ⚠️  解析失败: {response.bozo_exception}")

            entry_count = 0
            for entry in response.entries:
                # 解析发布时间
                published_str = entry.get("published", "")
                try:
                    published_dt = datetime.strptime(published_str[:19], "%Y-%m-%dT%H:%M:%S")
                    published_timestamp = published_dt.timestamp()
                except (ValueError, TypeError):
                    published_timestamp = 0

                # 过滤：只保留 last_scan 之后的新论文
                if published_timestamp <= last_scan_timestamp:
                    continue

                # 提取作者
                authors = [author.get("name", "") for author in entry.get("authors", [])]
                author_str = ", ".join(authors[:5])
                if len(authors) > 5:
                    author_str += f" 等 {len(authors)} 位作者"

                # 清理摘要
                summary = clean_text(entry.get("summary", ""))
                summary = truncate_text(summary)

                # 提取论文 URL
                arxiv_url = ""
                for link in entry.get("links", []):
                    if link.get("type", "").startswith("text/html"):
                        arxiv_url = link.get("href", "")
                        break
                if not arxiv_url:
                    arxiv_url = f"https://arxiv.org/abs/{entry.get('id', '').split('/abs/')[-1]}"

                # 提取 arXiv ID
                arxiv_id = entry.get("id", "").split("/abs/")[-1]

                paper = {
                    "id": arxiv_id,
                    "title": clean_text(entry.get("title", "")),
                    "summary": summary,
                    "url": arxiv_url,
                    "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                    "authors": author_str,
                    "published": parse_arxiv_date(published_str),
                    "published_raw": published_str,
                    "category": category,
                    "tags": [tag.get("term", "") for tag in entry.get("tags", [])],
                }

                all_papers.append(paper)
                entry_count += 1

                if len(all_papers) >= max_papers:
                    break

            print(f"   ✅ 获取 {entry_count} 篇新论文")

        except Exception as e:
            print(f"   ❌ 获取失败: {e}")
            continue

    # 按发布时间排序（降序）
    all_papers.sort(key=lambda x: x.get("published_raw", ""), reverse=True)

    # 去除重复（同一论文可能出现在多个分类）
    seen_ids = set()
    unique_papers = []
    for paper in all_papers:
        if paper["id"] not in seen_ids:
            seen_ids.add(paper["id"])
            unique_papers.append(paper)

    return unique_papers[:max_papers]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Monitor arXiv for new papers"
    )
    parser.add_argument(
        "--categories",
        type=str,
        default="cs.AI,cs.LG,cs.CL",
        help="arXiv categories (comma-separated)",
    )
    parser.add_argument(
        "--last-scan",
        type=str,
        default="",
        help="Last scan time (ISO format, e.g., 2026-01-01T00:00:00Z)",
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=10,
        help="Maximum number of papers to return",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/papers.json",
        help="Output JSON file path",
    )

    args = parser.parse_args(argv)

    # 解析分类列表
    categories = [c.strip() for c in args.categories.split(",") if c.strip()]

    # 如果没有指定 last-scan，默认 7 天前
    if not args.last_scan:
        last_scan = (datetime.now() - datetime.timedelta(days=7)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    else:
        last_scan = args.last_scan

    print(f"🔍 开始扫描 arXiv...")
    print(f"   分类: {', '.join(categories)}")
    print(f"   上次扫描: {last_scan}")
    print(f"   最大数量: {args.max_papers}")
    print()

    # 获取新论文
    papers = fetch_arxiv_papers(categories, last_scan, args.max_papers)

    print(f"\n📊 共找到 {len(papers)} 篇新论文")

    # 保存到 JSON 文件
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)

    print(f"💾 结果已保存到: {args.output}")

    # 打印摘要
    for i, paper in enumerate(papers, 1):
        print(f"   {i}. [{paper['category']}] {paper['title'][:50]}...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
