# Project overview generator

One-page, print-ready overviews of a single project, aimed at hiring managers and interviewers.
Each output is a **self-contained HTML file**: the stylesheet is inlined and every screenshot is
base64 encoded, so it can be emailed or uploaded as is, opens offline, and carries its own
"Save as PDF" button for whoever receives it.

## Usage

The work is done by a project-scoped Claude skill. In a session rooted in this repo:

```
> make a project overview for ~/repos/my-project
```

The skill reads the target repo, drafts everything the code can prove, asks once about what it
cannot (adoption numbers, timings, screenshots), writes `overviews/<slug>/content.json`, and
renders. See `.claude/skills/project-overview/SKILL.md`.

By hand, from the repo root:

```sh
python3 tools/render.py <slug>            # content.json -> out/overview-<slug>.html
python3 tools/check.py <slug>             # word budget and quality bar
python3 tools/check.py <slug> --strict    # the gate before sending: no TODO(verify) left
python3 -m unittest discover -s tests -t .
```

Screenshots go in `overviews/<slug>/images/` as `01-<name>.png`, `02-`, `03-`, around 1200px
wide. A missing file renders as a labelled dashed box, so a half-finished overview still lays out
correctly.

## How it is put together

You write content, never markup. `content.json` holds prose, chips, decisions, the diagram as
tiers of typed nodes, and image references. `tools/render.py` produces the HTML.

That split is what makes the quality bar enforceable rather than advisory. Because the content is
structured, `tools/check.py` can fail the build on things a prose guide could only recommend:

- a decision with no rejected alternative, since `over` is a required field
- a banned superlative (`robust`, `seamless`, `cutting-edge`, `leverage`, `utilize`)
- a per-section word budget overrun, 700 words hard across the document
- more than 12 diagram nodes, or not exactly one `core` node
- an output that would fetch anything at open time

```
assets/          style.css (single source of design) and the document shell
tools/           render.py, check.py. Standard library only, no dependencies
overviews/<slug>/  content.json and that project's images
out/             the shareable artifacts (gitignored)
tests/           82 tests, run with unittest
tests/golden/    the version 1 overview, kept as a regression baseline
```

`tests/test_golden.py` renders the version 1 worked example from `content.json` and compares it
against `tests/golden/` token for token. That is what proves a change to the renderer or the
stylesheet has not quietly altered the design.

## Exporting to PDF

Open the file and click "Save as PDF", or press Cmd+P. A4, default margins. The stylesheet does
not depend on the "background graphics" setting, so the document reads correctly either way.

Two checks need human eyes: the print preview should land on 2 A4 pages with no orphaned
headings, and screenshots should be legible at half width in the two-column grid.
