---
name: content-evals
description: >
  Decompose content-requirements into atomic scoring questions, build YAML
  scoring profiles, run TypeSafe content evals (jev-latest), and turn scores
  into concrete content improvements. Use when the user asks to evaluate,
  rate, score, or review writing quality; asks for a scoring profile for a
  content section (use cases, limitations, audience fit, how-it-works
  coverage...); wants broad quality questions decomposed into scored
  dimensions; asks to interpret eval results or fix flagged content; or
  mentions "content evals", "clarity score", or this framework.
---

# Content Evals

Generic engine: questions, levels and weights live in YAML profiles; the
engine executes, validates and aggregates. A new scoring profile is a
configuration task, not a coding task.

Workflow: Decompose → Profile → Run → Interpret → Improve.

## Available scripts

- **`scripts/score.py`** — scores one file against one profile. Self-contained
  (declares its own dependencies). Run it with `uv run`.

## Route 1 — Decompose a high-level question into atomic questions (HITL)

Rule: a broad question hides several judgments behind one answer. Never score
"is this section good?" — split it.

1. Collect the section's outline bullets or the user's high-level question.
2. Map each self-contained judgment to one atomic question. Expand headings:
   "Who can use it and why" = audience naming + why-fit (+ platform fit when
   the outline lists it). Treat numbered constraints as their own atoms
   ("at least 3 use cases" → a concreteness atom).
3. Adapt the count to the context; do not pad. Reference decompositions:
   How it works → 4 (steps, user perspective, inputs/outputs, end result);
   Use cases → 3 (concrete cases, when-to-use, when-not-use); Who can use it
   → 3 (audience, why-fit, platform fit); Limitations → 2 (technical,
   capability); Consistency → 3 (terminology, formatting, language); First
   read → 5 (what-it-is explicit/placed/first-reader,
   flow progression, forward references).
4. Present the two-level outline (criterion → atomic questions) to the user;
   confirm counts and wording BEFORE building the profile. Use ask_user or
   interview when available, else ask directly. Do not silently decide.
5. Give each atom a 4-level scale (0 poor / 1 needs_improvement / 2 good /
   3 excellent). Write levels as situations the reader can observe, never
   degrees: "Meaning is frequently unclear", not "very bad".

If the user supplies a confirmed outline or names the atoms → skip to Route 2.

## Route 2 — Build the profile (YAML only, no code)

1. Catalogue first — enable by name (optional `weight`, default 1.0):
   `clarity`, `structure`, `consistency`, `consistency_terminology`,
   `consistency_formatting`, `consistency_language`, `findability`,
   `audience_fit`,
   `how_it_works_steps`,
   `how_it_works_user_perspective`, `how_it_works_inputs_outputs`,
   `how_it_works_end_result`, `use_cases_concrete`,
   `use_cases_when_to_use`, `use_cases_when_not_use`, `who_audience_specific`,
   `who_why_fit`, `who_platform_fit`, `limitations_technical`,
   `limitations_capability`, `what_it_is_explicit`, `what_it_is_placement`,
   `what_it_is_first_reader`, `flow_progression`, `flow_no_forward_refs`.
2. Anything not in the catalogue goes inline. Template:

```yaml
name: <topic>
description: <one line>
context:
  subject: "the <thing> (owner/repo, context)"   # fills {{subject}}
  platforms: "edition A vs B vs C"                # fills {{platforms}}
criteria:
  <criterion>:        # snake_case, prefixed by topic
    weight: 1.0
    question: "…{{subject}}…"                    # judge exactly one thing
    levels:
      - "Absent / failing situation"
      - "Thin or partial situation"
      - "Solid with minor gaps"
      - "Complete / candid situation"
```

3. Start from a shipped profile in `profiles/` rather than inventing.
   Self-contained profiles (question + levels inline):
   `clarity.yaml`, `structure.yaml`, `findability.yaml`, `consistency.yaml`
   (terminology, formatting, language). Catalogue-referencing profiles
   (enable built-in criteria by name): `how-it-works.yaml`,
   `use-cases.yaml`, `who-can-use.yaml`, `limitations.yaml`,
   `first-read.yaml`.
4. Validate offline before spending an API call:

       uv run - <<'PY'
       import sys; sys.path.insert(0, 'scripts')
       from score import load_config, resolve_criteria
       resolve_criteria(load_config('profiles/<name>.yaml'), None)
       PY

5. All enabled criteria go in ONE TypeSafe request per document; re-runs
   cost one call each.

If it fails: unknown criterion name → the error lists the catalogue; add an
inline definition. Missing context param → add under `context:` or plan a
`--set` override. `weight must be a number >= 0` / `empty config` → YAML
mistake; fix it.

## Route 3 — Run

    uv run scripts/score.py --input <file.md> \
        --config profiles/<profile>.yaml [--set key=value] [--output r.json] [--pretty]

- `uv run` resolves the script's declared dependencies (Python ≥ 3.9 + pyyaml)
  on any machine — the supported path. Plain `python3` works only when that
  interpreter already has pyyaml.
- `--set subject=...` overrides one context param for one run, no new file.
- `--pretty` pretty-prints the terminal; `--output` stays single-line JSON.
- Needs `TYPESAFE_API_KEY` (env, fallback `~/.config/env/.env.keys`).

## Route 4 — Interpret results

Output shape: per-criterion `{score, level, confidence}`, plus weighted
`overall` 0–100.

1. Read per-criterion bands first; overall last. It compensates by design:
   a wrong-audience run scored overall 55 while audience_fit was 0.
2. Trust rules: confidence < 0.5 or a low-confidence flag → read the content
   yourself before acting. High confidence + low score → definite, nameable
   gap. Twos are edit targets. Threes with thin flags are fragile, not
   broken — verify, then move on.
3. Check the setup too: wrong `{{param}}` values in the profile produce
   confident wrong scores. Real case: an `audience_fit` score of 0 flagged a
   wrong config value, not a content flaw. When a top-confidence low score
   makes no sense, re-check the profile's context against the source doc.
4. Adversarial sanity when results surprise: score unrelated content
   (`samples/jargon.md`) with the same profile and expect collapse toward 0.

## Route 5 — Propose improvements

1. For every criterion scored < 3, read its level descriptions: the situation
   the lower level describes IS the missing piece in the content.
2. Rank fixes: one-sentence gaps ("state what is NOT supported — one line
   covers who_platform_fit") before structural ones ("no use-case section
   exists — needs a block, not a sentence").
3. Pair technical-limitation gaps with the workaround line; pair
   when-not-use gaps with the alternative to name.
4. Apply edits, re-run the same profile, report per-criterion movement —
   not just the overall.

## Exceptions

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: yaml` | plain python3 without pyyaml | use `uv run` — deps are declared in the script header |
| pip SSL errors / venv unusable | pyenv/conda python without ssl; venvs add nothing here | `brew install uv`, run via `uv run` |
| `{"error": "TYPESAFE_API_KEY not set"}` | key missing | export env var or add to `~/.config/env/.env.keys` |
| `criterion X: needs question and levels` | typo'd name, no inline definition | use a catalogue name or define question+levels inline |
| `missing context param <p>` | placeholder with no value | add under `context:` or pass `--set` |
| `empty config` / `weight must be a number >= 0` | YAML mistake | fix the profile |
| `no <criterion> answer` | API hiccup | rerun (one request per doc) |
| every doc scores the same band | broken rubric or response | run the samples regression (`samples/*.md` — expect 3 distinct bands) and investigate |

## Pointers

- Criterion theory and level-writing: `references/framework.md`
- Engine design brief (original design; the implemented engine is the
  single-file `scripts/score.py`): `references/framework-structure.md`
- Shipped profiles: `profiles/`
- Smoke test after install: score `samples/clear.md` (expect high), `samples/muddled.md`
  (expect middle), `samples/jargon.md` (expect 0) against `profiles/clarity.yaml`
- Deliberately not built: acceptance thresholds/gates (e.g. "audience_fit must
  be ≥ 2"), probability distributions in output, package layout — see
  `references/framework-structure.md`.
