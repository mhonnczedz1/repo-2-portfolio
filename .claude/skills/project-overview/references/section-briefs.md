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

## Result callout (`result`)

The most prominent element on the page, labelled `WHAT IS IT?` and set in the accent box directly
under the chips. It answers "why keep reading" in one sentence: the single thing that makes this
project different from the tutorial version of the same idea. A defensible number belongs here
when you have one.

- Weak: "A quiz app that turns PDFs into quizzes." (the tagline already said this)
- Strong: "Fully self-hosted: chunking, embedding, retrieval and generation all run on the host,
  so tenant documents never leave the machine."

The failure mode is restating the tagline or the architecture. If deleting this line would lose
nothing, it is not doing its job. It shares the 60 word header budget with the title, tagline and
chips, so one sentence is the whole allowance.

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

## Gallery captions, 50 words total, 14 words each

Two to five images. Each caption is **one sentence** saying what the screen **proves**, not what
it contains. The 50 word pool is shared, so two images can spend 14 words each while five have to
average ten.

- Weak: "The upload page."
- Strong: "Batch upload of 20 receipts stays responsive; extraction runs off the main thread."

Three or five images render three across, two or four render two across, so an odd count is fine.
Images expand when clicked, which means a dense screen is still readable at grid size, but the
caption has to work without expanding.

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

## Out-of-Scope, 30 words

Bullets. What you deliberately did not build and why that was the right call, then the one real
constraint as a consequence.

- Weak: "Not production ready, needs more work."
- Strong: "No auth on either endpoint, since the target was one trusted deploy. Sessions live in
  memory, so it runs on a single node. Next: an API key per namespace."

Scoping choices read as judgment. A constraint you name yourself reads as knowing your own
system. A vague apology reads as neither. This section is short and does more work per word than
any other.
