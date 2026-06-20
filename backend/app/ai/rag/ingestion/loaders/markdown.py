from langchain_community.document_loaders import UnstructuredMarkdownLoader

async def load_markdown(file_path):
    return await UnstructuredMarkdownLoader(file_path).aload()