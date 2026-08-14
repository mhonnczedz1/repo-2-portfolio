# Diagram kit

The architecture diagram is composed from CSS in `assets/style.css`. No external tools, no
dependencies, it prints reliably, and every project ends up looking like part of the same set.

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

Use `"mode": "image"` only when the real topology needs crossing lines or a feedback loop that
boxes and arrows in rows cannot express:

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

Prefer the kit. A hand-drawn diagram is one more thing to keep in sync, and it will not match the
other overviews in the set.
