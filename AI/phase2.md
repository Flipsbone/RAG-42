The lack of a GPU is actually a massive advantage for the ingestion phase of this specific project. Because the specifications strictly mandate the use of either TF-IDF or BM25, you are building a sparse lexical index, not a dense semantic vector database.  Lexical indexing relies purely on statistical frequency and math, which means it is entirely CPU-bound. You will not need to load heavy embedding models into VRAM to process the documents.Here is the exact stack of modules you should use for Phase 2, aligning with both the mandatory project rules and your CPU-only environment:


## Step 1: 
File Discovery and LoadingThe first requirement is to "Read and process all files from the VLLM repository provide in the attachments". You need to distinguish between Python code and Markdown documentation.
Define Target Extensions: You are primarily looking for .py and .md files.

Traverse the Directory: Write a function to recursively walk the extracted vLLM directory and collect the file paths.

Read File Contents: Open each file, read its contents, and store it along with its path.


## Step 2: Implement Intelligent Chunking Strategies

The subject requires "different chunking strategies for the different types of files" (Python code and Text/Markdown). The maximum chunk size is 2000 characters and must be configurable via the CLI.

Architecture: Data Models & Protocols
To keep the codebase clean and modular, separate your data structures from your chunking logic:

The Data Model (Pydantic): As you chunk, you must create metadata for each chunk. Use Pydantic's BaseModel to define a MinimalSource object. This model must track the file_path, first_character_index, last_character_index, and the extracted text itself. Using Pydantic makes serializing this data to disk later incredibly easy.  

The Chunker Protocol: Define a structural Protocol (e.g., ChunkerStrategy) that enforces a common interface for all file types. Every specific chunker class must implement a .chunk(text, file_path, max_chunk_size) method that returns a list of your MinimalSource objects.

The Strategy Dictionary: Centralize your strategies inside a dictionary mapping extensions to their respective implementations:
```python
chunkers: dict[str, ChunkerStrategy] = {
".py": PythonChunker(),
".md": MarkdownChunker()
}
```
***Python Code Chunking (.py):***

The AST Approach: Do not use simple character splitting for code. Use Python's built-in ast module to parse the code into logical blocks (classes, functions, and top-level statements).

Fallback: If a single function or class exceeds the 2000-character limit, you will need a fallback strategy, perhaps using langchain's RecursiveCharacterTextSplitter specifically configured for Python syntax (e.g., splitting on \n\n, then \n, etc.).
### 2.2.1 Convert the code string into an Abstract Syntax Tree (AST)

    Action: Read the raw Python file as a string (retaining all original formatting) and pass it to ast.parse().

    Why it matters: This builds a structural tree where code constructs (functions, classes, logic) are mapped out as distinct, hierarchical nodes without executing any code.

### 2.2.2 Traverse the tree linearly using ast.NodeVisitor

    Action: Implement a custom ast.NodeVisitor subclass to navigate the tree. Avoid ast.walk(), which scrambles the code order.

    Why it matters: A NodeVisitor guarantees a strict, top-to-bottom, depth-first traversal. This ensures your chunks maintain the natural sequence of the source file.

### 2.2.3 Map semantic block boundaries (Line Coordinates)

    Action: During traversal, target high-level structural nodes (like FunctionDef and ClassDef) and log their precise code coordinates using node.lineno and node.end_lineno.

    Why it matters: Because AST ignores standard comments (#), you cannot chunk the AST directly. Instead, you use the AST as a "boussole" (compass) to discover the exact line numbers where code blocks start and end.

### 2.2.4 Linearly slice and aggregate up to the 2000-character limit

    Action: Go back to your original raw code lines. Use the coordinates from the previous step to slice the text, which ensures all inline and structural comments are preserved. Linearly pile these slices into a single chunk, monitoring the string length.

    Why it matters: If adding the next full function pushes the current chunk over 2000 characters, you seal the current chunk and push it to the queue. This prevents a function from being sliced in half mid-syntax.

### 2.2.5 Finalize chunks and return for Embedding

    Action: Capture any remaining trailing comments or code at the end of the file, append them to the last chunk, and return the final array of text strings.

    Why it matters: Your RAG pipeline now receives clean, standalone code segments with full developer comments intact, maximizing the semantic accuracy of your downstream vector search.

***Markdown/Text Chunking (.md):***

Langchain Splitters: Utilize langchain's MarkdownTextSplitter or RecursiveCharacterTextSplitter. These are designed to respect Markdown structure (headers, paragraphs, lists) and will keep your chunks semantically coherent while strictly enforcing the configurable character limit.


## Step 3: Indexing with BM25sYou must create a searchable index within a 5-minute time limit. bm25s is perfectly suited for this. 

Prepare the Corpus: Extract the raw text from all your validated chunk objects into a single list of strings.Tokenization: bm25s requires tokenized input. You must define how to break your text into searchable terms.

Crucial Step: As discussed earlier, standard tokenization might fail on code (e.g., CamelCase or snake_case). You should write a custom tokenization function that splits these code-specific formats into individual words before passing them to the BM25 indexer.

Build the Index: Pass your tokenized corpus to the bm25s indexer to build the inverted index.
Save to Disk: The requirement is to "Store the index for fast retrieval". bm25s provides built-in methods to save the index to disk. You also need to serialize and save your chunk metadata (the list of pydantic objects) so that when a retrieval occurs, you can map the BM25 document ID back to the specific file path and character indices.


## Step 4: Wrap it in a CLI
The final step is to make this process accessible via the command line.

Python Fire: Use the fire library to expose your indexing function as a CLI command.

Arguments: Ensure the command accepts the repository path and the --max_chunk_size argument.

Progress Tracking: Wrap your file processing and chunking loops with tqdm to provide visual feedback during the ingestion process.  