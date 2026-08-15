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
   If it does not exist, ask once for name, email, and repo or demo link, then write it there in
   the shape `config.example.json` shows, so no later project asks again. `tools/render.py` merges
   that file over whatever `content.json` holds, so a committed placeholder never reaches a real
   render. It prints twice, in the header byline and in the footer.

Anything the user skips becomes the literal text `TODO(verify)` in that field, followed by what
to check. It stays visible in the draft, it does not count against the word budget, and
`--strict` refuses to pass while any remain.

Do not interview section by section. One batch, then work.

## Beat three: render and validate, on the first run only

**Everything in this beat applies to the first generation of an overview and to nothing else.** For
any later change, skip straight to Re-runs and updates, which runs no validation at all.

Write `overviews/<slug>/content.json`, then:

```sh
python3 tools/render.py <slug>
python3 tools/check.py <slug>
```

Fix what `check.py` reports and re-render. The loop is cheap because nothing regenerates markup.

A flow diagram is hand-authored, so check its geometry while drafting it. `check.py` runs the same
pass, but this prints the slack on every label, which is what you need to fix one:

```sh
python3 tools/svgcheck.py overviews/<slug>/images/architecture.svg
```

Before telling the user it is ready to send:

```sh
python3 tools/check.py <slug> --strict
```

`--strict` fails while any `TODO(verify)` remains. On this first run, treat a non-zero exit as not
done. This is the only run where that is true.

## Beat four: hand off

```sh
open out/overview-<slug>.html
```

Tell the user three things:

- The file is self-contained. Send it as is; images travel inside it.
- The "Save as PDF" button works for them and for anyone they forward it to. Tell them to untick
  "Headers and footers" in the print dialog, otherwise the browser stamps the file URL and the
  page number into the margins. That is the browser's print engine, not the document, so no
  stylesheet can remove it. The toolbar in the artifact repeats this for recipients.
- Gallery images expand when clicked, and close on the next click. No JavaScript is involved,
  so it works even where inline handlers are blocked.
- Two checks need human eyes, because no browser automation is available here: print preview
  should land on 2 A4 pages with no orphaned headings, and gallery images should be legible at
  grid size.

## Re-runs and updates

**Validation happens once, on the first run, and never again.** Once an overview exists and the user
has read it, they own it. Everything in Beat three is off.

When the user asks to change an existing overview:

1. Edit that project's `overviews/<slug>/content.json`. Never start over; verified numbers and
   answered `TODO(verify)` items are the expensive part and must survive.
2. Run `python3 tools/render.py <slug>`.
3. Stop.

Do not run `check.py`. Do not run `--strict`. Do not re-count the word budget, re-scan for banned
words, re-check counts or diagram geometry, and do not report any of it. Do not touch another
overview. `render.py` still refuses to produce a broken file, and that is the whole safety net an
update gets.

**An explicit instruction outranks every rule in this file.** The rules are a drafting aid for a
document that does not exist yet, not a gate on what the user may ask for. Never edit `tools/` or the
schema to make one document validate: a rule loosened for one overview is loosened for every future
one, and that trade is a separate conversation to have on its own terms.

For example, "omit the Impact section" leaves `impact` empty, which the validator would call a
required field being empty. Do not resolve that, and do not raise it. Re-render and hand it back.

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
    "mode": "image",
    "image": "images/architecture.svg",
    "caption": "What the reader should notice, in one clause. Not a restatement of the boxes."
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
- **The diagram is a request flow.** Copy `references/architecture-template.svg` to
  `overviews/<slug>/images/architecture.svg`, edit the labels, and declare it as `mode: "image"`.
  Two lanes, one per request path, with any shared component drawn once. No legend: the node names
  carry it. `references/diagram-flow.md` has the recipe, and `mode: "kit"` stays available for a
  genuinely linear pipeline.
- **Node `type`** applies to `mode: "kit"` only: `core` (the centerpiece, exactly one per diagram),
  `ext` (third party, dashed), `store` (datastore, pill), `ai` (model step, accent), or omitted for
  something you wrote. A flow SVG carries the same semantics as CSS classes.
- **`note`** carries the tech or the payload, never a sentence.
- **`footer.link`** renders as a clickable anchor only when it starts with `http`. The identity
  prints twice, in the header byline and the footer, and is budgeted for both.

## Word budget

700 printed words hard, 699 budgeted. Everything that prints counts, including chip labels,
diagram labels (every `<text>` inside a flow SVG, the same as kit node labels), captions and the
identity line. Fixed furniture the renderer emits does not
count: section headings, the `Fig 1.` prefix, the `WHAT IS IT?` label. On the first run `check.py` is
the authority; this table is the guide for how to spend it. On an update neither applies, because
nothing is counted again.

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

## Rules that fail the build, on the first run

These are checked when an overview is first generated, and at no other time. Do not fight them
there. On an update they are not evaluated at all: see Re-runs and updates.

- Every decision needs `chose`, `over`, and `because`. A bullet with no rejected alternative is
  a fact, not a decision.
- Banned words, stem-matched, anywhere: `robust`, `seamless`, `cutting-edge`, `leverage`,
  `utilize`. Say what it actually does instead.
- 12 diagram nodes maximum, 2 to 4 tiers, exactly one `core` node, in `mode: "kit"`.
- A flow SVG must hold together geometrically: no label wider than its box, no overlapping labels
  or boxes, nothing off canvas, and a `font-size` declared for every class it uses. Its `<text>`
  labels count against the 55 word diagram budget, the same as kit node labels.
- 5 chips maximum.
- `gallery` holds 2 to 5 images, and no caption exceeds 14 words.
- The rendered file must fetch nothing. The renderer guarantees this; do not add a `<link>`, an
  `@import`, or a remote image.

## References

- `references/section-briefs.md` for how to write each section, with weak versus strong examples.
  Read this before drafting prose.
- `references/diagram-flow.md` for the default diagram: the two-lane request flow, its fixed
  geometry, the label rules, and the geometry check. Read this before drawing.
- `references/architecture-template.svg` is the flow diagram to copy and edit.
- `references/diagram-kit.md` for the linear fallback: node types, tier rules, and the PNG escape
  hatch.
