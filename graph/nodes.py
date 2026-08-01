from agents.planner_agent import planner
from agents.response_agent import get_response
from agents.web_agent import search_web, format_web_results
from agents.retriever_agent import RetrieverAgent
from agents.validator_agent import validate_answer_standalone
from memory.memory_manager import memory_manager, save_message
from prompts.response_prompt import build_chat_prompt, build_hybrid_prompt


retriever_agent = RetrieverAgent()


def memory_node(state):
    session_id = state["session_id"]
    state["history"] = memory_manager.get_optimized_history(session_id)
    state["rag_context"] = ""
    state["web_context"] = ""
    state["available_docs"] = []
    state["routes_tried"] = []

    try:
        state["available_docs"] = retriever_agent.retriever.get_all_documents()
    except Exception:
        state["available_docs"] = []

    print(f"\n=== MEMORY NODE ===")
    print(f"Session: {session_id}")
    print(f"History messages: {len(state['history'])}")
    print(f"Available docs: {len(state['available_docs'])}")

    return state


def planner_node(state):
    state["route"] = planner(state["question"], state.get("history", []))

    print("\n========== PLANNER ==========")
    print("Question:", state["question"])
    print("Route:", state["route"])
    print("=============================\n")

    return state


def chat_node(state):
    doc_info = ""
    if state.get("available_docs"):
        doc_names = list(set(d if isinstance(d, str) else d.get("filename", "doc") for d in state["available_docs"]))
        doc_info = f"\nAvailable documents: {', '.join(doc_names[:10])}\n"

    prompt = build_chat_prompt(
        state["question"],
        state["history"],
        doc_info=doc_info
    )

    state["answer"] = get_response(prompt)
    state["sources"] = []
    state["routes_tried"].append("CHAT")

    print("\n=== CHAT Agent ===")
    return state


def rag_node(state):
    try:
        chunks = retriever_agent.retrieve_chunks(state["question"], top_k=8)

        if chunks:
            context, sources = retriever_agent.format_context(chunks)
            state["rag_context"] = context

            answer = get_response(
                build_hybrid_prompt(
                    state["question"],
                    rag_context=context,
                    history=state.get("history", [])
                ),
                system_prompt=(
                    "You are a helpful assistant that answers questions based on uploaded documents. "
                    "Use the document context to provide accurate, detailed answers. "
                    "Cite document names and page numbers when possible. "
                    "If the documents partially answer the question, provide what you can and note gaps."
                )
            )
            state["answer"] = answer
            state["sources"] = list(sources)
        else:
            state["answer"] = ""
            state["sources"] = []

    except Exception as e:
        print(f"RAG failed: {e}")
        state["answer"] = ""
        state["sources"] = []

    state["routes_tried"].append("RAG")
    print("\n=== RAG Agent ===")
    return state


def web_node(state):
    try:
        results = search_web(state["question"])

        if results:
            context = format_web_results(results)
            state["web_context"] = context

            answer = get_response(
                build_hybrid_prompt(
                    state["question"],
                    web_context=context,
                    history=state.get("history", [])
                ),
                system_prompt=(
                    "You are a helpful assistant that answers questions based on web search results. "
                    "Use the search results to provide accurate, up-to-date information. "
                    "Cite sources when possible. "
                    "If search results don't fully answer the question, provide what you can."
                )
            )
            state["answer"] = answer
            state["sources"] = [r["url"] for r in results[:3]]
        else:
            state["answer"] = ""
            state["sources"] = []

    except Exception as e:
        print(f"Web search failed: {e}")
        state["answer"] = ""
        state["sources"] = []

    state["routes_tried"].append("WEB")
    print("\n=== WEB Agent ===")
    return state


def validator_node(state):
    answer = state.get("answer", "")
    print("\n=== Validator ===")
    print("Answer:", answer[:100] + "..." if len(answer) > 100 else answer)

    state["valid"] = validate_answer_standalone(answer)
    print("Valid:", state["valid"])
    return state


def save_node(state):
    print("\n=== SAVE NODE ===")
    if state.get("answer"):
        save_message(state["session_id"], "user", state["question"])
        save_message(state["session_id"], "assistant", state["answer"])
        print("Conversation Saved Successfully!")
    else:
        print("No answer to save.")
    return state
