#!/usr/bin/env python3
"""Rewrite work text, summarize notes, or structure a rough brief with GLM."""

from __future__ import annotations

import argparse
import json
import sys

from openai import OpenAI

from client import BASE, key

MODEL = "zai/glm-5.3-flash"
MAX_TOKENS = 8192

SYSTEMS = {
    "rewrite": (
        "Rewrite workplace email in clear, calm, concise language. Preserve every fact, "
        "name, date, request, and commitment. Do not add facts. Return only the rewritten email."
    ),
    "summary": (
        "Turn the supplied work notes into a compact record with these headings: Decisions, "
        "Actions, Open questions. Include owners and due dates only when stated. Mark missing "
        "owners or dates as not stated. Do not infer facts. Return only the record."
    ),
    "brief": (
        "Turn the rough brief into the requested structured proposal or SOP outline. Use only "
        "facts in the brief. Put missing information in open_questions instead of inventing it."
    ),
}

BRIEF_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "work_brief",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "document_type": {"type": "string", "enum": ["proposal", "SOP"]},
                "title": {"type": "string"},
                "objective": {"type": "string"},
                "audience": {"type": "array", "items": {"type": "string"}},
                "scope": {"type": "array", "items": {"type": "string"}},
                "deliverables": {"type": "array", "items": {"type": "string"}},
                "steps": {"type": "array", "items": {"type": "string"}},
                "assumptions": {"type": "array", "items": {"type": "string"}},
                "open_questions": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "document_type", "title", "objective", "audience", "scope",
                "deliverables", "steps", "assumptions", "open_questions",
            ],
        },
    },
}


def source_text(parts: list[str]) -> str:
    text = " ".join(parts).strip() if parts else sys.stdin.read().strip()
    if not text:
        raise SystemExit("Provide text as arguments or pipe it on stdin.")
    return text


def run(mode: str, text: str) -> str:
    client = OpenAI(base_url=BASE, api_key=key(), timeout=360.0, max_retries=0)
    request = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEMS[mode]},
            {"role": "user", "content": text},
        ],
        "extra_body": {"reasoning_effort": "low"},
        "max_tokens": MAX_TOKENS,
    }
    if mode == "brief":
        request["response_format"] = BRIEF_SCHEMA

    chunks = client.chat.completions.create(stream=True, **request)
    content = "".join(
        chunk.choices[0].delta.content or ""
        for chunk in chunks
        if chunk.choices
    ).strip()
    if mode == "brief":
        return json.dumps(json.loads(content), indent=2, ensure_ascii=False)
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("rewrite", "summary", "brief"))
    parser.add_argument("text", nargs="*", help="source text; reads stdin when omitted")
    args = parser.parse_args()
    print(run(args.mode, source_text(args.text)))


if __name__ == "__main__":
    main()
