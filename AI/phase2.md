# Phase 2: Knowledge Base Ingestion System Roadmap

## Overview & Constraints
This phase focuses on parsing the vLLM repository, chunking the files, and creating a searchable index. Given the hardware constraints (CPU only) and strict performance requirements, this roadmap avoids heavy neural embeddings and leverages BM25 for fast, sparse vector indexing.

**Key Constraints:**
* **Indexing Time:** Maximum 5 minutes.
* **Chunk Size:** Maximum 2000 characters, configurable via CLI argument.
* **Chunking Types:** Distinct strategies for Python code and Text/Markdown.
* **Data Models:** Must use `pydantic` for `MinimalSource` and extend it to `ChunkSource` tracking text and context.
* **Package Management:** The project must be managed using `uv`.
* **Performance Opt-in:** Zero chunk overlap to minimize token usage and database size.
* **Architecture Standard:** Python 3.10+ strictly utilizing Structural Pattern Matching and the Composition Pattern (DRY principle).

---

## Step 1: File Discovery and Loading
The first requirement is to read and process all target files from the attached vLLM repository.

* **Define Target Extensions:** Target primarily `.py` and `.md` files.
* **Traverse the Directory:** Use `pathlib.Path.rglob` in the `Indexation` class to recursively walk the extracted directory and collect valid file paths.
* **Read File Contents:** Open each file, read its contents as a string (`utf-8`), and delegate processing to the appropriate strategy.

---

## Step 2: Architecture & Data Models
To keep the codebase clean, modular, and type-safe, separate your data structures from your chunking logic using the **Composition Pattern**.

* **The Data Model (Pydantic):** * `MinimalSource`: Strictly tracks the `file_path`, `first_character_index`, and `last_character_index`.
  * `ChunkSource`: Inherits from `MinimalSource` and adds the `text` content and its specific `context_name` (e.g., function or class name).
* **The Chunker Protocol:** Define a structural Protocol (`ChunkerStrategy`) enforcing a common interface: `.chunk(text, file_path, max_chunk_size)` returning a list of `ChunkSource` objects.
* **The ChunkBuilder (Composition):** A standalone class that manages state (`_current_chunk_text`, `_current_start_char_idx`, `_context_name`), handles strict length calculations natively, and safely seals chunks into data objects.
* **The Strategy Dictionary:** Centralize routers by mapping extensions:
    ```python
    chunkers: dict[str, ChunkerStrategy] = {
        ".py": PythonChunker(),
        ".md": MarkdownChunker()
    }
    ```

---

## Step 3: Intelligent Chunking Strategies
Implement different chunking strategies acting as **Semantic Routers**. The chunkers analyze file structure and delegate text assembly to the `ChunkBuilder` with zero chunk overlap.

### 3.1 Python Code Chunking (`.py`)
Use Python's built-in `ast` module combined with **Structural Pattern Matching**.

1.  **Generate the AST:** Pass the raw text string to `ast.parse()`.
2.  **Pattern Matching Routing:** Iterate through `tree.body` and use `match node:` to intelligently identify structural blocks:
    * `case ast.FunctionDef(name=func_name) | ast.AsyncFunctionDef(...)`: Set `context_name` to "Function: [name]".
    * `case ast.ClassDef(name=class_name)`: Set `context_name` to "Class: [name]".
    * `case _`: Fallback to "Module level".
3.  **Delegated Assembly (`process_segment`):** Pass the raw text block and the extracted context name to the `ChunkBuilder`. 
4.  **Line-by-Line Fallback & Hard Splitting:** If a block is larger than the maximum chunk size, the `ChunkBuilder` processes the block line-by-line natively without truncation.
5.  **Metadata Injection over Hardcoding:** Instead of injecting textual headers into the code chunks, the builder directly saves the current structural location to the `context_name` attribute of the `ChunkSource` object.
6.  **Finalize Code:** Pass trailing text to the builder and execute `seal_chunk()`.

### 3.2 Markdown/Text Chunking (`.md`)
* **AST Parsing with `markdown-it-py`:** Generate an Abstract Syntax Tree to provide a strict list of tokens.
* **Semantic Routing via Pattern Matching:** Iterate through the tokens to capture structural headings (updating the context when encountering `heading_open`).
* **Block Capture:** Leverage the token's `.map` attribute to calculate line intervals for valid blocks (e.g., `nesting == 1` or `fence`), delegating them to the `ChunkBuilder`.
* **Finalize Document:** Execute `process_tail_and_seal()` to cleanly capture trailing text and finalize the chunks.

---

## Step 4: Indexing with BM25s
Create a searchable index within the time limit using `bm25s` via the `Retriver` class.

* **Prepare the Expanded Corpus:** Extract the text from all `ChunkSource` objects. To maximize searchability, concatenate the `context_name` with the chunk's `text` (e.g., `chunk.context_name + chunk.text`).
* **Format and Humanize Text:** Pass the text through a formatting regex step (`_format_text`) to explicitly insert spaces between `camelCase` letters and replace `snake_case` underscores.
* **Full Tokenization Implementation:** Utilize `bm25s.tokenize()` with an optimal parameter payload:
    * `lower=True` and `stopwords="en"` to strip out noise.
    * `stemmer=Stemmer.Stemmer("english")` via `PyStemmer` for high-performance C-based word rooting.
    * `return_ids=True` to substitute words with integer IDs, significantly accelerating search.
    * `show_progress=True` for visual CLI feedback.
* **Build the Index:** Pass the tokenized corpus into `retriever.index()`.

---

## Step 5: Serialization and Storage
Achieve a cold start latency of under 60 seconds by saving pre-computed assets.

* **Save the Compiled Index:** Use the `retriever.save("./data/processed/bm25_index")` method to dump the fully structured search index and vocabulary to disk. The use of `return_ids=True` guarantees the index remains compressed and fast to load.
* *(Future capability)*: Consider serializing the raw `ChunkSource` Pydantic models to JSON to easily map retrieved BM25 IDs back to their full metadata and original text during the generation phase.

---

## Step 6: Command-Line Interface Integration
The pipeline is accessible via a custom CLI structure (`RagCLI`).

* **The Command:** Expose an `index()` method that orchestrates the `Indexation` and `Retriver` classes.
* **Arguments:** Accept configurations like `target_dir` (default: `"vllm-0.10.1"`) and `max_chunk_size` (default: `2000`).
* **Progress Tracking:** Utilize `tqdm` within the ingestion loop to provide clear visual loading bars while the repository is being read and chunked.