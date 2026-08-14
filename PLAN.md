# Project Overview Template: Spec, Plan, Tracker

## Context

Mhonn needs a reusable framework for one-page, high-level overviews of personal and
internal projects (RAG API, course pipeline, receipt OCR, quiz generator, report
generation). The overviews support job applications and interviews, so they must be
skimmable in 30 seconds by a hiring manager and hold up when an interviewer asks how it
works.

The template is handed to an AI agent that has already read the project repository. The
agent fills it in; Mhonn drops in screenshots and exports to PDF from the browser. The
template must read as a guide, not a rigid form: sections can be trimmed or merged when a
project does not warrant them.

The failure mode to design against: an agent turns the architecture section into a feature
list. The guide forces named components, boundaries, data flow, and a rejected alternative
behind every decision.

## Locked decisions

| Decision | Choice |
|---|---|
| Packaging | Two files: `GUIDE.md` (framework for the agent) + `template.html` (the artifact) |
| Diagrams | CSS diagram kit is primary; `images/architecture.png` slot is the fallback |
| Screenshots | Relative paths under `images/`, supplied by Mhonn, never base64 |
| Output | Self-contained HTML, printed to PDF from Chrome or Safari |
| Page target | A4, 2 pages, print-safe styling (borders and light tints, not filled headers) |
| Primary reader | Hiring managers and interviewers |
| Length | Filled prose under 500 words, hard requirement |

## Spec

### Files

```
project-overview/
  PLAN.md                  this document (spec, plan, tracker)
  GUIDE.md                 what to hand the agent along with the repo
  template.html            the skeleton the agent copies and fills
  check.py                 word count, placeholder and diagram checks
  images/                  screenshots and optional diagram fallback
  overview-<slug>.html     one filled overview per project
```

### Section structure and word budget

The budget is what keeps the result under 500 words without the agent guessing.

| Section | Words | Must answer |
|---|---|---|
| Title + one-liner | 20 | What it is, in language a non-engineer understands |
| At a glance chips | 25 | Role, timeline, stack, status, scale |
| Problem | 50 | Who was hurting, and what it cost in time, money, or risk |
| Architecture prose | 120 | Named components, boundaries, data flow, where the LLM sits versus deterministic code |
| Diagram labels + Fig 1 caption | 50 | The topology, and what the reader should notice |
| Decisions and tradeoffs | 95 | 3 to 4 bullets, each "chose X over Y because Z" |
| Screenshot captions | 35 | What each screen proves, not what it shows |
| Impact and outcome | 65 | Before and after numbers, adoption, who uses it now |
| Limits and next | 20 | One honest constraint and the next step |
| Footer | 5 | Name, email, link |
| **Total** | **485** | |

Corrected during Phase 3: the first budget ignored diagram node labels, which cost about 35
words for an 8-node diagram and pushed the worked example to 516. Architecture prose came down
from 140 to 120 and the diagram now has its own line.

### Quality bar the guide enforces

- Name components and the data moving between them. A feature list is a failed section.
- Every decision states the alternative that was rejected and why.
- No invented numbers. If the repo does not prove a claim, write `TODO(verify)` and move on.
- Concrete over superlative: "handles ~120 alerts/month" beats "highly scalable".
- State where it breaks. One honest limit buys credibility for everything else.
- Delete sections that do not apply rather than padding them.

### CSS diagram kit (composed from HTML, no dependencies)

```html
<div class="arch">
  <div class="tier" data-label="Ingest">
    <div class="node ext">Slack<span class="note">source</span></div>
    <span class="arrow">&rarr;</span>
    <div class="node">Scraper<span class="note">Python</span></div>
  </div>
  <span class="arrow down">&darr;</span>
  <div class="tier" data-label="Reason">
    <div class="node ai">Analyze<span class="note">Claude</span></div>
    <span class="arrow">&rarr;</span>
    <div class="node">Merge + audit<span class="note">deterministic</span></div>
  </div>
</div>
```

Classes: `.arch` wrapper, `.tier` row with a left-hand label, `.node` (own component),
`.node.ext` (third party, dashed), `.node.store` (datastore), `.node.ai` (model or LLM
step), `.arrow` / `.arrow.down` (text glyphs, print-reliable), `.note` (small caption
inside a node), `.legend`.

### Print rules

- `@page { size: A4; margin: 14mm }`, `print-color-adjust: exact` so tints survive.
- `break-inside: avoid` on figures, nodes, and the decisions list.
- Screen-only "how to use" banner hidden with `@media print { display: none }`.
- Missing screenshot renders as a dashed placeholder box showing the expected filename.

## Plan

### Phase 1: the artifact
1. Build `template.html`: print-safe stylesheet, header with chips, all sections in order,
   short `<!-- fill: ... -->` markers, image slots with dashed placeholders.
2. Build the CSS diagram kit inside the same stylesheet, with one commented example.

### Phase 2: the framework
3. Write `GUIDE.md`: how to invoke it, the word budget table, the quality bar, diagram
   selection (CSS kit versus image fallback), screenshot naming, and the fill checklist.

### Phase 3: prove it
4. Fill one worked example from a real project, using only facts already documented in the
   resume, marking anything unverified as `TODO(verify)`.
5. Verify with `check.py` (word count, leftover placeholders, diagram sanity), then a human
   print preview for page count and screenshot legibility.

## Tracker

- [x] Phase 1.1 `template.html` structure and print stylesheet
- [x] Phase 1.2 CSS diagram kit, 5 node types, tier labels, text-glyph arrows, legend
- [x] Phase 2.3 `GUIDE.md` framework, budgets, quality bar, weak-versus-strong examples, checklist
- [x] Phase 3.4 Worked example: Multi-Tenant RAG Documents API, 495 printed words
- [x] Phase 3.5 `check.py` written; word count, placeholder and diagram checks pass on both files
- [ ] Human check: open both files, confirm 2-page print preview and screenshot legibility

## Verification

| Check | How | Result |
|---|---|---|
| Under 500 words | `python3 check.py overview-<slug>.html` | 495 on the worked example |
| No leftover fill comments | same script, hard failure if present | pass |
| Diagram readable | same script: 12 nodes max, exactly one `.core` | 8 nodes, 1 core |
| Every CSS class defined | class names in body checked against the stylesheet | pass after fixing `l-core` |
| Prints to 2 A4 pages | Chrome print preview, no orphaned section headings | needs a human, see below |
| Missing images degrade | no images present yet, both slots show their filename | visible on open |
| Reusable | copy template, fill a second project, styling identical | untested until project 2 |

Headless rendering is blocked in this sandbox (Chrome cannot bind its singleton socket, and a
local HTTP server cannot bind a port), so page count and screenshot legibility are checked by
opening the file. Everything a script can assert is covered by `check.py`.
