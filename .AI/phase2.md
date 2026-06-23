# Phase 2: Knowledge Base Ingestion System

## Overview & Constraints
This phase implements the ingestion path for the vLLM repository and produces the BM25 assets consumed by retrieval. The code is CPU-oriented, uses sparse BM25 indexing, and keeps the chunking pipeline limited to `.py` and `.md` sources.

**Key Constraints:**
* **Indexing Time:** The CLI accepts a `max_chunk_size` value capped at 2000 characters.
* **Chunking Types:** Python files and Markdown files use separate chunking strategies.
* **Data Models:** `MinimalSource` and `ChunkSource` are Pydantic models, with `ChunkSource` carrying the text and context metadata.
* **Package Management:** The project is managed with `uv`.
* **Chunking Policy:** The current implementation uses zero overlap and preserves contiguous character ranges.
* **Architecture Standard:** The code uses Python 3.10 features such as structural pattern matching and a composition-based chunk builder.

---

## Step 1: File Discovery and Loading
`Indexation` is responsible for finding files and passing their contents to the correct chunker.

* `Indexation._discover_files()` walks the target directory with `Path.rglob("*")`.
* Only files with a suffix present in `self.chunkers` are kept.
* The current mapping is `.py -> PythonChunker` and `.md -> MarkdownChunker`.
* `processed_chunks()` reads each file as UTF-8 text and records any exception in `failed_logs`.
* If `failed_logs` is not empty at the end of the loop, `IndexationError` is raised with the collected failures.

---

## Step 2: Architecture & Data Models
The ingestion layer keeps the metadata models separate from the chunking logic.

* `MinimalSource` stores `file_path`, `first_character_index`, and `last_character_index`.
* `ChunkSource` extends `MinimalSource` with `context_name` and `text`.
* `NodeContext` is used internally by the Python chunker to associate an AST node with an optional parent class name.
* `ChunkerStrategy` is a structural `Protocol` that requires a `.chunk(text, file_path, max_chunk_size)` method returning `list[ChunkSource]`.
* `ChunkBuilder` owns the current accumulator, seals chunks, and handles the fast path for small documents.

---

## Step 3: Intelligent Chunking Strategies
The chunkers route text blocks into the shared `ChunkBuilder` and assign context names along the way.

### 3.1 Python Code Chunking (`.py`)
`PythonChunker` parses source text with `ast.parse()` and iterates over module-level nodes.

* Class children are wrapped in `NodeContext` so the child node can keep the parent class name.
* `match node:` routes `ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef`, and fallback nodes.
* Context labels are emitted as `Function: ...`, `Class: ...`, `Class: ... - Method: ...`, `Class: ... - Attribute/Setup`, or `Module level`.
* Small files are handled by `ChunkBuilder.try_process_full_document()`.
* Larger blocks are processed through `process_segment()`, `process_lines()`, and `process_tail_and_seal()`.

### 3.2 Markdown/Text Chunking (`.md`)
`MarkdownChunker` uses `markdown-it-py` tokens to split the document into section-aware chunks.

* The default context starts as `Section: Introduction`.
* Heading tokens update the current section title using the following inline token.
* The token `.map` information is used to extract line ranges from the original text.
* The chunker preserves section context while building chunks through the shared builder.

---

## Step 4: Indexing with BM25s
`Retriever.build_index()` creates the searchable BM25 index from the produced chunks.

* The corpus is built from `chunk.text` only.
* Tokenization uses `bm25s.tokenize()` with `lower=True`, `stopwords="en"`, `stemmer=Stemmer.Stemmer("english")`, `return_ids=True`, and `show_progress=True`.
* The resulting tokenized corpus is passed to `self.retriever.index()`.

---

## Step 5: Serialization, Storage, and Retrieval
`Retriever` persists both the BM25 index and the chunk mapping used during search.

* `save_index()` writes the BM25 data to `./data/processed/bm25_index`.
* The same method serializes the loaded chunks with `TypeAdapter(list[ChunkSource]).dump_json()` into `./data/processed/chunks/chunk_mapping.json`.
* Any `OSError` during save is wrapped in `RetrieverError`.
* `load_index()` restores the BM25 model and validates the chunk JSON back into `list[ChunkSource]`.
* `bulk_search()` accepts `list[UnansweredQuestion]` and `k`, tokenizes the queries, retrieves document ids, maps them back to `self.chunks`, and returns `StudentSearchResults`.
* `bulk_search()` rejects `k < 1` with `RetrieverError`.