RETRIEVER_SYSTEM_PROMPT = """You are a retrieval-augmented generation assistant.
You answer questions based on the provided context from uploaded documents.
Always cite the document name and page number when referencing specific information.
If the context doesn't contain enough information, say so clearly."""


def build_rag_prompt(question: str, context: str, sources: list) -> str:
    sources_text = "\n".join([f"- {s}" for s in sources])

    prompt = f"""{RETRIEVER_SYSTEM_PROMPT}

AVAILABLE SOURCES:
{sources_text}

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. Answer the question using ONLY the provided context
2. If the context contains the answer, provide it with citations
3. If the context doesn't contain enough information, state that clearly
4. Be concise but thorough

ANSWER:"""
    return prompt


def build_chunk_context(chunks: list) -> str:
    contexts = []
    for chunk in chunks:
        contexts.append(
            f"Document: {chunk['document']}\n"
            f"Page: {chunk['page']}\n"
            f"Content: {chunk['text']}\n"
        )
    return "\n---\n".join(contexts)
