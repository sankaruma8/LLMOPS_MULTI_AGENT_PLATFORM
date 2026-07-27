import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.config import settings


class LangSmithLogger:

    def __init__(self):

        self.enabled = settings.LANGCHAIN_TRACING_V2 == "true"
        self.project = settings.LANGCHAIN_PROJECT

        if self.enabled:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY or ""
            os.environ["LANGCHAIN_PROJECT"] = self.project

        self._runs = {}

    def _generate_run_id(self) -> str:
        return str(uuid.uuid4())

    def start_trace(
        self,
        name: str,
        run_type: str = "chain",
        metadata: Optional[Dict] = None,
        parent_run_id: Optional[str] = None
    ) -> str:

        if not self.enabled:
            return self._generate_run_id()

        run_id = self._generate_run_id()

        self._runs[run_id] = {
            "name": name,
            "run_type": run_type,
            "metadata": metadata or {},
            "parent_run_id": parent_run_id,
            "start_time": datetime.now().isoformat(),
            "inputs": {},
            "outputs": {}
        }

        return run_id

    def end_trace(
        self,
        run_id: str,
        outputs: Optional[Dict] = None,
        error: Optional[str] = None,
        status: str = "success"
    ):

        if not self.enabled or run_id not in self._runs:
            return

        run = self._runs[run_id]
        run["end_time"] = datetime.now().isoformat()
        run["outputs"] = outputs or {}
        run["status"] = status

        if error:
            run["error"] = error
            run["status"] = "error"

        del self._runs[run_id]

    def log_llm_call(
        self,
        model: str,
        prompt: str,
        completion: str,
        latency_ms: float,
        token_count: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):

        if not self.enabled:
            return

        run_id = self.start_trace(
            name=f"LLM Call: {model}",
            run_type="llm",
            metadata={
                "model": model,
                "latency_ms": latency_ms,
                "token_count": token_count,
                **(metadata or {})
            }
        )

        self.end_trace(
            run_id,
            outputs={
                "prompt": prompt[:1000],
                "completion": completion[:1000],
                "model": model
            }
        )

    def log_chain(
        self,
        chain_name: str,
        inputs: Dict,
        outputs: Dict,
        latency_ms: float,
        metadata: Optional[Dict] = None
    ):

        if not self.enabled:
            return

        run_id = self.start_trace(
            name=chain_name,
            run_type="chain",
            metadata={
                "latency_ms": latency_ms,
                **(metadata or {})
            }
        )

        self._runs[run_id]["inputs"] = inputs

        self.end_trace(run_id, outputs=outputs)

    def log_retriever(
        self,
        query: str,
        retrieved_docs: List[Dict],
        latency_ms: float
    ):

        if not self.enabled:
            return

        run_id = self.start_trace(
            name="Document Retriever",
            run_type="retriever",
            metadata={"latency_ms": latency_ms}
        )

        self._runs[run_id]["inputs"] = {"query": query}

        self.end_trace(
            run_id,
            outputs={
                "documents": [
                    {
                        "content": doc.get("text", "")[:500],
                        "metadata": {
                            "document": doc.get("document"),
                            "page": doc.get("page"),
                            "distance": doc.get("distance")
                        }
                    }
                    for doc in retrieved_docs[:5]
                ]
            }
        )

    def log_agent(
        self,
        agent_name: str,
        question: str,
        answer: str,
        route: str,
        latency_ms: float,
        metadata: Optional[Dict] = None
    ):

        if not self.enabled:
            return

        run_id = self.start_trace(
            name=f"Agent: {agent_name}",
            run_type="agent",
            metadata={
                "route": route,
                "latency_ms": latency_ms,
                **(metadata or {})
            }
        )

        self._runs[run_id]["inputs"] = {"question": question}

        self.end_trace(
            run_id,
            outputs={"answer": answer, "route": route}
        )

    def log_tool(
        self,
        tool_name: str,
        input_data: str,
        output_data: str,
        latency_ms: float
    ):

        if not self.enabled:
            return

        run_id = self.start_trace(
            name=f"Tool: {tool_name}",
            run_type="tool",
            metadata={"latency_ms": latency_ms}
        )

        self._runs[run_id]["inputs"] = {"input": input_data}

        self.end_trace(run_id, outputs={"output": output_data})

    def log_error(
        self,
        error_type: str,
        error_message: str,
        component: str,
        metadata: Optional[Dict] = None
    ):

        if not self.enabled:
            return

        run_id = self.start_trace(
            name=f"Error: {error_type}",
            run_type="error",
            metadata=metadata or {}
        )

        self.end_trace(
            run_id,
            error=f"{component}: {error_message}",
            status="error"
        )


langsmith_logger = LangSmithLogger()
