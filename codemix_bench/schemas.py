"""Data schemas for the code-mixed personalization benchmark.

Two kinds of records:
  Persona  - a synthetic user with a stable code-mixing style and memory facts.
  Scenario - a task situation, written once per language pair, with rubric checks.

Evaluation (later steps) crosses Persona x Scenario, so every response can be
scored on "did the model adapt to *this* person", not just "is it fluent".
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

LangPair = Literal["hi-en", "te-en"]
Script = Literal["roman", "native_mixed"]  # native_mixed = Devanagari/Telugu script + Latin English words
Formality = Literal["casual", "polite", "formal"]

# Rubric dimensions used by human raters and the LLM judge (Step 5-6).
RUBRIC_KEYS = (
    "lang_match",       # replies in the user's language pair, not pure English or pure Hindi/Telugu
    "mix_level_match",  # code-mixing density close to the user's own
    "script_match",     # same script/romanization convention as the user
    "address_form",     # correct pronoun/honorific (aap/tum/tu, meeru/nuvvu)
    "cultural_fit",     # references, food, festivals, norms that fit the user's context
    "preference_use",   # uses stored facts when relevant, ignores them when not
    "helpfulness",      # does the task well, independent of language
)


class Persona(BaseModel):
    id: str
    lang_pair: LangPair
    script: Script
    # 1 = mostly native language with English nouns, 2 = balanced, 3 = mostly English with native glue words
    mix_level: Literal[1, 2, 3]
    formality: Formality
    address_form: str = Field(description="How the user addresses the assistant, e.g. aap / tum / tu / meeru / nuvvu")
    age: int
    occupation: str
    region: str
    verbosity: Literal["terse", "medium", "verbose"]
    uses_emoji: bool
    sample_utterances: list[str] = Field(min_length=2, description="Gold examples of how this person writes")
    memory_facts: list[str] = Field(min_length=1, description="Stable facts an assistant with memory should know")

    @field_validator("sample_utterances")
    @classmethod
    def _non_empty(cls, v: list[str]) -> list[str]:
        if any(not s.strip() for s in v):
            raise ValueError("empty sample utterance")
        return v


class Scenario(BaseModel):
    id: str
    domain: str
    description: str = Field(description="English description of the situation, for annotators")
    # one hand-written opening message per language pair (romanized); Step 2 re-renders per persona
    seed_messages: dict[LangPair, str]
    checks: list[str] = Field(description="Which RUBRIC_KEYS matter most for this scenario")
    needs_memory: bool = False
    notes: str = ""

    @field_validator("checks")
    @classmethod
    def _valid_checks(cls, v: list[str]) -> list[str]:
        bad = [k for k in v if k not in RUBRIC_KEYS]
        if bad:
            raise ValueError(f"unknown rubric keys: {bad}")
        return v

    @field_validator("seed_messages")
    @classmethod
    def _both_pairs(cls, v: dict) -> dict:
        if set(v) != {"hi-en", "te-en"}:
            raise ValueError("seed_messages must cover hi-en and te-en")
        return v
