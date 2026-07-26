import json
import hashlib
import warnings
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, is_dataclass
from typing import Dict, Any, Optional

from models.building_state import BuildingState
from ai.decision_schema import Decision


class IterationLogger:

    def __init__(self, base_log_dir: Optional[Path] = None, session_name: Optional[str] = None):
        try:
            if base_log_dir is None:
                base_log_dir = Path("logs")

            if session_name is None:
                session_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.session_dir = base_log_dir / session_name
            self.session_dir.mkdir(parents=True, exist_ok=True)
            self.start_time = datetime.now().isoformat()
            self.history = []
        except Exception as e:
            warnings.warn(f"IterationLogger initialization warning: {e}")
            self.session_dir = None
            self.start_time = datetime.now().isoformat()
            self.history = []

    def log_iteration(
        self,
        iteration: int,
        building_state: BuildingState,
        prompt: str,
        prompt_sections: Dict[str, str],
        raw_response: str,
        decision: Decision,
        system_prompt: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        if self.session_dir is None:
            warnings.warn("IterationLogger session directory is not available. Skipping log.")
            return False

        try:
            iter_dir = self.session_dir / f"iteration_{iteration:03d}"
            iter_dir.mkdir(parents=True, exist_ok=True)

            # 1. building_state.json
            state_data = asdict(building_state) if is_dataclass(building_state) else building_state
            with open(iter_dir / "building_state.json", "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)

            # 2. prompt.txt
            with open(iter_dir / "prompt.txt", "w", encoding="utf-8") as f:
                f.write(prompt)

            # 3. prompt.json
            with open(iter_dir / "prompt.json", "w", encoding="utf-8") as f:
                json.dump(prompt_sections, f, indent=2)

            # 4. llm_response.json
            try:
                raw_json_obj = json.loads(raw_response)
            except Exception:
                raw_json_obj = {"raw_response": raw_response}

            with open(iter_dir / "llm_response.json", "w", encoding="utf-8") as f:
                json.dump(raw_json_obj, f, indent=2)

            # 5. decision.json
            decision_data = decision.model_dump() if hasattr(decision, "model_dump") else decision.dict()
            with open(iter_dir / "decision.json", "w", encoding="utf-8") as f:
                json.dump(decision_data, f, indent=2)

            # 6. metadata.json
            meta = {
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "simulation_window_hours": 24,
                "weather_file": "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
                "idf_file": "5ZoneAirCooled.idf",
                "prompt_version": "v2",
                "system_prompt_hash": hashlib.md5(system_prompt.encode()).hexdigest() if system_prompt else "",
                "user_prompt_hash": hashlib.md5(prompt.encode()).hexdigest() if prompt else "",
                "llm_model": "llama-3.3-70b-versatile",
                "runtime_seconds": round(metadata.get("response_time_ms", 0) / 1000.0, 3) if metadata else 0.0,
                "tool_registry_version": "v1.1"
            }

            if metadata:
                meta.update(metadata)
                if "response_time_ms" in metadata:
                    meta["runtime_seconds"] = round(metadata["response_time_ms"] / 1000.0, 3)


            with open(iter_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            self.history.append({
                "iteration": iteration,
                "response_time_ms": meta.get("response_time_ms", 0),
                "selected_candidate_index": decision.selected_candidate_index
            })

            return True

        except Exception as e:
            warnings.warn(f"IterationLogger log_iteration failed: {e}")
            return False

    def finalize_session(self, summary_data: Optional[Dict[str, Any]] = None) -> bool:
        if self.session_dir is None:
            warnings.warn("IterationLogger session directory is not available. Skipping summary.")
            return False

        try:
            total_iterations = len(self.history)
            avg_time = (
                sum(h["response_time_ms"] for h in self.history) / total_iterations
                if total_iterations > 0 else 0
            )
            final_candidate = self.history[-1]["selected_candidate_index"] if total_iterations > 0 else 0

            summary = {
                "iterations": total_iterations,
                "converged": True,
                "start_time": self.start_time,
                "end_time": datetime.now().isoformat(),
                "average_response_time_ms": round(avg_time, 2),
                "final_selected_candidate_index": final_candidate
            }

            if summary_data:
                summary.update(summary_data)

            with open(self.session_dir / "summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

            return True

        except Exception as e:
            warnings.warn(f"IterationLogger finalize_session failed: {e}")
            return False
