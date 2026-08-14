---
name: project-overview
description: Use when the user wants a one-page project overview, project one-pager, portfolio write-up, case study, or shareable summary of a codebase for hiring managers or interviewers. Produces a self-contained HTML file that exports itself to PDF. Triggers on "project overview", "one-pager", "write up this project", "portfolio page for this repo", "summarise this project for a hiring manager".
---

# Project Overview

Produce a one-page overview of a single project, aimed at hiring managers and interviewers. It
must be skimmable in 30 seconds and hold up when someone asks how it works.

The output is one HTML file that fetches nothing: the stylesheet is inlined and every screenshot
is base64 encoded. It can be emailed, uploaded, or opened offline, and it carries its own
"Save as PDF" button, so whoever receives it can print it without instructions.

You author content. A Python renderer produces the markup. Never hand-write HTML.

## Inputs

**A target project path.** This skill lives in the overview repo, not in the project being
documented, so the current directory is almost never the subject. If the user did not give a
path, ask for one before doing anything else.

Run every command from the overview repo root.

## Beat one: read, then separate provable from unprovable

Read the target repo. Draft every field you can support with evidence you actually saw.

Then build one list of what the repo cannot prove. This is the crux of the whole skill:

- adoption numbers, user counts, "used by N teams"
- before-and-after timings, cost savings, volume processed
- timeline, and the user's role if it was not a solo build
- current status in production versus prototype

For each item, name the exact thing the user should check, not just the gap. "Check the ingest
count in the ChromaDB collection" beats "how many documents?".

**Never invent a number.** A fabricated metric is the one failure that destroys the document's
credibility, and it is the thing an interviewer will probe first.

## Beat two: ask once, in a batch

Present that single list, plus the two things a repo never contains:

1. **Gallery images.** Which screens to use, 2 to 5. Copy them into
   `overviews/<slug>/images/` as `01-<name>.png`, `02-`, and so on. Around 1200px wide crops well
   into the grid. Each caption is **one sentence, 14 words maximum**, saying what the screen
   *proves*, not what it contains. The 50 word section pool is shared, so five images have to
   average ten words each.
2. **Footer identity.** Read `config.json` at the repo root if it exists and use it silently.
   If it does not exist, ask once for name, email, and repo or demo link, then write it there so
   no later project asks again. It renders twice, in the header byline and in the footer.

Anything the user skips becomes the literal text `TODO(verify)` in that field, followed by what
to check. It stays visible in the draft, it does not count against the word budget, and
`--strict` refuses to pass while any remain.

Do not interview section by section. One batch, then work.

## Beat three: render and validate

Write `overviews/<slug>/content.json`, then:

```sh
python3 tools/render.py <slug>
python3 tools/check.py <slug>
```

Fix what `check.py` reports and re-render. The loop is cheap because nothing regenerates markup.

Before telling the user it is ready to send:

```sh
python3 tools/check.py <slug> --strict
```

`--strict` fails while any `TODO(verify)` remains. Treat a non-zero exit as not done.

## Beat four: hand off

```sh
open out/overview-<slug>.html
```

Tell the user three things:

- The file is self-contained. Send it as is; images travel inside it.
- The "Save as PDF" button works for them and for anyone they forward it to.
- Gallery images expand when clicked, and close on the next click. No JavaScript is involved,
  so it works even where inline handlers are blocked.
- Two checks need human eyes, because no browser automation is available here: print preview
  should land on 2 A4 pages with no orphaned headings, and gallery images should be legible at
  grid size.

## Re-runs

If `overviews/<slug>/content.json` already exists, edit it. Never start over. Verified numbers
and answered `TODO(verify)` items are the expensive part and must survive.

## The content.json contract

Content only. No markup. Backticks become inline `<code>`, which is the only formatting.

```json
{
  "slug": "receipt-ocr",
  "title": "Receipt OCR Pipeline",
  "tagline": "Plain language, no stack names, no adjectives. What it does and for whom.",
  "chips": [
    {"label": "Scope", "value": "pipeline, API, deploy"},
    {"label": "Timeline", "value": "Mar 2026"},
    {"label": "Status", "value": "in production"},
    {"label": "Scale", "value": "TODO(verify) receipts processed"},
    {"label": "Stack", "value": "Python, Tesseract, SQLite"}
  ],
  "result": "The single strongest verified outcome, one sentence, with a number you can defend.",
  "problem": ["Who was hurting, and what the old path cost in time, money, or risk."],
  "architecture": [
    "Walk one request end to end. `/upload` takes a file, names each component and what it hands to the next.",
    "Then the boundary that actually matters: isolation, retries, or the contract between stages. Say which steps are model-driven and which are deterministic code."
  ],
  "diagram": {
    "mode": "kit",
    "legend": ["ext", "ai", "store"],
    "caption": "What the reader should notice, in one clause. Not a restatement of the boxes.",
    "tiers": [
      {"label": "Ingest", "nodes": [
        {"text": "Client", "note": "HTTP upload", "type": "ext"},
        {"text": "API", "note": "FastAPI", "type": "core"},
        {"text": "Preprocess", "note": "deskew, crop"}
      ]},
      {"label": "Extract", "nodes": [
        {"text": "OCR", "note": "Tesseract", "type": "ai"},
        {"text": "Validate", "note": "deterministic checks"},
        {"text": "Store", "note": "SQLite", "type": "store"}
      ]}
    ]
  },
  "gallery": [
    {"src": "images/01-upload.png", "caption": "What this screen proves, in one sentence."},
    {"src": "images/02-review.png", "caption": "What the second screen proves."}
  ],
  "decisions": [
    {"chose": "Tesseract locally", "over": "a hosted vision API",
     "because": "no per-page cost and receipts never leave the host, accepting worse accuracy on crumpled scans."}
  ],
  "metrics": [
    {"value": "4 min", "label": "per batch, was 2 hours"},
    {"value": "3", "label": "teams using it"}
  ],
  "impact": ["Before and after in concrete terms, who uses it now, and what it replaced."],
  "out_of_scope": [
    "What you deliberately did not build, and why that was the right call.",
    "Next: the one change that would lift the real constraint."
  ],
  "footer": {"name": "", "email": "", "link": "https://github.com/..."}
}
```

Field notes:

- **Optional sections vanish.** Omit `metrics` and the tile grid does not render. Omit `gallery`
  and the section disappears. Delete what does not apply rather than padding it.
- **`gallery` takes 2 to 5 entries**, never 1. Three or five images render three across, two or
  four render two across. Each image expands on click, with no JavaScript.
- **`metrics` takes 0, 2, or 3 entries. Never 1**, which reads as a stray number.
- **`chips` take 5 at most.** Use `Role` only when ownership is not obvious, such as a team or
  internal project, where "one of four, owned retrieval" tells the reader something. On a solo
  project spend the slot on `Scope` instead, since a portfolio one-pager already implies you
  built it.
- **Node `type`** is `core` (the centerpiece, exactly one per diagram), `ext` (third party,
  dashed), `store` (datastore, pill), `ai` (model step, accent), or omitted for something you
  wrote.
- **`note`** carries the tech or the payload, never a sentence.
- **`footer.link`** renders as a clickable anchor only when it starts with `http`. The identity
  prints twice, in the header byline and the footer, and is budgeted for both.

## Word budget

700 printed words hard, 699 budgeted. Everything that prints counts, including chip labels,
diagram node labels, captions and the identity line. Fixed furniture the renderer emits does not
count: section headings, the `Fig 1.` prefix, the `WHAT IS IT?` label. `check.py` is the
authority; this table is the guide for how to spend it.

| Section | Words | Must answer |
|---|---|---|
| Title, one-liner, chips, result | 60 | What it is in plain language; timeline, status, scale, stack |
| Identity, printed twice | 14 | Name, email, link, in the byline and the footer |
| Problem | 75 | Who was hurting, what it cost in time, money, or risk |
| Architecture prose | 190 | Named components, boundaries, data flow, model-driven vs deterministic |
| Diagram labels + Fig 1 caption | 55 | The topology, and what the reader should notice |
| Gallery captions | 50 | What each screen proves, one sentence each, 14 words maximum |
| Decisions and tradeoffs | 140 | 3 to 4 bullets, each "chose X over Y because Z" |
| Impact | 85 | Before and after, adoption, who uses it now |
| Out-of-Scope | 30 | What you left out on purpose, then the one real constraint |

The budget is rarely the binding constraint. The worked example lands well under 700 and reads as
complete. Page count is the real limit, so a short honest overview beats a padded one.

## Rules that fail the build

Do not fight these, they are checked:

- Every decision needs `chose`, `over`, and `because`. A bullet with no rejected alternative is
  a fact, not a decision.
- Banned words, stem-matched, anywhere: `robust`, `seamless`, `cutting-edge`, `leverage`,
  `utilize`. Say what it actually does instead.
- 12 diagram nodes maximum, 2 to 4 tiers, exactly one `core` node.
- 5 chips maximum.
- `gallery` holds 2 to 5 images, and no caption exceeds 14 words.
- The rendered file must fetch nothing. The renderer guarantees this; do not add a `<link>`, an
  `@import`, or a remote image.

## References

- `references/section-briefs.md` for how to write each section, with weak versus strong examples.
  Read this before drafting prose.
- `references/diagram-kit.md` for node types, tier rules, and when to fall back to an image.
