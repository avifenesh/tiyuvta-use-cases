# Write the work

Most work writing does not start blank. It starts with an email that came out too sharp, notes nobody shaped, or a brief that another system needs to read as JSON.

Use [GLM-5.3-Flash](/models/glm-5-3-flash) for that first pass. It is the cheapest model on this roster, and the strongest we serve. One prepaid key. One model call. Your text stays in your app.

[Get a key](/login) and run the example. Or read the three jobs first.

## Why start here

OpenAI and NBER looked at about 1.5 million consumer ChatGPT conversations in September 2025. Writing was about 40% of the work-related messages. Around two thirds of that writing was editing, critiquing, summarizing, or translating something that already existed.

That study is consumer ChatGPT, not enterprise API traffic. Still, it matches how most companies actually write: fix what is already there, then put the result back into the workflow.

## Three jobs

### Rewrite an email

Give GLM the draft, who it is for, and the tone you want. Ask it to keep the facts and cut the heat, jargon, or clutter. Your app can show the rewrite next to the original so a person can check it.

### Turn notes into decisions and actions

Send meeting notes or a call transcript. Ask for decisions, actions, owners, due dates, and open questions. Tell it not to invent what was not said. You get a short record instead of another wall of notes.

### Turn a rough brief into a proposal or SOP shape

When the next step is software, ask for structured JSON, not another paragraph. The example returns a document type, title, objective, audience, scope, deliverables, steps, assumptions, and open questions. Your app can validate it, fill a form, or save it.

## Why GLM

GLM-5.3-Flash is not the "good enough" model here. It is the cheapest on the roster, and the strongest we serve.

It does ordinary chat and structured JSON. It also does tools and vision when the workflow grows, a 262K served context for long source material, and prompt caching for repeated instructions. Reasoning stays on, and reasoning tokens bill as output. Use `reasoning_effort: low` for everyday rewriting and extraction, leave a generous `max_tokens`, and raise the effort only when the work needs it.

## A first run

Export `TIYUVTA_KEY` from the [console](/login). The runnable pack is [avifenesh/tiyuvta-use-cases](https://github.com/avifenesh/tiyuvta-use-cases).

```bash
export TIYUVTA_KEY="YOUR_KEY"
pip install -r requirements.txt

python examples/work_writing.py rewrite \
  "Hi Sam. This is the third time I have asked for the signed quote. Send it today."

python examples/work_writing.py summary \
  "We chose the annual plan. Maya will send legal the terms by Friday. Price approval is still open."

python examples/work_writing.py brief \
  "Create an SOP for approving supplier invoices. Finance owns it. Cover invoices above \$5,000 and flag missing purchase orders."
```

Each command makes one streamed OpenAI-compatible call to `https://api.tiyuvta.ai/v1`. The `brief` mode asks for JSON Schema output. Streaming keeps a generous `max_tokens` inside the platform timeout. There is no product-specific SDK.

## What this is not

This is inference. It is not a hosted editor, inbox, or document system. You bring the thin workflow. You decide where inputs and outputs live.

The model does not know your company unless you tell it. For decisions and facts you want recalled later, see [Give your tools a memory](/use-cases/agent-memory). For filing papers and asking with the path attached, a company knowledge base page is coming soon.

A clean sentence can still carry a wrong date, name, promise, or policy. Read high-stakes text before it leaves the business, especially legal, financial, medical, employment, and customer commitments.

## What it costs

You pay GLM for input and output, including reasoning tokens. Repeated prompt material may get the cached-input rate when the response reports cached tokens. Prices are on [Pricing](/pricing).

## Next

- [Use cases](/use-cases): the rest of this section
- [GLM-5.3-Flash](/models/glm-5-3-flash)
- [Give your tools a memory](/use-cases/agent-memory) when the workflow needs prior decisions
- Example repo: [avifenesh/tiyuvta-use-cases](https://github.com/avifenesh/tiyuvta-use-cases)
