"""Validate seed personas/scenarios and write them to data/*.jsonl."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .seeds import PERSONAS, SCENARIOS


def build(root: Path) -> dict:
    ids = [p.id for p in PERSONAS] + [s.id for s in SCENARIOS]
    dupes = [i for i, c in Counter(ids).items() if c > 1]
    if dupes:
        raise ValueError(f"duplicate ids: {dupes}")
    (root / "data").mkdir(exist_ok=True)
    with open(root / "data" / "personas.jsonl", "w", encoding="utf-8") as f:
        for p in PERSONAS:
            f.write(p.model_dump_json() + "\n")
    with open(root / "data" / "scenarios.jsonl", "w", encoding="utf-8") as f:
        for s in SCENARIOS:
            f.write(s.model_dump_json() + "\n")
    return {"personas": len(PERSONAS), "by_pair": dict(Counter(p.lang_pair for p in PERSONAS)),
            "scenarios": len(SCENARIOS), "cells": len(PERSONAS) * len(SCENARIOS)}
