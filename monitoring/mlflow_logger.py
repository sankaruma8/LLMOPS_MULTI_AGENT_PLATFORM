import mlflow
import mlflow.sklearn
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import settings


class MLflowLogger:

    def __init__(self):
        self._initialized = False
        self._run = None

    def _ensure_init(self):
        if self._initialized:
            return
        try:
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            mlflow.set_experiment("LLMOps-Multi-Agent")
            self._initialized = True
        except Exception:
            self._initialized = False

    def start_run(self, run_name: Optional[str] = None, tags: Optional[Dict] = None):
        self._ensure_init()
        if not self._initialized:
            return None
        self._run = mlflow.start_run(run_name=run_name, tags=tags or {})
        return self._run

    def end_run(self, status: str = "FINISHED"):
        self._ensure_init()
        if self._run and self._initialized:
            mlflow.end_run(status=status)
            self._run = None

    def log_query(
        self,
        query: str,
        route: str,
        answer: str,
        latency_ms: float,
        token_count: Optional[int] = None,
        is_valid: bool = True,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self._ensure_init()
        if not self._initialized:
            return

        metrics = {
            "latency_ms": latency_ms,
            "is_valid": 1 if is_valid else 0,
            "answer_length": len(answer),
            "query_length": len(query)
        }

        if token_count:
            metrics["token_count"] = token_count

        params = {
            "route": route,
            "session_id": session_id or "anonymous"
        }

        if metadata:
            params.update(metadata)

        mlflow.log_metrics(metrics)
        mlflow.log_params(params)
        mlflow.log_text(query, "query.txt")
        mlflow.log_text(answer, "answer.txt")

    def log_agent_metrics(
        self,
        agent_name: str,
        latency_ms: float,
        success: bool,
        metadata: Optional[Dict] = None
    ):
        self._ensure_init()
        if not self._initialized:
            return

        metrics = {
            f"{agent_name}_latency_ms": latency_ms,
            f"{agent_name}_success": 1 if success else 0
        }

        mlflow.log_metrics(metrics)

        if metadata:
            mlflow.log_params({f"{agent_name}_{k}": str(v) for k, v in metadata.items()})

    def log_rag_metrics(
        self,
        query: str,
        retrieved_chunks: int,
        avg_distance: float,
        latency_ms: float
    ):
        self._ensure_init()
        if not self._initialized:
            return

        metrics = {
            "rag_retrieved_chunks": retrieved_chunks,
            "rag_avg_distance": avg_distance,
            "rag_latency_ms": latency_ms
        }

        mlflow.log_metrics(metrics)

    def log_upload_metrics(
        self,
        filename: str,
        chunk_count: int,
        page_count: int,
        file_size: int,
        is_duplicate: bool,
        version: int
    ):
        self._ensure_init()
        if not self._initialized:
            return

        metrics = {
            "upload_chunks": chunk_count,
            "upload_pages": page_count,
            "upload_file_size": file_size,
            "upload_is_duplicate": 1 if is_duplicate else 0,
            "upload_version": version
        }

        params = {
            "upload_filename": filename
        }

        mlflow.log_metrics(metrics)
        mlflow.log_params(params)

    def log_error(
        self,
        error_type: str,
        error_message: str,
        component: str,
        metadata: Optional[Dict] = None
    ):
        self._ensure_init()
        if not self._initialized:
            return

        metrics = {
            "error_count": 1
        }

        mlflow.log_metrics(metrics)

        params = {
            "error_type": error_type,
            "error_component": component,
            "error_message": error_message[:500]
        }

        if metadata:
            params.update({f"error_{k}": str(v) for k, v in metadata.items()})

        mlflow.log_params(params)

    def log_model_comparison(
        self,
        model_name: str,
        latency_ms: float,
        quality_score: float,
        token_count: int
    ):
        self._ensure_init()
        if not self._initialized:
            return

        metrics = {
            f"{model_name}_latency": latency_ms,
            f"{model_name}_quality": quality_score,
            f"{model_name}_tokens": token_count
        }

        mlflow.log_metrics(metrics)

    def create_experiment(self, experiment_name: str, tags: Optional[Dict] = None):
        self._ensure_init()
        if not self._initialized:
            return None

        try:
            experiment_id = mlflow.create_experiment(experiment_name, tags=tags or {})
            return experiment_id
        except Exception as e:
            print(f"Experiment may already exist: {e}")
            return None


mlflow_logger = MLflowLogger()
