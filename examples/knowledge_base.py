#!/usr/bin/env python3
"""File a local corpus, then ask with path citations."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

from client import chat, cosine, embed, rerank_order

CHUNK, OVERLAP = 3000, 400
SUFFIXES = {".md", ".txt", ".markdown"}
ASK_INSTRUCT = (
    "Instruct: Retrieve passages from a company document corpus that answer this question\nQuery: "
)
RERANK_INSTRUCT = (
    "Given a workplace question, retrieve passages from internal papers and notes that answer it"
)
ARRANGE = """You file a company corpus. Return JSON:
{"topic": "...", "summary": "one line", "tags": ["..."], "doc_type": "paper|note|policy|other"}
Use the filename and extract. Do not invent a title the extract does not support."""


def corpus_dir() -> Path:
    return Path(__file__).with_name("corpus")


def db_path() -> Path:
    return Path(__file__).with_name("kb.sqlite")


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(db_path())
    db.execute(
        "create table if not exists chunk (id integer primary key, path text, start int, end int, text text, vec text)"
    )
    db.execute(
        "create table if not exists file_meta (path text primary key, topic text, summary text, tags text, doc_type text)"
    )
    return db


def chunks_of(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    i, n = 0, len(text)
    while i < n:
        j = min(n, i + CHUNK)
        yield i, j, text[i:j]
        if j == n:
            break
        i = max(i + 1, j - OVERLAP)


def ingest(db: sqlite3.Connection) -> None:
    if db.execute("select count(*) from chunk").fetchone()[0]:
        return
    docs = []
    for path in sorted(corpus_dir().rglob("*")):
        if path.suffix.lower() in SUFFIXES and path.is_file():
            for start, end, text in chunks_of(path):
                docs.append((str(path), start, end, text))
    if not docs:
        raise SystemExit(f"no .md/.txt files under {corpus_dir()}")
    vectors = embed([t for *_, t in docs])
    for (path, start, end, text), vec in zip(docs, vectors):
        db.execute(
            "insert into chunk(path, start, end, text, vec) values (?,?,?,?,?)",
            (path, start, end, text, json.dumps(vec)),
        )
    db.commit()


def arrange(db: sqlite3.Connection) -> None:
    c = chat()
    for (path,) in db.execute("select distinct path from chunk"):
        if db.execute("select 1 from file_meta where path=?", (path,)).fetchone():
            continue
        first = db.execute(
            "select text from chunk where path=? order by start limit 1", (path,)
        ).fetchone()[0]
        r = c.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": ARRANGE},
                {"role": "user", "content": f"filename: {path}\n\n{first[:4000]}"},
            ],
            response_format={"type": "json_object"},
            extra_body={"reasoning_effort": "none"},
            max_tokens=256,
        )
        meta = json.loads(r.choices[0].message.content or "{}")
        db.execute(
            "insert or replace into file_meta(path, topic, summary, tags, doc_type) values (?,?,?,?,?)",
            (
                path,
                meta.get("topic"),
                meta.get("summary"),
                json.dumps(meta.get("tags", [])),
                meta.get("doc_type"),
            ),
        )
    db.commit()
    print("filed:")
    for row in db.execute("select path, topic, summary from file_meta"):
        print(f"  {row[1]} — {row[2]} ({row[0]})")


def ask(db: sqlite3.Connection, question: str, k: int = 20, n: int = 6) -> str:
    q = embed([ASK_INSTRUCT + question])[0]
    rows = db.execute("select path, start, text, vec from chunk").fetchall()
    ranked = sorted(
        ((cosine(q, json.loads(vec)), path, start, text) for path, start, text, vec in rows),
        reverse=True,
    )[: min(k, 64)]
    docs = [t for _, _, _, t in ranked]
    order = rerank_order(question, docs, RERANK_INSTRUCT, n)
    hits = [ranked[i][1:] for i in order if i < len(ranked)]
    cited = "\n\n".join(
        f"[{i}] {path}@{start}\n{text}" for i, (path, start, text) in enumerate(hits, 1)
    )
    r = chat().chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer only from the passages. Cite as [n]. "
                    "If the passages are not enough, say what is missing. "
                    "Do not cite a path you were not given."
                ),
            },
            {"role": "user", "content": cited + "\n\nQuestion: " + question},
        ],
        extra_body={"reasoning_effort": "none"},
        max_tokens=1024,
    )
    return r.choices[0].message.content or ""


def main() -> None:
    db = connect()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "ask"
    if cmd == "ingest":
        ingest(db)
        arrange(db)
        return
    if cmd == "ask":
        ingest(db)
        arrange(db)
        q = " ".join(sys.argv[2:]) or "What is our prepaid billing rule?"
        print(ask(db, q))
        return
    raise SystemExit("usage: knowledge_base.py ingest | ask [question]")


if __name__ == "__main__":
    main()
