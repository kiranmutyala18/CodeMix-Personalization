import json

from conftest import needs_hunspell

from codemix_bench import dataset, demo, prompts, scoring
from codemix_bench.cli import DEFAULT_ROOT
from codemix_bench.ratings import load_cells


def test_prompts_share_user_message_within_pair(tmp_path):
    dataset.build(tmp_path)
    counts = prompts.build(tmp_path)
    assert counts["bare"] == 8 and counts["profile-hi-en"] == 16 and counts["profile-te-en"] == 16
    rows = [json.loads(l) for l in (tmp_path / "data/prompts/profile-hi-en.jsonl").read_text(encoding="utf-8").splitlines()]
    by_sid = {}
    for r in rows:
        by_sid.setdefault(r["scenario"], set()).add(r["user"])
    assert all(len(v) == 1 for v in by_sid.values())


def test_lexicon_is_single_source_in_demo(tmp_path):
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "template.html").write_text("A/*LEX_HI*/B/*LEX_TE*/C/*DATA*/", encoding="utf-8")
    dataset.build(tmp_path)
    html = demo.build(tmp_path).read_text(encoding="utf-8")
    assert "/*LEX" not in html and " hai " in html or "hai" in html


@needs_hunspell
def test_committed_results_reproduce():
    out = scoring.run(DEFAULT_ROOT)
    stored = json.loads((DEFAULT_ROOT / "data" / "results.json").read_text(encoding="utf-8"))
    assert out["summary"] == stored["summary"]
    assert len(load_cells(DEFAULT_ROOT)) == 64
