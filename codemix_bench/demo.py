"""Embed data and the shared lexicon into demo/template.html -> demo/index.html (single static file)."""
from __future__ import annotations

import json
from pathlib import Path

from . import lexicon


def build(root: Path) -> Path:
    def load(name):
        with open(root / "data" / name, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    data = {"personas": load("personas.jsonl"), "scenarios": load("scenarios.jsonl")}
    results = root / "data" / "results.json"
    if results.exists():
        data["results"] = json.loads(results.read_text(encoding="utf-8"))
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = (root / "demo" / "template.html").read_text(encoding="utf-8")
    html = html.replace("/*LEX_HI*/", " ".join(sorted(lexicon.hindi()))).replace("/*LEX_TE*/", " ".join(sorted(lexicon.telugu())))
    html = html.replace("/*DATA*/", blob)
    out = root / "demo" / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
