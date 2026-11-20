# CodeMix-Persona

[![CI](https://github.com/kiranmutyala18/CodeMix-Personalization/actions/workflows/ci.yml/badge.svg)](https://github.com/kiranmutyala18/CodeMix-Personalization/actions/workflows/ci.yml)
**[Live demo](https://huggingface.co/spaces/white0404/codemix-demo)** | Python | pydantic | pytest | GitHub Actions

An evaluation framework for personalized LLM replies to Hindi-English and Telugu-English speakers:
typed data pipeline, rule-based scoring engine, CLI, tests with CI, and a SQLite-backed human-ratings API.
Also see its sibling project, [StaleMem](https://github.com/kiranmutyala18/Stale-memory).

A small benchmark for one question: **do LLMs adapt to *how* a specific Hindi-English or Telugu-English
speaker writes, or do they default to fluent but generic replies?**

Most personalization benchmarks are English and Western-centric. Real users here mix languages
mid-sentence, switch scripts, and expect different honorifics for elders versus friends. This project
measures whether models handle that, and whether memory or persona context helps.

## Architecture
```
codemix_bench/schemas.py    Persona, Scenario models + validators
codemix_bench/seeds.py      hand-written personas and scenarios
codemix_bench/prompts.py    persona x scenario -> bare / profile prompts
codemix_bench/scoring.py    pure metric functions (classify, address, elder, violations) + run()
codemix_bench/english.py    lazy hunspell English word list
codemix_bench/lexicon*.txt  Hindi/Telugu lexicon, single source for scorer AND demo page
codemix_bench/ratings.py    human-rating store (SQLite) + WSGI app: /api/cells, /api/ratings, /api/summary
codemix_bench/cli.py        `codemix <command>`
demo/template.html          static results page; `codemix demo` injects data and lexicon
```
The ratings API is plain WSGI, so it runs with `codemix serve` locally or `gunicorn
"codemix_bench.ratings:make_app(...)"`-style on a host such as Azure App Service. It is not deployed yet.

## Run
```bash
sudo apt-get install hunspell-en-us   # English word list used by the scorer
pip install -e ".[dev]"
pytest -q            # 24 tests: scorer rules, ratings API, pipeline reproduces committed results
codemix validate     # check seeds, write data/*.jsonl
codemix prompts      # write data/prompts/*.jsonl
codemix score        # data/responses/*.jsonl -> data/results.json
codemix demo         # embed everything into demo/index.html (static page)
codemix serve        # ratings API on :8000, SQLite file ratings.db
```

## Demo
`demo/index.html` is a single static file (no server, no API keys). Host it on any static host,
for example a Hugging Face Static Space (live: https://huggingface.co/spaces/white0404/codemix-demo).

## Research questions
1. **RQ1** - How well do LLMs match a user's code-mixing level, script, and address form?
2. **RQ2** - Does giving the model memory facts (diet, family, region) improve cultural and preference fit?
3. **RQ3** - Does an LLM judge agree with native-speaker ratings on these dimensions?

## Design
- **Personas** (`data/personas.jsonl`): 8 hand-written users, 4 per language pair, varying in mix level
  (1-3), script (romanized or native script), register, and address form.
- **Scenarios** (`data/scenarios.jsonl`): 8 everyday tasks, each written for both language pairs.
- **Cells:** persona x scenario = 64 prompts in the seed set. Each response is rated on 7 rubric dimensions
  (see `codemix_bench/schemas.py`).
- **Conditions:** (a) bare prompt, (b) persona description in the system prompt, (c) memory facts only.

## Roadmap
| Step | What | Status |
|------|------|--------|
| 1 | Scaffold, schemas, seed personas and scenarios | done |
| 2 | Prompt set: 8 personas x 4 scenarios, bare vs profile (`codemix prompts`) | done |
| 3 | Native-speaker review pass and fixes | |
| 4 | Response collection: one model family so far, cached in `data/responses/` | partial |
| 5 | Automatic metrics (`codemix score`): pair, script, mix gap, address form, elder honorifics, stored constraints | done |
| 5b | Package, CLI, tests, CI; shared lexicon; ratings API (SQLite, WSGI) | done |
| 6 | LLM-as-judge, rating web UI on top of the API, agreement stats | next |
| 7 | Analysis, plots, write-up | |

## First results (automatic metrics, one model family, 32 prompts per condition)
Telling the model about the user removed wrong address forms (12 of 24 -> 0) and fixed script for native-script
users (0 of 8 -> 8 of 8), but did not fix code-mixing level: replies stay too native-language for English-heavy
users. Small sample, one reply per prompt, no human validation yet; see the Results tab for caveats.

## Caveat
A few ambiguous words (e.g. "ye", "me") are counted as English on purpose; this adds small, known noise to the mix metrics.
Romanized Telugu and Hindi have no standard spelling. All seed text should be reviewed by native
speakers before any result is reported.
