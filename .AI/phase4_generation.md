# Phase 4: Answer Generation System Roadmap

## Overview & Constraints
This phase focuses on synthesizing the retrieved code snippets and documentation into a coherent, accurate response. You will integrate the required Large Language Model (LLM) and construct a robust Retrieval-Augmented Generation (RAG) pipeline that guarantees answers are strictly grounded in the provided context.

**Key Constraints:**
* **Mandatory Model:** Must use `Qwen/Qwen3-0.6B` (default) for natural language generation.
* **Output strictness:** Output must be structured JSON validated by Pydantic models (`MinimalAnswer` and `StudentSearchResultsAndAnswer`).
* **Answer Quality Criteria:**
  * *Self-contained:* Readable without seeing the original question.
  * *Source-grounded:* Implicitly or explicitly draws from the provided context.
  * *Faithful:* Strictly limits itself to source content (Zero Hallucination).
  * *Relevant:* Directly answers the requested question.
* **CLI Integration:** Must support single query answering (`answer`) and bulk dataset processing (`answer_dataset`) via `python-fire`.
* **Performance UX:** Use `tqdm` for progress bars during long-running batch generations.
* **Generation Speed:** Generation must be as fast as possible. Use low temperature settings (≤0.1), efficient tokenization, and constrain `max_new_tokens` to minimize latency. Leverage `torch.no_grad()` for inference efficiency and use `device_map="auto"` for optimal hardware utilization.

---

## Step 1: Data Models Setup
The answer models correctly inherit and extend the retrieval models from Phase 3 to package the LLM's generated output.

* **The Answer Models (Pydantic):**
  * `MinimalAnswer`: Inherits from `MinimalSearchResults` (contains `question_id`, `question_str`, `retrieved_sources`) and adds the newly generated `answer: str`.
  * `StudentSearchResultsAndAnswer`: Inherits from `StudentSearchResults` (contains `k`) and overrides the `search_results` field to be a `Sequence[MinimalAnswer]`.
* **Location:** Models are defined in `src/model/model_generation.py` and inherit from `src/model/model_retrivial.py`.
* **Validation:** Both models use Pydantic's `model_dump_json()` for serialization.

---

## Step 2: Prompt Engineering & Context Injection
The system uses a strict instruction set to process retrieved chunks without relying on the model's internal pre-trained knowledge.

* **Context Stitching (`_stitch_context`):**
  * Formats each `ChunkSource` with a header: `--- Snippet from {file_path} ---`
  * Concatenates all sources into a single context block with newline separators.
  * Validates total token count against `max_context_length` (default 2000).
  * Truncates tokenized context if it exceeds the limit using `tokenizer.decode()` on truncated token ids.
* **The System Prompt (`_build_prompt`):**
  * Instructs the model to act as an "expert technical assistant".
  * **Critical directive:** "answer the user's question based STRICTLY on the provided context."
  * **Fallback instruction:** If context lacks the answer, respond exactly with `'Information not found in context'`.
  * **Guardrail:** "Do not hallucinate or use external knowledge."
* **Message Format:** Uses Qwen's chat template format: `<|im_start|>system\n...<|im_end|>` blocks for system, user, and assistant roles.
* **User Prompt:** Combines context and question: `Context:\n{context}\n\nQuestion: {query}`

---

## Step 3: Inference Integration
Initialize the model and set up the generation pipeline for optimal speed and efficiency.

* **Model Loading (`__init__`):**
  * Uses `AutoModelForCausalLM.from_pretrained()` with `device_map="auto"` for automatic GPU/CPU placement.
  * Loads `AutoTokenizer.from_pretrained()` with `trust_remote_code=True` for Qwen compatibility.
  * Model is loaded once during initialization and reused across multiple generations to avoid cold-start overhead.
* **Generation Parameters:**
  * `max_new_tokens`: Set to 250 (constrained for speed while allowing sufficient answer length).
  * `temperature`: Set to 0.1 (low value ensures deterministic, faithful answers; sampling only used when `temperature > 0`).
  * `pad_token_id`: Set to `tokenizer.eos_token_id` to prevent padding warnings.
  * `do_sample`: Conditional on `temperature > 0` to optimize inference speed.
* **Inference Execution (`generate_answer`):**
  * Uses `torch.no_grad()` context manager to disable gradient computation and reduce memory overhead.
  * Tokenizes prompt and moves tensors to model device: `tokenizer(..., return_tensors="pt").to(self.model.device)`.
  * Extracts generated tokens only (excluding input): `outputs[0][inputs.input_ids.shape[1]:]`.
  * Decodes output with `skip_special_tokens=True` for clean text.
  * Calls `_parse_response()` to strip template overhead.

---

## Step 4: Single Query Answering (`answer`)
Combines Phase 3 (Retrieval) and Phase 4 (Generation) into a single cohesive pipeline.

* **Method Signature:** `answer(self, query: str, k: int = 5) -> None`
* **Workflow:**
  1. Initialize `Retriever` and call `load_index()` to restore the BM25 index and chunk mapping.
  2. Wrap the query in an `UnansweredQuestion` object.
  3. Call `Retriever.bulk_search([unanswered_query], k)` to retrieve top-$k$ `ChunkSource` objects.
  4. Extract the first (and only) `MinimalSearchResults` from the returned `StudentSearchResults`.
  5. Initialize `Generator` and call `generate_answer(query, retrieved_sources)`.
  6. Package the result into a `MinimalAnswer` object containing `question_id`, `question_str`, `retrieved_sources`, and `answer`.
  7. Serialize and print the result using `model_dump_json(indent=4)`.
* **Error Handling:** All exceptions are caught by the main CLI exception handler in `src/__main__.py`.

---

## Step 5: Batch Processing (`answer_dataset`)
Implements the bulk generation workflow to process previously generated search results datasets.

* **Method Signature:** `answer_dataset(self, student_search_results_path: str, save_directory: str = "data/output/search_results_and_answer") -> None`
* **Dataset Ingestion:**
  * Read the JSON file located at `student_search_results_path` (output from Phase 3's `search_dataset`).
  * Parse it directly into a `StudentSearchResults` object using `model_validate_json()`.
  * Catch `OSError` and raise `GeneraterError` if the file cannot be read.
* **Batch Execution & UX:**
  * Print confirmation of loaded question count.
  * Initialize `Generator` once (model loading is performed once during `__init__` to avoid redundant loading).
  * Iterate through each `MinimalSearchResults` in the dataset using `tqdm` with description `"Generating Answers"`.
  * For each item, call `generator.generate_answer(question_str, retrieved_sources)`.
  * Upgrade each `MinimalSearchResults` to a `MinimalAnswer` by adding the generated answer.
* **Aggregation & Serialization:**
  * Collect all `MinimalAnswer` objects into a list.
  * Create a `StudentSearchResultsAndAnswer` structure with `search_results=answered_results` and `k=answer_obj.k`.
  * Create the output directory if it does not exist.
  * Write the serialized JSON to `save_directory/{original_filename}.json` using `model_dump_json(indent=4)`.
  * Print confirmation of processed question count and output file path.

---

## Step 6: Error Handling & Robustness
The generation pipeline is designed to be robust and fail-safe.

* **Empty Source Handling:** `generate_answer()` checks if `chunks_source` is empty and immediately returns `"Information not found in context"` without attempting inference.
* **Exception Management:** All exceptions during inference are caught in a broad `try-except` block that returns `"Information not found in context"` instead of crashing. This includes:
  * Out-of-Memory (OOM) errors during model loading or generation.
  * Token limit exceptions or malformed tensor issues.
  * File I/O errors during dataset loading (caught separately as `GeneraterError`).
* **CLI Exception Routing:** The main entry point (`src/__main__.py`) catches:
  * `GeneraterError` for generation-specific issues.
  * `RetrieverError` for retrieval pipeline failures.
  * Generic exceptions (OSError, PermissionError, FileNotFoundError, ValueError) and exits with appropriate status codes.
* **Speed Optimization Notes:** All error paths are designed to fail fast without retries or exponential backoff, ensuring minimal latency impact during dataset processing.
