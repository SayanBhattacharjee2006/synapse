from langchain_openai import OpenAIEmbeddings
from fastembed import SparseTextEmbedding, LateInteractionTextEmbedding

dense_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

sparse_embeddings = SparseTextEmbedding(model_name="qdrant/bm25")

late_interaction_embeddings = LateInteractionTextEmbedding(model_name="answerdotai/answerai-colbert-small-v1")

def embed_sparse_documents(texts: list[str]): 
    return list(sparse_embeddings.embed(texts))

def embed_sparse_query(text: str):
    return list(sparse_embeddings.embed([text]))[0]

def embed_late_interaction_documents(texts: list[str]): 
    return list(late_interaction_embeddings.embed(texts))

def embed_late_interaction_query(text: str):
    return list(late_interaction_embeddings.query_embed([text]))[0]

# these returns numpy arrays so we need to convert back to python lists thats why we used list() in all the returns