# Project overview generator

A Claude Code skill that turns a codebase into a one-page project overview for hiring managers
and interviewers.

The output is a **single self-contained HTML file**. The stylesheet is inlined and every
screenshot is base64 encoded, so it renders from an email attachment, a Downloads folder, or a
laptop in flight mode, with no server, no CDN and no broken images. It carries its own
"Save as PDF" button for whoever receives it.

The HTML is the primary artifact and is styled for a laptop or wide screen. A `@media print`
block compacts it back onto two A4 pages for the PDF.

## See the output first

`samples/overview-example.html` is a rendered overview. Download it and open it, or clone and open
it locally; it needs nothing else to render. Its screenshots are painted placeholders labelled as
samples, not real product captures, and its gallery images expand when clicked.

Regenerate it after any design change with `python3 tools/make_sample.py`. A test fails if it goes
stale.

## Install

Requires Python 3 and Claude Code. No packages, no build step, no virtualenv.

```sh
git clone <this-repo> project-overview
cd project-overview
cp config.example.json config.json            # then fill in your name and email
python3 -m unittest discover -s tests -t .    # 122 tests, should pass immediately
```

The skill is project-scoped: it lives in `.claude/skills/project-overview/` and is discovered by
any Claude Code session started **in this directory**. To confirm, run `/skills` in a session
here and look for `project-overview`.

To use it from elsewhere, copy `.claude/skills/project-overview/` into that project's `.claude/`
directory, along with `assets/` and `tools/`, which the skill shells out to.

## Use

In a Claude Code session rooted in this repo, give it a path:

```
> make a project overview for ~/repos/my-project
```

The target is always passed in. The skill never assumes the current directory is the subject,
because the current directory is this tool.

What happens next:

1. It reads the target repo and drafts every field the code can prove.
2. It asks **once**, in a single batch, about the things a repo cannot contain: which screenshots
   to use, and any numbers it cannot verify. Anything you skip becomes a literal `TODO(verify)`
   marker rather than an invented figure.
3. It writes `overviews/<slug>/content.json`, renders, and validates until clean.
4. It opens the result.

Add your screenshots to `overviews/<slug>/images/` as `01-<name>.png`, `02-`, and so on. Two to
five per overview, around 1200px wide. A missing file renders as a labelled dashed box, so a
half-finished overview still lays out correctly. Then re-render.

### By hand

```sh
python3 tools/render.py <slug>            # content.json -> out/overview-<slug>.html
python3 tools/check.py <slug>             # word budget and quality bar
python3 tools/check.py <slug> --strict    # the gate before sending: no TODO(verify) left
```

### Your name and email

Copy the tracked example and fill it in:

```sh
cp config.example.json config.json
```

```json
{ "footer": { "name": "Your Name", "email": "you@example.com", "link": "" } }
```

`config.json` is gitignored, so your details never enter version control. `tools/render.py` merges
it over whatever `content.json` holds, which is why the tracked files can carry a placeholder while
your own renders carry the real thing.

Empty values never overwrite. That is why `link` is blank above: a repo or demo URL is specific to
each project, so it belongs in that project's `content.json`, and leaving it empty here means it
survives. Set it only if you want one link used everywhere.

The skill writes this file for you the first time it asks, so a later project never asks again. If
it is missing, `render.py` says so and tells you the command.

## What it produces

Nine sections, in this order, with a per-section word budget:

| Section | Words | Must answer |
|---|---|---|
| Title, one-liner, chips, result | 60 | What it is in plain language; timeline, status, scale, stack |
| Identity, printed twice | 14 | Name, email, link, in the byline and the footer |
| Problem | 75 | Who was hurting, what it cost in time, money, or risk |
| Architecture | 190 | Named components, boundaries, data flow, model-driven vs deterministic |
| Diagram | 55 | The topology, and what the reader should notice |
| Gallery | 50 | What each screen proves, one sentence each, 14 words maximum |
| Decisions and tradeoffs | 140 | 3 to 4 bullets, each "chose X over Y because Z" |
| Impact | 85 | Before and after, adoption, who uses it now |
| Out-of-Scope | 30 | What you left out on purpose, then the one real constraint |

699 budgeted against a 700 word hard limit, which lands on two A4 pages with slack. The budget is
rarely the binding constraint; page count is. A short honest overview beats a padded one.

The architecture diagram is declarative: you describe tiers of typed nodes in JSON and CSS draws
the boxes and arrows. No image, no diagramming tool, no external renderer. Fall back to a
screenshot only for a topology needing crossing lines or a feedback loop.

## How it is put together

You write content, never markup. `content.json` holds prose, chips, decisions, the diagram as
tiers of typed nodes, and image references. `tools/render.py` composes the HTML.

That split is what makes the quality bar enforceable rather than advisory. Because the content is
structured, `tools/check.py` fails the build on things a prose style guide could only recommend:

- a decision with no rejected alternative, since `over` is a required field
- a banned superlative: `robust`, `seamless`, `cutting-edge`, `leverage`, `utilize`
- any per-section word budget overrun, or 700 words across the document
- a gallery outside 2 to 5 images, or a caption over 14 words
- more than 12 diagram nodes, or not exactly one `core` node
- an output that would fetch anything at open time

```
.claude/skills/project-overview/   SKILL.md and its references. The instructions Claude follows
config.example.json  the shape of the gitignored config.json. Copy it, fill it in
assets/          style.css (the single source of design) and the document shell
tools/           render.py, check.py, make_sample.py. Standard library only
samples/         a rendered example, so you can see the output without running anything
overviews/<slug>/  your content.json and screenshots. Generated on first run, gitignored
out/             your rendered artifacts. Gitignored
tests/           122 tests, run with unittest
tests/fixtures/  valid.json, the example content the repo tracks and the sample renders from
tests/golden/    the committed design snapshot
```

Your overviews and their screenshots are yours, so `overviews/` and `out/` are gitignored. The
skill creates what it needs. The repo tracks the tool, one example `content.json` under
`tests/fixtures/`, and one rendered sample.

`tests/test_golden.py` renders that fixture and compares it against
`tests/golden/design-snapshot.html` token for token, which catches a change to the renderer or the
stylesheet that alters the design by accident. When the change is deliberate, regenerate it with
`python3 -m tests.test_golden --write` and read the diff.

## Exporting to PDF

Open the file and click "Save as PDF", or press Cmd+P. A4, default margins.

**Untick "Headers and footers" in the print dialog.** With it on, the browser prints the file URL
and "Page 1 of 2" into the margins. Those are drawn by the browser's print engine, not by the
document, so no `@page` rule can suppress them; the checkbox is the only control. The toolbar in
the artifact says so, which is how a recipient finds out.

The stylesheet does not depend on the "background graphics" setting, so every distinction survives
with it off: third-party nodes stay dashed, model steps keep an accent border, datastores keep a
pill shape. An image left expanded on screen returns to the flow when printed.

Two checks need human eyes, since no browser automation is available: the print preview should
land on two A4 pages with no orphaned headings, and gallery images should be legible at grid size.

## Design constraints

Deliberate, and worth knowing before changing anything:

- **Zero dependencies.** Standard library only, in the tools and the tests. `unittest`, not
  `pytest`.
- **The artifact fetches nothing.** No `<link>`, no `@import`, no remote `url()`, no non-`data:`
  `src`. Links to a repo or demo are fine; self-containment means it fetches nothing to *render*
  itself.
- **One line of JavaScript**, the print button's `onclick`. Click-to-expand on gallery images is
  a CSS `:target` overlay that lifts the same `<img>`, so nothing is duplicated and the payload
  does not grow.
- **No em dashes or en dashes** in any output copy.
