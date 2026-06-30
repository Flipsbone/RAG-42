*This project has been created as part of the 42 curriculum by advacher.*

# RAG - Retrieving Augmented Generation

## Description
This project implements a local Retrieval-Augmented Generation (RAG) pipeline designed to extract, index, and query the vLLM source folder. The goal is to provide an entirely local, CPU-friendly system that processes source code (`.py`) and documentation (`.md`), indexes it using a sparse BM25 retrieval system, and generates accurate, context-aware JSON responses using a local Ollama model (`qwen3:0.6b`).

## Instructions
**Installation & Setup:**
This project relies on `uv` for package management and uses Python 3.10 features.
* Install dependencies via `uv`.
* Ensure Ollama is installed and running locally with the `qwen3:0.6b` model pulled.

**Execution:**
The application provides a command-line interface via Python Fire.
**Execution:**
*(Note: You can use `make install` to synchronize and install dependencies via `uv sync`.)*

To operate the pipeline, you can utilize the Makefile aliases or run the exact underlying commands manually
(command-line interface via Python Fire.):

* **Index the Dataset (`make run`):**
  `uv run python3 -m src index --max_chunk_size=2000 --target_dir=data/raw/vllm-0.10.1`

* **Search for a Single Query (`make search`):**
  `uv run python3 -m src search --query="What are the default values for FP8_MIN and FP8_MAX constants in vLLM's triton_flash_attention module?" --k=1`

* **Search Over a Dataset (`make search_dataset`):**
  `uv run python3 -m src search_dataset --dataset_path datasets_public/public/UnansweredQuestions/dataset_docs_public.json --save_directory data/output/search_results --k=5`

* **Evaluate Results (`make evaluate`):** 
  `uv run python3 -m src evaluate --student_search_results_path data/output/search_results/dataset_docs_public.json --dataset_path datasets_public/public/AnsweredQuestions/dataset_docs_public.json --k=5 --max_context_length=2000`

* **Generate an Answer for a Query (`make answer`):** 
  `uv run python3 -m src answer --query="my question is" --k=1`

* **Answer an Entire Dataset (`make answer_dataset`):** 
  `uv run python3 -m src answer_dataset --student_search_results_path data/output/search_results/dataset_docs_public.json --save_directory data/output/search_results_and_answer`

* **Run Moulinette Evaluation (`make moulinette`):**
  `./moulinette_pkg/moulinette-ubuntu list_valid_questions data/output/search_results/dataset_docs_public.json datasets_public/public/AnsweredQuestions/dataset_docs_public.json --k 5`

## System Architecture
The RAG pipeline follows a distinct linear flow to process and answer queries: `raw files -> indexing/chunking -> BM25 retrieval -> context stitching -> Ollama generation -> JSON output`.

* **Ingestion & Indexing:** `src/indexing/indexation.py` discovers files and launches indexing. `src/indexing/chunking.py` splits the files using `PythonChunker` and `MarkdownChunker`.
* **Retrieval:** `src/retrieval/retriever.py` saves, loads, and queries the BM25 index.
* **Generation:** `src/generation/generator.py` formats retrieved chunks and calls Ollama.
* **Data Models:** The ingestion layer uses Pydantic models like `MinimalSource` and `ChunkSource`, while retrieval output validates through `StudentSearchResults` and `MinimalSearchResults`.
* **CLI:** `src/cli/command_line_interface.py` exposes the core commands. `fire.Fire(RagCLI)` is executed from `src/__main__.py`.

## Chunking Strategy
The chunking system applies different strategies based on file extensions, capped at a `max_chunk_size` of 2000 characters. The current implementation uses zero overlap and preserves contiguous character ranges.
* **Python Code (`.py`):** `PythonChunker` parses source text with `ast.parse()` and iterates over module-level nodes. Class children are wrapped in `NodeContext` to keep the parent class name, emitting context labels such as `Class: ... - Method: ...`.
* **Markdown (`.md`):** `MarkdownChunker` uses `markdown-it-py` tokens to split the document into section-aware chunks. It preserves section context while building chunks, starting with a default `Section: Introduction`.

## Retrieval Method
The retrieval method leverages the `bm25s` library to construct a sparse, CPU-optimized inverted index. 
* Tokenization uses `bm25s.tokenize()` with `lower=True`, `stopwords="en"`, and `stemmer=Stemmer.Stemmer("english")`.
* During a query, the same tokenization settings are applied. 
* Document ids are converted to `int` and mapped back to `ChunkSource` objects for search results, preserving `file_path` and `text`.

## Performance Analysis
Through iterative refinements, the recall system observed significant improvements:
* Refining the chunking cuts directly improved code chunk indexation (21% -> 34%) and documentation chunk indexation (48% -> 55%).
* Embedding file paths directly into the chunk context caused a substantial leap in recall (Code: 34% -> 45%, Doc: 55% -> 58%).
* Implementing an LLM-based query expansion mechanism bumped up the scores (Code: 45% -> 47%, Doc: 58% -> 62%).
* Widening the retrieval net to `k=5` proved highly effective, culminating in a strong peak score of 86 compared to 82.

## Design Decisions
* **Pydantic for Data Flow:** Models are strictly defined and serialized with Pydantic models and written as JSON. 
* **CPU-Oriented & Local-First:** The code is CPU-oriented, uses sparse BM25 indexing, and relies on a local Ollama client (`qwen3:0.6b` at temperature 0.1).
* **Context Stitching:** `_stitch_context()` formats each chunk as `--- Snippet from {file_path} ---` followed by the text. It truncates the final context string when it exceeds `max_char_length`.
* **Python 3.10 Structural Pattern Matching:** `match node:` is used to route `ast.FunctionDef`, `ast.AsyncFunctionDef`, and `ast.ClassDef` inside the Python chunker.

## Challenges Faced
* **Missing Files:** Only files with a suffix present in `self.chunkers` (`.py` and `.md`) are kept; exceptions are recorded in `failed_logs` and trigger an `IndexationError` if not empty.
* **Context Loss in Code Segments:** Standard splits lose class associations. The solution was using AST to associate an AST node with an optional parent class name via `NodeContext`.
* **Context Window Limits:** The generator requires truncation. `_stitch_context()` safely stops adding chunk contents at the maximum character bound (`max_char_length`) to avoid failures.

## Example Usage
To query the indexed files for specific knowledge and generate a response:
* `python -m src answer --question="How does the ChunkBuilder work?"`

## Resources
* Documentation for `bm25s`, Ollama, and `uv`.
* **AI Usage:** Artificial Intelligence was utilized during the development lifecycle to generate structural documentation, refine chunking logic based on AST parsing, optimize prompt engineering for the generation phase, and formulate the README file.


## Project Architecture
Below is a visual representation of how the different components of **RAG** interact:
```mermaid
graph TD
    %% Node Styling Definitions
    classDef input_data fill:#eceff1,stroke:#607d8b,stroke-width:2px,color:#333;
    classDef indexing_phase fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#333;
    classDef retrieval_phase fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#333;
    classDef generation_phase fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#333;
    classDef cli_phase fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#333;

    %% Input Layer
    subgraph InputData ["Input Data"]
        A["<b>Raw Files</b><br/>.py & .md"]
    end
    class A input_data;

    %% Phase 2: Indexing & Ingestion
    subgraph Phase2 ["Phase 2: Ingestion & Indexing"]
        B["<b>Indexation Module</b>"]
        C1["<b>PythonChunker</b><br/>AST Parsing"]
        C2["<b>MarkdownChunker</b><br/>Header Parsing"]
        D["<b>ChunkBuilder</b>"]
        E[("<b>BM25 Index</b>")]
        F[("<b>Chunk Mapping JSON</b>")]

        A -->|"Discovers files"| B
        B -->|".py files"| C1
        B -->|".md files"| C2
        C1 -->|"NodeContext"| D
        C2 -->|"Section limits"| D
        D -->|"Tokenizes text"| E
        D -->|"Serializes metadata"| F
    end
    class B,C1,C2,D,E,F indexing_phase;

    %% Phase 3: Retrieval
    subgraph Phase3 ["Phase 3: Retrieval"]
        G["<b>Retriever Module</b>"]
        H["<b>User Query / Dataset</b>"]
        I["<b>Query Tokenization</b>"]

        H --> G
        G --> I
        I -->|"Search"| E
        E -->|"Document IDs"| F
        F -->|"StudentSearchResults"| G
    end
    class G,H,I retrieval_phase;

    %% Phase 4: Generation
    subgraph Phase4 ["Phase 4: Answer Generation"]
        J["<b>Generator Module</b>"]
        K["<b>Context Stitching</b>"]
        L(("<b>Ollama Model</b><br/>qwen3:0.6b"))
        M["<b>JSON Output</b><br/>MinimalAnswer"]

        G -->|"Top-k Chunks"| J
        J --> K
        K -->|"Prompt + Snippets"| L
        L --> M
    end
    class J,K,L,M generation_phase;

    %% CLI 
    subgraph CLI ["CLI Integration (RagCLI)"]
        N["<b>python-fire CLI</b>"]
        N -.->|"index"| B
        N -.->|"search / search_dataset"| G
        N -.->|"answer / answer_dataset"| J
    end
    class N cli_phase;