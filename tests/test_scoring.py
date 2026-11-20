from conftest import needs_hunspell

from codemix_bench import scoring as sc

PERSONA_TE = {"id": "te01", "lang_pair": "te-en", "script": "romanized", "mix_level": 2, "address_form": "meeru"}
PERSONA_HI_VEG = {"id": "hi02", "lang_pair": "hi-en", "script": "romanized", "mix_level": 2, "address_form": "aap"}


def test_script_detection():
    assert sc.script_of("नमस्ते") == "deva"
    assert sc.script_of("నమస్తే") == "tel"
    assert sc.script_of("hello") == "latin"


def test_tokens_strip_punctuation_and_digits():
    assert sc.tokens("Hello, world! 123 ... ok?") == ["Hello", "world", "ok"]


def test_level_thresholds():
    assert sc.level_of(0.1) == 1 and sc.level_of(0.5) == 2 and sc.level_of(0.9) == 3


def test_address_detection():
    assert sc.address_status("Aap yeh kijiye", "aap", "hi-en") == "match"
    assert sc.address_status("Tum yeh karo", "aap", "hi-en") == "mismatch"
    assert sc.address_status("Aap kijiye, tum bhi karo", "aap", "hi-en") == "mixed"
    assert sc.address_status("Here is a recipe", "aap", "hi-en") == "unclear"
    assert sc.address_status("మీరు చేయండి", "meeru", "te-en") == "match"


def test_draft_extraction_picks_longest_quote():
    text = 'Sure. "Namaste, aap kaise hain, main theek hoon" and "ok"'
    assert sc.draft_of(text).startswith("Namaste")


@needs_hunspell
def test_classify_mixed_sentence():
    c = sc.classify("Aap yeh recipe try kijiye, bahut easy hai and tasty", "hi-en")
    assert c["labeled"]["hi"] >= 4
    assert 0.2 < c["en_share"] < 0.6


@needs_hunspell
def test_classify_native_script():
    c = sc.classify("आप यह कीजिए", "hi-en")
    assert c["native_script"] == 3 and c["native_share"] == 1.0


@needs_hunspell
def test_veg_violation_and_negation():
    bad = sc.score_reply("Aap chicken curry banaiye.", PERSONA_HI_VEG, "s02_recipe", 0.5)
    ok = sc.score_reply("Aap bina pyaaz ke paneer banaiye, no chicken needed.", PERSONA_HI_VEG, "s02_recipe", 0.5)
    assert bad["violation"] is True and ok["violation"] is False


@needs_hunspell
def test_elder_message_requires_respect():
    good = sc.score_reply('Draft: "Namaste ji, aap kaise hain? Pranam."', PERSONA_HI_VEG, "s03_message_to_elder", 0.5)
    bad = sc.score_reply('Draft: "Hey, tum kaise ho? Kal milte hain bhai."', PERSONA_HI_VEG, "s03_message_to_elder", 0.5)
    assert good["elder_ok"] is True and bad["elder_ok"] is False
    assert "address" not in good


@needs_hunspell
def test_mix_gap_and_bias_signs():
    m = sc.score_reply("This is entirely written in plain english words only here", PERSONA_TE, "s05_explain_concept", 0.4)
    assert m["mix_bias"] > 0 and m["mix_gap"] == abs(m["mix_bias"])


def test_aggregate_counts():
    cell = lambda: {"pair_ok": True, "mix_gap": 0.2, "mix_bias": 0.1, "mix_level_ok": True, "script_ok": True, "address": "match"}
    out = sc.aggregate([{"pair": "hi-en", "bare": cell()}], "bare")
    assert out["cells"] == 1 and out["address_match"] == 1 and out["mix_gap_mean"] == 0.2
