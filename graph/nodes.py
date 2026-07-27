from agents.planner_agent import planner
from agents.response_agent import get_response
from agents.web_agent import web_search, search_web, format_web_results
from agents.research_agent import research_search
from agents.retriever_agent import RetrieverAgent
from agents.tool_agent import classify_tool, process_with_tool
from rag.rag_pipeline import RAGPipeline
from agents.validator_agent import validate_answer_standalone
from memory.memory_manager import memory_manager, save_message
from prompts.response_prompt import build_chat_prompt, build_hybrid_prompt


rag = RAGPipeline()
retriever_agent = RetrieverAgent()


def memory_node(state):
    session_id = state["session_id"]
    state["history"] = memory_manager.get_optimized_history(session_id)
    state["user_memories"] = []
    state["rag_context"] = ""
    state["web_context"] = ""
    state["available_docs"] = []
    state["routes_tried"] = []

    try:
        doc_list = rag.retriever.get_all_documents()
        state["available_docs"] = doc_list
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
        state.get("user_memories", []),
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


def research_node(state):
    try:
        results = search_web(state["question"])

        doc_chunks = []
        if rag:
            try:
                query_embedding = rag.embedder.create_embeddings([state["question"]])[0]
                doc_chunks = rag.retriever.retrieve(query_embedding)
            except Exception:
                pass

        state["answer"] = research_search(state["question"], results, rag)
        state["sources"] = [r["url"] for r in results[:3]] if results else []

    except Exception as e:
        print(f"Research failed: {e}")
        state["answer"] = "I encountered an error during research."

    state["sources"] = state.get("sources", [])
    state["routes_tried"].append("RESEARCH")
    print("\n=== RESEARCH Agent ===")
    return state


def tool_node(state):
    try:
        tool_name = classify_tool(state["question"])

        if tool_name == "CALCULATOR":
            from tools.calculator import extract_math_from_query, calculate
            math_expr = extract_math_from_query(state["question"])
            result = calculate(math_expr)
            state["answer"] = get_response(
                f"Tool Result: {result}\nOriginal Question: {state['question']}\n\nFormat the result into a clear, helpful response.",
                system_prompt="You are a helpful math assistant. Format the calculation result clearly."
            )
        elif tool_name == "PYTHON":
            from tools.python_tool import extract_python_from_query, execute_code
            code = extract_python_from_query(state["question"])
            result = execute_code(code)
            if result["success"]:
                state["answer"] = get_response(
                    f"Code Result: {result.get('output', 'No output')}\nOriginal Question: {state['question']}\n\nExplain the result.",
                    system_prompt="You are a helpful coding assistant."
                )
            else:
                state["answer"] = f"Code execution error: {result['error']}"
        else:
            state["answer"] = ""

        state["tool_used"] = tool_name
        state["sources"] = []

    except Exception as e:
        print(f"Tool agent failed: {e}")
        state["answer"] = ""
        state["tool_used"] = None
        state["sources"] = []

    state["routes_tried"].append("TOOL")
    print("\n=== TOOL Agent ===")
    return state


def hybrid_node(state):
    """Combines whatever sources succeeded for a comprehensive answer."""
    question = state["question"]
    rag_ctx = state.get("rag_context", "")
    web_ctx = state.get("web_context", "")
    history = state.get("history", [])
    doc_info = ""
    if state.get("available_docs"):
        doc_names = list(set(d if isinstance(d, str) else d.get("filename", "doc") for d in state["available_docs"]))
        doc_info = f"Available documents: {', '.join(doc_names[:10])}\n"

    if not rag_ctx and not web_ctx:
        prompt = build_chat_prompt(question, history, [], doc_info=doc_info)
        state["answer"] = get_response(prompt)
    else:
        prompt = build_hybrid_prompt(
            question,
            rag_context=rag_ctx,
            web_context=web_ctx,
            history=history
        )

        system = (
            "You are a comprehensive AI assistant. You have access to multiple information sources. "
            "Combine information from ALL available sources to give the most complete answer possible. "
            "If sources agree, reinforce the answer. If they conflict, note the discrepancy. "
            "Always provide a clear, well-structured response."
        )

        state["answer"] = get_response(prompt, system_prompt=system)

    state["routes_tried"].append("HYBRID")
    print("\n=== HYBRID Agent ===")
    print(f"  Sources: RAG={'yes' if rag_ctx else 'no'} WEB={'yes' if web_ctx else 'no'}")
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
