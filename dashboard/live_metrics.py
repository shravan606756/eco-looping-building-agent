"""
Optimization Metrics Module — Widgets for displaying optimization progress
and iteration results.

Renders iteration-by-iteration data from completed optimization reports.
All values are sourced exclusively from the report.  No data is fabricated
and no real-time streaming is simulated.

Terminology note
~~~~~~~~~~~~~~~~
The backend executes synchronously and does not expose real-time callbacks.
Functions in this module use terms like "status panel" and "iteration
results" rather than "live metrics" to remain technically accurate.
"""

import streamlit as st
from typing import Dict, Any, List, Optional


# ── Colors ──────────────────────────────────────────────────

_GREEN = "#2ECC71"
_ORANGE = "#E67E22"
_RED = "#E74C3C"
_BLUE = "#3498DB"
_TEXT_SEC = "#8899AA"
_SURFACE = "#1E2530"
_BORDER = "#2C3E6B"
_DARK_BLUE = "#1B2A4A"


# ── Progress ────────────────────────────────────────────────


def render_progress_bar(current: int, maximum: int, stage: str = "") -> None:
    """Render a styled CSS progress bar showing iteration completion."""
    pct = min(current / maximum, 1.0) if maximum > 0 else 0.0

    st.markdown(f"""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between;
                    margin-bottom: 6px;">
            <span style="color: #FAFAFA; font-weight: 500;
                         font-size: 0.95rem;">
                Iteration {current} / {maximum}
            </span>
            <span style="color: {_TEXT_SEC}; font-size: 0.85rem;">
                {stage}
            </span>
        </div>
        <div style="background: {_SURFACE}; border-radius: 6px;
                    height: 8px; overflow: hidden;
                    border: 1px solid {_BORDER};">
            <div style="
                background: linear-gradient(90deg, {_BLUE}, {_GREEN});
                width: {pct * 100:.0f}%;
                height: 100%;
                border-radius: 6px;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Status Panel ────────────────────────────────────────────


def render_status_panel(report: Dict[str, Any]) -> None:
    """Render optimization status cards sourced from the report."""
    opt = report.get("optimization", {})
    iterations = opt.get("iterations")
    runtime = opt.get("runtime_seconds")
    h_sp = opt.get("final_heating_setpoint")
    c_sp = opt.get("final_cooling_setpoint")

    def _val(v: Any, suffix: str = "", fmt: Optional[str] = None) -> str:
        if v is None:
            return "N/A"
        if fmt:
            return f"{v:{fmt}}{suffix}"
        return f"{v}{suffix}"

    cards = [
        ("Status", "Converged", _GREEN),
        ("Iterations", _val(iterations), _BLUE),
        ("Runtime", _val(runtime, "s", ".1f"), _BLUE),
        (
            "Final Setpoints",
            f"H: {_val(h_sp, '°C')}  C: {_val(c_sp, '°C')}",
            _ORANGE,
        ),
    ]

    cols = st.columns(len(cards))
    for col, (label, value, accent) in zip(cols, cards):
        with col:
            txt_color = accent if label == "Status" else "#FAFAFA"
            st.markdown(f"""
            <div style="background: {_SURFACE};
                        border-left: 3px solid {accent};
                        padding: 16px; border-radius: 6px;">
                <div style="color: {_TEXT_SEC}; font-size: 0.75rem;
                            text-transform: uppercase;
                            letter-spacing: 0.5px;">{label}</div>
                <div style="color: {txt_color}; font-size: 1.2rem;
                            font-weight: 600;
                            margin-top: 4px;">{value}</div>
            </div>
            """, unsafe_allow_html=True)


# ── Iteration Engineering Assessment ────────────────────────


def render_iteration_assessment(records: List[Dict[str, Any]]) -> None:
    """Render per-iteration engineering assessment cards.

    All values come from ``iteration_records`` in the report.
    """
    if not records:
        st.info("No iteration data available.")
        return

    for rec in records:
        iteration = rec.get("iteration", "?")
        hvac_mode = rec.get("hvac_mode", "N/A")
        temp_trend = rec.get("temperature_trend", "N/A")
        comfort = rec.get("comfort_percentage")
        comfort_str = f"{comfort:.1f}%" if comfort is not None else "N/A"

        h_energy = rec.get("total_heating_energy_wh")
        c_energy = rec.get("total_cooling_energy_wh")
        h_str = f"{h_energy:,.1f} Wh" if h_energy is not None else "N/A"
        c_str = f"{c_energy:,.1f} Wh" if c_energy is not None else "N/A"

        st.markdown(f"""
        <div style="background: {_SURFACE}; border: 1px solid {_BORDER};
                    border-radius: 8px; padding: 16px; margin-bottom: 10px;">
            <div style="color: {_BLUE}; font-weight: 600;
                        margin-bottom: 10px; font-size: 0.95rem;">
                Iteration {iteration}
            </div>
            <div style="display: flex; gap: 32px; flex-wrap: wrap;">
                <div>
                    <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                                text-transform: uppercase;
                                letter-spacing: 0.5px;">HVAC Mode</div>
                    <div style="color: #FAFAFA; font-weight: 500;
                                margin-top: 2px;">{hvac_mode}</div>
                </div>
                <div>
                    <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                                text-transform: uppercase;
                                letter-spacing: 0.5px;">Temp Trend</div>
                    <div style="color: #FAFAFA; font-weight: 500;
                                margin-top: 2px;">{temp_trend}</div>
                </div>
                <div>
                    <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                                text-transform: uppercase;
                                letter-spacing: 0.5px;">Comfort</div>
                    <div style="color: #FAFAFA; font-weight: 500;
                                margin-top: 2px;">{comfort_str}</div>
                </div>
                <div>
                    <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                                text-transform: uppercase;
                                letter-spacing: 0.5px;">Heating</div>
                    <div style="color: {_ORANGE}; font-weight: 500;
                                margin-top: 2px;">{h_str}</div>
                </div>
                <div>
                    <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                                text-transform: uppercase;
                                letter-spacing: 0.5px;">Cooling</div>
                    <div style="color: {_BLUE}; font-weight: 500;
                                margin-top: 2px;">{c_str}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Iteration LLM Decisions ─────────────────────────────────


def render_iteration_decisions(records: List[Dict[str, Any]]) -> None:
    """Render LLM decisions for each iteration.

    Setpoint deltas are computed from consecutive iterations present in the
    report.  No default values are assumed — if the previous iteration's
    setpoint is unavailable the delta is shown as *N/A*.
    """
    if not records:
        st.info("No iteration decision data available.")
        return

    for i, rec in enumerate(records):
        iteration = rec.get("iteration", "?")
        reason = rec.get("reason", "No reason recorded")
        h_sp = rec.get("heating_setpoint")
        c_sp = rec.get("cooling_setpoint")

        # Compute deltas from consecutive report records only
        if i > 0:
            prev_h = records[i - 1].get("heating_setpoint")
            prev_c = records[i - 1].get("cooling_setpoint")
            h_delta = (h_sp - prev_h) if (h_sp is not None and prev_h is not None) else None
            c_delta = (c_sp - prev_c) if (c_sp is not None and prev_c is not None) else None
        else:
            # First iteration — no previous record to compare against
            h_delta = None
            c_delta = None

        h_delta_str = f"{h_delta:+.1f}°C" if h_delta is not None else "N/A"
        c_delta_str = f"{c_delta:+.1f}°C" if c_delta is not None else "N/A"
        h_sp_str = f"{h_sp:.1f}°C" if h_sp is not None else "N/A"
        c_sp_str = f"{c_sp:.1f}°C" if c_sp is not None else "N/A"

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {_SURFACE} 0%,
                                {_DARK_BLUE} 100%);
                    border: 1px solid {_BORDER}; border-radius: 10px;
                    padding: 20px; margin-bottom: 12px;">
            <div style="color: {_BLUE}; font-weight: 600;
                        font-size: 0.95rem; margin-bottom: 12px;">
                Iteration {iteration} — LLM Decision
            </div>
            <div style="display: flex; gap: 24px; margin-bottom: 14px;
                        flex-wrap: wrap;">
                <div style="background: rgba(0,0,0,0.2);
                            border-radius: 6px; padding: 10px 16px;">
                    <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                                text-transform: uppercase;">Heating SP</div>
                    <div style="color: {_ORANGE}; font-weight: 600;
                                font-size: 1.1rem;">{h_sp_str}</div>
                    <div style="color: {_TEXT_SEC};
                                font-size: 0.75rem;">Δ {h_delta_str}</div>
                </div>
                <div style="background: rgba(0,0,0,0.2);
                            border-radius: 6px; padding: 10px 16px;">
                    <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                                text-transform: uppercase;">Cooling SP</div>
                    <div style="color: {_BLUE}; font-weight: 600;
                                font-size: 1.1rem;">{c_sp_str}</div>
                    <div style="color: {_TEXT_SEC};
                                font-size: 0.75rem;">Δ {c_delta_str}</div>
                </div>
            </div>
            <div style="color: #B0B8C8; font-size: 0.9rem; line-height: 1.5;
                        border-top: 1px solid rgba(255,255,255,0.1);
                        padding-top: 12px;">
                <strong style="color: {_TEXT_SEC};">Reasoning:</strong>
                {reason}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Log Window ──────────────────────────────────────────────


def render_log_window(logs: Optional[str]) -> None:
    """Render a scrollable console-output viewer."""
    if not logs:
        st.info("No optimization logs available.")
        return

    # Escape HTML characters in the log text
    import html as _html
    safe_logs = _html.escape(logs)

    st.markdown(f"""
    <div style="
        background: #0a0a0a;
        border: 1px solid {_BORDER};
        border-radius: 8px;
        padding: 16px;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
        font-size: 0.8rem;
        line-height: 1.6;
        color: #A0A0A0;
        white-space: pre-wrap;
        word-wrap: break-word;
    ">{safe_logs}</div>
    """, unsafe_allow_html=True)
