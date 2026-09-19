# Retrieval stack (example data)

Qwen3-Embedding-8B turns documents into 4096-dimension vectors, truncatable via dimensions.
Qwen3-Reranker-8B scores a query against a document list. Cap is 64 documents per call.
A chat model generates over the surviving passages. The embedder and reranker run on your own hardware; the chat model here is DeepSeek-V4.1-Flash on the tiyuvta trial endpoint.
