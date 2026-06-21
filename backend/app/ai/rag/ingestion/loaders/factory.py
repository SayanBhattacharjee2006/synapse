from app.ai.rag.ingestion.loaders.pdf import load_pdf
from app.ai.rag.ingestion.loaders.word import load_word
from app.ai.rag.ingestion.loaders.txt import load_txt
from app.ai.rag.ingestion.loaders.markdown import load_markdown

loaders = {
    "pdf": load_pdf,
    "doc": load_word,
    "docx": load_word,
    "txt": load_txt,
    "md": load_markdown,
    "markdown": load_markdown
}



async def load_document(file_path):
    print("Reached load_document function")
    ext = file_path.rsplit(".", 1)[-1].lower()
    
    if ext not in loaders.keys():
        raise ValueError(f"Unsupported file type: {ext}")

    loader = loaders.get(ext)

    print("Loader : ", loader)

    if loader is None:
        raise ValueError(f"Unsupported file type: {ext}")

    return await loader(file_path)

    