from langchain_community.document_loaders import UnstructuredMarkdownLoader
from app.core.logging import logger

async def load_markdown(file_path):
    logger.bind(loader="markdown").info("document.loader.started")
    return await UnstructuredMarkdownLoader(file_path).aload()
