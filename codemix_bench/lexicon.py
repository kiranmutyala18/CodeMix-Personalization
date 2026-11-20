"""Hindi/Telugu romanized lexicons (one word per line in lexicon_*.txt, shared with the demo page)."""
from __future__ import annotations

from functools import lru_cache
from importlib import resources

from .english import AMBIG


def _read(name: str) -> frozenset[str]:
    text = resources.files(__package__).joinpath(name).read_text(encoding="utf-8")
    return frozenset(text.split()) - AMBIG


@lru_cache(maxsize=1)
def hindi() -> frozenset[str]:
    return _read("lexicon_hi.txt")


@lru_cache(maxsize=1)
def telugu() -> frozenset[str]:
    return _read("lexicon_te.txt")
