 
# Architecture

This project implements a local BM25-based RAG pipeline over the extracted vLLM source tree.

## Flow
`raw files -> indexing/chunking -> BM25 retrieval -> context stitching -> Ollama generation -> JSON output`

## Main Modules
* `src/model/model_indexing.py` defines `MinimalSource`, `ChunkSource`, and `NodeContext`.
* `src/indexing/chunking.py` implements `ChunkBuilder`, `PythonChunker`, and `MarkdownChunker`.
* `src/indexing/indexation.py` discovers files and launches indexing.
* `src/retrieval/retriever.py` saves, loads, and queries the BM25 index.
* `src/generation/generator.py` formats retrieved chunks and calls Ollama.
* `src/cli/command_line_interface.py` exposes `index`, `search`, `search_dataset`, `answer`, `answer_dataset`, and `evaluate`.
* `src/evaluate/evaluation.py` compares retrieved spans with the expected answer sources.

## Design Notes
* The ingestion layer only handles `.py` and `.md` files.
* Chunk metadata preserves file path, character offsets, and context labels.
* Retrieval uses bm25s with English stopwords and stemming.
* Generation uses the local Ollama model `qwen3:0.6b`.
* Outputs are serialized with Pydantic models and written as JSON.

## CLI Entry Point
`fire.Fire(RagCLI)` is executed from `src/__main__.py`, so each public method on `RagCLI` becomes a command directly.