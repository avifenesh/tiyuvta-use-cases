# tiyuvta use cases

Public examples, MIT. Two endpoints, both OpenAI-compatible, no product SDK:

* **The tiyuvta trial endpoint** (`https://api.tiyuvta.ai/v1`) serves one model, **DeepSeek-V4.1-Flash**: chat and tool calls. It exists so you can put a few dollars in and test your own workload before we talk about deploying on your hardware: [tiyuvta.ai/services/try](https://tiyuvta.ai/services/try/).
* **Your deployment.** Embeddings and rerank are not served on the trial endpoint. They are models tiyuvta deploys on your cards or in your cloud (Qwen3-Embedding-8B and Qwen3-Reranker-8B in these examples), behind the same gateway shapes. Point `RETRIEVAL_BASE_URL` at that deployment; without it the retrieval examples stop with a message instead of calling an endpoint that does not exist. [What a deployment includes](https://tiyuvta.ai/services/).

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

Design notes: [agent memory](./agent-memory.md) · [company knowledge base](./company-knowledge-base.md) · [index](./INDEX.md).
