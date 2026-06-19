# Phase 3: Retrieval System Roadmap

## Overview & Constraints
This phase bridges the gap between the ingested knowledge base (BM25 index) and the final Answer Generation system. The goal is to accurately fetch the top-$k$ most relevant chunks for a given query while strictly adhering to the required Pydantic data models.

**Key Constraints:**
* **Performance Requirements:** Must achieve at least 80% recall@5 on documentation questions and 50% on code questions.
* **Output strictness:** Retrieved sources must strictly include `file_path`, `first_character_index`, and `last_character_index`.
* **Data Models:** Outputs must validate against `StudentSearchResults` and `MinimalSearchResults`.
* **CLI Integration:** Must support both single query search (`search`) and batch dataset processing (`search_dataset`) via `python-fire`.
* **Latency:** Warm retrieval throughput must be capable of processing 1000 questions in under 90 seconds.

---

## Step 1: Data Models & Validation Setup
Ensure your data structures strictly follow the specifications to guarantee validation throughout the pipeline.

* **Pydantic Models:** * `MinimalSource`: Strictly tracks location data.
  * `UnansweredQuestion`: Validates incoming query structure (UUID and string).
  * `MinimalSearchResults`: Contains `question_id`, `question`, and `retrieved_sources`.
  * `StudentSearchResults`: Aggregates a list of `MinimalSearchResults` and tracks the `k` parameter.
* **Validation Layer:** Use these models via `TypeAdapter` or `.model_validate_json()` to parse incoming datasets and serialize outputs.

---

## Step 2: Single Query Retrieval Logic (`search`)
Implement the core logic to query the BM25 index loaded from Phase 2.

* **Index & Chunk Loading:** Implement a fast-loading mechanism in your `Retriever` class to load the pre-computed BM25 index from `./data/processed/bm25_index` and your serialized chunk mapping (e.g., `chunk_mapping.json`) from `./data/processed/chunks/`.
* **Query Tokenization:** Convert the incoming user query into tokens. **Crucial:** You must use the exact same tokenizer configurations (lowercasing, stemmer, stop words) used during the indexing phase.
* **BM25 Search Execution:** Pass the tokenized query to the loaded BM25 model to retrieve the top-$k$ document IDs and their scores.
* **Metadata Mapping:** * Map the returned BM25 IDs back to your original `ChunkSource` objects using the JSON dictionary you loaded into memory.
  * Extract the `file_path`, `first_character_index`, and `last_character_index` to build `MinimalSource` objects for the retrieved chunks.

---

## Step 3: Batch Processing (`search_dataset`)
All retrieval operations funnel through a single, highly optimized batch search method to respect the 90-second throughput limit

* **Signature:** `bulk_search(self, queries: list[UnansweredQuestion], k: int) -> StudentSearchResults`
* **BM25 Search Execution:** Pass the fully formatted and tokenized queries to `self.retriever.retrieve(queries_tokens, k=k)`.
* **Metadata Mapping:** * Iterate through the paired `queries` and returned `docs_idx`.
  * Map the returned integer IDs directly to the original `ChunkSource` objects loaded in memory.
  * Package the extracted chunks into `MinimalSearchResults` objects.
* **Aggregation:** Wrap all processed query results inside the final `StudentSearchRes

---

## Step 4: CLI Integration (Python Fire)
Expose the retrieval functionalities to the command-line using `RagCLI.

* **`search` Command:**
  * **Action:** Wraps a single query string into an `UnansweredQuestion`, passes it to `bulk_search` (with a default `k=5`), and prints the `.model_dump_json(indent=4)` to the console.

* **`search_dataset` Command:**
  * **Dataset Ingestion:** Opens the target JSON file and parses the entire structure using `RagDataset.model_validate_json()`. If the file cannot be read, raise a `DatasetError`.
  * **Performance & UX:** **Use `tqdm`** to display a progress bar while iterating through the parsed dataset or executing the bulk queries, fulfilling the mandatory CLI requirement for long-running operations. Ensure your BM25 index and JSON mapping are only loaded into memory *once* before the loop starts.
  * **Batch Execution:** Flattens the parsed dataset into a single list of `UnansweredQuestion` objects and passes them to `bulk_search`.
  * **Serialization:** Saves the aggregated JSON output to the specified `save_directory`.

## Step 5: Optimization & Recall Checking
Before moving to Phase 4, you must verify your retrieval performance.

* **Sanity Check:** Manually verify that `first_character_index` and `last_character_index` accurately map to the raw text in the original files.
* **Baseline Measurement:** Use the provided evaluation script (`moulinette evaluate_student_search_results`) to measure your current recall@k score against the `AnsweredQuestions` ground truth dataset. 
* **Refinement (If Needed):** If recall is below 80% for docs or 50% for code, revisit your Phase 2 chunking strategy (e.g., adjust chunk sizes, enhance context names) or tweak the BM25 tokenization parameters.