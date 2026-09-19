# tiyuvta use cases

**[tiyuvta](https://tiyuvta.ai)** deploys open-source frontier models on hardware you can afford: the lab reworks the serving engine and the model so a frontier model fits the cards you can buy and runs fast there, then keeps supporting the deployment. These are working shapes for what runs on such a deployment, MIT, no product SDK, every call OpenAI-compatible. [What a deployment includes](https://tiyuvta.ai/services/).

Two endpoints appear in the code:

* **Your deployment.** Embeddings and rerank (Qwen3-Embedding-8B and Qwen3-Reranker-8B in these examples) are models tiyuvta puts on your cards or in your cloud, behind the same gateway shapes. Point `RETRIEVAL_BASE_URL` at that deployment; without it the retrieval examples stop with a message instead of calling an endpoint that does not exist.
* **The proof.** tiyuvta runs one deployment itself on its own engine, DeepSeek-V4.1-Flash at `https://api.tiyuvta.ai/v1` (chat and tool calls), so you can put a few dollars in and test your workload before we talk: [tiyuvta.ai/services/try](https://tiyuvta.ai/services/try/). The chat steps below run there.

```bash
export TIYUVTA_KEY="YOUR_KEY"            # https://tiyuvta.ai/services/try/
pip install -r requirements.txt

# trial endpoint only (DeepSeek-V4.1-Flash)
python examples/work_writing.py rewrite "Please rewrite this email in a calmer tone: ..."
python examples/work_writing.py summary "Decision: annual plan. Maya sends terms Friday."
python examples/work_writing.py brief "Create an SOP for approving supplier invoices above \$5,000."
python examples/support_desk.py "Hi, order A1842 still is not here. Can I get a refund?"

# retrieval: embed + rerank on YOUR deployment, the answer from the trial endpoint
export RETRIEVAL_BASE_URL="https://your-deployment.example/v1"   # RETRIEVAL_KEY if it needs one
python examples/agent_memory.py
python examples/knowledge_base.py ingest
python examples/knowledge_base.py ask "What is our prepaid billing rule?"
```

These are working shapes, not a bake-off. DeepSeek-V4.1-Flash runs every chat step; reasoning is on and bills as output, so keep `max_tokens` in the thousands. `TIYUVTA_BASE_URL`, `TIYUVTA_CHAT_MODEL`, `RETRIEVAL_EMBED_MODEL` and `RETRIEVAL_RERANK_MODEL` override the defaults when your deployment names things differently.

Design notes: [agent memory](./agent-memory.md) · [company knowledge base](./company-knowledge-base.md) · [index](./INDEX.md). The lab: [tiyuvta.ai](https://tiyuvta.ai).
