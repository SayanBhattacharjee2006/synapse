from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

async def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=settings.RAG_CHUNK_SIZE, chunk_overlap=settings.RAG_OVERLAP)


    text_chunks = text_splitter.split_documents(documents)

    return text_chunks
