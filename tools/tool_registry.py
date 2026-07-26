import json
import time
import warnings
from pathlib import Path
from datetime import datetime
from dataclasses import is_dataclass, asdict
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

TOOL_REGISTRY_VERSION = "v1.1"


class ToolRegistry:

    def __init__(self, session_dir: Optional[Path] = None):
        self._tools: Dict[str, BaseTool] = {}
        self.session_dir = session_dir
        self.execution_sequence: List[str] = []
        self.tool_calls: List[Dict[str, Any]] = []

    def register_tool(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_available_tools(self) -> List[Dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    def get_manifest(self) -> Dict[str, Any]:
        return {
            "tool_registry_version": TOOL_REGISTRY_VERSION,
            "tools": self.get_available_tools()
        }

    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        tool = self.get_tool(name)
        started_at = datetime.now().isoformat()
        start_time = time.perf_counter()

        sanitized_args = self._sanitize_args(kwargs)

        if not tool:
            completed_at = datetime.now().isoformat()
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            err_msg = f"Tool '{name}' is not registered in ToolRegistry."

            record = {
                "tool": name,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_ms": elapsed_ms,
                "arguments": sanitized_args,
                "status": "ERROR",
                "error": err_msg
            }
            output = {
                "status": "error",
                "tool": name,
                "error": err_msg
            }
            self._record_invocation(name, record)
            return output

        try:
            result = tool.execute(**kwargs)
            completed_at = datetime.now().isoformat()
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            record = {
                "tool": name,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_ms": elapsed_ms,
                "arguments": sanitized_args,
                "status": "SUCCESS",
                "error": None
            }
            output = {
                "status": "success",
                "tool": name,
                "execution_time_ms": elapsed_ms,
                "result": result
            }
        except Exception as e:
            completed_at = datetime.now().isoformat()
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            err_msg = str(e)

            record = {
                "tool": name,
                "started_at": started_at,
                "completed_at": completed_at,
                "duration_ms": elapsed_ms,
                "arguments": sanitized_args,
                "status": "ERROR",
                "error": err_msg
            }
            output = {
                "status": "error",
                "tool": name,
                "execution_time_ms": elapsed_ms,
                "error": err_msg,
                "exception_obj": e
            }
            warnings.warn(f"Tool '{name}' execution failed: {e}")

        self._record_invocation(name, record)
        return output

    def _record_invocation(self, tool_name: str, record: Dict[str, Any]):
        self.execution_sequence.append(tool_name)
        self.tool_calls.append(record)

        if self.session_dir:
            try:
                log_file = self.session_dir / "tool_calls.json"
                log_data = {
                    "execution_sequence": self.execution_sequence,
                    "tool_calls": self.tool_calls
                }
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump(log_data, f, indent=2)
            except Exception as e:
                warnings.warn(f"Failed to update tool_calls.json: {e}")

    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for k, v in args.items():
            sanitized[k] = self._make_serializable(v)
        return sanitized

    def _make_serializable(self, obj: Any) -> Any:
        if is_dataclass(obj):
            return asdict(obj)
        elif hasattr(obj, "model_dump"):
            return obj.model_dump()
        elif hasattr(obj, "dict"):
            return obj.dict()
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(v) for v in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return str(obj)
