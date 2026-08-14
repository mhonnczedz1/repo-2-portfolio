# Section briefs

How to write each section. Read this before drafting prose. Every weak versus strong pair below
is the same project written two ways; the difference is always concreteness.

**This is a guide, not a form.** Keep the section order, delete what does not apply, merge what
overlaps. A short honest overview beats a padded complete one.

---

## One-liner (`tagline`)

Plain language, no stack names, no adjectives. What it does and for whom. A non-engineer should
understand it.

- Weak: "A scalable AI-powered document intelligence platform."
- Strong: "A question-answering service that lets separate teams upload their own documents and
  query only their own."

## Problem, 75 words

The cost of the old path, in units. Time, money, or risk. Who was actually hurting.

- Weak: "There was no easy way to make quizzes from PDFs."
- Strong: "Reviewers hand-wrote quizzes from 40-page PDFs, about 2 hours per deck, so revision
  material trailed the source docs by a week."

If existing tools did not fit, say why in one clause. "Most retrieval examples assume one corpus
and one user" is a reason. "Nothing else was suitable" is not.

## Architecture, 190 words

The section that decides whether this reads as system design or as a README. It gets the largest
budget for that reason.

Walk one request end to end, naming each component and what it hands to the next. Then spend the
second paragraph on the boundary that actually matters: tenant isolation, retry and failure
handling, or the contract between pipeline stages. State explicitly which steps are model-driven
and which are deterministic code.

- Weak: "Built with FastAPI, ChromaDB and Ollama for a fast and scalable RAG pipeline."
- Strong: "`/ingest` accepts a document and a namespace, splits it into overlapping chunks,
  embeds each with a local Ollama model, and writes vectors into a per-namespace ChromaDB
  collection. `/ask` embeds the question, retrieves top-k within one namespace only, and passes
  the chunks to the generation model. Retrieval is deterministic; only the final answer is
  model-generated, so a wrong answer is traceable to the chunks it cited."

**A feature list here is a failed section.** If the paragraph could be reordered without changing
its meaning, it is a list, not an architecture. Name the pieces and what moves between them.

Where state lives is worth a clause. Where the model is called, and what deterministic code
wraps it, is worth a sentence.

## Decisions and tradeoffs, 140 words, 3 to 4 bullets

Each bullet needs three parts, and the schema enforces it: what you chose, what you rejected, and
why, including the cost you accepted.

A bullet with no rejected alternative is a fact, not a decision. Cut it or complete it.

Prefer decisions a reader might have made differently, including the ones you would now reverse.
Those are the ones an interviewer follows up on, and having an answer ready is the point.

- Weak: "Used ChromaDB for vector storage." (No alternative. This is a fact.)
- Strong: "Namespaces over one collection per tenant: one warm index instead of many, and
  isolation becomes a property of the query rather than a setting someone can get wrong."

Note that the strong version names the cost implicitly by naming what it bought. Where the cost
is real, say it: "accepting slower generation and manual model management".

## Screenshot captions, 50 words

Two, three at most. The caption says what the screen **proves**, not what it contains.

- Weak: "The upload page."
- Strong: "Batch upload of 20 receipts stays responsive; extraction runs off the main thread."

A missing image file renders as a dashed box showing the expected filename, so the layout never
collapses while you are still gathering screenshots.

## Impact, 85 words

Before and after, adoption, current users. Every number must be provable from the repo, a
dashboard, or something you can show on demand. Otherwise write `TODO(verify)` with the exact
thing to check.

Use the `metrics` grid only when you have two or three hard numbers. Omit it otherwise; it
renders nothing and the section still reads.

For a personal project with no users, the honest line is what it taught you or what it proves you
can build. Not a fabricated adoption number. An interviewer who catches one invented figure will
discount every other claim on the page.

## Limits and next step, 30 words

Pick a real one: single-node only, no auth on an endpoint, cost per call at volume, model swap
untested. Then the one change that would fix it.

Stating where it breaks is what makes the other claims believable. This section is short, and it
does more work per word than any other.

---

## The bar, in one list

- Name components and the data between them. A feature list is a failed architecture section.
- Every decision names the rejected alternative and the cost accepted.
- No invented numbers. `TODO(verify)` and move on.
- Concrete over superlative. "Handles ~120 alerts/month" beats "highly scalable".
- One honest limit.
- Delete sections that do not apply rather than padding them.
