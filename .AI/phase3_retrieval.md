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

* `UnansweredQuestion` stores `question_id` and the question string.
* `AnsweredQuestion` extends `UnansweredQuestion` with `sources` and `answer`.
* `RagDataset` wraps answered and unanswered questions.
* `MinimalSearchResults` stores `question_id`, `question_str`, and `retrieved_sources`.
* `StudentSearchResults` stores the batch results plus `k`.

## Loading the Index
`Retriever.load_index()` restores the retrieval state from disk.

* The BM25 index is loaded from `./data/processed/bm25_index`.
* The chunk mapping is loaded from `./data/processed/chunks/chunk_mapping.json`.
* Saved files are verified with the hash helpers before loading.
* The chunk JSON is validated back into `list[ChunkSource]`.

## Query Handling
`Retriever.bulk_search()` is the main retrieval entry point.

* It rejects `k < 1` with `RetrieverError`.
* It extracts the raw question strings from the input questions.
* It tokenizes them with `bm25s.tokenize(..., lower=True, stopwords="en", stemmer=self._stemmer, return_ids=True, show_progress=True)`.
* It calls `self.retriever.retrieve(queries_tokens, k=k)`.
* Returned document ids are converted to `int` and used to index `self.chunks`.
* Each query becomes a `MinimalSearchResults` entry in `StudentSearchResults`.

## CLI Integration
`RagCLI` exposes retrieval through Python Fire.

* `search()` creates an `UnansweredQuestion`, loads the index, runs `bulk_search()`, and prints JSON.
* `search_dataset()` loads a `RagDataset`, runs batch retrieval, and saves the results to the requested directory.
* `answer()` consumes the retrieval output for the generation phase.
* The CLI entry point is `fire.Fire(RagCLI)` in [src/__main__.py](../src/__main__.py).

## Notes
The retrieval layer does not implement its own recall metric. Evaluation is handled separately by [src/evaluate/evaluation.py](../src/evaluate/evaluation.py).


