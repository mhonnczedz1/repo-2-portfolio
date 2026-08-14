# Project overview generator

One-page overviews of a single project, aimed at hiring managers and interviewers. Each output is
a **self-contained HTML file**: the stylesheet is inlined and every screenshot is base64 encoded,
so it can be emailed or uploaded as is, opens offline, and carries its own "Save as PDF" button
for whoever receives it.

The HTML is the primary artifact and is styled for a laptop or wide screen. `@media print`
compacts it back onto two A4 pages for the PDF.

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

Gallery images go in `overviews/<slug>/images/` as `01-<name>.png`, `02-`, and so on, around
1200px wide. Two to five per overview. A missing file renders as a labelled dashed box, so a
half-finished overview still lays out correctly. Clicking an image expands it, using a CSS
`:target` overlay rather than JavaScript, so the same image is reused and the file does not carry
a second full-size copy of every screenshot.

## How it is put together

You write content, never markup. `content.json` holds prose, chips, decisions, the diagram as
tiers of typed nodes, and image references. `tools/render.py` produces the HTML.

That split is what makes the quality bar enforceable rather than advisory. Because the content is
structured, `tools/check.py` can fail the build on things a prose guide could only recommend:

- a decision with no rejected alternative, since `over` is a required field
- a banned superlative (`robust`, `seamless`, `cutting-edge`, `leverage`, `utilize`)
- a per-section word budget overrun, 700 words hard across the document
- a gallery outside 2 to 5 images, or a caption over 14 words
- more than 12 diagram nodes, or not exactly one `core` node
- an output that would fetch anything at open time

```
assets/          style.css (single source of design) and the document shell
tools/           render.py, check.py. Standard library only, no dependencies
overviews/<slug>/  content.json and that project's images
out/             the shareable artifacts (gitignored)
tests/           107 tests, run with unittest
tests/golden/    the committed design snapshot. v1/ holds the retired version 1 document
```

`tests/test_golden.py` renders the worked example from `content.json` and compares it against the
snapshot in `tests/golden/` token for token. That is what catches a change to the renderer or the
stylesheet that alters the design by accident. When a design change is deliberate, regenerate the
snapshot with `--out` and review the diff; the command is in that file's docstring.

## Exporting to PDF

Open the file and click "Save as PDF", or press Cmd+P. A4, default margins. The stylesheet does
not depend on the "background graphics" setting, so the document reads correctly either way, and
an image left expanded on screen returns to the flow when printed.

**Untick "Headers and footers" in the print dialog.** With it on, the browser prints the file URL
and "Page 1 of 2" in the page margins. Those are drawn by the browser's print engine, not by the
document, so no `@page` rule or `@media print` block can suppress them; the checkbox is the only
control. The in-artifact toolbar says so, which is how a recipient finds out.

Two checks need human eyes: the print preview should land on 2 A4 pages with no orphaned
headings, and gallery images should be legible at grid size.
