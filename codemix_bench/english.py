"""English word list from the system hunspell en_US dictionary (affix rules expanded).

Loaded lazily so importing the package never fails; `english_words()` raises a clear
error if hunspell data is missing (install `hunspell-en-us`).
"""
from __future__ import annotations

import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

HUNSPELL_DIR = Path("/usr/share/hunspell")
AMBIG = frozenset("us is to do me so am an as at be by go he if in it my no of on or up we hi ho ye pan tab".split())
LOANWORDS = frozenset("ok okay tbsp tsp ml kg g min mins hrs hr whatsapp upi emoji metro app wifi email gps cafe cafes".split())


def hunspell_available() -> bool:
    return (HUNSPELL_DIR / "en_US.dic").exists() and (HUNSPELL_DIR / "en_US.aff").exists()


def _expand() -> set[str]:
    aff = (HUNSPELL_DIR / "en_US.aff").read_text(encoding="utf-8", errors="ignore").splitlines()
    dic = (HUNSPELL_DIR / "en_US.dic").read_text(encoding="utf-8", errors="ignore").splitlines()[1:]
    rules = defaultdict(list)  # flag -> [(kind, strip, add, cond)]
    cur = None
    for line in aff:
        parts = line.split()
        if len(parts) >= 4 and parts[0] in ("SFX", "PFX") and parts[3].isdigit():
            cur = (parts[0], parts[1])
        elif len(parts) >= 5 and parts[0] in ("SFX", "PFX") and cur and parts[1] == cur[1]:
            strip = "" if parts[2] == "0" else parts[2]
            add = parts[3].split("/")[0]
            add = "" if add == "0" else add
            cond = parts[4]
            rules[parts[1]].append((parts[0], strip, add, cond))
    words = set()
    for entry in dic:
        if not entry.strip():
            continue
        w, _, flags = entry.partition("/")
        w = w.strip()
        words.add(w.lower())
        for fl in flags.strip():
            for kind, strip, add, cond in rules.get(fl, []):
                try:
                    if kind == "SFX":
                        if re.search(cond + "$", w):
                            base = w[: len(w) - len(strip)] if strip else w
                            if not strip or w.endswith(strip):
                                words.add((base + add).lower())
                    else:
                        if re.match(cond, w):
                            base = w[len(strip):] if strip else w
                            if not strip or w.startswith(strip):
                                words.add((add + base).lower())
                except re.error:
                    pass
    return words



@lru_cache(maxsize=1)
def english_words() -> frozenset[str]:
    if not hunspell_available():
        raise RuntimeError("hunspell en_US dictionary not found; install hunspell-en-us")
    return frozenset(_expand() | AMBIG | LOANWORDS)
