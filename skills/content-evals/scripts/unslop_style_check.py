#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""Check the unslop skill's Style patterns 17-19 — the mechanically
detectable part of the '### Style' section, deliberately excluded from
profiles/unslop-style.yaml (a regex is the right tool, not a Score
question):

  17  Title case headings (sentence case expected)
  18  Decorative emojis in headings and bullets
  19  Curly quotes (straight quotes expected)

Limitations: pattern 17 uses a heuristic (capitalised non-first words >
half the heading, excluding acronyms and numbers) — proper-noun-heavy
headings can false-positive; judge flagged lines yourself. Emojis are
checked in headings and bullets only, per the skill rule. Dashes are out
of scope: they belong to profiles/unslop-style.yaml (pattern 13).

CLI: uv run scripts/unslop_style_check.py --input file.md
Prints one JSON object: {"file", "counts", "findings": [{pattern, line,
detail, text}]} with findings sorted by line. Exit 0 when clean, 1 when
any finding (lint convention: findings are the answer)."""
import argparse, json, re, sys

CURLY = re.compile(r"[\u2018\u2019\u201A\u201C\u201D\u201E]")
EMOJI = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"   # regional indicators (flags)
    "\U0001F300-\U0001F5FF"   # misc symbols and pictographs
    "\U0001F600-\U0001F64F"   # emoticons
    "\U0001F680-\U0001F6FF"   # transport and maps
    "\U0001F700-\U0001F77F"   # alchemical symbols
    "\U0001F780-\U0001F7FF"   # geometric shapes extended
    "\U0001F800-\U0001F8FF"   # supplemental arrows-c
    "\U0001F900-\U0001F9FF"   # supplemental symbols
    "\U0001FA00-\U0001FAFF"   # symbols and pictographs extended-a
    "\u2600-\u26FF"           # misc symbols (☀-⛿)
    "\u2700-\u27BF"           # dingbats
    "\uFE0F"                  # variation selector
    "]")
HEADING = re.compile(r"^#{1,6}\s+(.*)$")
BULLET = re.compile(r"^\s*[-*+]\s+(.*)$")
SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "in",
               "of", "on", "or", "the", "to", "with"}


def title_case_line(line: str) -> bool:
    """Pattern 17 heuristic: heading looks title-cased. Sentence case keeps
    all but the first word (plus proper nouns) lower-case; title case
    capitalises most content words. Flags when more than half of the words
    after the first are capitalised content words (acronyms, digits and
    small words excluded). Single-word headings and lines of fewer than
    three words can never trip it."""
    words = line.split()
    if len(words) < 3:
        return False
    rest = words[1:]
    caps = [w for w in rest
            if w[:1].isupper() and not w.isupper() and any(c.isalpha() for c in w)
            and w.lower().strip(".,:;!?()[]\"'") not in SMALL_WORDS]
    return len(caps) > len(rest) / 2


def check(text: str):
    findings = []
    for n, line in enumerate(text.splitlines(), start=1):
        for m in CURLY.finditer(line):
            findings.append({"pattern": 19, "line": n,
                             "detail": f"curly quote {m.group()!r} — use straight quotes",
                             "text": line.strip()})
        head = HEADING.match(line)
        stripped = head.group(1) if head else (BULLET.match(line).group(1)
                                               if BULLET.match(line) else None)
        if stripped is not None:
            if EMOJI.search(stripped):
                findings.append({"pattern": 18, "line": n,
                                 "detail": "decorative emoji in heading/bullet — remove",
                                 "text": line.strip()})
            if head and title_case_line(stripped):
                findings.append({"pattern": 17, "line": n,
                                 "detail": "heading looks title-cased — use sentence case",
                                 "text": line.strip()})
    return findings


def main():
    ap = argparse.ArgumentParser(description="unslop Style patterns 17-19 checker")
    ap.add_argument("--input", required=True, help="markdown file to check")
    args = ap.parse_args()
    try:
        text = open(args.input, encoding="utf-8").read()
    except OSError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(2)
    findings = check(text)
    counts = {str(p): sum(1 for f in findings if f["pattern"] == p) for p in (17, 18, 19)}
    print(json.dumps({"file": args.input, "counts": counts, "findings": findings}))
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()