# tiyuvta inference use cases

Public examples for a Use cases tab on [inference.tiyuvta.ai](https://inference.tiyuvta.ai/). MIT.

Example code for two shapes on [inference.tiyuvta.ai](https://inference.tiyuvta.ai/): agent memory, and a company knowledge base. One prepaid key covers embed, rerank, and chat. There is no product-specific SDK.

Website-ready copy lives in `INDEX.md`, `agent-memory.md`, and `company-knowledge-base.md`.

```bash
export TIYUVTA_KEY="YOUR_KEY"   # https://inference.tiyuvta.ai/login
pip install -r requirements.txt
cd examples
python agent_memory.py
python knowledge_base.py ingest
python knowledge_base.py ask "What is our prepaid billing rule?"
```

These are working shapes, not a recall bake-off. Embed/rerank retry a `429`. Qwen3.8 27B runs the memory loop and the knowledge-base filing. Embed and rerank are Qwen3 8B. One family, one key.
