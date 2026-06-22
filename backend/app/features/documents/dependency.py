def create_context(docs):
    context = "\n\n--\n\n".join(doc.page_content for doc, score in docs)

    return context
