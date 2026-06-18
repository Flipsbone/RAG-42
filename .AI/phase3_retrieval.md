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

* **Pydantic Models:** * Ensure `MinimalSource` is imported and used exactly as defined.
  * Implement `MinimalSearchResults`: Must contain `question_id` (str), `question` (str), and `retrieved_sources` (List[MinimalSource]).
  * Implement `StudentSearchResults`: Must contain `search_results` (List[MinimalSearchResults]) and `k` (int).
* **Validation Layer:** Use these models to parse incoming JSON datasets (like `dataset_docs_public.json`) and to serialize your final outputs.

---

## Step 2: Single Query Retrieval Logic (`search`)
Implement the core logic to query the BM25 index loaded from Phase 2.

* [cite_start]**Index & Chunk Loading:** Implement a fast-loading mechanism in your `Retriever` class to load the pre-computed BM25 index from `./data/processed/bm25_index` and your serialized chunk mapping (e.g., `chunk_mapping.json`) from `./data/processed/chunks/`.
* **Query Tokenization:** Convert the incoming user query into tokens. **Crucial:** You must use the exact same tokenizer configurations (lowercasing, stemmer, stop words) used during the indexing phase.
* **BM25 Search Execution:** Pass the tokenized query to the loaded BM25 model to retrieve the top-$k$ document IDs and their scores.
* **Metadata Mapping:** * Map the returned BM25 IDs back to your original `ChunkSource` objects using the JSON dictionary you loaded into memory.
  * Extract the `file_path`, `first_character_index`, and `last_character_index` to build `MinimalSource` objects for the retrieved chunks.

---

## Step 3: Batch Processing (`search_dataset`)
The system must be capable of processing multiple questions efficiently for evaluation.

* **Dataset Ingestion:** Read the input JSON file (e.g., `./data/datasets/UnansweredQuestions/dataset_docs_public.json`). Parse the file into your predefined dataset Pydantic model (e.g., a list of `UnansweredQuestion` objects).
* **Batch Execution Loop:**
  * Iterate through the list of questions.
  * For each question, execute the Single Query Retrieval logic.
  * Collect the mapped `MinimalSource` results and package them into a `MinimalSearchResults` object.
* **Performance Optimization:** Use `tqdm` to display a progress bar. Ensure your BM25 index and chunk JSON mapping are loaded only **once** into memory before starting the loop to respect the 90-second throughput limit.
* **JSON Serialization:** Aggregate all results into a `StudentSearchResults` object and dump it to a properly formatted JSON file in the specified output directory.

---

## Step 4: CLI Integration (Python Fire)
Expose the retrieval functionalities to the command-line using `python-fire`.

* **`search` Command:**
  * **Signature:** `search(query: str, k: int = 5)`
  * **Action:** Prints the retrieved sources to the console in a readable format.
* **`search_dataset` Command:**
  * **Signature:** `search_dataset(dataset_path: str, save_directory: str, k: int = 10)`
  * **Action:** Loads the dataset, processes all queries, and saves the output JSON file in `save_directory` with the same filename as the input dataset.

---

## Step 5: Optimization & Recall Checking
Before moving to Phase 4, you must verify your retrieval performance.

* **Sanity Check:** Manually verify that `first_character_index` and `last_character_index` accurately map to the raw text in the original files.
* **Baseline Measurement:** Use the provided evaluation script (`moulinette evaluate_student_search_results`) to measure your current recall@k score against the `AnsweredQuestions` ground truth dataset. 
* **Refinement (If Needed):** If recall is below 80% for docs or 50% for code, revisit your Phase 2 chunking strategy (e.g., adjust chunk sizes, enhance context names) or tweak the BM25 tokenization parameters.