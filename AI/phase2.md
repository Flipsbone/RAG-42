# Phase 2: Knowledge Base Ingestion System Roadmap

## Overview & Constraints
This phase focuses on parsing the vLLM repository, chunking the files, and creating a searchable index. Given the hardware constraints (CPU only) and strict performance requirements, this roadmap avoids heavy neural embeddings and leverages BM25 for fast, sparse vector indexing. 

**Key Constraints:**
* **Indexing Time:** Maximum 5 minutes.
* **Chunk Size:** Maximum 2000 characters, configurable via CLI argument.
* **Chunking Types:** Distinct strategies for Python code and Text/Markdown.
* **Data Models:** Must use `pydantic` for `MinimalSource` tracking (`file_path`, `first_character_index`, `last_character_index`).
* **Package Management:** The project must be managed using `uv`.

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
You must implement different chunking strategies for different file types while strictly enforcing the configurable 2000-character maximum.

### 3.1 Python Code Chunking (`.py`)
Do not use simple character splitting for code. Use Python's built-in `ast` module to parse the code into logical blocks.

1.  **Generate the AST:** Read the raw Python file as a string (retaining all original formatting) and pass it to `ast.parse()`. This builds a structural tree mapped out as distinct nodes without executing code.
2.  **Traverse with `ast.NodeVisitor`:** Implement a custom `ast.NodeVisitor` subclass to navigate the tree top-to-bottom. Avoid `ast.walk()`, which scrambles the code order.
3.  **Map Semantic Boundaries:** During traversal, target high-level structural nodes (`FunctionDef`, `ClassDef`) and log their precise code coordinates using `node.lineno` and `node.end_lineno`. Since the AST ignores standard comments, use it as a compass to discover exact line numbers.
4.  **Slice and Aggregate:** Go back to your original raw code lines. Use the coordinates to slice the text, ensuring inline and structural comments are preserved. Linearly pile these slices into a single chunk. If adding the next full block pushes the chunk over 2000 characters, seal the current chunk to prevent splitting syntax in half.
5.  **Finalize Chunks:** Capture any remaining trailing comments at the end of the file, append them to the last chunk, and calculate the exact `first_character_index` and `last_character_index` for each final string. 

### 3.2 Markdown/Text Chunking (`.md`)
* **Langchain Splitters:** Utilize Langchain's `RecursiveCharacterTextSplitter`. It is designed to respect Markdown structure (headers, paragraphs, lists) and keeps chunks semantically coherent.
* **Configuration:** Set the `chunk_size` to your CLI parameter and define a reasonable overlap (e.g., 100-200 characters) to preserve context. Configure it to return string indices so you can accurately populate the Pydantic fields.

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