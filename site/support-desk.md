# Put GLM on the desk

Support repeats itself. The same refund question, the same “where is my order,” the same policy that already exists in a doc nobody opens.

You do not need a second vendor for that. You need a model cheap enough to leave on, and strong enough to close the ticket. On this roster that is [GLM-5.3-Flash](/models/glm-5-3-flash).

This page is a working shape: an incoming ticket, a few tools into *your* store, a reply or a handoff. The store stays on your side.

[Get a key](/login) and run the example. Or read the story first.

## Why GLM

One model, the cheapest on the roster, and the strongest we serve.

It has tools. It has vision if the ticket is a screenshot. It has a 262K window if the thread is long. Reasoning stays on. You see it, and you pay for it as output, so send a real `max_tokens` and stream.

That is the product pitch. The desk is yours. The model is a prepaid call.

## What this is not

This is not a hosted helpdesk. We do not store your tickets, your orders, or your policy. We only see the text and the tool results you send.

It is also not a handle-time bake-off. We have run the shape against the live endpoint. We have not published a “percent of tickets closed” for your queue.

## What you do

**Keep the store local.** Orders, policy, who already refunded whom. A dict is enough to start.

**Give the model three tools.** Look up an order. Look up a policy. Escalate when the store has no answer.

**Do not let it invent.** If the order is missing, it should hand off. A confident wrong refund is worse than a slow human.

## A first run

Export `TIYUVTA_KEY` from the [console](/login). The runnable pack is [avifenesh/tiyuvta-use-cases](https://github.com/avifenesh/tiyuvta-use-cases).

```bash
export TIYUVTA_KEY="YOUR_KEY"
pip install -r requirements.txt
python examples/support_desk.py "Hi, order A1842 still is not here. Can I get a refund?"
```

The loop, if you want it in your own app:

```python
client.chat.completions.create(
    model="zai/glm-5.3-flash",
    messages=[{"role": "user", "content": ticket}],
    tools=[
        {"type": "function", "function": {"name": "lookup_order", "...": "..."}},
        {"type": "function", "function": {"name": "lookup_policy", "...": "..."}},
        {"type": "function", "function": {"name": "escalate", "...": "..."}},
    ],
    # reasoning is always on; it bills as output
    extra_body={"reasoning_effort": "low"},
    max_tokens=4096,
)
```

When the model returns `tool_calls`, you run them against your store and send the results back. Same OpenAI shape. No product-specific SDK.

The example uses `reasoning_effort: low` so a first run does not spend the default (max) thinking budget. Raise it when the ticket is the work.

## What it costs, roughly

You pay GLM input and output, including reasoning tokens. Tool results you send back are input on the next turn. Prompt caching is on for this model: a repeated policy block can bill at the cached-input rate when the response reports `cached_tokens`. Prices are on [Pricing](/pricing).

## Next

- [Use cases](/use-cases): the rest of this section
- [Give your tools a memory](/use-cases/agent-memory) if the desk should remember last quarter
- [GLM-5.3-Flash](/models/glm-5-3-flash)
- Example repo: [avifenesh/tiyuvta-use-cases](https://github.com/avifenesh/tiyuvta-use-cases)
