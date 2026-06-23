To successfully complete the RAG against the machine project, you can break down the development into a structured, step-by-step roadmap. Following this progression ensures you build a robust pipeline that meets all the mandatory requirements while preparing you effectively for the evaluation defense.

Phase 1: Project Setup & EnvironmentBefore writing any core logic, establish a clean and reproducible development workspace.Initialize the Repository: Set up your project directory ensuring all code goes into a src/ directory as required.Configure Dependency Management: Use uv to initialize your project, creating a valid pyproject.toml and generating a uv.lock file. Avoid checking in heavy data files or model weights.Draft the Architecture: Create the basic file structure within src/ (e.g., ingestion.py, retrieval.py, generation.py, evaluation.py, and cli.py).

Phase 2: Knowledge Base Ingestion SystemThis module is responsible for processing source documents so they can be searched efficiently.Document Parsing: Implement robust text extractors for the target file formats (PDFs, Markdown, or text files).Text Chunking: Design a strategy to split long documents into smaller, coherent segments. Consider using fixed-size token windows with a predefined overlap to preserve contextual continuity.Embedding Generation: Integrate an embedding model to convert text chunks into vector representations.Vector Storage: Set up a lightweight vector database or a localized vector indexing mechanism to store and query these embeddings along with their raw text metadata.

Phase 3: Retrieval SystemThe goal here is to find the most relevant pieces of information matching a user's query.Query Embedding: Convert the incoming user query into a vector using the exact same embedding model applied during ingestion.Similarity Search: Implement a vector search mechanism (such as Cosine Similarity or Dot Product) to compare the query vector against your stored knowledge base vectors.Top-K Selection: Extract the top $k$ highest-scoring chunks that provide the most contextually relevant information.

Phase 4: Answer Generation SystemThis component synthesizes the retrieved chunks into a final, accurate response.Prompt Engineering: Design a robust system prompt that clearly instructs the Large Language Model (LLM) to answer the query only using the provided context blocks.Context Injection: Format and stitch the retrieved chunks seamlessly into the LLM prompt.Inference Integration: Connect to your LLM engine to run the inference and capture the generated response cleanly.

Phase 5: Evaluation & CLI IntegrationA working pipeline needs a user interface and a method to measure its performance.Build the CLI: Develop a straightforward command-line interface using a library like argparse or click. Ensure it supports key workflows: ingesting documents, querying the system, and running evaluations.Implement the Evaluation System: Create automated checks or metrics to evaluate both the retrieval accuracy (did you fetch the right chunks?) and generation quality (is the answer grounded in the context without hallucinating?).

Phase 6: Documentation & Defense PreparationThe final step is proving you understand your code and ensuring it passes peer evaluation.Write a Comprehensive README.md: Document how to install dependencies via uv sync, how to run the ingestion pipeline, how to trigger queries via the CLI, and how to execute the evaluation system.Prepare for "Recode" Instructions: Review your code thoroughly. Be ready to quickly modify a data structure, tweak a prompt, or adjust a chunking parameter on the fly during your evaluation to prove complete ownership of the implementation.


add good cut into chunk code == 21% -> 34%
add good cut into chunk document == 48% -> 55%

creation 2 index chunk code == 34% -> 31%
creation 2 index chunk doc == 55% -> 41%

add path into chunk == 25% ->
add path into chunk == 53% ->  


Keep the original snake_case, but also append a space-separated version
47% -> 52% for code
58 -> 59% for doc 