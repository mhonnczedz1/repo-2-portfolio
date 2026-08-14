# Flow diagram

The default architecture diagram: a hand-authored SVG tracing the requests a system actually
serves. Copy `references/architecture-template.svg` to `overviews/<slug>/images/architecture.svg`,
edit the label text, verify the geometry, and declare it in `content.json`:

```json
"diagram": {
  "mode": "image",
  "image": "images/architecture.svg",
  "caption": "One embedder serves both paths, and the owner filter narrows retrieval before generation."
}
```

It inlines as a base64 data URI like any screenshot, so the artifact still fetches nothing. Being
vector, it stays sharp in the PDF, and because it is an `<img>` rather than a CSS background it
prints even with background graphics turned off.

## Why this replaced rows of boxes

The CSS kit places nodes in rows and adds arrows by position: horizontal inside a tier, vertical
between tiers. That expresses exactly one thing, a single linear pipeline.

Give it a system with two request paths sharing one store and it starts lying. Tiers stop being
stages and become groupings, while the arrows keep asserting sequence, so the diagram claims steps
that do not exist and draws the store twice because a node cannot appear in two tiers. A reader
notices this as "hard to understand". The cause is that it is wrong.

Trace the requests instead. Almost every project worth writing up has two: something goes in,
something comes back out.

## Shape

Two lanes, each one real request path, read left to right. Between them the shared datastore,
drawn once, where both paths meet.

```
WRITE PATH   client  ->  POST /ingest  ->  transform  ->  embed  --,
                                                                write
                                    ( Datastore, scoped by owner )
                                                                 read
READ PATH    caller  ->  POST /query   ->  retrieve   ->  generate  '
                 ^------------- streamed response --------------'
```

A component used by both paths is drawn once and reached from both. That is the whole reason this
mode exists, so do not duplicate a node to keep the rows tidy.

## Fixed geometry

Do not improvise these. The template has them; keep them.

| Thing | Value |
|---|---|
| Canvas | 660 x 300 maximum, `viewBox` and `width`/`height` all set |
| Node rows | y 34 to 74, and y 204 to 244. Height 40, radius 6 |
| Node columns | x 24 w92, x 140 w140, x 304 w150, x 478 w134 |
| Inner padding | 12px left. Title baseline +17, note baseline +31 from the box top |
| Shared store | x 300 w190, y 118 h42, radius 21 |
| Lane labels | x 24, baselines 22 and 192 |
| Return edge | y 262, its label baseline 258, centred |
| Arrow gaps | the 24px between columns |

Canvas width matters for print: an `<img>` has no width rule in the stylesheet, so intrinsic px
become print px. 660px lands at about 174mm, inside A4's 182mm text column. A wider canvas
overflows the page.

## Node styling

Same semantics as the kit, so both modes read as one family. Every distinction is a border or a
shape, never a fill alone.

| Class | Use for | Renders as |
|---|---|---|
| `n` | a component you wrote | plain box, grey border |
| `core` | the entry points, one per lane | heavier ink border |
| `ext` | client, browser, anything outside your app | dashed on tint |
| `ai` | a model call | accent border on accent tint |
| `store` | the datastore | pill radius on tint |

Unlike the kit there is no one-`core`-per-diagram rule, because each lane has its own entry point
and they are the same application.

## Labels

- **Title** (`.t`): the step, lowercase unless it is a proper noun or an endpoint. `retrieve`,
  `embed`, `POST /chat`, `ChromaDB`.
- **Note** (`.s`): the tech or the payload, never a sentence. `nomic-embed-text`,
  `375 words, 75 overlap`, `owner-tagged chunks`.
- **Edge label** (`.elab`): what moves, in one or two words. `write`, `owner-filtered`,
  `streamed NDJSON`.
- **Lane label** (`.lane`): the request, uppercase. `UPLOAD A DOCUMENT`, `ASK A QUESTION`.

## No legend

Flow diagrams carry no legend. The node names already say what the shapes say: `browser` is
plainly outside the app, `qwen2.5:0.5b` is plainly a model, `ChromaDB` is plainly a datastore. A
legend explaining that costs 6 words of budget and roughly 20px of height, and the page has
neither to spare.

## Budget

Diagram labels print, so they count. `check.py` reads every `<text>` in the SVG and charges it to
the 55 word diagram line along with the `caption`. The template spends 38, leaving 17 for a
caption. If a diagram cannot fit, cut notes before cutting nodes: a node with no note still says
what the step is.

## Verify the geometry

No renderer runs in this environment, so a label wider than its box is invisible until someone
opens the file. Check it arithmetically instead:

```sh
python3 tools/svgcheck.py overviews/<slug>/images/architecture.svg
```

It prints every label with the slack to its box's right edge, and fails on: a label overflowing
its box, two labels overlapping, a floating label sitting on a box, boxes overlapping, anything
off canvas, and any class whose `font-size` is not declared in the SVG's own `<style>`. `check.py`
runs the same pass, so a broken diagram fails the build.

Under 8px of slack is reported as tight. That is a warning worth heeding, not a failure.

This is geometry only. Whether the diagram reads well is a human call, and the one thing worth
asking the user to look at.

## Caption

The `figcaption` renders as **Fig 1.** plus your text. Say what the reader should notice, in one
clause, not a restatement of the boxes.

- Weak: "Diagram showing the client, API, embedding model and database."
- Strong: "One embedder serves both paths, and the owner filter narrows retrieval before generation."

## When the kit is still right

Fall back to `references/diagram-kit.md` when the system genuinely is one linear pipeline with no
response worth drawing and no shared component: a batch job, an ETL chain, a build pipeline. The
kit is declarative, so there is no geometry to get wrong, and for that shape it is the better tool.

Reach for neither if the topology needs crossing lines or a feedback loop that two lanes cannot
express. Draw it, export a PNG, and point `mode: "image"` at that instead. The geometry check only
applies to SVGs.
