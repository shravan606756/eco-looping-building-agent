"""
Dashboard Controller — Thin interface between the Streamlit UI and the
optimization backend.

Architecture:
    Streamlit UI (app.py) → DashboardController → ClosedLoopAgent / WorkspaceReset / ReportReader

All backend interaction flows through this module.  The Streamlit UI should
never import backend classes directly.

No UI rendering is performed here.
"""

import sys
import io
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class DashboardController:
    """Single entry-point for every backend operation the dashboard requires."""

    def __init__(self) -> None:
        from config import OUTPUT_DIR, OPTIMIZED_IDF, WEATHER_FILE

        self._output_dir: Path = OUTPUT_DIR
        self._optimized_idf: Path = OPTIMIZED_IDF
        self._weather_file: Path = WEATHER_FILE

    # ── Report Loading ──────────────────────────────────────

    def load_report_json(self) -> Optional[Dict[str, Any]]:
        """Load ``optimization_report.json``.  Returns *None* if unavailable."""
        from utils.report_reader import ReportReader
        return ReportReader.read_report(self._output_dir)

    def load_report_markdown(self) -> Optional[str]:
        """Load ``optimization_report.md`` as text.  Returns *None* if unavailable."""
        md_path = self._output_dir / "optimization_report.md"
        if not md_path.exists():
            return None
        try:
            return md_path.read_text(encoding="utf-8")
        except Exception:
            return None

    def load_report_csv(self) -> Optional[str]:
        """Load ``optimization_summary.csv`` as text.  Returns *None* if unavailable."""
        csv_path = self._output_dir / "optimization_summary.csv"
        if not csv_path.exists():
            return None
        try:
            return csv_path.read_text(encoding="utf-8")
        except Exception:
            return None

    def load_optimized_idf_bytes(self) -> Optional[bytes]:
        """Load ``optimized.idf`` as bytes for download.  Returns *None* if unavailable."""
        if not self._optimized_idf.exists():
            return None
        try:
            return self._optimized_idf.read_bytes()
        except Exception:
            return None

    # ── Status Checks ───────────────────────────────────────

    def has_optimized_idf(self) -> bool:
        """Check whether ``optimized.idf`` exists on disk."""
        return self._optimized_idf.exists()

    def has_reports(self) -> bool:
        """Check whether ``optimization_report.json`` exists on disk."""
        return (self._output_dir / "optimization_report.json").exists()

    def get_weather_file_name(self) -> str:
        """Return the configured weather-file basename."""
        return self._weather_file.name if self._weather_file.exists() else "Not configured"

    # ── Backend Actions ─────────────────────────────────────

    def run_optimization(self, max_iterations: int = 3) -> Dict[str, Any]:
        """
        Execute a full closed-loop optimization.

        Captures *stdout* from the backend so the dashboard can display
        console logs without modifying backend code.

        Returns
        -------
        dict
            ``status`` — ``"success"`` | ``"error"``
            ``result`` — optimization result dict (on success)
            ``logs``   — captured stdout text
            ``error``  — error message (on failure)
        """
        log_capture = io.StringIO()
        old_stdout = sys.stdout

        try:
            sys.stdout = log_capture

            from optimizer.closed_loop_agent import ClosedLoopAgent
            from config import OUTPUT_DIR

            agent = ClosedLoopAgent()
            result = agent.run_optimization(
                max_iterations=max_iterations,
                output_root=OUTPUT_DIR,
            )

            sys.stdout = old_stdout
            return {
                "status": "success",
                "result": result,
                "logs": log_capture.getvalue(),
            }

        except Exception as e:
            sys.stdout = old_stdout
            return {
                "status": "error",
                "error": str(e),
                "logs": log_capture.getvalue(),
            }

    def reset_workspace(self) -> Dict[str, Any]:
        """
        Reset the optimization workspace via the backend utility.

        Returns
        -------
        dict
            ``status``  — ``"success"`` | ``"error"``
            ``actions`` — list of actions performed
            ``error``   — error message (on failure)
        """
        try:
            from utils.workspace_reset import WorkspaceReset

            reset_util = WorkspaceReset()
            result = reset_util.reset_workspace()
            return {
                "status": "success",
                "actions": result.get("actions", []),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "actions": [],
            }

    def can_continue(self) -> Tuple[bool, str]:
        """
        Check whether the *Continue* operation is supported.

        The backend does not expose a resume / restore API, so this
        always returns ``(False, reason)``.
        """
        return (
            False,
            "Resume optimization is currently unavailable. "
            "The backend does not support mid-session restore.",
        )
