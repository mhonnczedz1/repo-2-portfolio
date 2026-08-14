# Diagram kit, the linear fallback

**Read `references/diagram-flow.md` first.** A hand-authored flow SVG is the default, because most
projects serve two request paths and share a component between them, which rows of boxes cannot
express without asserting steps that do not exist.

Use the kit when the system genuinely is one linear pipeline: a batch job, an ETL chain, a build
pipeline. Nothing comes back to the caller, nothing is shared between paths, and each stage feeds
the next. For that shape the kit is the better tool, because it is declarative and there is no
geometry to get wrong.

The kit is composed from CSS in `assets/style.css`. No external tools, no dependencies, it prints
reliably, and every project using it ends up looking like part of the same set.

You declare it as data in `content.json`. The renderer produces the markup.

## Shape

Map the system into 2 to 4 tiers, each a labelled row of nodes, read top to bottom.
`Ingest, Reason, Deliver` is a good default. `Client, Service, Data` works for request paths.

```json
"diagram": {
  "mode": "kit",
  "legend": ["ext", "ai", "store"],
  "caption": "Both model calls stay local; the namespace narrows retrieval before generation.",
  "tiers": [
    {"label": "Ingest", "nodes": [
      {"text": "Client", "note": "HTTP upload", "type": "ext"},
      {"text": "FastAPI service", "note": "/ingest, /ask", "type": "core"},
      {"text": "Chunker", "note": "overlapping split"}
    ]},
    {"label": "Index", "nodes": [
      {"text": "Embedding model", "note": "Ollama, local", "type": "ai"},
      {"text": "ChromaDB", "note": "one namespace per tenant", "type": "store"}
    ]}
  ]
}
```

Arrows are added automatically: horizontal between nodes in a tier, vertical between tiers.

## Node types

| `type` | Use for | Renders as |
|---|---|---|
| omitted | a component you wrote | plain bordered box |
| `core` | the centerpiece, exactly one per diagram | heavier border |
| `ext` | third-party service or client | dashed border |
| `store` | database, index, cache, bucket | pill shape |
| `ai` | a model or LLM step | accent border and tint |

Every type is distinguished by border or shape, not by fill alone, so the diagram survives being
printed with background graphics turned off.

## Rules

Checked by `tools/check.py`, so these fail the build:

- 12 nodes maximum across the whole diagram
- exactly one `core` node
- 2 to 4 tiers

Warned about, worth heeding:

- 3 to 5 nodes per tier reads best. A tier of one or two looks unfinished; six is a crowd.

## Notes inside a node

`note` carries the tech or the payload, never a sentence.

- Good: `"FastAPI"`, `"/ingest, /ask"`, `"one namespace per tenant"`, `"deterministic checks"`
- Bad: `"This is where the request gets validated before being passed downstream"`

Node labels and notes count against the diagram word budget of 55, alongside tier labels and the
caption. An 8-node diagram costs roughly 35 words on its own, which is why the diagram has its
own budget line rather than being folded into the architecture prose.

## Legend

`legend` is a list of the types the diagram actually uses, in the order you want them shown:
`["ext", "ai", "store"]`. Available keys are `own`, `ext`, `ai`, `store`. Use `true` for all four.

Omit `legend` entirely when the node names speak for themselves. A legend explaining three
obvious boxes wastes vertical space that the page does not have.

## Caption

The `figcaption` renders as **Fig 1.** followed by your text. Say what the reader should notice,
in one clause. Not a restatement of the boxes.

- Weak: "Diagram showing the client, API, embedding model and database."
- Strong: "Both model calls stay local; the namespace narrows retrieval before generation."

## When to fall back to an image

Both other modes are images. For a request flow, which is the default, see
`references/diagram-flow.md`. For a topology that needs crossing lines or a feedback loop that
neither rows nor two lanes can express, draw it and point at the export:

```json
"diagram": {
  "mode": "image",
  "image": "images/architecture.png",
  "caption": "What the reader should notice."
}
```

The file must exist in `overviews/<slug>/`, and `check.py` fails if it does not. It gets
base64 inlined like any screenshot, so the output stays self-contained. Keep the caption either
way.

A hand-drawn PNG is the last resort: it is one more thing to keep in sync, its text escapes the
word budget, and its geometry cannot be checked. An SVG flow diagram is checked on both counts.
