#!/usr/bin/env python3
"""scan_project.py — 扫描项目资料目录，输出结构树 + 关键文件分档清单。

用法:
    python scan_project.py <项目目录> [--depth N] [--no-tree]

设计目标(配合 project-intro-writer 技能):
  - 过滤噪音目录(.git/node_modules/.obsidian/.venv/dist/build 等), 不做穷尽式深挖
  - 按"方案汇报 / 需求设计 / 工程资产 / 其他"四档给文件打标, 指引按优先级取用
"""
import argparse
import os
import re
import sys
from datetime import datetime

NOISE_DIRS = {
    ".git", ".obsidian", ".opencode", ".venv", "venv", "env", "__pycache__",
    "node_modules", "dist", "build", "out", "target", ".idea", ".vscode",
    ".next", ".nuxt", "coverage", ".pytest_cache", ".mypy_cache",
}

# 文件名关键词 -> 分档
TIER1 = ["方案", "汇报", "kickoff", "简介", "ppt", "slides", "演示"]          # 方案汇报
TIER2 = ["需求", "设计", "prd", "架构", "drawio", "确认", "规格", "功能"]      # 需求设计
TIER3_EXT = {".sql", ".json", ".yaml", ".yml", ".toml", ".ini", ".conf", ".cfg"}
TIER3 = ["package.json", "pom.xml", "requirements.txt", "go.mod", "dockerfile",
         "docker-compose", "nginx", "csproj", "sln"]                        # 工程资产
DOC_EXT = {".docx", ".doc", ".pptx", ".ppt", ".pdf", ".xlsx", ".xls", ".md", ".txt", ".drawio"}


def tier_of(name: str, ext: str) -> int:
    low = name.lower()
    if any(k in low for k in TIER1) and ext in {".pptx", ".ppt", ".docx", ".doc", ".pdf"}:
        return 1
    if any(k in low for k in TIER2) or ext == ".drawio":
        return 2
    if ext in TIER3_EXT or low in TIER3:
        return 3
    if ext in DOC_EXT:
        return 4
    return 5


def human(size: int) -> str:
    for unit in ("B", "K", "M", "G"):
        if size < 1024 or unit == "G":
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}G"


def scan(root: str, depth: int):
    tree_lines, buckets = [], {1: [], 2: [], 3: [], 4: [], 5: []}
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in NOISE_DIRS)
        rel = os.path.relpath(dirpath, root)
        level = 0 if rel == "." else rel.count(os.sep) + 1
        if level > depth:
            dirnames[:] = []
            continue
        if rel != ".":
            tree_lines.append("  " * (level - 1) + f"[D] {os.path.basename(dirpath)}/")
        for f in sorted(filenames):
            full = os.path.join(dirpath, f)
            try:
                st = os.stat(full)
            except OSError:
                continue
            mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")
            tree_lines.append("  " * level + f"[F] {f}  ({human(st.st_size)}, {mtime})")
            t = tier_of(f, os.path.splitext(f)[1].lower())
            buckets[t].append((full, st.st_size, mtime))
    return tree_lines, buckets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--depth", type=int, default=4)
    ap.add_argument("--no-tree", action="store_true")
    args = ap.parse_args()
    if not os.path.isdir(args.root):
        sys.exit(f"目录不存在: {args.root}")

    tree, buckets = scan(args.root, args.depth)
    if not args.no_tree:
        print("========== 目录结构树(已过滤噪音目录) ==========")
        print("\n".join(tree))
    labels = {
        1: "【第一档】方案/汇报类(最先读)",
        2: "【第二档】需求/设计类",
        3: "【第三档】工程资产类(配置/依赖清单)",
        4: "【第四档】其他文档",
        5: "【第五档】其余文件(按需)",
    }
    print("\n========== 关键文件分档清单 ==========")
    for t in (1, 2, 3, 4):
        print(f"\n{labels[t]}  (共 {len(buckets[t])} 个)")
        for full, size, mtime in buckets[t]:
            print(f"  {human(size):>7}  {mtime}  {full}")
    print(f"\n(第五档共 {len(buckets[5])} 个文件未列出，多为二进制/中间产物)")


if __name__ == "__main__":
    main()
