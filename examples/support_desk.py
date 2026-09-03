#!/usr/bin/env python3
"""A tiny support desk. GLM looks up orders and policy, then answers or escalates.

The store is local. The endpoint only sees the text and tool results you send.
"""

from __future__ import annotations

import json
import sys

from client import chat

MODEL = "zai/glm-5.3-flash"

ORDERS = {
    "A1842": {"status": "shipped", "item": "prepaid inference credit", "eta": "Thursday"},
    "A1901": {"status": "refunded", "item": "prepaid inference credit", "eta": None},
}

POLICY = {
    "refund": "Prepaid credit does not expire. Refunds on unused credit within 14 days of purchase. No subscription to cancel.",
    "billing": "One prepaid balance. Embed, rerank, and chat share the same key. No monthly minimum.",
    "sla": "Support replies on business days. If we cannot find the order, escalate. Do not invent a status.",
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order by id. Returns status or not_found.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_policy",
            "description": "Look up a written policy. Topics: refund, billing, sla.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string", "enum": ["refund", "billing", "sla"]}},
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate",
            "description": "Hand the ticket to a person. Use when the store has no answer.",
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string"}},
                "required": ["reason"],
            },
        },
    },
]

SYSTEM = (
    "You run a small support desk. Use tools before you answer. "
    "If the order or policy is missing, escalate. Do not invent a status or a rule. "
    "Write the customer a short, plain reply."
)


def run_tool(name: str, args: dict) -> str:
    if name == "lookup_order":
        oid = str(args.get("order_id") or "").strip().upper()
        row = ORDERS.get(oid)
        return json.dumps(row or {"order_id": oid, "status": "not_found"})
    if name == "lookup_policy":
        topic = str(args.get("topic") or "").strip().lower()
        text = POLICY.get(topic)
        return json.dumps({"topic": topic, "text": text or "no policy on this topic"})
    if name == "escalate":
        return json.dumps({"escalated": True, "reason": args.get("reason")})
    return json.dumps({"error": f"unknown tool {name}"})


def desk(ticket: str) -> str:
    client = chat()
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": ticket},
    ]
    for _ in range(6):
        r = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            extra_body={"reasoning_effort": "low"},
            max_tokens=4096,
        )
        msg = r.choices[0].message
        calls = msg.tool_calls or []
        if not calls:
            return (msg.content or "").strip()
        messages.append(msg)
        for call in calls:
            args = json.loads(call.function.arguments or "{}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": run_tool(call.function.name, args),
                }
            )
    return "escalated: the model kept calling tools"


if __name__ == "__main__":
    ticket = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Hi, order A1842 still is not here. Can I get a refund?"
    )
    print(desk(ticket))
