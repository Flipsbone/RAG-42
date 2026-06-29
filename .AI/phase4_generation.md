# Phase 4: Answer Generation System

## Overview
This phase turns retrieval results into a final answer using the current implementation in src/generation/generator.py. The generator is Ollama-based, and the CLI exposes both single-query and batch generation through RagCLI.answer() and RagCLI.answer_dataset().

## Answer Models
The generation models extend the retrieval models from src/model/model_retrivial.py.

* MinimalAnswer extends MinimalSearchResults with an answer: str field.
* StudentSearchResultsAndAnswer extends StudentSearchResults and replaces search_results with a sequence of MinimalAnswer objects.
* Both models are serialized with model_dump_json(indent=4).

## Generator Behavior
The current Generator class loads an Ollama client in __init__ and reuses it across requests.

* The default model name is qwen3:0.6b.
* temperature is set to 0.1.
* max_char_length is used as the context length limit.
* _stitch_context() formats each retrieved chunk as --- Snippet from {file_path} --- followed by the chunk text.
* _stitch_context() truncates the final context string when it exceeds max_char_length.
* _build_prompt() returns a short system instruction that forces the answer to rely only on the provided context.
* generate_answer() returns the trimmed Ollama response content.
* Any generation failure raises GeneratorError.

## Single Query Flow
RagCLI.answer() combines retrieval and generation.

1. Load the BM25 index with Retriever.load_index().
2. Wrap the input in UnansweredQuestion.
3. Retrieve the top k chunks with Retriever.bulk_search([unanswered_query], k).
4. Take the first MinimalSearchResults result.
5. Call Generator.generate_answer(query, retrieved_sources).
6. Build a MinimalAnswer and print model_dump_json(indent=4).

## Batch Flow
RagCLI.answer_dataset() processes a JSON file produced by search.

* The input file is parsed with StudentSearchResults.model_validate_json().
* The generator is instantiated once and reused for every question.
* Each result is wrapped into MinimalAnswer after generation.
* The final output is written to data/output/search_results_and_answer by default.

## Robustness
* If chunks_source is empty, generate_answer() returns Information not found in context immediately.
* Any exception during generation is wrapped in GeneratorError.
* Dataset loading issues are also wrapped in GeneratorError by the CLI.
