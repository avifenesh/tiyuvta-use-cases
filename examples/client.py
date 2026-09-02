"""Shared tiyuvta calls. Retry 429 with the published backoff. No product SDK."""

from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.request

from openai import OpenAI

BASE = "https://api.tiyuvta.ai/v1"
DIM = 1024
EMBED_MODEL = "qwen/qwen3-embedding-8b"
RERANK_MODEL = "qwen/qwen3-reranker-8b"


def key() -> str:
    k = os.environ.get("TIYUVTA_KEY") or os.environ.get("TIYUVTA_API_KEY")
    if not k:
        raise SystemExit("export TIYUVTA_KEY (or TIYUVTA_API_KEY)")
    return k


def chat() -> OpenAI:
    return OpenAI(base_url=BASE, api_key=key())


def post(path: str, body: dict) -> dict:
    payload = json.dumps(body).encode()
    headers = {
        "Authorization": f"Bearer {key()}",
        "Content-Type": "application/json",
    }
    for i in range(1, 6):
        req = urllib.request.Request(BASE + path, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 5:
                raise
            time.sleep(i * i)
    raise RuntimeError("unreachable")


def embed(texts: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(texts), 32):
        data = post(
            "/embeddings",
            {
                "model": EMBED_MODEL,
                "input": texts[i : i + 32],
                "dimensions": DIM,
            },
        )
        out.extend(v["embedding"] for v in sorted(data["data"], key=lambda x: x["index"]))
    return out


def cosine(a: list[float], b: list[float]) -> float:
    den = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return sum(x * y for x, y in zip(a, b)) / den if den else 0.0


def rerank_order(query: str, documents: list[str], instruction: str, top_n: int) -> list[int]:
    """Return indexes into `documents` in rerank order.

    Live body (2026-09-03): {results:[{index, relevance_score, document:{text}}], usage}.
    """
    if not documents:
        return []
    data = post(
        "/rerank",
        {
            "model": RERANK_MODEL,
            "query": query,
            "documents": documents[:64],
            "top_n": min(top_n, 64),
            "instruction": instruction,
            "return_documents": True,
        },
    )
    results = data.get("results")
    if isinstance(results, list) and results and isinstance(results[0], dict):
        order: list[int] = []
        for hit in results:
            if "index" in hit:
                order.append(int(hit["index"]))
        if order:
            return order
    return list(range(min(top_n, len(documents))))
