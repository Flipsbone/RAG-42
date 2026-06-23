# Phase 3: Retrieval System

## Overview & Constraints
This phase covers the retrieval path built on top of the BM25 index from Phase 2. The current code loads the saved index and chunk mapping, tokenizes queries with the same BM25 settings used at indexing time, and maps BM25 document ids back to `ChunkSource` objects for search results.

**Key Constraints:**
* **Data Models:** Retrieval output must validate through `StudentSearchResults` and `MinimalSearchResults`.
* **Output strictness:** Retrieved sources preserve `file_path`, `first_character_index`, `last_character_index`, `context_name`, and `text` because they are reconstructed from `ChunkSource`.
* **CLI Integration:** Retrieval is exposed through `RagCLI.search()` and `RagCLI.search_dataset()` via `python-fire`.
* **Tokenizer parity:** Query tokenization reuses the same `bm25s.tokenize()` configuration as indexing.
* **Error handling:** Invalid `k` values raise `RetrieverError`.

---

## Step 1: Data Models & Validation Setup
The retrieval models are defined in `src/model/model_retrivial.py`.

* `UnansweredQuestion` stores a generated `question_id` plus the question string.
* `AnsweredQuestion` extends `UnansweredQuestion` with `sources` and `answer`.
* `RagDataset` wraps a list of answered or unanswered questions.
* `MinimalSearchResults` stores `question_id`, `question_str`, and `retrieved_sources`.
* `StudentSearchResults` stores the list of search results plus the `k` value used.
* `TypeAdapter` and `model_validate_json()` are used for JSON parsing and serialization in the CLI and retriever flow.

---

## Step 2: Single Query Retrieval Logic (`search`)
Single-query retrieval is handled by `Retriever.load_index()` and `Retriever.bulk_search()`.

* `load_index()` reloads the BM25 model from `./data/processed/bm25_index`.
* The same method reads `./data/processed/chunks/chunk_mapping.json` and validates it into `list[ChunkSource]`.
* `_format_text()` currently returns the input unchanged.
* `_tokenizing()` applies the same lowercase, stopword, stemmer, and `return_ids=True` configuration used during indexing.
* `bulk_search()` can then run `self.retriever.retrieve()` on the tokenized query and map doc ids back to the stored chunk list.

---

## Step 3: Batch Processing (`search_dataset`)
Batch retrieval also funnels through `Retriever.bulk_search(self, queries: list[UnansweredQuestion], k: int) -> StudentSearchResults`.

* The method validates that `k` is greater than zero.
* Incoming questions are formatted with `_format_text()` and tokenized with `_tokenizing()`.
* `self.retriever.retrieve(queries_tokens, k=k)` returns document ids for each query.
* The returned ids are cast with `int(doc_idx)` and used to index into `self.chunks`.
* Each query is wrapped into a `MinimalSearchResults` object and collected into `StudentSearchResults`.

---

## Step 4: CLI Integration (Python Fire)
`RagCLI` exposes the retrieval workflow through the command line.

* `search()` creates an `UnansweredQuestion`, loads the index, runs `bulk_search()`, and prints `model_dump_json(indent=4)`.
* `search_dataset()` loads a `RagDataset`, loads the index once, and writes the aggregated search results to the requested output directory.
* `answer()` currently loads a `StudentSearchResults` file for the next phase of the pipeline.
* The CLI uses `fire.Fire(RagCLI)` in `src/__main__.py`.

## Step 5: Optimization & Recall Checking
This phase does not currently include a baked-in recall evaluator, but the retrieval code is structured so that the output can be validated externally.

* Verify that the chunk indices still map to the original raw text ranges.
* Run the project evaluation flow against the answered dataset after indexing.
* If retrieval quality is low, adjust Phase 2 chunking or tokenization before changing the retrieval mapping logic.