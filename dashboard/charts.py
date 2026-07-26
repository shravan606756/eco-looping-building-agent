"""
Charts Module — All visualization logic for the Eco-Loop dashboard.

Every chart function accepts report data (``dict``) and returns a Plotly
figure or ``None`` when insufficient data is available.

No business logic.  No Streamlit state manipulation.  No data fabrication.

Sections
--------
Energy   — Heating, Cooling, Total HVAC energy per iteration
Control  — Setpoint progression
Comfort  — Comfort percentage per iteration
Summary  — Energy breakdown pie, optimization timeline
"""

import plotly.graph_objects as go
from typing import Dict, Any, List, Optional


# ── Theme Constants ─────────────────────────────────────────

_DARK_BLUE = "#1B2A4A"
_ACCENT_BLUE = "#3498DB"
_GREEN = "#2ECC71"
_ORANGE = "#E67E22"
_RED = "#E74C3C"
_BG = "#0E1117"
_SURFACE = "#1E2530"
_TEXT = "#FAFAFA"
_TEXT_SEC = "#8899AA"
_GRID = "#1E2530"
_BORDER = "#2C3E6B"

_LAYOUT_BASE: Dict[str, Any] = dict(
    template="plotly_dark",
    paper_bgcolor=_BG,
    plot_bgcolor=_BG,
    font=dict(
        family="Inter, system-ui, -apple-system, sans-serif",
        size=13,
        color=_TEXT,
    ),
    margin=dict(l=60, r=30, t=50, b=50),
    hoverlabel=dict(bgcolor=_SURFACE, font_size=13, bordercolor=_BORDER),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
)


def _base_layout(**overrides: Any) -> Dict[str, Any]:
    """Build a Plotly layout dict from the base template with caller overrides."""
    layout = dict(_LAYOUT_BASE)
    layout.update(overrides)

    # Ensure axis styling is always applied
    for key in ("xaxis", "yaxis"):
        defaults = dict(gridcolor=_GRID, zerolinecolor=_GRID, linecolor=_BORDER)
        if key in overrides and isinstance(overrides[key], dict):
            defaults.update(overrides[key])
        layout[key] = defaults
    return layout


def _get_records(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract ``iteration_records`` from the report dict."""
    return report.get("iteration_records", [])


# ════════════════════════════════════════════════════════════
#  Energy Section
# ════════════════════════════════════════════════════════════


def render_heating_energy_chart(report: Dict[str, Any]) -> Optional[go.Figure]:
    """Line chart — heating energy (Wh) per iteration."""
    records = _get_records(report)
    if not records:
        return None

    iters = [r["iteration"] for r in records]
    values = [r.get("total_heating_energy_wh", 0) for r in records]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=iters, y=values,
        mode="lines+markers",
        name="Heating Energy",
        line=dict(color=_ORANGE, width=2.5),
        marker=dict(size=8, color=_ORANGE, line=dict(width=1, color=_TEXT)),
        hovertemplate="Iteration %{x}<br>%{y:,.1f} Wh<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        title="Heating Energy per Iteration",
        xaxis=dict(title="Iteration", dtick=1),
        yaxis=dict(title="Energy (Wh)"),
    ))
    return fig


def render_cooling_energy_chart(report: Dict[str, Any]) -> Optional[go.Figure]:
    """Line chart — cooling energy (Wh) per iteration."""
    records = _get_records(report)
    if not records:
        return None

    iters = [r["iteration"] for r in records]
    values = [r.get("total_cooling_energy_wh", 0) for r in records]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=iters, y=values,
        mode="lines+markers",
        name="Cooling Energy",
        line=dict(color=_ACCENT_BLUE, width=2.5),
        marker=dict(size=8, color=_ACCENT_BLUE, line=dict(width=1, color=_TEXT)),
        hovertemplate="Iteration %{x}<br>%{y:,.1f} Wh<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        title="Cooling Energy per Iteration",
        xaxis=dict(title="Iteration", dtick=1),
        yaxis=dict(title="Energy (Wh)"),
    ))
    return fig


def render_total_hvac_energy_chart(report: Dict[str, Any]) -> Optional[go.Figure]:
    """Stacked line chart — heating, cooling, and total HVAC energy."""
    records = _get_records(report)
    if not records:
        return None

    iters = [r["iteration"] for r in records]
    heating = [r.get("total_heating_energy_wh", 0) for r in records]
    cooling = [r.get("total_cooling_energy_wh", 0) for r in records]
    total = [h + c for h, c in zip(heating, cooling)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=iters, y=heating, mode="lines+markers", name="Heating",
        line=dict(color=_ORANGE, width=2), marker=dict(size=6),
    ))
    fig.add_trace(go.Scatter(
        x=iters, y=cooling, mode="lines+markers", name="Cooling",
        line=dict(color=_ACCENT_BLUE, width=2), marker=dict(size=6),
    ))
    fig.add_trace(go.Scatter(
        x=iters, y=total, mode="lines+markers", name="Total HVAC",
        line=dict(color=_GREEN, width=3), marker=dict(size=8),
    ))
    fig.update_layout(**_base_layout(
        title="Total HVAC Energy per Iteration",
        xaxis=dict(title="Iteration", dtick=1),
        yaxis=dict(title="Energy (Wh)"),
    ))
    return fig


# ════════════════════════════════════════════════════════════
#  Control Section
# ════════════════════════════════════════════════════════════


def render_setpoint_progression_chart(report: Dict[str, Any]) -> Optional[go.Figure]:
    """Dual-line chart — heating and cooling setpoints per iteration."""
    records = _get_records(report)
    if not records:
        return None

    iters = [r["iteration"] for r in records]
    h_sp = [r.get("heating_setpoint") for r in records]
    c_sp = [r.get("cooling_setpoint") for r in records]

    # Skip if setpoint data is entirely absent
    if all(v is None for v in h_sp) and all(v is None for v in c_sp):
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=iters, y=h_sp, mode="lines+markers", name="Heating Setpoint",
        line=dict(color=_ORANGE, width=2.5),
        marker=dict(size=8, symbol="triangle-up"),
        hovertemplate="Iteration %{x}<br>%{y:.1f}°C<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=iters, y=c_sp, mode="lines+markers", name="Cooling Setpoint",
        line=dict(color=_ACCENT_BLUE, width=2.5),
        marker=dict(size=8, symbol="triangle-down"),
        hovertemplate="Iteration %{x}<br>%{y:.1f}°C<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        title="Setpoint Progression",
        xaxis=dict(title="Iteration", dtick=1),
        yaxis=dict(title="Temperature (°C)"),
    ))
    return fig


# ════════════════════════════════════════════════════════════
#  Comfort Section
# ════════════════════════════════════════════════════════════


def render_comfort_chart(report: Dict[str, Any]) -> Optional[go.Figure]:
    """Line chart — comfort percentage per iteration (with fill)."""
    records = _get_records(report)
    if not records:
        return None

    iters = [r["iteration"] for r in records]
    comfort = [r.get("comfort_percentage") for r in records]

    if all(v is None for v in comfort):
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=iters, y=comfort,
        mode="lines+markers",
        name="Comfort %",
        line=dict(color=_GREEN, width=2.5),
        marker=dict(size=8, color=_GREEN),
        fill="tozeroy",
        fillcolor="rgba(46, 204, 113, 0.1)",
        hovertemplate="Iteration %{x}<br>%{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        title="Comfort Percentage per Iteration",
        xaxis=dict(title="Iteration", dtick=1),
        yaxis=dict(title="Comfort (%)", range=[0, 105]),
    ))
    return fig


# ════════════════════════════════════════════════════════════
#  Summary Section
# ════════════════════════════════════════════════════════════


def render_energy_breakdown_pie(report: Dict[str, Any]) -> Optional[go.Figure]:
    """Donut pie — final heating vs cooling energy split."""
    optimized = report.get("optimized", {})
    heating = optimized.get("heating_energy_wh", 0)
    cooling = optimized.get("cooling_energy_wh", 0)

    if heating == 0 and cooling == 0:
        return None

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=["Heating", "Cooling"],
        values=[heating, cooling],
        marker=dict(colors=[_ORANGE, _ACCENT_BLUE]),
        textinfo="label+percent",
        textfont=dict(size=14),
        hole=0.45,
        hovertemplate="%{label}<br>%{value:,.1f} Wh<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        title="Energy Breakdown — Optimized",
        showlegend=True,
    ))
    return fig


def render_optimization_timeline(report: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Bar chart — runtime per iteration.

    Returns ``None`` because the backend does **not** store per-iteration
    runtime in the report.  The chart is intentionally omitted rather than
    fabricating data.
    """
    return None
