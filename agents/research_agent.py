from agents.response_agent import get_response


RESEARCH_SYSTEM_PROMPT = (
    "You are a research assistant that synthesizes information from multiple sources. "
    "Combine web search results with document knowledge to provide comprehensive answers. "
    "Always cite sources using [Web] or [Document] format. "
    "If sources conflict, mention the discrepancy."
)


def research_query(question: str, web_results: list, doc_chunks: list):

    web_context = ""
    for result in web_results:
        web_context += (
            f"[Web] Title: {result['title']}\n"
            f"Content: {result['content']}\n"
            f"URL: {result['url']}\n\n"
        )

    doc_context = ""
    for chunk in doc_chunks:
        doc_context += (
            f"[Document: {chunk['document']}, Page {chunk['page']}]\n"
            f"{chunk['text']}\n\n"
        )

    prompt = (
        f"QUESTION: {question}\n\n"
        f"WEB SEARCH RESULTS:\n{web_context if web_context else 'No web results available.'}\n\n"
        f"DOCUMENT CONTEXT:\n{doc_context if doc_context else 'No document context available.'}\n\n"
        f"Provide a comprehensive answer synthesizing information from both sources:"
    )

    return get_response(prompt, system_prompt=RESEARCH_SYSTEM_PROMPT)


def research_search(question: str, web_results: list, rag_pipeline):

    doc_chunks = []

    if rag_pipeline:
        try:
            query_embedding = rag_pipeline.embedder.create_embeddings([question])[0]
            doc_chunks = rag_pipeline.retriever.retrieve(query_embedding)
        except Exception as e:
            print(f"Document retrieval failed during research: {e}")

    return research_query(question, web_results, doc_chunks)
