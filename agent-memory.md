# Agent memory

A loop that actually remembers. You write facts into a local store as vectors, then every later turn retrieves the nearest ones, reranks them, and only then asks the model. One key covers all three calls.

This is not a hosted memory product. The store is yours (SQLite in the snippet). The endpoint supplies the three models a retrieval stack needs: embed, rerank, generate.

## The stack

1. **Write.** Chunk a fact. Embed the chunk as-is. Persist text + vector.
2. **Read.** Embed the user turn with Qwen’s query instruction. Take the nearest *k* by cosine.
3. **Rerank.** Send those *k* to the reranker with a task instruction. Keep the top *n*.
4. **Answer.** Put the surviving memories in the prompt. Generate. Optionally write new facts back.

Same key, same balance. Embed and rerank bill input only. Chat bills in and out.

| Role | Model id | Why this one |
|---|---|---|
| Embed | `qwen/qwen3-embedding-8b` | Native 4096-d, MRL-truncatable. Site default example uses `dimensions: 1024`. |
| Rerank | `qwen/qwen3-reranker-8b` | Scores 0–1, sorted. Pass `instruction` for the task. |
| Generate | `zai/glm-5.3-flash` | Cheapest chat model on the roster, built for agent loops. Swap the id if you want Ornith’s pace or Qwen’s depth. |

Ids are live names from `GET /v1/models`. A wrong id is a `400`, not a guess.

## What you must get right

**Query instruction, documents plain.** On this endpoint you prepend the vendor format to *query* texts yourself. Documents go in as-is. Qwen’s own card says skipping the query instruction typically costs about 1–5% retrieval quality. That figure is Qwen’s, not a measurement from this endpoint.

```
Instruct: Retrieve stored memories that help answer this user message
Query: {the user turn}
```

That is the hosted prefix (`Query:` plus a space). It is not an embeddings JSON field.

**Rerank instruction in the field, not the query string.** Omit `instruction` and the endpoint uses Qwen’s default web-search wording. For memory, set it.

**Batch caps.** Embed accepts at most 32 inputs per request. Rerank accepts at most 64 documents. A retrieve-*k* larger than 64 has to be split; do not send 100 hits in one rerank call.

**A `429` is retryable.** Embed and rerank publish a backoff loop. Retry; nothing is charged for the shed request. That is the client contract on the model pages.

**Reasoning is output.** GLM bills thinking tokens as completion. A small `max_tokens` can return empty `content`. Keep the cap in the thousands. `response_format` works on this model the same as on the rest of the chat roster.

**Do not invent a second vendor.** Point the OpenAI SDK at `https://api.tiyuvta.ai/v1`. Embeddings speak the OpenAI embeddings schema. Rerank is Cohere-shaped, so that one call is raw HTTP.

## First, store a memory

```python
import json, math, os, sqlite3, time, urllib.error, urllib.request
from openai import OpenAI

BASE = "https://api.tiyuvta.ai/v1"
KEY = os.environ["TIYUVTA_KEY"]
DIM = 1024  # native is 4096; 1024 is the size on the model page example

chat = OpenAI(base_url=BASE, api_key=KEY)

def post(path, body):
    for i in range(1, 6):
        req = urllib.request.Request(
            BASE + path,
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 5:
                raise
            time.sleep(i * i)

def embed(texts):
    out = []
    for i in range(0, len(texts), 32):
        data = post("/embeddings", {
            "model": "qwen/qwen3-embedding-8b",
            "input": texts[i:i+32],
            "dimensions": DIM,
        })
        # OpenAI embeddings schema, which this route advertises.
        out.extend(v["embedding"] for v in sorted(data["data"], key=lambda x: x["index"]))
    return out

db = sqlite3.connect("memory.sqlite")
db.execute("create table if not exists mem (id integer primary key, text text, vec text)")

facts = [
    "Avi Fenesh builds memra, a Rust + CUDA inference engine, and operates inference.tiyuvta.ai.",
    "Prepaid credit does not expire. There is no subscription and no minimum.",
    "Embed and rerank share the same API key as chat. They bill input tokens only.",
]
for text, vec in zip(facts, embed(facts)):
    db.execute("insert into mem(text, vec) values (?, ?)", (text, json.dumps(vec)))
db.commit()
```

## Then, recall before you answer

```python
QUERY_INSTRUCT = (
    "Instruct: Retrieve stored memories that help answer this user message\nQuery: "
)
RERANK_INSTRUCT = (
    "Given a user message, retrieve stored memories that are useful for answering it"
)

def cosine(a, b):
    return sum(x*y for x, y in zip(a, b)) / (
        math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b))
    )

def remember(user, k=20, n=5):
    q = embed([QUERY_INSTRUCT + user])[0]
    rows = db.execute("select id, text, vec from mem").fetchall()
    ranked = sorted(
        ((cosine(q, json.loads(vec)), text) for _, text, vec in rows),
        reverse=True,
    )[: min(k, 64)]
    if not ranked:
        return []
    docs = [text for _, text in ranked]
    data = post("/rerank", {
        "model": "qwen/qwen3-reranker-8b",
        "query": user,
        "documents": docs,
        "top_n": n,
        "instruction": RERANK_INSTRUCT,
        "return_documents": True,
    })
    # Request shape is published. Response keys are not on the docs page.
    # The route is advertised Cohere-shaped: results already sorted, top_n trimmed.
    # Print one live body against your key before you depend on a field name.
    results = data.get("results", data)
    if isinstance(results, list) and results and isinstance(results[0], dict):
        out = []
        for hit in results:
            doc = hit.get("document")
            if isinstance(doc, dict) and doc.get("text"):
                out.append(doc["text"])
            elif isinstance(doc, str):
                out.append(doc)
            elif "index" in hit:
                out.append(docs[hit["index"]])
        return out
    return docs[:n]

def answer(user):
    memories = remember(user)
    messages = [
        {
            "role": "system",
            "content": (
                "Answer from the recalled memories. If they are not enough, say so. "
                "Do not invent a memory that was not recalled."
            ),
        },
        {
            "role": "user",
            "content": "Recalled memories:\n- "
            + "\n- ".join(memories or ["(none)"])
            + "\n\nUser: "
            + user,
        },
    ]
    return chat.chat.completions.create(
        model="zai/glm-5.3-flash",
        messages=messages,
        max_tokens=2048,
    ).choices[0].message.content

print(answer("Who runs the hosted inference endpoint, and how am I billed?"))
```

Curl for the two retrieval calls, same bodies:

```bash
export TIYUVTA_KEY="YOUR_KEY"

curl https://api.tiyuvta.ai/v1/embeddings \
  -H "Authorization: Bearer $TIYUVTA_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-embedding-8b",
       "input":["Instruct: Retrieve stored memories that help answer this user message\nQuery: Who runs the hosted endpoint?"],
       "dimensions":1024}'

curl https://api.tiyuvta.ai/v1/rerank \
  -H "Authorization: Bearer $TIYUVTA_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-reranker-8b",
       "query":"Who runs the hosted endpoint?",
       "instruction":"Given a user message, retrieve stored memories that are useful for answering it",
       "documents":["Avi Fenesh builds memra and operates inference.tiyuvta.ai.",
                    "Prepaid credit does not expire."],
       "top_n":3}'
```

## Write-back

After a turn, ask GLM for facts worth keeping as JSON, then embed those strings the same way you stored the seed facts. Skip this if the turn was a lookup. A memory store that writes every reply back will remember its own hallucinations.

```python
extract = chat.chat.completions.create(
    model="zai/glm-5.3-flash",
    messages=[
        {"role": "system", "content": "Return JSON {\"facts\":[...]} of durable user or world facts from this turn. Empty list if none."},
        {"role": "user", "content": f"User: {user}\nAssistant: {reply}"},
    ],
    response_format={"type": "json_object"},
    max_tokens=2048,
)
```

## What this does not prove

The snippet is a shape that matches the published request contract. It is not a quality bake-off against mem0, a vector database, or a graph memory. Cosine over SQLite is the smallest store that runs; replace it with whatever you already operate. We have not published an end-to-end recall@k for this recipe on the hosted endpoint.

Vectors for the same `(input, dimensions)` pair are deterministic (byte-for-byte) on this endpoint, so you can cache them. Rerank scores for the same `(query, document, instruction)` triple are likewise deterministic.

## Next

- Model cards: [Qwen3-Embedding-8B](/models/qwen3-embedding-8b), [Qwen3-Reranker-8B](/models/qwen3-reranker-8b), [GLM-5.3-Flash](/models/glm-5-3-flash), [Qwen3.8 27B](/models/qwen3-8)
- [Company knowledge base](./company-knowledge-base.md) — the same three calls, pointed at a corpus of papers
- [Quickstart](/quickstart) · [Docs](/docs) · [Integrations](/integrations)
