"""Shared calls. Two endpoints, both OpenAI-compatible, no product SDK.

* The tiyuvta TRIAL endpoint (api.tiyuvta.ai) serves ONE model, DeepSeek-V4.1-Flash: chat and
  tool calls. Put a few dollars in at https://tiyuvta.ai/services/try/ and test your workload.
* Embeddings and rerank are NOT served there. They are models tiyuvta deploys on YOUR hardware
  (or in your cloud) as part of a deployment: Qwen3-Embedding-8B and Qwen3-Reranker-8B behind the
  same gateway shape. Point RETRIEVAL_BASE_URL at that deployment; without it the retrieval
  examples stop with a message instead of calling an endpoint that does not exist.
Retry 429 with the published backoff.
"""

from __future__ import annotations

import json
import math
import os
import time
import urllib.error
import urllib.request

from openai import OpenAI

BASE = os.environ.get("TIYUVTA_BASE_URL", "https://api.tiyuvta.ai/v1")  # the trial endpoint
CHAT_MODEL = os.environ.get("TIYUVTA_CHAT_MODEL", "deepseek-ai/deepseek-v4.1-flash")
# Your own deployment (the models tiyuvta deploys on your hardware). No default on purpose.
RETRIEVAL_BASE = os.environ.get("RETRIEVAL_BASE_URL")
DIM = 1024
EMBED_MODEL = os.environ.get("RETRIEVAL_EMBED_MODEL", "qwen/qwen3-embedding-8b")
RERANK_MODEL = os.environ.get("RETRIEVAL_RERANK_MODEL", "qwen/qwen3-reranker-8b")

NO_RETRIEVAL = (
    "embeddings and rerank are not served on the tiyuvta trial endpoint (it serves DeepSeek-V4.1-Flash "
    "only). They run on your own hardware as part of a tiyuvta deployment: set RETRIEVAL_BASE_URL (and "
    "RETRIEVAL_KEY if it needs one) to your deployment, or book one at https://tiyuvta.ai/services/"
)


def key() -> str:
    k = os.environ.get("TIYUVTA_KEY") or os.environ.get("TIYUVTA_API_KEY")
    if not k:
        raise SystemExit("export TIYUVTA_KEY (or TIYUVTA_API_KEY): https://tiyuvta.ai/services/try/")
    return k


def retrieval_base() -> str:
    if not RETRIEVAL_BASE:
        raise SystemExit(NO_RETRIEVAL)
    return RETRIEVAL_BASE.rstrip("/")


def retrieval_key() -> str:
    return os.environ.get("RETRIEVAL_KEY") or key()


def chat() -> OpenAI:
    return OpenAI(base_url=BASE, api_key=key())


def post(path: str, body: dict) -> dict:
    """POST to YOUR retrieval deployment (embeddings / rerank). The trial endpoint is chat-only."""
    payload = json.dumps(body).encode()
    headers = {
        "Authorization": f"Bearer {retrieval_key()}",
        "Content-Type": "application/json",
    }
    base = retrieval_base()
    for i in range(1, 6):
        req = urllib.request.Request(base + path, data=payload, headers=headers)
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

    Body shape of the tiyuvta gateway (2026-09-03): {results:[{index, relevance_score, document:{text}}], usage}.
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
