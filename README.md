*This project has been created as part of the 42 curriculum by advacher.*

# RAG - Retrieving Augmented Generation

## Description
This project implements a local Retrieval-Augmented Generation (RAG) pipeline designed to extract, index, and query the vLLM source folder. The goal is to provide an entirely local, CPU-friendly system that processes source code (`.py`) and documentation (`.md`), indexes it using a sparse BM25 retrieval system, and generates accurate, context-aware JSON responses using a local Ollama model (`qwen3:0.6b`).

## Instructions
**Installation & Setup:**
This project relies on `uv` for package management and uses Python >=3.13 features.
* Install dependencies via `uv`.
  * Ensure Ollama [is installed](https://ollama.com/) and running locally with the `qwen3:0.6b` model pulled  (command:`ollama pull qwen3:0.6b`).

**Execution:**
You can use `make run` to execute the entire RAG pipeline.
The programe provides a command-line interface via Python Fire.  
*(Note: You can use `make install` to synchronize and install dependencies via `uv sync`.)*

To operate the pipeline, you can utilize the Makefile aliases or run the exact underlying commands manually
(command-line interface via Python Fire.):

* **Index the Dataset (`make index`):**
  `uv run python3 -m src index --max_chunk_size=2000 --target_dir=data/raw/vllm-0.10.1`

* **Search for a Single Query (`make search`):**
  `uv run python3 -m src search --query="What are the default values for FP8_MIN and FP8_MAX constants in vLLM's triton_flash_attention module?" --k=1`

* **Search Over a Dataset (`make search_dataset`):**
  `uv run python3 -m src search_dataset --dataset_path data/datasets_public/public/UnansweredQuestions/dataset_docs_public.json --save_directory data/output/search_results --k=5`

* **Evaluate Results (`make evaluate`):** 
  `uv run python3 -m src evaluate --student_search_results_path data/output/search_results/dataset_docs_public.json --dataset_path data/datasets_public/public/AnsweredQuestions/dataset_docs_public.json --k=5 --max_context_length=2000`

* **Generate an Answer for a Query (`make answer`):** 
  `uv run python3 -m src answer --query="what is VLLM ?" --k=1`

* **Answer an Entire Dataset (`make answer_dataset`):** 
  `uv run python3 -m src answer_dataset --student_search_results_path data/output/search_results/dataset_docs_public.json --save_directory data/output/search_results_and_answer`

* **Run Moulinette Evaluation (`make moulinette`):**
  `./moulinette_pkg/moulinette-ubuntu list_valid_questions data/output/search_results/dataset_docs_public.json data/datasets_public/public/AnsweredQuestions/dataset_docs_public.json --k 5`

## System Architecture
The RAG pipeline follows a distinct linear flow to process and answer queries: `raw files -> indexing/chunking -> BM25 retrieval -> Context Stitching -> Ollama generation -> JSON output`.

* **Ingestion & Indexing:** `src/indexing/indexation.py` discovers files and launches indexing. `src/indexing/chunking.py` splits the files using `PythonChunker` and `MarkdownChunker`.
* **Retrieval:** `src/retrieval/retriever.py` saves, loads, and queries the BM25 index.
* **Generation:** `src/generation/generator.py` formats retrieved chunks and calls Ollama.
* **Data Models:** The ingestion layer uses Pydantic models like `MinimalSource` and `ChunkSource`, while retrieval output validates through `StudentSearchResults` and `MinimalSearchResults`.
* **CLI:** `src/cli/command_line_interface.py` exposes the core commands. `fire.Fire(RagCLI)` is executed from `src/__main__.py`.

## Chunking Strategy
The chunking system applies different strategies based on file extensions, capped at a `max_chunk_size` of 2000 characters. The current implementation uses zero overlap and preserves contiguous character ranges.
* **Python Code (`.py`):** The `PythonChunker` utilizes `ast.parse()` to analyze the source text, iterating through module-level nodes. In this Abstract Syntax Tree (AST) context, "class children" (nested `def` methods and attributes) are wrapped within a `NodeContext`. 
  * **Context Preservation:** Because the chunker splits code to adhere to strict character limits, isolated methods would normally lose their structural identity. The `NodeContext` solves this by explicitly memorizing the parent class name. 
  * **Metadata Injection:** By prepending specific descriptive metadata labels to every chunk (e.g., `Class: ServeurOpenAI - Method: configurer_port`), I ensure the LLM always understands the exact architectural placement adding this code snippet.

* **Markdown (`.md`):** `MarkdownChunker` uses `markdown-it-py` tokens to split the document into section like title `heading_open`. It preserves section context while building chunks.
  * **Context Preservation:**: Maintains a `current_header` state. It assigns the current section title as the `context_name` for all subsequent text blocks until a new header is encountered. If no header exists, it defaults to `Section: Introduction`..
  * **Metadata Injection**: Every chunk is injected with its parent section title and file path (e.g., `Section: Configuration | File: docs/guide.md`). This provides explicit text for the BM25 sparse retriever, allowing it to differentiate between similarly phrased content across the repository.
  * **Overflow Handling**: If a section surpasses the `max_chunk_size`, the `ChunkBuilder` splits it into several smaller pieces. Each new chunk inherits the original context_name, guaranteeing the LLM always understands the broader context during retrieval.

## Retrieval Method
The retrieval method leverages the `bm25s` library to construct a sparse, CPU-optimized inverted index. 
* Tokenization uses `bm25s.tokenize()` with `lower=True`, `stopwords="en"`, and `stemmer=Stemmer.Stemmer("english")`.
* During a query, the same tokenization settings are applied. 
* Document ids are converted to `int` and mapped back to `ChunkSource` objects for search results, preserving `file_path` and `text`.

## Performance Analysis

We measured and optimized `recall@k` metric (specifically evaluating the top 5 retrieved results). The required 80% (docs) and 50% (code) thresholds with `recall@5`.

### Iterative Recall Progression `recall@1`

| Optimization Phase | Recall (Code) | Recall (Docs) | Impact & Notes |
| :--- | :--- | :--- | :--- |
| **Baseline** | 21% | 48% | Basic BM25 retrieval with naive chunking. |
| **Intelligent Chunking** | 34% | 55% | Implementing logical cuts and sliding window overlap prevented critical context from being split across chunks. |
| **Split Indexes** | 31% | 41% | *Regression.* Separating code and doc into two distinct BM25 indexes harmed term-frequency statistics. Reverted to a unified index. |
| **Metadata Injection** | 45% | 58% | Prepending the file path directly into the chunk context significantly boosted exact-match routing for the sparse retriever. |
| **LLM Query Expansion** | 47% | 62% | Using `Qwen3-0.6B` to generate synonyms bridged the vocabulary gap between user queries and technical source code. |
| **Extended File Discovery** | 45% | 60% | Adding a fallback chunker for non-standard files (e.g., `CMakeLists.txt`). While the expanded search space introduced slight noise (dropping strict top-1 scores by ~5%), it drastically improved overall top-5 retrieval, allowing the `k=5` recall to peak at 88% on doc. |

### Resultat final `recall@5`
| Final result | Recall (Code) | Recall (Docs) | Impact & Notes |
| :--- | :--- | :--- | :--- |
|  | **`72%`** | **`86%`** | Using 5 or 10 sources is the most effective approach, retrieving too much information reduces the overall quality.|


### System Performance & Bottlenecks

* **Indexing Throughput:** The ingestion pipeline processes the entire repository, applies the `ChunkBuilder` on strategies, and serializes the BM25 index well within the 5-minute maximum constraint.
* **Warm Retrieval Latency:** By implementing a disk-persistent JSON query cache (`query_cache.json`), the system bypasses the LLM query expansion and BM25 tokenization for repeated queries. This drops warm retrieval times to near-zero, easily meeting the throughput requirement for batch processing 1000 questions.
* **Query Expansion Overhead:** Deploying a local `Qwen3-0.6B` model for synonym generation incurs an initial cold-start latency. To optimize efficiency, the system prompt was strictly constrained and the temperature lowered to 0.3. Also a variable `use_query_expansion=False` is indroduce inside the file command_line_interface.py to have the choice to use or not this feature . 
* **Metadata vs. Semantic Search:** As demonstrated by the metrics progression, explicitly injecting metadata (file paths and section headers) into the chunk text provided the largest single jump in performance for the sparse BM25 retriever, proving to be a highly effective lightweight alternative to dense vector embeddings.


## Design Decisions
* **Pydantic for Data Flow:** Models are strictly defined and serialized with Pydantic models and written as JSON. 
* **CPU-Oriented & Local-First:** The code is CPU-oriented, uses sparse BM25 indexing, and relies on a local Ollama client (`qwen3:0.6b` at temperature 0.3).
* **Context Stitching:** `_stitch_context()` This function is the pivot of the augmentation pipeline. It formats retrieved chunks as `--- Snippet from {file_path} ---` followed by the text. providing the LLM with explicit source identity to improve grounding and minimize hallucinations. It also enforces a strict `max_char_length` to ensure the prompt remains within the model's context window.  
**Hash Verification (Integrity):** To ensure data integrity, every critical file (index, chunk mappings, and query cache) is accompanied by a `hash file`. Before loading, the system verifies the hash of the data file against its corresponding hash file to detect unauthorized modifications or data corruption.


## Challenges Faced
* **Missing Files:** Only files with a suffix present in `self.chunkers` (`.py` and `.md`) are kept; exceptions are recorded in `failed_logs` and trigger an `IndexationError` if not empty.
* **Context Loss in Code Segments:** Standard splits lose class associations. The solution was using AST to associate an AST node with an optional parent class name via `NodeContext`.
* **Context Window Limits:** The generator requires truncation. `_stitch_context()` safely stops adding chunk contents at the maximum character bound (`max_char_length`) to avoid failures.
* **Reducing Hallucinations:** `Context Stitching`: As the pivot of my augmentation pipeline, _stitch_context() explicitly labels retrieved text with its source file (--- Snippet from {file_path} ---). This grounds the LLM to prevent fabricated answers, i also applying a strict max_char_length to guarantee the final prompt fits within the model's context limits.
* **Controlling Answer Length:** I tried to make the generated answers shorter and more direct by changing the instructions and settings, like num_predict. However, this did not work very well. When I forced the small qwen3:0.6b model to be brief, it often stopped in the middle of a sentence or missed important technical details. This showed that it is difficult to get short answers that still have all the right information.  

## Bonus Features Implementation

To maximize the efficiency, reliability, and accuracy of the Retrieval-Augmented Generation (RAG) pipeline, several advanced features were implemented beyond the mandatory requirements.

### 1. Query Expansion (Vocabulary Bridging)
Users rarely phrase questions using the exact vocabulary found in the technical source code or documentation. To bridge this gap, the pipeline intercepts queries before BM25 tokenization and uses the local `qwen3:0.6b` model to generate technical synonyms. Use the variable `use_query_expansion=True` in the file command_line_interface.py

### 2. Disk-Persistent Result Caching
To optimize warm retrieval throughput and avoid unnecessary LLM inferences for duplicate questions, a caching mechanism was implemented. the system saves a `query_cache.json` directly to the disk . Thanks to that the program bypasses both the LLM query expansion and BM25 tokenization phases. 

### 3. Hash Verification for Data Integrity
To ensure the integrity of the data pipeline a security layer using hash verification was introduced. Every critical file (such as the BM25 index, chunk mappings, and the query cache) is accompanied by a `.hash` file.

### 4. Advanced BM25 Tokenization (Stemming)
To improve the semantic matching capabilities of the sparse retriever, the system enhances the default indexing and tokenization implementation. An English stemmer (`Stemmer.Stemmer("english")`) is applied during the `bm25s.tokenize()` This reduces words to their root forms (e.g., mapping "configuring" and "configured" to the same base token).


## Example Usage
To query the indexed files for specific knowledge and generate a response:
* `python -m src answer --question="How to configure OpenAI server?"`

## Resources

* **Ollama :** [Ollama - QuickStart](https://docs.ollama.com/quickstart)

* **Langchain**: [RAG From Scratch](https://www.youtube.com/watch?v=wd7TZ4w1mSw&list=PLfaIDFEXuae2LXbO1_PKyVJiQ23ZztA0x)

* **AI Usage:** AI was utilized during the development lifecycle to generate structural documentation, refine chunking logic based on AST parsing, optimize prompt engineering for the generation phase, and formulate the README file.


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