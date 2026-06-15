# Phase 2: Knowledge Base Ingestion System Roadmap

## Overview & Constraints
This phase focuses on parsing the vLLM repository, chunking the files, and creating a searchable index. Given the hardware constraints (CPU only) and strict performance requirements, this roadmap avoids heavy neural embeddings and leverages BM25 for fast, sparse vector indexing. 

**Key Constraints:**
* **Indexing Time:** Maximum 5 minutes.
* **Chunk Size:** Maximum 2000 characters, configurable via CLI argument.
* **Chunking Types:** Distinct strategies for Python code and Text/Markdown.
* **Data Models:** Must use `pydantic` for `MinimalSource` tracking (`file_path`, `first_character_index`, `last_character_index`).
* **Package Management:** The project must be managed using `uv`.
* **Performance Opt-in:** Zero chunk overlap to minimize token usage and database size.

---

## Step 1: File Discovery and Loading
The first requirement is to read and process all target files from the attached vLLM repository.

* **Define Target Extensions:** Target primarily `.py` and `.md` files.
* **Traverse the Directory:** Use `pathlib.Path.rglob` to recursively walk the extracted vLLM directory and collect the file paths.
* **Read File Contents:** Open each file (using context managers), read its contents as a string, and store it along with its path.

---

## Step 2: Architecture & Data Models
To keep the codebase clean, modular, and type-safe, separate your data structures from your chunking logic.

* **The Data Model (Pydantic):** Use Pydantic's `BaseModel` to define a `MinimalSource` object. This model must strictly track the `file_path`, `first_character_index`, and `last_character_index`. Using Pydantic makes validation and serialization to disk trivial.
* **The Chunker Protocol:** Define a structural Protocol (e.g., `ChunkerStrategy`) enforcing a common interface. Every chunker must implement a `.chunk(text, file_path, max_chunk_size)` method that returns a list of your chunk objects.
* **The Strategy Dictionary:** Centralize your strategies by mapping extensions to their respective implementations:
    ```python
    chunkers: dict[str, ChunkerStrategy] = {
        ".py": PythonChunker(),
        ".md": MarkdownChunker()
    }
    ```

---

## Step 3: Intelligent Chunking Strategies
You must implement different chunking strategies for different file types while strictly enforcing the configurable maximum size without losing any data. **Do not use chunk overlap** in any strategy, as it negatively impacts performance metrics.

### 3.1 Python Code Chunking (`.py`)
Do not use simple character splitting for code. Use Python's built-in `ast` module to parse the code into logical blocks and route them efficiently.

1.  **Generate the AST:** Read the raw Python file as a string (retaining all original formatting) and pass it to `ast.parse()`. This builds a structural tree mapped out as distinct nodes without executing code.
2.  **Segment Routing (`process_segment`):** Extract text blocks using the AST line numbers. Pass these blocks to a router that evaluates size limits (`<= max_chunk_size`). If a block fits, append it. If not, seal the current chunk and evaluate again.
3.  **Line-by-Line Fallback (`process_lines`):** If a single AST node is larger than the maximum chunk size, delegate it to a specialized function that processes the block line-by-line (`splitlines(keepends=True)`) to preserve semantic meaning where possible.
4.  **Hard Splitting without Truncation:** If a single line of code (e.g., a massive base64 string or long comment) exceeds the limit natively, use a `while` loop to enforce a hard split exactly at the character limit. Do not truncate or discard any remaining text.
5.  **Contextual Continuation Headers:** Because overlap is disabled, maintain semantic continuity by injecting a header (e.g., `# [Continued: function_name]\n`) at the start of any new chunk that inherits an over-limit block.
6.  **Finalize Code (`process_trailing_code`):** Process any remaining text or trailing comments left after AST traversal, seal the final chunk, and ensure absolute precision for `first_character_index` and `last_character_index`.

### 3.2 Markdown/Text Chunking (`.md`)
* **Langchain Splitters:** Utilize Langchain's `RecursiveCharacterTextSplitter`. It is designed to respect Markdown structure (headers, paragraphs, lists) and keeps chunks semantically coherent.
* **Configuration:** Set the `chunk_size` to your CLI parameter. To align with the strict performance requirements established in the Python chunker, set `chunk_overlap=0`. Configure it to return string indices so you can accurately populate the Pydantic fields.

---

## Step 4: Indexing with BM25s
You must create a searchable index within the 5-minute time limit. `bm25s` is highly optimized for CPU execution.

* **Prepare the Corpus:** Extract the raw text from all your validated chunk objects into a single list of strings.
* **Custom Code Tokenization:** Standard tokenization often fails on code. Write a custom tokenization function that splits code-specific formats (CamelCase, snake_case) into individual words before passing them to the indexer to maximize retrieval accuracy.
* **Build the Index:** Pass your tokenized corpus to the `bm25s` indexer to build the inverted sparse index.

---

## Step 5: Serialization and Storage
To achieve a cold start latency of under 60 seconds, the system must load pre-computed assets rather than re-indexing.

* **Save the Index:** Use `bm25s` built-in methods to save the compiled index to disk (e.g., `data/processed/bm25_index`).
* **Save the Metadata:** Serialize your list of Pydantic chunk objects to a JSON file (e.g., `data/processed/chunks`). When a query retrieves a BM25 document ID later, you will use this file to map the ID back to the specific `MinimalSource` metadata.

---

## Step 6: Command-Line Interface Integration
The pipeline must be accessible via a CLI using Python Fire.

* **The Command:** Expose an `index` command that handles the full ingestion pipeline.
* **Arguments:** Ensure it accepts `--max_chunk_size` (defaulting to 2000).
* **Progress Tracking:** Wrap your file processing and chunking loops with `tqdm` to provide visual feedback for long-running operations.