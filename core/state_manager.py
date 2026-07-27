import json
import hashlib
import time
from typing import Any, Dict, Optional, List
from datetime import datetime
from copy import deepcopy
import threading


class StateVersion:

    def __init__(self, version: int, state: Dict, timestamp: float):
        self.version = version
        self.state = state
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "version": self.version,
            "state": self.state,
            "timestamp": self.timestamp
        }


class StateManager:

    def __init__(self, max_versions: int = 50):

        self._states: Dict[str, Dict] = {}
        self._versions: Dict[str, List[StateVersion]] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self._max_versions = max_versions
        self._global_lock = threading.Lock()

    def _get_lock(self, state_id: str) -> threading.Lock:

        if state_id not in self._locks:
            with self._global_lock:
                if state_id not in self._locks:
                    self._locks[state_id] = threading.Lock()

        return self._locks[state_id]

    def create_state(self, state_id: str, initial_state: Dict) -> Dict:

        lock = self._get_lock(state_id)

        with lock:
            self._states[state_id] = deepcopy(initial_state)
            self._versions[state_id] = [
                StateVersion(1, deepcopy(initial_state), time.time())
            ]

            return deepcopy(self._states[state_id])

    def get_state(self, state_id: str) -> Optional[Dict]:

        lock = self._get_lock(state_id)

        with lock:
            if state_id not in self._states:
                return None

            return deepcopy(self._states[state_id])

    def update_state(self, state_id: str, updates: Dict) -> Optional[Dict]:

        lock = self._get_lock(state_id)

        with lock:
            if state_id not in self._states:
                return None

            self._states[state_id].update(updates)

            version = len(self._versions.get(state_id, [])) + 1
            self._versions.setdefault(state_id, []).append(
                StateVersion(version, deepcopy(self._states[state_id]), time.time())
            )

            if len(self._versions[state_id]) > self._max_versions:
                self._versions[state_id] = self._versions[state_id][-self._max_versions:]

            return deepcopy(self._states[state_id])

    def delete_state(self, state_id: str) -> bool:

        lock = self._get_lock(state_id)

        with lock:
            if state_id in self._states:
                del self._states[state_id]
                self._versions.pop(state_id, None)
                return True

            return False

    def get_version_history(self, state_id: str) -> List[Dict]:

        lock = self._get_lock(state_id)

        with lock:
            versions = self._versions.get(state_id, [])
            return [v.to_dict() for v in versions]

    def rollback(self, state_id: str, target_version: int) -> Optional[Dict]:

        lock = self._get_lock(state_id)

        with lock:
            versions = self._versions.get(state_id, [])

            for version in reversed(versions):
                if version.version <= target_version:
                    self._states[state_id] = deepcopy(version.state)
                    return deepcopy(self._states[state_id])

            return None

    def compute_checksum(self, state_id: str) -> Optional[str]:

        lock = self._get_lock(state_id)

        with lock:
            if state_id not in self._states:
                return None

            state_str = json.dumps(self._states[state_id], sort_keys=True)
            return hashlib.sha256(state_str.encode()).hexdigest()

    def list_states(self) -> List[str]:

        with self._global_lock:
            return list(self._states.keys())

    def clear(self):

        with self._global_lock:
            self._states.clear()
            self._versions.clear()
            self._locks.clear()


state_manager = StateManager(max_versions=50)


class DeterministicWorkflow:

    def __init__(self):

        self._step_history: Dict[str, List[Dict]] = {}
        self._checkpoints: Dict[str, Dict] = {}

    def _generate_step_id(self, workflow_id: str, step_name: str) -> str:

        history = self._step_history.get(workflow_id, [])
        step_number = len(history) + 1
        return f"{workflow_id}:{step_name}:{step_number}"

    def start_workflow(self, workflow_id: str, initial_state: Dict) -> Dict:

        state_manager.create_state(workflow_id, initial_state)

        self._step_history[workflow_id] = []

        self.save_checkpoint(workflow_id, "start", initial_state)

        return {
            "workflow_id": workflow_id,
            "status": "started",
            "state": state_manager.get_state(workflow_id)
        }

    def execute_step(
        self,
        workflow_id: str,
        step_name: str,
        step_function,
        *args,
        **kwargs
    ) -> Dict:

        start_time = time.time()

        state = state_manager.get_state(workflow_id)
        if state is None:
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "error": "Workflow not found"
            }

        try:
            result = step_function(state, *args, **kwargs)

            latency_ms = (time.time() - start_time) * 1000

            step_record = {
                "step_name": step_name,
                "step_id": self._generate_step_id(workflow_id, step_name),
                "status": "completed",
                "latency_ms": latency_ms,
                "timestamp": time.time()
            }

            self._step_history.setdefault(workflow_id, []).append(step_record)

            state_manager.update_state(workflow_id, result)

            self.save_checkpoint(workflow_id, step_name, state_manager.get_state(workflow_id))

            return {
                "workflow_id": workflow_id,
                "status": "step_completed",
                "step": step_name,
                "latency_ms": latency_ms
            }

        except Exception as e:

            step_record = {
                "step_name": step_name,
                "step_id": self._generate_step_id(workflow_id, step_name),
                "status": "failed",
                "error": str(e),
                "timestamp": time.time()
            }

            self._step_history.setdefault(workflow_id, []).append(step_record)

            return {
                "workflow_id": workflow_id,
                "status": "step_failed",
                "step": step_name,
                "error": str(e)
            }

    def save_checkpoint(self, workflow_id: str, checkpoint_name: str, state: Dict):

        self._checkpoints[f"{workflow_id}:{checkpoint_name}"] = {
            "state": deepcopy(state),
            "timestamp": time.time(),
            "checkpoint_name": checkpoint_name
        }

    def load_checkpoint(self, workflow_id: str, checkpoint_name: str) -> Optional[Dict]:

        key = f"{workflow_id}:{checkpoint_name}"

        if key in self._checkpoints:
            return deepcopy(self._checkpoints[key]["state"])

        return None

    def get_workflow_history(self, workflow_id: str) -> List[Dict]:

        return self._step_history.get(workflow_id, [])

    def complete_workflow(self, workflow_id: str) -> Dict:

        history = self.get_workflow_history(workflow_id)

        final_state = state_manager.get_state(workflow_id)

        self._step_history.pop(workflow_id, None)

        checkpoint_keys = [k for k in self._checkpoints if k.startswith(workflow_id)]
        for key in checkpoint_keys:
            del self._checkpoints[key]

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "total_steps": len(history),
            "final_state": final_state,
            "history": history
        }


deterministic_workflow = DeterministicWorkflow()
