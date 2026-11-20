"""Rule-based scoring of replies. Pure functions first; `run` does the file I/O.

Language ID (word level):
  1. native script (Devanagari / Telugu)                  -> hi / te
  2. romanized word in the hand-built Hindi/Telugu lexicon -> hi / te
  3. romanized word found in the hunspell English list     -> en
  4. anything else (romanized, unknown)                    -> the prompt's native language
     (mostly romanized Hindi/Telugu vocabulary, but also names; a known source of noise)

Metrics per (persona, scenario, condition) cell:
  pair_ok       reply is in the persona's language pair
  mix_gap       |English share of reply - English share of the persona's own messages|
  mix_level_ok  reply's mix level (1/2/3) equals the persona's mix level
  script_ok     native-script persona -> native script in reply; romanized persona -> none
  address       match / mixed / mismatch / unclear for the persona's address form (not on s03)
  elder_ok      s03 only: the quoted draft uses respectful forms and no casual ones
  violation     s02/s07: a stored constraint is broken
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from . import lexicon
from .english import english_words

ADDR = {
    "aap": re.compile(r"\b(aap|aapko|aapka|aapki|aapke|aapse|kijiye|dijiye|bataiye|rakhiyega|sakte hain|chahein|batayein)\b", re.I),
    "tum": re.compile(r"\b(tum|tumhe|tumhara|tumhari|tumhare|karo|batao|bolo|dekho|daalo|lo)\b", re.I),
    "tu": re.compile(r"\b(tu|tujhe|tera|teri|tere)\b", re.I),
    "meeru": re.compile(r"\b(meeru|mee|meeku|meeda|cheppandi|cheyyandi|vellandi|chudandi|choodandi|veyandi|veyyandi|teesukellandi|chesukondi|chusukondi)\b", re.I),
    "nuvvu": re.compile(r"\b(nuvvu|nee|neeku|cheyyi|cheppu|veyyi|chedam|cheddam|chudam|raa|ra)\b", re.I),
}
PAIR_FORMS = {"hi-en": ["aap", "tum", "tu"], "te-en": ["meeru", "nuvvu"]}
# native-script address/respect patterns (no \b: it is unreliable for Indic scripts)
D, T = r"ऀ-ॿ", r"ఀ-౿"
ADDR_NATIVE = {
    "aap": re.compile(rf"आप|कीजिए|दीजिए|बताइए|रखिएगा|देखिए|चाहें|बता दीजिए"),
    "tum": re.compile(rf"तुम|(?<![{D}])(करो|बताओ|बोलो|देखो|डालो)(?![{D}])"),
    "tu": re.compile(rf"(?<![{D}])(तू|तुझे|तेरा|तेरी)(?![{D}])"),
    "meeru": re.compile(rf"మీరు|మీకు|మీ(?![{T}])|చెప్పండి|చేయండి|చూడండి|వెళ్ళండి|చేసుకోండి|తీసుకెళ్ళండి|వేయండి"),
    "nuvvu": re.compile(rf"నువ్వు|నీకు|(?<![{T}])నీ(?![{T}])|(?<![{T}])(చెప్పు|చేయి|వేయి|చేద్దాం|చూద్దాం)(?![{T}])"),
}
RESPECT = re.compile(r"\b(aap|aapka|aapki|aapke|aapse|aapko|ji|garu|meeru|mee|meeku|namaste|namaskaram|pranam|pranamalu)\b", re.I)
RESPECT_N = re.compile(rf"आप|प्रणाम|नमस्ते|(?<![{D}])जी(?![{D}])|గారు|మీరు|మీకు|మీ(?![{T}])|నమస్కారం|ప్రణామ")
CASUAL = re.compile(r"\b(tum|tumhe|tumhara|tu|tujhe|tera|teri|nuvvu|nee|neeku)\b", re.I)
CASUAL_N = re.compile(rf"तुम|(?<![{D}])(तू|तुझे|तेरा)(?![{D}])|నువ్వు|నీకు|(?<![{T}])నీ(?![{T}])")
# a constraint that the reply explicitly honours ("boat lekunda", "bina pyaaz", "without onion") is not a violation
NEGATED = re.compile(r"\b(bina|without|no|avoid|skip)\s+[\w-]+(\s+(or|and|aur|ya)\s+[\w-]+)?|[\w-]+(\s+(or|and|aur|ya)\s+[\w-]+)?\s+(lekunda|ledu|nahi|nahin|free)\b", re.I)
NONVEG = re.compile(r"\b(chicken|mutton|egg|eggs|anda|fish|machli|prawn|prawns|shrimp|meat|gosht|murgh|kodi|mamsam|chepa|royyalu|lamb|keema|seafood|kebab|kebabs|nihari)\b|మాంసం|చికెన్|గుడ్డు|చేప", re.I)
JAIN = re.compile(r"\b(onion|onions|pyaaz|pyaz|garlic|lehsun|lasun|ullipaya|ullipayalu|vellulli|velulli|velluli)\b", re.I)
BOAT = re.compile(r"\b(boat|boating|boats|ferry|cruise|speedboat|ship)\b", re.I)
VEG_PERSONAS = {"te02", "te03", "hi02", "hi04"}
JAIN_PERSONAS = {"hi02"}
SEASICK_PERSONAS = {"te04"}


def has_letter(s):
    return any(unicodedata.category(c).startswith("L") for c in s)


def script_of(w):
    if re.search(r"[ऀ-ॿ]", w):
        return "deva"
    if re.search(r"[ఀ-౿]", w):
        return "tel"
    return "latin"


def tokens(text):
    out = []
    for raw in re.split(r"[\s\-–—/|]+", text):
        raw = raw.strip(".,;:!?()[]{}\"'“”‘’*_…।॥0123456789•")
        if raw and has_letter(raw):
            out.append(raw)
    return out


def classify(text, pair):
    expected = pair.split("-")[0]
    HI_, TE_, EN_ = lexicon.hindi(), lexicon.telugu(), english_words()
    counts = {"hi": 0, "te": 0, "en": 0}
    labeled = {"hi": 0, "te": 0}
    native_script = 0
    for w in tokens(text):
        s = script_of(w)
        lw = w.lower().replace("'", "")
        if s == "deva":
            counts["hi"] += 1; labeled["hi"] += 1; native_script += 1
        elif s == "tel":
            counts["te"] += 1; labeled["te"] += 1; native_script += 1
        elif lw in HI_ and lw not in TE_:
            counts["hi"] += 1; labeled["hi"] += 1
        elif lw in TE_ and lw not in HI_:
            counts["te"] += 1; labeled["te"] += 1
        elif lw in HI_ and lw in TE_:
            counts[expected] += 1; labeled[expected] += 1
        elif lw in EN_:
            counts["en"] += 1
        else:
            counts[expected] += 1
    n = sum(counts.values())
    native = counts["hi"] + counts["te"]
    return {
        "n": n, "en_share": counts["en"] / n if n else 0.0, "native_share": native / n if n else 0.0,
        "labeled": labeled, "native_script": native_script, "counts": counts,
    }


def level_of(en_share):
    return 1 if en_share < 0.35 else (2 if en_share <= 0.65 else 3)


def address_status(text, expected, pair):
    found = {f for f in PAIR_FORMS[pair] if ADDR[f].search(text) or ADDR_NATIVE[f].search(text)}
    if not found:
        return "unclear"
    if expected in found:
        return "match" if len(found) == 1 else "mixed"
    return "mismatch"


def draft_of(text):
    blocks = re.findall(r"[\"“”]([^\"“”]{15,})[\"“”]", text)
    return max(blocks, key=len) if blocks else text


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def score_reply(text: str, persona: dict, scenario_id: str, target_en: float) -> dict:
    """All automatic metrics for one reply."""
    pair = persona["lang_pair"]
    pid = persona["id"]
    c = classify(text, pair)
    other = "te" if pair == "hi-en" else "hi"
    m = {
        "response": text,
        "en_share": round(c["en_share"], 3),
        "level": level_of(c["en_share"]),
        "pair_ok": c["native_share"] >= 0.10 and c["labeled"][pair.split("-")[0]] >= c["labeled"][other],
        "mix_gap": round(abs(c["en_share"] - target_en), 3),
        "mix_bias": round(c["en_share"] - target_en, 3),
        "mix_level_ok": level_of(c["en_share"]) == persona["mix_level"],
        "script_ok": (c["native_script"] > 0) == (persona["script"] == "native_mixed"),
    }
    if scenario_id != "s03_message_to_elder":
        m["address"] = address_status(text, persona["address_form"], pair)
    else:
        d = draft_of(text)
        m["elder_ok"] = bool(RESPECT.search(d) or RESPECT_N.search(d)) and not (CASUAL.search(d) or CASUAL_N.search(d))
    clean = NEGATED.sub(" ", text)
    if scenario_id == "s02_recipe" and pid in VEG_PERSONAS:
        m["violation"] = bool(NONVEG.search(clean)) or (pid in JAIN_PERSONAS and bool(JAIN.search(clean)))
    if scenario_id == "s07_weekend_plan" and pid in SEASICK_PERSONAS:
        m["violation"] = bool(BOAT.search(clean))
    return m


def aggregate(cells: list[dict], cond: str, pair: str | None = None) -> dict:
    rows = [c[cond] for c in cells if pair is None or c["pair"] == pair]
    n = len(rows)
    addr = [r["address"] for r in rows if "address" in r]
    elder = [r["elder_ok"] for r in rows if "elder_ok" in r]
    viol = [r["violation"] for r in rows if "violation" in r]
    return {
        "cells": n,
        "pair_ok": sum(r["pair_ok"] for r in rows),
        "mix_gap_mean": round(sum(r["mix_gap"] for r in rows) / n, 3),
        "mix_bias_mean": round(sum(r["mix_bias"] for r in rows) / n, 3),
        "mix_level_ok": sum(r["mix_level_ok"] for r in rows),
        "script_ok": sum(r["script_ok"] for r in rows),
        "address_n": len(addr),
        "address_match": addr.count("match"), "address_mixed": addr.count("mixed"),
        "address_mismatch": addr.count("mismatch"), "address_unclear": addr.count("unclear"),
        "elder_n": len(elder), "elder_ok": sum(elder),
        "violation_n": len(viol), "violations": sum(viol),
    }


def run(root: Path) -> dict:
    personas = {p["id"]: p for p in load_jsonl(root / "data" / "personas.jsonl")}
    prompts, responses = {}, {}
    for name in ("bare", "profile-hi-en", "profile-te-en"):
        for r in load_jsonl(root / "data" / "prompts" / f"{name}.jsonl"):
            prompts[r["id"]] = r
        for r in load_jsonl(root / "data" / "responses" / f"{name}.jsonl"):
            responses[r["id"]] = r["response"]
    if set(prompts) != set(responses):
        raise ValueError("prompt/response id mismatch")

    targets = {pid: classify(" ".join(p["sample_utterances"]), p["lang_pair"])["en_share"] for pid, p in personas.items()}
    scenarios = sorted({v["scenario"] for v in prompts.values()})
    cells = []
    for pid, p in personas.items():
        pair = p["lang_pair"]
        for sid in scenarios:
            entry = {"persona": pid, "scenario": sid, "pair": pair,
                     "user": prompts[f"profile|{pid}|{sid}"]["user"], "target_en": round(targets[pid], 3)}
            entry["bare"] = score_reply(responses[f"bare|{pair}|{sid}"], p, sid, targets[pid])
            entry["profile"] = score_reply(responses[f"profile|{pid}|{sid}"], p, sid, targets[pid])
            cells.append(entry)
    summary = {cond: {"all": aggregate(cells, cond), "hi-en": aggregate(cells, cond, "hi-en"),
                      "te-en": aggregate(cells, cond, "te-en")} for cond in ("bare", "profile")}
    out = {"summary": summary, "cells": cells, "scenarios": scenarios,
           "english_dictionary_size": len(english_words())}
    (root / "data" / "results.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out
