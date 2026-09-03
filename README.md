# tiyuvta inference use cases

Public examples for a Use cases tab on [inference.tiyuvta.ai](https://inference.tiyuvta.ai/). MIT.

One prepaid key covers chat, tools, embed, and rerank. There is no product-specific SDK.

Website-ready copy lives in `site/`.

```bash
export TIYUVTA_KEY="YOUR_KEY"   # https://inference.tiyuvta.ai/login
pip install -r requirements.txt

python examples/work_writing.py rewrite "Please rewrite this email in a calmer tone: ..."
python examples/work_writing.py summary "Decision: annual plan. Maya sends terms Friday."
python examples/work_writing.py brief "Create an SOP for approving supplier invoices above \$5,000."

python examples/support_desk.py "Hi, order A1842 still is not here. Can I get a refund?"
python examples/agent_memory.py
python examples/knowledge_base.py ingest
python examples/knowledge_base.py ask "What is our prepaid billing rule?"
```

These are working shapes, not a bake-off. GLM-5.3-Flash runs the everyday writing and support examples; reasoning is always on and bills as output. Qwen3.8 27B runs the memory loop and knowledge-base filing. Embed and rerank are Qwen3 8B.
