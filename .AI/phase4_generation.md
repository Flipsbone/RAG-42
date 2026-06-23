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

---

## Step 1: Data Models Setup
Ensure your data structures correctly inherit and extend the retrieval models from Phase 3 to package the LLM's generated output.

* **The Answer Models (Pydantic):**
  * `MinimalAnswer`: Inherits from `MinimalSearchResults` (contains `question_id`, `question`, `retrieved_sources`) and adds the newly generated `answer: str`.
  * `StudentSearchResultsAndAnswer`: Inherits from `StudentSearchResults` (contains `k`) and overrides the `search_results` field to be a `List[MinimalAnswer]`.
* **Validation:** These models must be used to validate the final output before serializing it to JSON.

---

## Step 2: Prompt Engineering & Context Injection
Design a strict instruction set for the LLM to process the retrieved chunks without relying on its internal pre-trained knowledge.

* **Context Stitching:** Create a function to format the `retrieved_sources` (list of `MinimalSource`) into a single, clean text block. 
  * Ensure the total length of the stitched context does not exceed the model's token limits (or a defined `max_context_length`).
* **The System Prompt:** Craft a highly constrained system prompt. 
  * *Directive:* Instruct the model to act as a codebase assistant.
  * *Constraint:* Explicitly command the model to say "I don't know" or "Information not found in context" if the retrieved chunks do not contain the answer. 
* **The User Prompt:** Combine the user's `question` with the stitched context block seamlessly.

---

## Step 3: Inference Integration
Initialize the model and set up the generation pipeline. 

* **Model Loading:** Use the `transformers` library (recommended) to load `Qwen/Qwen3-0.6B`. 
  * *Optimization:* Load the model efficiently (e.g., using `device_map="auto"` or appropriate precision settings) to ensure it fits within hardware constraints while maintaining cold start latency under 60 seconds.
* **Text Generation:** Implement the inference call.
  * Pass the formatted prompt to the model.
  * Configure generation parameters (e.g., `max_new_tokens`, `temperature=0.1` or lower to enforce determinism and faithfulness).
  * Clean the output by stripping out the prompt overhead to capture only the generated answer string.

---

## Step 4: Single Query Answering (`answer`)
Combine Phase 3 (Retrieval) and Phase 4 (Generation) into a single cohesive pipeline.

* **Signature:** `answer(self, query: str, k: int = 5)`
* **Workflow:**
  1. Wrap the query in an `UnansweredQuestion`.
  2. Call your Phase 3 retrieval logic to get the top-$k$ `MinimalSource` chunks.
  3. Pass the query and the retrieved chunks to the Context Injection and Inference pipeline.
  4. Package the result into a `MinimalAnswer` object.
  5. Print or return the output as a formatted JSON string using `.model_dump_json(indent=4)`.

---

## Step 5: Batch Processing (`answer_dataset`)
Implement the bulk generation workflow to process previously generated search results datasets.

* **Signature:** `answer_dataset(self, student_search_results_path: str, save_directory: str)`
* **Dataset Ingestion:** * Read the JSON file located at `student_search_results_path`.
  * Validate and parse it directly into a `StudentSearchResults` object using Pydantic.
* **Batch Execution & UX:**
  * Initialize `tqdm` to display a progress bar indicating the number of questions being processed.
  * Iterate through each `MinimalSearchResults` object in the dataset.
  * For each item, inject the pre-retrieved sources and the question into the LLM prompt.
  * Run inference to generate the answer.
  * Upgrade the `MinimalSearchResults` object to a `MinimalAnswer` object.
* **Aggregation & Serialization:**
  * Collect all `MinimalAnswer` objects into a single `StudentSearchResultsAndAnswer` structure.
  * Serialize the final object and write it to `save_directory/<original_filename>.json`.

---

## Step 6: Refinement & Error Handling
Ensure the generation pipeline is robust and fail-safe.

* **Edge Cases:** Handle scenarios where the retrieval system returns an empty list of sources. The system should gracefully generate a fallback answer (e.g., "No context provided") without crashing.
* **Exception Management:** Wrap the inference calls in `try-except` blocks to catch Out-of-Memory (OOM) errors or token limit exceptions, allowing the pipeline to continue processing subsequent dataset questions instead of fatally crashing.
