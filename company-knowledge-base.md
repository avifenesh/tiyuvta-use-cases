# Company knowledge base

Drop a folder of papers and notes on disk. The embedder indexes them. The chat model proposes a filing scheme (topic, owner, status) and writes it back as metadata. Later questions retrieve, rerank, and answer with the file path attached. Same three models, same key, as [agent memory](./agent-memory.md).

This does not host your documents. The files stay where you put them. The endpoint never sees a file path, only the text you send.

## The stack

1. **Ingest.** Read `.md`, `.txt`, and text you already extracted from PDFs. Chunk. Embed each chunk as-is. Store path, offsets, text, vector.
2. **File.** Ask the model to assign each *document* (not each chunk) a topic, a one-line summary, and tags. Save that as metadata. Re-run when the corpus grows.
3. **Ask.** Embed the question with a query instruction. Nearest chunks, rerank, generate with citations.

| Role | Model id | Why this one |
|---|---|---|
| Embed | `qwen/qwen3-embedding-8b` | Prompt window 32,768 tokens. Index at `dimensions: 1024` unless you have a reason for 4096. |
| Rerank | `qwen/qwen3-reranker-8b` | Same prompt window per query+document pair. `instruction` names the corpus. |
| Arrange + answer | `qwen/qwen3.8-27b` | The middle of the curve: enough depth to file and cite, still one request. `response_format` is enforced here. Use `stepfun/step-3.7-flash` if the paper is the work, and raise `max_tokens` so reasoning does not eat the JSON. |

PDF bytes are not an API input. Extract text on your side (`pdftotext`, your parser) and ingest the `.txt`. A snippet that pretends the endpoint reads PDFs would be a lie.

## Ingest

Chunk by characters, not tokens. The embedder’s prompt window is 32,768 tokens; staying near 2–4k characters per chunk leaves headroom and gives the reranker a passage, not a book.

```python
from pathlib import Path

CHUNK, OVERLAP = 3000, 400
SUFFIXES = {".md", ".txt", ".markdown"}

def chunks_of(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    i, n = 0, len(text)
    while i < n:
        j = min(n, i + CHUNK)
        yield i, j, text[i:j]
        if j == n:
            break
        i = j - OVERLAP

docs = []
for path in Path("corpus").rglob("*"):
    if path.suffix.lower() in SUFFIXES and path.is_file():
        for start, end, text in chunks_of(path):
            docs.append({"path": str(path), "start": start, "end": end, "text": text})

# embed() from the memory snippet: 32 inputs/request, retry 429
vectors = embed([d["text"] for d in docs])
for d, vec in zip(docs, vectors):
    db.execute(
        "insert into chunk(path, start, end, text, vec) values (?,?,?,?,?)",
        (d["path"], d["start"], d["end"], d["text"], json.dumps(vec)),
    )
db.commit()
```

## Arrange

One pass per file, not per chunk. Send a short extract (filename + first chunk) and ask for JSON. `response_format` is enforced during decoding. Turn reasoning off on Qwen so the token budget is not spent thinking. GLM takes `response_format` too; keep a large `max_tokens` there because reasoning still bills as output.

```python
ARRANGE = """You file a company corpus. Return JSON:
{"topic": "...", "summary": "one line", "tags": ["..."], "doc_type": "paper|note|policy|other"}
Use the filename and extract. Do not invent a title the extract does not support."""

def arrange(path, extract):
    r = chat.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {"role": "system", "content": ARRANGE},
            {"role": "user", "content": f"filename: {path}\n\n{extract[:4000]}"},
        ],
        response_format={"type": "json_object"},
        extra_body={"reasoning_effort": "none"},
        max_tokens=256,
    )
    return json.loads(r.choices[0].message.content)

for path, in db.execute("select distinct path from chunk"):
    first = db.execute(
        "select text from chunk where path=? order by start limit 1", (path,)
    ).fetchone()[0]
    meta = arrange(path, first)
    db.execute(
        "insert or replace into file_meta(path, topic, summary, tags, doc_type) values (?,?,?,?,?)",
        (path, meta["topic"], meta["summary"], json.dumps(meta.get("tags", [])), meta.get("doc_type")),
    )
db.commit()
```

This is a filing suggestion, not a librarian. Review the topics before you build navigation on them.

## Ask, with a path on every claim

```python
ASK_INSTRUCT = (
    "Instruct: Retrieve passages from a company document corpus that answer this question\nQuery: "
)
RERANK_INSTRUCT = (
    "Given a workplace question, retrieve passages from internal papers and notes that answer it"
)

def ask(question, k=20, n=6):
    q = embed([ASK_INSTRUCT + question])[0]
    rows = db.execute("select path, start, text, vec from chunk").fetchall()
    ranked = sorted(
        ((cosine(q, json.loads(vec)), path, start, text) for path, start, text, vec in rows),
        reverse=True,
    )[: min(k, 64)]
    docs = [t for _, _, _, t in ranked]
    data = post("/rerank", {
        "model": "qwen/qwen3-reranker-8b",
        "query": question,
        "documents": docs,
        "top_n": n,
        "instruction": RERANK_INSTRUCT,
        "return_documents": True,
    })
    # Live body: results[].index, relevance_score, document.text. Already sorted.
    hits = []
    for hit in data["results"]:
        path, start, text = ranked[hit["index"]][1:]
        hits.append({"path": path, "start": start, "text": text, "score": hit["relevance_score"]})
    cited = "\n\n".join(
        f"[{i}] {h['path']}@{h['start']}\n{h['text']}" for i, h in enumerate(hits, 1)
    )
    r = chat.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer only from the passages. Cite as [n]. "
                    "If the passages are not enough, say what is missing. "
                    "Do not cite a path you were not given."
                ),
            },
            {"role": "user", "content": cited + "\n\nQuestion: " + question},
        ],
        extra_body={"reasoning_effort": "none"},
        max_tokens=1024,
    )
    return r.choices[0].message.content, hits
```

## What this does not prove

No recall@k, no PDF-parser bake-off, no claim that auto-topics match how your company files. The arrangement step is a model proposing labels from an extract; it will miss a paper whose first page is a cover. Retry a `429` on embed and rerank.

## Next

- [Agent memory](./agent-memory.md) — the same retrieve loop, pointed at facts instead of files
- Model cards: [Qwen3-Embedding-8B](/models/qwen3-embedding-8b), [Qwen3-Reranker-8B](/models/qwen3-reranker-8b), [Qwen3.8 27B](/models/qwen3-8)
- [Quickstart](/quickstart) · [Docs](/docs)
