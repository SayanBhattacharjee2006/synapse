from app.ai.rag.ingestion.loaders.pdf import load_pdf
from app.ai.rag.ingestion.loaders.word import load_word
from app.ai.rag.ingestion.loaders.txt import load_txt
from app.ai.rag.ingestion.loaders.markdown import load_markdown
from app.core.logging import logger

loaders = {
    "pdf": load_pdf,
    "doc": load_word,
    "docx": load_word,
    "txt": load_txt,
    "md": load_markdown,
    "markdown": load_markdown
}



async def load_document(file_path):
    ext = file_path.rsplit(".", 1)[-1].lower()
    
    if ext not in loaders.keys():
        raise ValueError(f"Unsupported file type: {ext}")

    loader = loaders.get(ext)

    logger.bind(loader=loader.__name__, file_extension=ext).info("document.loader.selected")

    if loader is None:
        raise ValueError(f"Unsupported file type: {ext}")

    return await loader(file_path)

