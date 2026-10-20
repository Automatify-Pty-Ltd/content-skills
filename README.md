# content-skills

Agent skills for evaluating content quality — decomposing content requirements
into atomic scoring questions, scoring documents with TypeSafe, and turning
the scores into concrete edits.

## Skills

| Skill | What it does |
|---|---|
| [`skills/content-evals`](skills/content-evals) | Decompose a content requirement into atomic questions, build a YAML scoring profile, score a document, interpret the results, propose improvements |

## Install

The skill lives in `skills/content-evals` (a directory with `SKILL.md`).

**Pi** — point Pi at the folder:

```bash
pi --skill ./skills/content-evals
```

or copy it into your project or user skills directory:

```bash
# project
cp -r skills/content-evals .agents/skills/
# user
cp -r skills/content-evills ~/.agents/skills/
```

**Other clients** — any Agent Skills compatible tool discovers a skill folder
by its `SKILL.md`. Copy or symlink `skills/content-evals` into the location
your client scans (Claude Code: `.claude/skills/`, VS Code Copilot:
`.agents/skills/`).

Run `/reload` (or restart) after copying so the client picks it up.

## Use

The skill works on your content and needs a TypeSafe API key:

```bash
export TYPESAFE_API_KEY=...   # or put it in ~/.config/env/.env.keys
```

Score a document directly:

```bash
cd skills/content-evals
uv run scripts/score.py --input article.md --config profiles/clarity.yaml --pretty
```

`uv run` reads the script's declared dependencies (Python >= 3.9 + pyyaml) and
builds the environment itself, so there is nothing to install.

## Smoke test

```bash
cd skills/content-evals
for f in samples/*.md; do uv run scripts/score.py --input "$f" --config profiles/clarity.yaml; done
```

Expect three distinct bands: `clear.md` high, `muddled.md` middle,
`jargon.md` 0. If they collapse into one band, the rubric or the API response
is broken.

## Layout

```
content-skills/
├── skills/
│   └── content-evals/
│       ├── SKILL.md          # the workflow: decompose → profile → run → interpret → improve
│       ├── scripts/
│       │   └── score.py      # scoring engine (self-contained, PEP 723 deps)
│       ├── references/       # criterion theory, engine design
│       ├── profiles/         # ready-made scoring profiles
│       └── samples/          # smoke-test content
├── LICENSE
└── README.md
```

## License

MIT
