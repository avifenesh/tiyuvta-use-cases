#!/usr/bin/env python3
"""Local SQLite memory over tiyuvta embed + rerank + GLM."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from client import chat, cosine, embed, rerank_order

QUERY_INSTRUCT = (
    "Instruct: Retrieve stored memories that help answer this user message\nQuery: "
)
RERANK_INSTRUCT = (
    "Given a user message, retrieve stored memories that are useful for answering it"
)
SEED = [
    "Avi Fenesh builds memra, a Rust + CUDA inference engine, and operates inference.tiyuvta.ai.",
    "Prepaid credit does not expire. There is no subscription and no minimum.",
    "Embed and rerank share the same API key as chat. They bill input tokens only.",
]


def db_path() -> Path:
    return Path(__file__).with_name("memory.sqlite")


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(db_path())
    db.execute("create table if not exists mem (id integer primary key, text text, vec text)")
    return db


def seed(db: sqlite3.Connection) -> None:
    n = db.execute("select count(*) from mem").fetchone()[0]
    if n:
        return
    for text, vec in zip(SEED, embed(SEED)):
        db.execute("insert into mem(text, vec) values (?, ?)", (text, json.dumps(vec)))
    db.commit()


def remember(db: sqlite3.Connection, user: str, k: int = 20, n: int = 5) -> list[str]:
    q = embed([QUERY_INSTRUCT + user])[0]
    rows = db.execute("select text, vec from mem").fetchall()
    ranked = sorted(
        ((cosine(q, json.loads(vec)), text) for text, vec in rows),
        reverse=True,
    )[: min(k, 64)]
    docs = [text for _, text in ranked]
    return [docs[i] for i in rerank_order(user, docs, RERANK_INSTRUCT, n) if i < len(docs)]


def answer(db: sqlite3.Connection, user: str) -> str:
    memories = remember(db, user)
    r = chat().chat.completions.create(
        model="zai/glm-5.3-flash",
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer from the recalled memories. If they are not enough, say so. "
                    "Do not invent a memory that was not recalled."
                ),
            },
            {
                "role": "user",
                "content": "Recalled memories:\n- "
                + "\n- ".join(memories or ["(none)"])
                + "\n\nUser: "
                + user,
            },
        ],
        max_tokens=2048,
    )
    return r.choices[0].message.content or ""


def write_back(db: sqlite3.Connection, user: str, reply: str) -> None:
    r = chat().chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "system",
                "content": 'Return JSON {"facts":[...]} of durable user or world facts from this turn. Empty list if none.',
            },
            {"role": "user", "content": f"User: {user}\nAssistant: {reply}"},
        ],
        response_format={"type": "json_object"},
        extra_body={"reasoning_effort": "none"},
        max_tokens=256,
    )
    raw = r.choices[0].message.content or "{}"
    facts = json.loads(raw).get("facts") or []
    texts = [f for f in facts if isinstance(f, str) and f.strip()]
    if not texts:
        return
    for text, vec in zip(texts, embed(texts)):
        db.execute("insert into mem(text, vec) values (?, ?)", (text, json.dumps(vec)))
    db.commit()


def main() -> None:
    q = " ".join(sys.argv[1:]) or "Who runs the hosted inference endpoint, and how am I billed?"
    db = connect()
    seed(db)
    reply = answer(db, q)
    print(reply)
    write_back(db, q, reply)


if __name__ == "__main__":
    main()
