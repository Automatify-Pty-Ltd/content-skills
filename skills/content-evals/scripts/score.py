#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml>=6"]
# ///
"""Content-evals v3: generic engine per skills/content-evals/references/
framework-structure.md. Criterion questions, levels and weights live in YAML
profiles; Python executes, validates and aggregates (design rule: a new
scoring profile is a configuration task, not a coding task). The built-in
CRITERIA catalogue supplies defaults; profiles can also define criteria fully
inline. {{param}} placeholders fill from context. Composite overall: normalize
per-criterion scores, weight, average, scale to 0-100. Library API:
evaluate(content, config, context). CLI: thin layer on top."""
import argparse, json, os, re, sys, time, urllib.request

try:
    import yaml
except ImportError:
    sys.exit('{"error": "missing dependency: pip install pyyaml (or conda install pyyaml) in the active Python environment"}')

KEY_PATH = os.path.expanduser("~/.config/env/.env.keys")
API = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"

LEVEL_NAMES = ["poor", "needs_improvement", "good", "excellent"]

# Built-in criteria catalogue (design: definitions + reusable question
# templates in code; profiles in YAML select, weight, parameterise, and can
# override or add criteria). {{param}} placeholders fill from profile context
# (+ evaluate() overrides); an unfilled placeholder is a config error.
CRITERIA = {
    "clarity": {
        "question": (
            "Rate clarity for the text in `content`. How easily can a first-time "
            "reader with minimal context understand the ideas, explanations and "
            "relationships? Pick the level whose situation matches the text as a whole."),
        "levels": [
            "Meaning is frequently unclear: sentences must be re-read or guessed, and explanations confuse more than they help.",
            "Noticeable clarity problems hinder understanding: vague terms, missing links between ideas, or confusing passages appear in several places.",
            "The content is clear with minor issues: occasional awkward phrasing or a small gap that does not slow the reader much.",
            "The content communicates ideas clearly and precisely: explanations, transitions and terminology are easy to follow throughout.",
        ],
    },
    "structure": {
        "question": (
            "Rate structure for the text in `content`. How well does the "
            "organisation and sequence of sections support a first-time "
            "reader's understanding and progress? Pick the level whose "
            "situation matches the text as a whole."),
        "levels": [
            "Disorganised: sections appear in no discernible order and the reader cannot tell where the text is going.",
            "Noticeable structure problems: key information is buried, sections feel out of place, or the reader must hunt for the thread.",
            "The content is well organised with minor issues: mostly logical order and headings, with an occasional rough transition.",
            "Organisation and sequence strongly support the reader: clear headings, logical progression, each section builds on the previous.",
        ],
    },
    "consistency": {
        "question": (
            "Rate consistency for the text in `content`. How consistently does "
            "it use terminology, naming, formatting and language conventions? "
            "Pick the level whose situation matches the text as a whole."),
        "levels": [
            "Inconsistent throughout: the same concept is called different things in different places, or naming, capitalisation and formatting shift randomly.",
            "Noticeable inconsistencies: several terms or style conventions drift between sections, though the meaning stays recoverable.",
            "Mostly consistent: one concept keeps one name and conventions hold, with a few slips a careful reader will catch.",
            "Fully consistent: every concept keeps one name, and terminology, capitalisation, formatting and tone are uniform across the whole text.",
        ],
    },
    "findability": {
        "question": (
            "Rate findability for the text in `content`. How easily can a "
            "scanning reader locate the information they need? Pick the "
            "level whose situation matches the text as a whole."),
        "levels": [
            "Not scannable: flat walls of text, headings that name nothing, and key facts buried where nobody would look.",
            "Hard to scan: some headings exist but they are vague or inconsistent, and key information sits in unexpected places.",
            "Mostly findable: informative headings and a predictable layout, with occasional key facts buried deeper than expected.",
            "Fully findable: precise, consistent headings; key information front-loaded where a scanning reader would look; easy to navigate on first contact.",
        ],
    },
    "audience_fit": {
        "question": (
            "Rate audience fit for the text in `content`. How well does it "
            "address the needs, knowledge level and goals of this audience: "
            "{{audience}}? Pick the level whose situation matches the text as a whole."),
        "levels": [
            "Wrong audience: assumes knowledge this audience lacks, or explains basics they already know while missing what they actually need.",
            "Partial fit: some sections serve this audience while others are too generic or too specialist for them.",
            "Good fit: the content consistently addresses this audience's needs and knowledge level, with minor mismatches.",
            "Strong fit: the content speaks directly to this audience's role, knowledge level and goals throughout.",
        ],
    },

    "how_it_works_steps": {
        "question": (
            "Does the text explain the steps of how {{subject}} works — what happens, "
            "in what order, including what happens when a step fails or needs retry?"),
        "levels": [
            "Steps are entirely absent: the text never says what happens or in what order.",
            "Steps appear only in passing: some actions are named, but the order, completeness or connections between them stay unclear.",
            "Steps are covered for the main path: the reader can follow what happens in what order, with minor gaps or unexplained hops.",
            "Steps are covered thoroughly: complete and ordered, each step concrete, including failure, retry and cancellation paths.",
        ],
    },
    "how_it_works_user_perspective": {
        "question": (
            "Does the text describe {{subject}} from the user's point of view — who does what, "
            "where in the product, and what they see or receive at each point?"),
        "levels": [
            "No user perspective: the system is described abstractly and the reader cannot place themselves anywhere in the flow.",
            "User actions appear sporadically: some things the user does or sees are mentioned, but the point of view is inconsistent.",
            "The user's viewpoint is covered for the main path: what the user does, opens and observes is mostly clear, with minor gaps.",
            "The text consistently speaks from the user's perspective: who does what, where, what screen or dialog they use, and what feedback they get at each point.",
        ],
    },
    "how_it_works_inputs_outputs": {
        "question": (
            "Does the text state what {{subject}} takes as input and what it produces as output?"),
        "levels": [
            "No inputs or outputs stated: what goes in and what comes out must be guessed.",
            "Inputs or outputs are partially stated: one side is named, the other missing or vague.",
            "Main inputs and outputs are stated: what to provide (credentials, IDs, URLs) and what comes back is mostly clear, with minor gaps.",
            "Inputs and outputs are explicit and complete: every required input, every produced output, and what each is used for.",
        ],
    },
    "how_it_works_end_result": {
        "question": (
            "Does the text state the end result — what exists or what the user can do "
            "after {{subject}} has done its job, and how they can tell it worked?"),
        "levels": [
            "No end result stated: the text never says what exists or what the user can do afterwards.",
            "The end result is implied or generic: some outcome is suggested but not tied to how {{subject}} actually works.",
            "The end result is stated: the reader knows what working state they end up in, with minor gaps.",
            "The end result is concrete: the final working state, what the user can now do, and how they can tell it succeeded.",
        ],
    },
    "use_cases_concrete": {
        "question": (
            "Does the text present concrete use cases for {{subject}} — specific situations "
            "showing who uses it for what?"),
        "levels": [
            "No use cases: the text never shows an actual situation where someone would use {{subject}}.",
            "One or two vague use cases: situations are named but stay generic — who runs into them or what exactly they do with {{subject}} is left open.",
            "Several concrete use cases: at least three identifiable situations, though some remain thin or overlap.",
            "Three or more sharp, distinct use cases: each names the situation, the actor, and what {{subject}} does for them.",
        ],
    },
    "use_cases_when_to_use": {
        "question": (
            "Does the text say when to use {{subject}} — which situations call for it?"),
        "levels": [
            "No when-to-use guidance: nothing helps the reader match their situation to {{subject}}.",
            "Hints only: fit is implied by features, but no explicit statement of when {{subject}} is the right choice.",
            "When-to-use is covered for the main situations, with minor gaps at the edges.",
            "Explicit and complete: which situations call for {{subject}} and why they match.",
        ],
    },
    "use_cases_when_not_use": {
        "question": (
            "Does the text say when NOT to use {{subject}} — which situations call for something else?"),
        "levels": [
            "No when-not-to-use guidance: the text pretends {{subject}} fits every situation.",
            "Barely addressed: a passing cue ('if you need X, this is not for you') without naming what to use instead.",
            "Honest boundaries for the main cases: situations where {{subject}} does not fit are named and mostly point elsewhere.",
            "Explicit and honest: clear not-a-fit situations with alternatives or workarounds named.",
        ],
    },
    "who_audience_specific": {
        "question": (
            "Does the text name who can use {{subject}} — specific roles or personas rather than 'anyone'?"),
        "levels": [
            "No audience named: the text never says who the product is for.",
            "Generic audience only: 'users', 'teams', 'developers' — no specific roles or personas.",
            "Two or more specific roles or personas named, though some stay generic or loosely tied to {{subject}}.",
            "Sharp personas: distinct roles, each tied to what they do and why {{subject}} matters to them.",
        ],
    },
    "who_why_fit": {
        "question": (
            "Does the text explain why each audience can use {{subject}} — what it gives them and "
            "why it fits their situation?"),
        "levels": [
            "No reasons given: audiences are named but the text never says why {{subject}} suits them.",
            "Generic benefits only: 'save time', 'stay in control' — not tied to a specific audience's situation.",
            "A reason is given for the main audiences, though some are thinner than others.",
            "Every named audience gets a specific, concrete reason grounded in what {{subject}} actually does.",
        ],
    },
    "who_platform_fit": {
        "question": (
            "Does the text state which platform, edition or hosting {{subject}} works on "
            "({{platforms}}) — and what is NOT supported?"),
        "levels": [
            "Nothing said: the reader cannot tell which of {{platforms}} {{subject}} runs on.",
            "Vague or partial: one option is mentioned, but the reader cannot rule out the others without guessing.",
            "The applicable options are stated clearly, with minor gaps in what is excluded.",
            "Explicit both ways: the supported options are named AND what is not supported is stated, so nobody guesses wrong.",
        ],
    },
    "limitations_technical": {
        "question": (
            "Does the text cover the technical limitations of {{subject}} — constraints imposed by "
            "how it is built, and what they mean in practice?"),
        "levels": [
            "No technical limitations covered: the text presents {{subject}} as if it had no constraints at all.",
            "One constraint appears in passing without being framed as a limit or explained for the reader.",
            "Main technical limits are stated plainly: the reader knows the boundaries without hunting for them.",
            "Complete and candid: technical constraints are each paired with what they mean in practice and any workaround.",
        ],
    },
    "limitations_capability": {
        "question": (
            "Does the text cover what {{subject}} cannot do — capability limits, features "
            "deliberately out of scope?"),
        "levels": [
            "No capability limits covered: nothing hints at features {{subject}} lacks or leaves out.",
            "Implied only: exclusions must be guessed and nothing is named outright.",
            "The main out-of-scope features are named: the reader knows what they will NOT find inside.",
            "Candid and complete: out-of-scope features are named and positioned (alternative product, roadmap, or deliberate scope), leaving no false expectations.",
        ],
    },
    "what_it_is_explicit": {
        "question": (
            "Does the text explicitly state what {{subject}} IS — a plain definition (not just "
            "what it does or why it matters), understandable with zero prior context?"),
        "levels": [
            "No statement of what the product is: after the opening, the reader still cannot answer 'what is this thing?'.",
            "Implied only: the reader must infer what the product is from the title or feature lists; no plain defining sentence.",
            "A defining statement exists but is thin — it says what the product does without saying what it is, or assumes category knowledge.",
            "A plain, explicit definition: one or two sentences state what the product is in terms a zero-context reader understands, before any features or benefits.",
        ],
    },
    "what_it_is_placement": {
        "question": (
            "Is the definition of {{subject}} placed at the top — before any why, features, or "
            "setup detail — where a first-time reader needs it?"),
        "levels": [
            "No definition exists anywhere in the text, so the first-time reader never gets oriented.",
            "A definition exists but is buried: the reader wades through why, features or detail before learning what the thing is.",
            "The definition appears in the opening area, but some why/what's-included content comes first — persuasion or detail precedes orientation.",
            "Orientation first: the reader learns what the product is before any why, features, or setup detail.",
        ],
    },
    "what_it_is_first_reader": {
        "question": (
            "Is the opening written for a first-time reader — no unexplained jargon, every term "
            "defined at first use?"),
        "levels": [
            "The opening assumes domain knowledge: undefined jargon, product names or category terms from the first lines.",
            "Mostly insider language: some terms are explained but a newcomer stumbles repeatedly in the opening.",
            "Mostly first-time friendly: an occasional term slips in undefined, but a newcomer can broadly follow.",
            "Fully first-time-reader optimized: every term is defined at first use and no prior context is assumed anywhere in the opening.",
        ],
    },
    "flow_progression": {
        "question": (
            "Do the sections appear in an order a first-time reader can follow — each section "
            "answering the question the previous one raised?"),
        "levels": [
            "The order defeats a first-time reader: no discernible narrative; understanding cannot build as the reader goes.",
            "Partial order: some sections follow sensibly, but key jumps leave the reader lost (e.g. detail before the what/why).",
            "A sensible order overall that a first-time reader can follow, with one or two sections feeling misplaced.",
            "Deliberate progression: each section answers the question the previous one raised, building from what it is to how to start.",
        ],
    },
    "flow_no_forward_refs": {
        "question": (
            "Does the text avoid forward references — nothing leans on a feature or concept "
            "before it is introduced in reading order?"),
        "levels": [
            "Pervasive forward references: the text constantly relies on things explained later or never.",
            "Several forward references: the reader is asked to trust or use things not yet introduced.",
            "Minor forward references: one or two spots assume later content, but the reader can still follow.",
            "No forward references: everything is introduced before it is used, in reading order.",
        ],
    },
}


def load_key():
    key = os.environ.get("TYPESAFE_API_KEY")
    if key:
        return key.strip()
    if os.path.exists(KEY_PATH):
        m = re.search(r"TYPESAFE_API_KEY\s*=\s*(\S+)", open(KEY_PATH).read())
        if m:
            return m.group(1).strip().strip('"')
    sys.exit('{"error": "TYPESAFE_API_KEY not set"}')


def fail(msg):
    sys.exit(json.dumps({"error": msg}))


def load_config(path):
    """YAML profile -> dict. `path` may also be an already-loaded dict
    (library calls)."""
    if isinstance(path, dict):
        return path
    try:
        cfg = yaml.safe_load(open(path, encoding="utf-8").read())
    except Exception as e:
        fail(f"bad config {path}: {e}")
    if not cfg:  # empty file or only comments -> explicit error, not silent defaults
        fail(f"empty config {path}")
    return cfg


def resolve_criteria(cfg, overrides):
    """Profile -> (questions, weights, max_levels). Design rule: criterion
    definitions live in YAML; the built-in catalogue only supplies defaults.
    Per criterion: optional inline question/levels (override or replace the
    catalogue entry), optional weight (default 1.0). {{param}} placeholders
    fill from merged context (profile context + evaluate() overrides)."""
    ctx = dict(cfg.get("context") or {})
    ctx.update(overrides or {})
    entries = cfg.get("criteria")
    if not isinstance(entries, dict) or not entries:
        fail("config has no criteria section (mapping of name -> {question, levels, weight})")
    questions, weights, max_levels = {}, {}, {}
    for name, spec in entries.items():
        spec = spec if isinstance(spec, dict) else {}
        base = CRITERIA.get(name) or {}
        question = spec.get("question") or base.get("question")
        levels = spec.get("levels") or base.get("levels")
        if not question or not levels or len(levels) < 2:
            fail(f"criterion {name}: needs question and levels (>=2) inline, "
                 f"or a catalogue name — available: {', '.join(CRITERIA)}")
        weight = spec.get("weight", 1.0)
        if not isinstance(weight, (int, float)) or weight < 0:
            fail(f"criterion {name}: weight must be a number >= 0")

        def fill(text, name=name):
            missing = set(re.findall(r"\{\{(\w+)\}\}", text)) - set(ctx)
            if missing:
                fail(f"criterion {name}: missing context param {sorted(missing)[0]} "
                     f"— add it under context or pass an override")
            return re.sub(r"\{\{(\w+)\}\}", lambda m: str(ctx[m.group(1)]), text)

        questions[name] = {"type": "score",
                           "instructions": {"question": fill(question)},
                           "criteria": [fill(l) for l in levels]}
        weights[name] = weight
        max_levels[name] = len(levels) - 1
    if sum(weights.values()) <= 0:
        fail("total weight must be positive")
    return questions, weights, max_levels


def composite(raw_scores, weights, max_levels):
    """Design §5: normalize each score to 0-1 (s/L), weighted average, ×100."""
    tw = sum(weights[k] for k in raw_scores)
    if tw <= 0:
        fail("total weight must be positive")
    return round(100 * sum(weights[k] * raw_scores[k] / max_levels[k]
                           for k in raw_scores) / tw, 1)


def ask(key, text, questions):
    body = json.dumps({"state": {"content": text},
                       "model": MODEL, "questions": questions}).encode()
    req = urllib.request.Request(API, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + key})
    for attempt in (0, 2, 5):  # same retry ladder as wiki score-typesafe block
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            if getattr(e, "code", None) not in (429, 529) or attempt == 5:
                raise
            time.sleep((attempt + 1) * 2)
    raise RuntimeError("unreachable")


def evaluate(content, config, context=None):
    """Library API (design §3): score `content` (str) against a YAML profile
    (path or dict). `context` overrides profile context per evaluation.
    Returns the result dict; exits with an error JSON on config or answer
    problems."""
    cfg = load_config(config)
    questions, weights, max_levels = resolve_criteria(cfg, context)
    answers = ask(load_key(), content, questions).get("answers", {})
    scores, flags, raw_scores = {}, [], {}
    for name in questions:
        a = answers.get(name)
        if not a or "score" not in a:
            fail(f"no {name} answer")
        raw = a["score"]
        level = max(0, min(int(round(raw)), max_levels[name]))
        raw_scores[name] = raw
        scores[name] = {"score": level, "confidence": a.get("confidence")}
        if max_levels[name] == len(LEVEL_NAMES) - 1:  # 4-level scale -> band name
            scores[name]["level"] = LEVEL_NAMES[level]
        if (a.get("confidence") or 1) < 0.5:
            flags.append(f"low confidence: {name}")
    out = {"scores": scores,
           "overall": composite(raw_scores, weights, max_levels)}
    if cfg.get("name"):
        out["config"] = cfg["name"]
    if flags:
        out["flags"] = flags
    return out


def main():
    ap = argparse.ArgumentParser(description="Score content against a YAML profile via TypeSafe")
    ap.add_argument("--input", "-i", required=True, help="text or markdown file to score")
    ap.add_argument("--config", "-c", required=True, help="YAML profile: criteria (question/levels/weight) + context")
    ap.add_argument("--set", action="append", default=[], metavar="key=value",
                    help="context override, repeatable (e.g. --set audience=...)")
    ap.add_argument("--output", "-o", help="also write the result JSON to this file")
    ap.add_argument("--pretty", action="store_true", help="pretty-print the JSON result in the terminal")
    args = ap.parse_args()
    overrides = {}
    for s in args.set:
        if "=" not in s:
            fail(f'--set expects key=value, got "{s}"')
        k, v = s.split("=", 1)
        overrides[k.strip()] = v.strip()
    result = evaluate(open(args.input, encoding="utf-8").read(),
                      args.config, overrides or None)
    result = {"file": os.path.basename(args.input), **result}
    line = json.dumps(result)
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(line)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(line + "\n")


if __name__ == "__main__":
    main()