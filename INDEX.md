# Use cases

Working shapes for two things tiyuvta does: the model it serves itself as a proof you can test your workload against (DeepSeek-V4.1-Flash, the trial endpoint at api.tiyuvta.ai), and the models it deploys on your own hardware (here: an embedder and a reranker for retrieval). No product SDK; every call is the OpenAI-compatible shape.

| | Runs on | |
|---|---|---|
| [Write the work](./examples/work_writing.py) | trial endpoint | Rewrite an email, turn notes into decisions and actions, or make a rough brief into structured JSON. |
| [Support desk](./examples/support_desk.py) | trial endpoint | Tool calls: look up an order and the policy, answer or escalate. |
| [Agent memory](./agent-memory.md) | your deployment + trial endpoint | Notes, decisions, and "we already decided this," recalled before the model answers. |
| [Company knowledge base](./company-knowledge-base.md) | your deployment + trial endpoint | File your papers, then ask with the path attached. |
