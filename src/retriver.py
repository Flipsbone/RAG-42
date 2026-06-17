import bm25s

chunks = [
    "def hello_world(): print('hello')",
    "The vLLM server requires an OpenAI compatible endpoint.",
    "BM25 is a great ranking function."
]

# 2. Tokenize the text (splits sentences into distinct words, makes them lowercase, etc.)
corpus_tokens = bm25s.tokenize(chunks)

# 3. Create the retriever object
retriever = bm25s.BM25()

# 4. Index the tokens
retriever.index(corpus_tokens)

# 5. Save the index to disk so you don't have to rebuild it every time
retriever.save("data/processed/bm25_index")

# 6. Load the pre-built index
retriever = bm25s.BM25.load("data/processed/bm25_index", load_corpus=True)

# 7. The user's raw question
question = "How do I configure the OpenAI server?"

# 8. Tokenize the question using the exact same tokenizer
query_tokens = bm25s.tokenize(question)

# 9. Retrieve the top-k results
# It returns the matched text (or their IDs) and their relevance scores
results, scores = retriever.retrieve(query_tokens, k=1)

# Print the top results
for i in range(results.shape[1]):
    doc, score = results[0, i], scores[0, i]
    print(f"Rank {i+1} (Score: {score:.2f}): {doc}")