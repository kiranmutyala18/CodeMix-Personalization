from collections import Counter

from codemix_bench.seeds import PERSONAS, SCENARIOS


def test_seed_counts():
    assert len(PERSONAS) == 8 and len(SCENARIOS) == 8
    assert Counter(p.lang_pair for p in PERSONAS) == {"hi-en": 4, "te-en": 4}


def test_ids_unique():
    ids = [p.id for p in PERSONAS] + [s.id for s in SCENARIOS]
    assert len(ids) == len(set(ids))


def test_every_scenario_has_seed_message_per_pair():
    for s in SCENARIOS:
        assert set(s.seed_messages) >= {"hi-en", "te-en"}
