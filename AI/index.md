question -> indexing (document) -> retrival (relevant document) -> Generation -> answer

INDEXING: 
you have external document that we want to load and put into the retriver
the goal of the retriver is given an input question , and fish out document that are related to my question in some way 
for that we have to creat a numerical representation of document because it is easy to compare vector. 
there are few method : 
- use frequency of words and you build what they call sparse vector large vocabulary of possible words each value
reprensents the number of occurences of that particular words.

each document are split and compressed into a vector . vector captures a semantic meaning of the document itself 
the vector are indexed question can be embedded in the exactly same way 

```bash
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

docs = text_splitter.split_text("Ton texte long ici...")
```

```bash
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrought
```

indexing process basically makes documents easy to retrieve and goes throught a flow
that look like you take our document you split it in some way these in smaller chunks
that can be easily embedded and thos embeddings are then numerical representation of those 
documents that are easily searchable and they stored in an index when given a question 
thats also embedded the index performs a similarity search and returns splits that are 
relevant to the question


retrieval 
```
vectorstore.as_retriever(search_kwargs={"k": 1})
```

k = nb of neighbors to fetch when you do retrieval process ( nb of document near to the question)

generation 

```
from langchain.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_template(template)



QUERY TRANSLATION
multiple query break the query into different perspective of the same question rewriting
rat fusion : multipequery
decomposition : retrieve each answered of question and feed the other question turn by turn to make more precise