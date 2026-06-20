from langchain_community.document_loaders import UnstructuredWordDocumentLoader

async def load_word(file_path):
    return await UnstructuredWordDocumentLoader(file_path).aload()


