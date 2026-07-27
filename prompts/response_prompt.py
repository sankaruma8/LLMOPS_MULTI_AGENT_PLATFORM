RESPONSE_SYSTEM_PROMPT = """You are a highly knowledgeable AI assistant powered by advanced language models.
You provide accurate, detailed, and helpful responses to user queries.
You draw from multiple knowledge sources to give comprehensive answers.
If you don't know something specific, you explain what you do know and suggest where to find more information.
Keep responses focused, well-structured, and relevant to the question asked.
Use markdown formatting for clarity when appropriate."""

MEMORY_AWARE_PROMPT = """You are a helpful AI assistant with access to conversation history and user context.

IMPORTANT RULES:
1. Use the conversation history to maintain context and avoid asking for information already provided
2. If user preferences are provided, respect them in your responses
3. Be thorough but concise
4. If the history contains a summary, use it to understand previous context
5. Never repeat information already covered in the conversation
6. If document context is available, use it to enhance your response"""


def build_chat_prompt(
    question: str,
    history: list,
    user_memories: list = None,
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

    memories_text = ""
    if user_memories:
        memories_text = "\nUser Preferences:\n"
        for memory in user_memories[:5]:
            memories_text += f"- {memory.get('content', '')}\n"

    doc_section = ""
    if doc_info:
        doc_section = f"\n{doc_info}\n"

    prompt = f"""{MEMORY_AWARE_PROMPT}

{doc_section}Conversation History:
{history_text}
{memories_text}User: {question}

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


def build_rag_chat_prompt(
    question: str,
    history: list,
    context: str,
    sources: list,
    user_memories: list = None
) -> str:

    history_text = ""
    for msg in history[-5:]:
        role = msg.get("role", "user").capitalize()
        content = msg.get("message", "")
        if role.lower() != "system":
            history_text += f"{role}: {content}\n"

    sources_text = "\n".join([f"- {s}" for s in sources]) if sources else "No specific sources"

    memories_text = ""
    if user_memories:
        memories_text = "\nUser Context:\n"
        for memory in user_memories[:3]:
            memories_text += f"- {memory.get('content', '')}\n"

    prompt = f"""You are a helpful assistant answering questions based on uploaded documents.

Available Sources: {sources_text}
{memories_text}
Recent Conversation:
{history_text}

Document Context:
{context}

Question: {question}

Answer based on the document context above. Cite sources when possible:"""
    return prompt


def build_simple_prompt(question: str) -> str:
    return f"""{RESPONSE_SYSTEM_PROMPT}

User: {question}

Assistant:"""


def build_memory_summary_prompt(messages: list) -> str:

    history_text = ""
    for msg in messages:
        role = msg.get("role", "user").capitalize()
        content = msg.get("message", "")
        history_text += f"{role}: {content}\n"

    return (
        "Create a concise summary of this conversation. "
        "Focus on key topics, user preferences, and important decisions.\n\n"
        f"Conversation:\n{history_text}\n\n"
        "Summary (2-3 sentences):"
    )
