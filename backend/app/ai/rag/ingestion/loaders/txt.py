from langchain_community.document_loaders import TextLoader

async def load_txt(file_path):
    return await TextLoader(file_path).aload() 