#!/usr/bin/env python3
"""Check a filled project overview before printing it to PDF.

Usage:  python3 check.py overview-<slug>.html [more.html ...]

Reports the printed word count (screen-only banner, CSS, JS and fill comments excluded),
anything left unfilled, and diagram sanity. Exits non-zero if a hard rule is broken.
"""
import html
import re
import sys

LIMIT = 500
STRIP = (
    r'<div class="banner">.*?</div>',      # screen-only, never prints
    r'<(script|style)[^>]*>.*?</\1>',
    r'<!--.*?-->',                          # fill guidance
)


def printed_words(src: str) -> int:
    for pat in STRIP:
        src = re.sub(pat, " ", src, flags=re.S)
    return len(html.unescape(re.sub(r"<[^>]+>", " ", src)).split())


def check(path: str) -> bool:
    src = open(path, encoding="utf-8").read()
    words = printed_words(src)
    placeholders = len(re.findall(r'class="[^"]*\bph\b', src))
    todos = len(re.findall(r"TODO\(verify\)", src))
    fills = sum("fill:" in c for c in re.findall(r"<!--.*?-->", src, flags=re.S))
    nodes = len(re.findall(r'class="node\b', src))
    cores = len(re.findall(r'class="node core\b', src))

    print(f"\n{path}")
    print(f"  printed words     {words}  (limit {LIMIT})")
    print(f"  placeholders left {placeholders}")
    print(f"  TODO(verify)      {todos}")
    print(f"  fill comments     {fills}")
    print(f"  diagram nodes     {nodes}  (max 12, .core exactly 1: found {cores})")

    problems = []
    if words > LIMIT:
        problems.append(f"over the word limit by {words - LIMIT}")
    if fills:
        problems.append("fill comments still present")
    if nodes > 12:
        problems.append("diagram has too many nodes to read at a glance")
    if nodes and cores != 1:
        problems.append(f"expected exactly 1 .core node, found {cores}")
    if placeholders or todos:
        print("  note: resolve placeholders and TODO(verify) lines before sending")

    for p in problems:
        print(f"  FAIL {p}")
    return not problems


if __name__ == "__main__":
    targets = sys.argv[1:] or ["overview-multi-tenant-rag-api.html"]
    sys.exit(0 if all(check(t) for t in targets) else 1)
