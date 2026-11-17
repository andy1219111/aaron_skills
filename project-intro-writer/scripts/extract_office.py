#!/usr/bin/env python3
"""extract_office.py — 提取项目资料中常见文档的纯文本，用于证据摘录。

支持: .docx .pptx .xlsx .pdf .drawio .md .txt .log .csv(预览)
用法:
    python extract_office.py <文件> [--max-chars N] [--slides N]
    python extract_office.py <文件1> <文件2> ...   # 批量

依赖策略: docx/pptx/xlsx/drawio 用 zipfile+正则(零依赖); pdf 优先 PyMuPDF(fitz),
不可用时提示 pip install pymupdf。输出为纯文本，直接阅读即可。
"""
import argparse
import os
import re
import sys
import zipfile


def _xml_text(xml: str) -> str:
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"</a:p>", "\n", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    return re.sub(r"\n{2,}", "\n", text)


def docx_text(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        return _xml_text(z.read("word/document.xml").decode("utf-8", "ignore"))


def pptx_text(path: str, max_slides: int) -> str:
    out = []
    with zipfile.ZipFile(path) as z:
        slides = [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
        slides.sort(key=lambda n: int(re.findall(r"\d+", n)[0]))
        for n in slides[:max_slides]:
            xml = z.read(n).decode("utf-8", "ignore")
            runs = re.findall(r"<a:t>(.*?)</a:t>", xml, re.S)
            txt = " | ".join(r.strip() for r in runs if r.strip())
            if txt:
                out.append(f"--- {os.path.basename(n)} ---\n{txt}")
    return "\n".join(out)


def xlsx_text(path: str) -> str:
    out = []
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            ss = z.read("xl/sharedStrings.xml").decode("utf-8", "ignore")
            shared = [re.sub(r"<[^>]+>", "", si) for si in re.findall(r"<si>(.*?)</si>", ss, re.S)]
        for n in sorted(z.namelist()):
            if re.match(r"xl/worksheets/sheet\d+\.xml$", n):
                xml = z.read(n).decode("utf-8", "ignore")
                cells = []
                for c in re.findall(r'<c[^>]*?(?:\st="(\w+)")?[^>]*>(?:<v>(.*?)</v>)?</c>', xml):
                    t, v = c
                    if not v:
                        continue
                    cells.append(shared[int(v)] if t == "s" and v.isdigit() else v)
                if cells:
                    out.append(f"--- {os.path.basename(n)} ---\n" + " | ".join(cells))
    return "\n".join(out)


def drawio_text(path: str) -> str:
    xml = open(path, encoding="utf-8", errors="ignore").read()
    vals, seen = [], set()
    for v in re.findall(r'value="([^"]+)"', xml):
        v = (v.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
              .replace("<br>", " / "))
        v = re.sub(r"<[^>]+>", "", v).strip()
        if v and v not in seen:
            seen.add(v)
            vals.append(v)
    return "\n".join(vals)


def pdf_text(path: str, max_chars: int) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return "[提示] 需要 PyMuPDF: pip install pymupdf，或直接用 Read 工具读取 PDF"
    doc = fitz.open(path)
    parts = [f"pages: {doc.page_count}"]
    for i in range(doc.page_count):
        t = doc[i].get_text().strip()
        if t:
            parts.append(f"--- p{i+1} ---\n{t}")
    return "\n".join(parts)[:max_chars]


def extract(path: str, max_chars: int, max_slides: int) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return docx_text(path)
    if ext == ".pptx":
        return pptx_text(path, max_slides)
    if ext == ".xlsx":
        return xlsx_text(path)
    if ext == ".drawio":
        return drawio_text(path)
    if ext == ".pdf":
        return pdf_text(path, max_chars)
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read(max_chars)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--max-chars", type=int, default=20000)
    ap.add_argument("--slides", type=int, default=200)
    args = ap.parse_args()
    for p in args.files:
        if not os.path.isfile(p):
            print(f"!! 文件不存在: {p}")
            continue
        print("=" * 25, p)
        try:
            text = extract(p, args.max_chars, args.slides)
            print(text[: args.max_chars])
        except Exception as e:  # noqa: BLE001
            print(f"!! 提取失败: {e}")


if __name__ == "__main__":
    main()
