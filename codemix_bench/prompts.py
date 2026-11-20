"""Build the prompt set: persona x scenario, under two conditions (bare, profile).

The user message is identical across personas of one language pair, so any difference in a
reply can only come from the persona context.
"""
from __future__ import annotations

import json
from pathlib import Path

SCENARIO_IDS = ["s02_recipe", "s03_message_to_elder", "s05_explain_concept", "s07_weekend_plan"]
BARE_SYSTEM = "You are a helpful assistant. Keep your reply under 120 words."


def profile_system(p):
    ex = "\n".join(f'- "{u}"' for u in p["sample_utterances"])
    facts = "\n".join(f"- {m}" for m in p["memory_facts"])
    return (
        "You are a helpful assistant. Keep your reply under 120 words.\n\n"
        "Context about the user you are talking to:\n"
        f"- {p['age']} years old, {p['occupation']}, from {p['region']}\n"
        f"- They address you as \"{p['address_form']}\"\n"
        f"- Examples of how this user writes:\n{ex}\n"
        f"- Things you know about them:\n{facts}\n"
    )


def build(root: Path) -> dict[str, int]:
    def load(name):
        with open(root / "data" / name, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    personas = {p["id"]: p for p in load("personas.jsonl")}
    scenarios = {s["id"]: s for s in load("scenarios.jsonl")}
    out = {"bare": [], "profile-hi-en": [], "profile-te-en": []}
    for pair in ("hi-en", "te-en"):
        for sid in SCENARIO_IDS:
            out["bare"].append({"id": f"bare|{pair}|{sid}", "condition": "bare", "persona": None, "pair": pair,
                                "scenario": sid, "system": BARE_SYSTEM, "user": scenarios[sid]["seed_messages"][pair]})
    for p in personas.values():
        for sid in SCENARIO_IDS:
            out[f"profile-{p['lang_pair']}"].append({
                "id": f"profile|{p['id']}|{sid}", "condition": "profile", "persona": p["id"],
                "pair": p["lang_pair"], "scenario": sid, "system": profile_system(p),
                "user": scenarios[sid]["seed_messages"][p["lang_pair"]]})
    pdir = root / "data" / "prompts"
    pdir.mkdir(parents=True, exist_ok=True)
    for name, rows in out.items():
        with open(pdir / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {k: len(v) for k, v in out.items()}
