RESEARCH_SYSTEM_PROMPT = """You are a research assistant that synthesizes information from multiple sources.
You combine web search results with document knowledge to provide comprehensive answers.
Always cite your sources and indicate when information comes from web vs documents."""


def build_research_prompt(
    question: str,
    web_results: list,
    doc_chunks: list
) -> str:
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

    prompt = f"""{RESEARCH_SYSTEM_PROMPT}

QUESTION: {question}

WEB SEARCH RESULTS:
{web_context if web_context else "No web results available."}

DOCUMENT CONTEXT:
{doc_context if doc_context else "No document context available."}

INSTRUCTIONS:
1. Synthesize information from both web and document sources
2. Clearly indicate the source of each piece of information
3. If sources conflict, mention the discrepancy
4. Provide a comprehensive, well-structured answer
5. Cite sources using [Web] or [Document: name, Page X] format

COMPREHENSIVE ANSWER:"""
    return prompt
