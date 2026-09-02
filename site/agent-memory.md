# Give your tools a memory

Most tools forget you the moment the chat ends. A new hire asks the same question last quarter’s hire already answered. Support repeats itself. The model is fine. It just has nothing to stand on.

This page is a working shape: store what matters, find the right note later, then let the model answer from that — not from a guess.

You do it with three Qwen models on one prepaid key. No second bill. No product-specific SDK to rip out later.

[Get a key](/login) and run the example. Or read the story first.

## Why Qwen, three times

One family, three jobs:

1. **Remember.** [Qwen3-Embedding-8B](/models/qwen3-embedding-8b) turns each note into a vector you keep on your side. You pay once to store it. After that, retrieval is yours.
2. **Pick the right note.** Nearest is not always right. [Qwen3-Reranker-8B](/models/qwen3-reranker-8b) reads the question against the shortlist and scores what actually helps.
3. **Answer.** [Qwen3.8 27B](/models/qwen3-8) writes from those notes. If the notes are not enough, it should say so.

That is the whole product pitch. Embed, choose, answer. Same key as chat.

## What this is not

This is not a hosted memory product. Your notes stay in your database. We never see the file path. We only see the text you send.

It is also not a quality bake-off. We have run the shape against the live endpoint. We have not published a recall score for “your company’s Slack.”

## What you do

**Write a note.** A decision, a price, a name, a policy. Save the text and its vector.

**Ask later.** The question is turned into a vector the same way. You take a shortlist, the reranker ranks it, Qwen 27B answers from the survivors.

**Keep only what is true.** After a turn, you can extract facts worth keeping. Do not write every reply back. That is how a store learns its own mistakes.

## A first run

Export `TIYUVTA_KEY` from the [console](/login). The runnable pack is [avifenesh/tiyuvta-use-cases](https://github.com/avifenesh/tiyuvta-use-cases).

```bash
export TIYUVTA_KEY="YOUR_KEY"
pip install -r requirements.txt
python examples/agent_memory.py "Who runs the hosted endpoint, and how am I billed?"
```

The three calls, if you want them in your own app:

```python
# 1. store a note
client.embeddings.create(
    model="qwen/qwen3-embedding-8b",
    input=["Prepaid credit does not expire. No subscription, no minimum."],
    dimensions=1024,
)

# 2. find notes for a later question — prefix the question, not the stored note
q = client.embeddings.create(
    model="qwen/qwen3-embedding-8b",
    input=["Instruct: Retrieve stored notes that help answer this question\nQuery: How are we billed?"],
    dimensions=1024,
)

# 3. rerank the shortlist (at most 64 notes per call)
# POST https://api.tiyuvta.ai/v1/rerank
# model: qwen/qwen3-reranker-8b

# 4. answer from the notes that survived
client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[{"role": "user", "content": notes + "\n\nQuestion: How are we billed?"}],
)
```

A `429` on embed or rerank means retry in a moment. Nothing was charged for that try. Details live on the [embedding](/models/qwen3-embedding-8b) and [rerank](/models/qwen3-reranker-8b) pages.

## What it costs, roughly

You pay to write a note once (embed, input only). You pay a little to rerank a shortlist (input only). You pay Qwen 27B to answer. One balance. Prices are on [Pricing](/pricing).

## Next

- [Use cases](/use-cases) — the rest of this section
- [Quickstart](/quickstart) if you just want a first request
- Example repo: [avifenesh/tiyuvta-use-cases](https://github.com/avifenesh/tiyuvta-use-cases)
