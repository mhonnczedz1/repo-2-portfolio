#!/usr/bin/env python3
"""Validate a project overview before it ships.

Usage:  python3 tools/check.py <slug> [--strict]

Checks content.json against the word budget and the quality bar, and checks the
rendered output when it exists. Exits non-zero on any hard failure. --strict also
fails on unresolved TODO(verify) claims, which is the gate before sending.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BUDGETS = {"header": 60, "problem": 75, "architecture": 190, "diagram": 55,
           "shots": 50, "decisions": 140, "impact": 85, "limits": 30, "footer": 7}
TOTAL = 700
TODO = "TODO(verify)"
REQUIRED = {"slug": str, "title": str, "tagline": str, "chips": list, "result": str,
            "problem": list, "architecture": list, "diagram": dict, "decisions": list,
            "impact": list, "limits": list, "footer": dict}


def words(*texts) -> int:
    """Printed words. The TODO marker is scaffolding and does not count."""
    return len(" ".join(str(t) for t in texts if t).replace(TODO, " ").split())


def section_texts(c: dict) -> dict:
    """Every string that prints, grouped by the budget line it belongs to."""
    d = c.get("diagram") or {}
    diagram = [d.get("caption", "")]
    for tier in d.get("tiers", []):
        diagram.append(tier.get("label", ""))
        for n in tier.get("nodes", []):
            diagram += [n.get("text", ""), n.get("note") or ""]
    f = c.get("footer") or {}
    return {
        "header": [c.get("title", ""), c.get("tagline", ""), c.get("result", "")]
                  + [f'{ch.get("label", "")} {ch.get("value", "")}' for ch in c.get("chips", [])],
        "problem": list(c.get("problem", [])),
        "architecture": list(c.get("architecture", [])),
        "diagram": diagram,
        "shots": [s.get("caption", "") for s in c.get("shots", [])],
        "decisions": [f'{x.get("chose", "")} over {x.get("over", "")} {x.get("because", "")}'
                      for x in c.get("decisions", [])],
        "impact": list(c.get("impact", []))
                  + [f'{m.get("value", "")} {m.get("label", "")}' for m in c.get("metrics", [])],
        "limits": list(c.get("limits", [])),
        "footer": [f.get("name", ""), f.get("email", ""), f.get("link", "")],
    }


def check_schema(c: dict) -> list:
    out = []
    for field, kind in REQUIRED.items():
        if field not in c:
            out.append(f"{field}: required field is missing")
        elif not isinstance(c[field], kind):
            out.append(f"{field}: expected {kind.__name__}, found {type(c[field]).__name__}")
        elif not c[field]:
            out.append(f"{field}: required field is empty")
    return out


def check_budgets(c: dict) -> list:
    out, total = [], 0
    for name, texts in section_texts(c).items():
        n = words(*texts)
        total += n
        if n > BUDGETS[name]:
            out.append(f"{name}: {n} words, budget {BUDGETS[name]}, over by {n - BUDGETS[name]}")
    if total > TOTAL:
        out.append(f"total: {total} words, hard limit {TOTAL}, over by {total - TOTAL}")
    return out
