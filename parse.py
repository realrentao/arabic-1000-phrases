# -*- coding: utf-8 -*-
"""Parse 阿拉伯语常用语1000句.md into structured data (data.js + data.json)."""
import re, json, os

SRC = r"D:/阿拉伯语常用语1000句.md"
OUT_DIR = r"D:\workbuddy工作区\2026-07-09-22-10-17\arabic1000"
DATA_JS = os.path.join(OUT_DIR, "js", "data.js")
DATA_JSON = os.path.join(OUT_DIR, "data.json")

ROM_RE = re.compile(r"\s*\(([^()]*[A-Za-z][^()]*)\)\s*$")
NOTE_RE = re.compile(r"\\\[([^\]]*)\\?\]")  # matches \[核] (opening backslash; closing ] optional)

def split_ar_rom(cell):
    """Return (arabic, romanization, note) from a dialect cell.

    Strips a trailing/inline ``[核]`` note (used in the source to flag
    Maghreb synthetic/borrowed words) so it is never merged into the
    Arabic text, which previously broke both display and TTS audio.
    """
    cell = cell.strip()
    note = ""
    nm = NOTE_RE.search(cell)
    if nm:
        note = nm.group(1).strip()
        cell = (cell[:nm.start()] + cell[nm.end():]).strip()
    m = ROM_RE.search(cell)
    if m:
        ar = cell[:m.start()].strip()
        rom = m.group(1).strip()
        return ar, rom, note
    return cell, "", note

def map_header_cell(h):
    h = h.strip()
    if h.startswith("#") or h == "**#**":
        return "num"
    if "中文" in h:
        return "cn"
    if "标准语" in h:
        return "msa"
    if "埃及" in h:
        return "egyptian"
    if "黎凡特" in h or "海湾" in h:
        return "levantine"
    if "马格里布" in h:
        return "maghreb"
    if "最通用" in h:
        return "common"
    return None

def parse_table_row(line):
    # split by |, drop leading/trailing empty
    parts = [p.strip() for p in line.split("|")]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts

def main():
    with open(SRC, encoding="utf-8") as f:
        lines = f.read().split("\n")

    title = ""
    legend_lines = []
    intro_bullets = []
    sections = []

    i = 0
    n = len(lines)
    cur_section = None
    in_intro = False
    first_h2_seen = False

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # H1
        if stripped.startswith("# ") and not stripped.startswith("##"):
            title = stripped[2:].strip()
            i += 1
            continue

        # blockquote legend (only those before the first H2 -> header area)
        if stripped.startswith(">") and not first_h2_seen:
            legend_lines.append(stripped.lstrip(">").strip())
            i += 1
            continue

        # H2 section header
        if stripped.startswith("## "):
            first_h2_seen = True
            in_intro = False
            head = stripped[3:].strip()
            if head == "使用说明":
                in_intro = True
                i += 1
                continue
            # new content section
            cur_section = {"title": head, "rows": []}
            sections.append(cur_section)
            i += 1
            continue

        # intro bullets
        if in_intro and stripped.startswith("*"):
            intro_bullets.append(stripped.lstrip("*").strip())
            i += 1
            continue
        if in_intro and stripped.startswith("-"):
            intro_bullets.append(stripped.lstrip("-").strip())
            i += 1
            continue

        # table rows belonging to current section
        if stripped.startswith("|") and cur_section is not None:
            cells = parse_table_row(stripped)
            # header detection: find a cell containing "中文"
            if any("中文" in c for c in cells) and cur_section.get("_header") is None:
                colmap = [map_header_cell(c) for c in cells]
                cur_section["_header"] = colmap
                i += 1
                # skip separator row next
                if i < n and set(lines[i].replace("|", "").strip()) <= set("-: "):
                    i += 1
                continue
            # data row
            colmap = cur_section.get("_header")
            if colmap is not None and len(cells) == len(colmap):
                row = {"num": None, "cn": "", "dialects": {}, "common": ""}
                for key, val in zip(colmap, cells):
                    if key is None:
                        continue
                    if key == "num":
                        row["num"] = int(val) if val.strip().isdigit() else val.strip()
                    elif key == "cn":
                        row["cn"] = val.strip()
                    elif key == "common":
                        row["common"] = val.strip()
                    else:
                        ar, rom, note = split_ar_rom(val)
                        row["dialects"][key] = {"ar": ar, "rom": rom, "note": note}
                # only add if it has content
                if row["cn"] or row["dialects"]:
                    cur_section["rows"].append(row)
            i += 1
            continue

        i += 1

    # cleanup helper key
    for s in sections:
        s.pop("_header", None)

    data = {
        "title": title,
        "legend": "  ".join(legend_lines),
        "intro": intro_bullets,
        "sections": sections,
    }

    os.makedirs(os.path.dirname(DATA_JS), exist_ok=True)
    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write("// Auto-generated from 阿拉伯语常用语1000句.md\n")
        f.write("const DATA = ")
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    # summary
    total_rows = sum(len(s["rows"]) for s in sections)
    unique_ar = set()
    for s in sections:
        for r in s["rows"]:
            for d in r["dialects"].values():
                if d["ar"]:
                    unique_ar.add(d["ar"])
    print("Title:", title)
    print("Sections:", len(sections))
    print("Total rows:", total_rows)
    print("Unique arabic texts (4 dialects):", len(unique_ar))

if __name__ == "__main__":
    main()
