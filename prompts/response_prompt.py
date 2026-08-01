MEMORY_AWARE_PROMPT = """You are a helpful AI assistant with access to conversation history and user context.

IMPORTANT RULES:
1. Use the conversation history to maintain context and avoid asking for information already provided
2. Be thorough but concise
3. If the history contains a summary, use it to understand previous context
4. Never repeat information already covered in the conversation
5. If document context is available, use it to enhance your response"""


def build_chat_prompt(
    question: str,
    history: list,
    doc_info: str = ""
) -> str:

    history_text = ""
    for msg in history:
        role = msg.get("role", "user").capitalize()
        content = msg.get("message", "")
        if role.lower() == "system" and "summary" in content.lower():
            history_text += f"[Context]: {content}\n"
        else:
            history_text += f"{role}: {content}\n"

    doc_section = ""
    if doc_info:
        doc_section = f"\n{doc_info}\n"

    prompt = f"""{MEMORY_AWARE_PROMPT}

{doc_section}Conversation History:
{history_text}
User: {question}

Assistant:"""
    return prompt


def build_hybrid_prompt(
    question: str,
    rag_context: str = "",
    web_context: str = "",
    history: list = None
) -> str:

    history_text = ""
    if history:
        for msg in history[-3:]:
            role = msg.get("role", "user").capitalize()
            content = msg.get("message", "")
            history_text += f"{role}: {content}\n"

    sections = []
    if rag_context:
        sections.append(f"DOCUMENT CONTEXT:\n{rag_context}")
    if web_context:
        sections.append(f"WEB SEARCH RESULTS:\n{web_context}")

    context_block = "\n\n".join(sections) if sections else "No specific context available. Use your general knowledge."

    history_section = f"\nRecent Conversation:\n{history_text}" if history_text else ""

    prompt = f"""Answer the following question comprehensively using all available information.

{context_block}
{history_section}
Question: {question}

Provide a detailed, accurate, and helpful answer:"""
    return prompt
