# Use cases

Working shapes for what runs on a [tiyuvta](https://tiyuvta.ai) deployment: open-source frontier models on hardware you can afford, on a serving engine the lab reworks to fit your cards. The retrieval models (an embedder and a reranker) run on your deployment; the chat steps run against the one deployment tiyuvta operates itself as the proof (DeepSeek-V4.1-Flash, api.tiyuvta.ai). No product SDK; every call is the OpenAI-compatible shape.

| | Runs on | |
|---|---|---|
| [Write the work](./examples/work_writing.py) | trial endpoint | Rewrite an email, turn notes into decisions and actions, or make a rough brief into structured JSON. |
| [Support desk](./examples/support_desk.py) | trial endpoint | Tool calls: look up an order and the policy, answer or escalate. |
| [Agent memory](./agent-memory.md) | your deployment + trial endpoint | Notes, decisions, and "we already decided this," recalled before the model answers. |
| [Company knowledge base](./company-knowledge-base.md) | your deployment + trial endpoint | File your papers, then ask with the path attached. |
