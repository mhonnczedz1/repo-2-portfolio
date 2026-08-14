# Project Overview: framework for filling `template.html`

A one-page, print-ready overview of a single project, aimed at hiring managers and
interviewers. It must be skimmable in 30 seconds and hold up when someone asks how it works.

**This is a guide, not a form.** Keep the section order, delete what does not apply, merge
what overlaps. A short honest overview beats a padded complete one.

---

## Invoking it

Paste this to an agent that has access to the project repository:

> Read this repository, then read `GUIDE.md` and fill in a copy of `template.html` named
> `overview-<project-slug>.html`. Follow the word budget per section. Compose the
> architecture diagram from the CSS kit already in the template. Leave the screenshot
> `<img>` paths as they are; I add the images. Any claim the repo does not prove, mark
> `TODO(verify)` with the exact thing I should check. Finish by running
> `python3 check.py overview-<project-slug>.html` and report its output.

---

## Non-negotiables

1. **Under 500 words of prose.** The budget below adds to ~480. Verify before you finish.
2. **No invented numbers.** No metric, adoption figure, or percentage unless the repo,
   a dashboard, or a screenshot proves it. Otherwise: `TODO(verify) — check X`.
3. **Replace every placeholder.** Orange text and `<!-- fill -->` comments must all be gone.
4. **Concrete over superlative.** "Handles ~120 alerts/month" beats "highly scalable".
   Never write robust, seamless, cutting-edge, leverage, or utilize.
5. **One honest limit.** Stating where it breaks is what makes the other claims believable.

## Word budget

Everything that prints counts, including chips, node labels in the diagram, captions and the
footer. An 8-node diagram costs about 35 words on its own, which is why the architecture
prose gets 120 and not 140.

| Section | Words | Must answer |
|---|---|---|
| Title, one-liner, chips, result | 45 | What it is in plain language; role, timeline, status, scale, stack |
| Problem | 50 | Who was hurting, what it cost in time, money, or risk |
| Architecture prose | 120 | Named components, boundaries, data flow, model-driven vs deterministic |
| Diagram labels + Fig 1 caption | 50 | The topology, and what the reader should notice |
| Screenshot captions | 35 | What each screen proves |
| Decisions and tradeoffs | 95 | 3 to 4 bullets, each "chose X over Y because Z" |
| Impact | 65 | Before and after, adoption, who uses it now |
| Limits and next step | 20 | One constraint and the fix |
| Footer | 5 | Name, email, link |

---

## Section briefs

**One-liner.** Plain language, no stack names, no adjectives. What it does and for whom.
- Weak: "A scalable AI-powered document intelligence platform."
- Strong: "A question-answering service that lets separate teams upload their own documents
  and query only their own."

**Problem.** Cost of the old path, in units.
- Weak: "There was no easy way to make quizzes from PDFs."
- Strong: "Reviewers hand-wrote quizzes from 40-page PDFs, about 2 hours per deck, so
  revision material trailed the source docs by a week."

**Architecture.** The section that decides whether this reads as system design or as a
README. Walk one request end to end, naming each component and what it hands to the next.
Then spend a paragraph on the boundary that actually matters: tenant isolation, retry and
failure handling, or the contract between pipeline stages. State explicitly which steps are
model-driven and which are deterministic code.
- Weak: "Built with FastAPI, ChromaDB and Ollama for a fast and scalable RAG pipeline."
- Strong: "`/ingest` accepts a document and a namespace, splits it into overlapping chunks,
  embeds each with a local Ollama model, and writes vectors into a per-namespace ChromaDB
  collection. `/ask` embeds the question, retrieves top-k within one namespace only, and
  passes the chunks to the generation model. Retrieval is deterministic; only the final
  answer is model-generated, so a wrong answer is traceable to the chunks it cited."

**Decisions.** A bullet with no rejected alternative is not a decision, it is a fact. Cut it
or complete it. Prefer decisions a reader might have made differently, including the ones you
would now reverse.

**Impact.** Before and after, adoption, current users. Use the three-tile `.metrics` grid
only if you have two or three hard numbers; delete it otherwise. For a personal project with
no users, the honest line is what it taught you or what it proves you can build, not a
fabricated adoption number.

**Limits.** Pick a real one: single-node only, no auth on an endpoint, cost per call at
volume, model swap untested. Then the one change that would fix it.

---

## Architecture diagram

Compose it from the CSS kit already in `template.html`. No external tools, no dependencies,
prints reliably, and every project ends up looking like part of the same set.

Map the system into 2 to 4 tiers, each a labelled row of nodes read top to bottom. Ingest,
Reason, Deliver is a good default; Client, Service, Data works for request paths.

| Class | Use for |
|---|---|
| `.node` | a component you wrote |
| `.node.core` | the centerpiece, one per diagram |
| `.node.ext` | third-party service or client (dashed) |
| `.node.store` | database, index, cache, bucket (pill) |
| `.node.ai` | a model or LLM step (accent) |

Rules: 3 to 5 nodes per tier, 12 nodes total maximum. `<span class="note">` inside a node
carries the tech or the payload, not a sentence. `<span class="arrow">&rarr;</span>` between
nodes, `<span class="arrow down">&darr;</span>` between tiers. Delete the `.legend` when the
node names speak for themselves.

Fall back to `images/architecture.png` only when the real topology needs crossing lines or a
feedback loop that boxes and arrows cannot express. Keep the `figcaption` either way.

## Screenshots

Two, three at most, in `images/` named `01-<slug>.png`, `02-`, `03-`. Widths around 1200px
crop well into the two-column grid. A missing file prints as a dashed box with the expected
filename, so the layout never collapses.

The caption says what the screen **proves**, not what it contains.
- Weak: "The upload page."
- Strong: "Batch upload of 20 receipts stays responsive; extraction runs off the main thread."

---

## Finishing checklist

- [ ] Every placeholder and `<!-- fill -->` comment replaced or removed
- [ ] Architecture names components and the data between them, no feature list
- [ ] Every decision bullet names the rejected alternative
- [ ] Every number is provable, or marked `TODO(verify)`
- [ ] Diagram is 12 nodes or fewer, one `.core` node
- [ ] Word count under 500

## Verify

```sh
python3 check.py overview-<slug>.html
```

It reports the printed word count (screen-only banner, CSS and fill comments excluded),
placeholders and `TODO(verify)` lines still outstanding, and diagram sanity. Run it on the
filled copy, not on `template.html`. It exits non-zero on a hard failure: over 500 words, fill
comments left in, more than 12 diagram nodes, or not exactly one `.core` node.

Then open the file and check what a script cannot: print preview should be 2 A4 pages with no
orphaned headings, and screenshots should not be squeezed unreadably by the two-column grid.

```sh
open overview-<slug>.html
```

In Chrome: A4, default margins, "Background graphics" on, save as PDF.

## Your part

1. Drop screenshots into `images/` using the names above.
2. Answer any `TODO(verify)` lines, or delete the claim.
3. Print to PDF.
