# RAG
How RAG Works [Retrieval-Augmented Generation (RAG)] prevents AI models from guessing or hallucinating by forcing them to reference a dedicated external knowledge base.\
It operates in four distinct phases:

**Indexing:** Raw data is structured and organized to make it searchable.\
**Retrieving:** The system interprets a user query, matches it against the indexed database, and pulls out the most relevant pieces of information.\
**Augmenting:** The retrieved snippets are filtered and inserted directly into the AI's context window alongside the user's prompt.\
**Generating:** The AI reads the provided context, blends the knowledge, and generates a coherent answer.\

question indexing(document) -> retrieval(relevant document) -> generation -(context windows) -> answer

| Feature                   | Mandatory Implementation                                                  | Column 3  |
|:--------                  |:-------------------------------------------------------------------------:| --------: |
| Retrieval Algorithm       | Keyword-based scoring using BM25.                                         | Right     |
| Data Parsing              | Configurable chunking (max 2000 chars)customized for Python and Markdown. |           |
| Query Handling            | Direct search using the exact user prompt.                                |           |
| Performance               | Basic inference within context limits.                                    |           |



**VLLM(virtual Large Language Model)** -> Maximise speed and requests flow thanks to memory management called : `PagedAttention`, and `continous batching`, it exploit hardward capacity to the fullest.

**BM25(Best Matching 25)** -> Is a highly optimized search algorithm for lexical search (searching by exact words rather than AI-generated "meanings").\
How does it works : `Term Saturation` and `Penalty for Rambling`.\

***Term saturation :*** \
0 times = 0 points.\
1 time = 10 points.\
2 times = 15 points.\
3 times = 17 points.\
100 times = 18 points.\

BM25 uses a mathematical curve that flattens out. It knows that if a file mentions "database" 5 times, it's definitely about databases. Mentioning it 50 more times doesn't make it 50 times more relevant;

***Penalty for Rambling :***\
File A is a tiny 10-line configuration script. It mentions "database" twice.\
File B is a massive 10,000-line documentation manual. It also mentions "database" twice.

BM25 heavily penalizes File B for being long. If File A is that short and the word "database" appears twice, the entire file is likely dedicated to that exact topic.

Then to avoid re-reading your texts every time, the program extracts and saves three elements:

***The Dictionary (vocab.index.json) :*** \
The library tokenizes your text (splits sentences into words, lowers the case, and removes punctuation/stopwords). It counts every unique word in your entire dataset and assigns each one a unique sequential integer ID.

***The Configuration Panel (params.index.json) :*** \
This file saves the global statistics of your corpus alongside the mathematical settings of your BM25 model configuration.

***The Score Tables (Background Data Files) :*** \
This is the heart of the system. BM25 creates a large table that crosses words and your documents. In advance, it calculates and records a score (a relevance score) for each word in each sentence.

**Fire** Command Line Interfaces (CLIs) -> It looks at the Python object you passed to it (which can be a function, a class, a dictionary, or even the entire script), reads its arguments, default values, and docstrings, and automatically maps them to command-line arguments and flags.

## 2 Indexation
### 2.1 File Discovery and Loading
Read and process all files from the VLLM repository\
**Define Target Extensions:** `.py` and `.md` files\
**Traverse the Directory:** Write a function to recursively walk the extracted vLLM directory and collect the file paths.\
**Read File Contents:** Open each file, read its contents, and store in a dict[Path, str] it along with its path.
### 2.2 Implement Intelligent Chunking Strategies
**created model_indexation :** `PythonChunker` use AST (Abstract syntax Tree) python uses this module to read and understand code structure.
#### 2.2.1 Convert the code string into an Abstract Syntax Tree (AST)
#### 2.2.2 Walk through the main branches
#### 2.2.3 Find the coordinates (Indices) of each node
#### 2.2.4 Check the character length against your limit
#### 2.2.5 Collect and Return


**created model_indexation :** 
### 2.3 Indexing with BM25s
### 2.4 Wrap it in a CLI


# Start README Notes

This workspace contains a local RAG pipeline implemented in src/.

## Main Commands
* index builds the BM25 index from .py and .md sources.
* search retrieves top-k snippets for a single query.
* search_dataset runs retrieval for a batch of unanswered questions.
* answer combines retrieval with Ollama generation for one query.
* answer_dataset generates answers for a saved search-results dataset.
* evaluate compares generated retrieval output against the answered dataset.

## Implementation Notes
* Chunking is handled by AST-based Python chunking and Markdown token-based chunking.
* Retrieval uses bm25s with hashed index files under data/processed/bm25_index.
* Generation uses ollama.Client with the default model qwen3:0.6b.
* CLI entry points are defined in src/cli/command_line_interface.py and exposed through src/__main__.py.
