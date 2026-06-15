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
* **Architecture Standard:** Python 3.10+ strictly utilizing Structural Pattern Matching and the Composition Pattern (DRY principle).

---

## Step 1: File Discovery and Loading
The first requirement is to read and process all target files from the attached vLLM repository.

* **Define Target Extensions:** Target primarily `.py` and `.md` files.
* **Traverse the Directory:** Use `pathlib.Path.rglob` to recursively walk the extracted vLLM directory and collect the file paths.
* **Read File Contents:** Open each file (using context managers), read its contents as a string, and store it along with its path.

---

## Step 2: Architecture & Data Models
To keep the codebase clean, modular, and type-safe, separate your data structures from your chunking logic using the **Composition Pattern**.

* **The Data Model (Pydantic):** Use Pydantic's `BaseModel` to define a `MinimalSource` object. This model must strictly track the `file_path`, `first_character_index`, and `last_character_index`. Using Pydantic makes validation and serialization to disk trivial.
* **The Chunker Protocol:** Define a structural Protocol (e.g., `ChunkerStrategy`) enforcing a common interface. Every chunker must implement a `.chunk(text, file_path, max_chunk_size)` method that returns a list of your chunk objects.
* **The ChunkBuilder (Composition):** Instead of duplicating text accumulation logic in every chunker, implement a standalone `ChunkBuilder` class. This builder manages the state (`_current_chunk_text`, `_current_start_char_idx`), handles strict length calculations, and safely applies continuation headers. 
* **The Strategy Dictionary:** Centralize your strategies by mapping extensions to their respective router implementations:
    ```python
    chunkers: dict[str, ChunkerStrategy] = {
        ".py": PythonChunker(),
        ".md": MarkdownChunker()
    }
    ```

---

## Step 3: Intelligent Chunking Strategies
You must implement different chunking strategies acting as **Semantic Routers**. The chunkers analyze the file structure and delegate the text assembly to the `ChunkBuilder`. **Do not use chunk overlap**.

### 3.1 Python Code Chunking (`.py`)
Do not use simple character splitting for code. Use Python's built-in `ast` module combined with **Structural Pattern Matching** (Python 3.10+).

1.  **Generate the AST:** Read the raw Python file as a string (retaining all original formatting) and pass it to `ast.parse()`. 
2.  **Pattern Matching Routing:** Iterate through `tree.body` and use `match node:` to intelligently identify structural blocks:
    * `case ast.FunctionDef(name=func_name) | ast.AsyncFunctionDef(...)`: Extract function names.
    * `case ast.ClassDef(name=class_name)`: Extract class names.
    * `case _`: Fallback to module-level scope.
3.  **Delegated Assembly (`process_segment`):** Pass the raw text block and the extracted context name to the `ChunkBuilder`. The builder handles the math (size limits `<= max_chunk_size`).
4.  **Line-by-Line Fallback & Hard Splitting:** If a single AST node is larger than the maximum chunk size, the `ChunkBuilder` processes the block line-by-line (`splitlines(keepends=True)`), employing a `while` loop to enforce a hard split without truncation if a single line exceeds the limit natively.
5.  **Contextual Continuation Headers:** The `ChunkBuilder` automatically injects headers (e.g., `# [Continued: Function: func_name]
`) when a semantic block spans multiple chunks.
6.  **Finalize Code:** Pass trailing text to the builder and execute `seal_chunk()` to finalize exact `first_character_index` and `last_character_index` mappings.

### 3.2 Markdown/Text Chunking (`.md`)
* **AST Parsing with `markdown-it-py`:** Generate an Abstract Syntax Tree (AST) using `markdown-it-py`. This provides a strict list of tokens, preventing context errors.
* **Semantic Routing via Pattern Matching:** Iterate through the token stream and use `match token.type:` to capture structural headings (e.g., updating the context when encountering `heading_open` followed by an `inline` token).
* **Gap and Block Capture:** Leverage the token's `.map` attribute to calculate line intervals. Capture both mapped blocks and unmapped gaps (like spacing or separators), and delegate them to the `ChunkBuilder`.
* **Unified Logic:** By using the same `ChunkBuilder` as the Python chunker, the Markdown chunker guarantees the same strict zero-overlap compliance and absolute character index accuracy with zero duplicated logic.

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