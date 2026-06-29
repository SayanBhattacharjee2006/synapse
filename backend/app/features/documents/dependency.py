def create_context(docs):
    context = "\n\n--\n\n".join(doc.payload.get("page_content", "") for doc in docs)

    return context