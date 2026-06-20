from langchain_community.document_loaders import PyMuPDFLoader

async def load_pdf(file_path):
    return await PyMuPDFLoader(file_path).aload()