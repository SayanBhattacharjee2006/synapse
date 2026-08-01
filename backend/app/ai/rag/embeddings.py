from langchain_openai import OpenAIEmbeddings
from fastembed import SparseTextEmbedding, LateInteractionTextEmbedding
from functools import lru_cache
import asyncio


@lru_cache(maxsize=1)
def get_dense_embeddings():
    return OpenAIEmbeddings(model="text-embedding-3-small")


@lru_cache(maxsize=1)
def get_sparse_embeddings():
    return SparseTextEmbedding(model_name="qdrant/bm25")


@lru_cache(maxsize=1)
def get_late_interaction_embeddings():
    return LateInteractionTextEmbedding(
        model_name="answerdotai/answerai-colbert-small-v1"
    )


def embed_sparse_documents(texts: list[str]):
    return list(get_sparse_embeddings().embed(texts))


def embed_sparse_query(text: str):
    return list(get_sparse_embeddings().embed([text]))[0]


def embed_late_interaction_documents(texts: list[str]):
    return list(get_late_interaction_embeddings().embed(texts))


def embed_late_interaction_query(text: str):
    return list(get_late_interaction_embeddings().query_embed([text]))[0]

# these returns numpy arrays so we need to convert back to python lists thats why we used list() in all the returns

async def embed_chunks_in_batches(texts: list[str], batch_size: int = 32):
    dense_vectors = []
    sparse_vectors = []
    multi_vectors = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"Embedding batch {i // batch_size + 1} ({len(batch)} chunks)...")

        batch_dense = await get_dense_embeddings().aembed_documents(batch)
        batch_sparse = await asyncio.to_thread(embed_sparse_documents, batch)
        batch_multi = await asyncio.to_thread(embed_late_interaction_documents, batch)

        dense_vectors.extend(batch_dense)
        sparse_vectors.extend(batch_sparse)
        multi_vectors.extend(batch_multi)

    return dense_vectors, sparse_vectors, multi_vectors
