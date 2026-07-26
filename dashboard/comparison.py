"""
Comparison Module — Baseline vs Optimized comparison widgets.

Renders comparison cards and tables from optimization report data.
All values are sourced exclusively from the report; nothing is hard-coded
or fabricated.

No business logic.  No backend interaction.
"""

import streamlit as st
from typing import Dict, Any, Optional


# ── Color Constants ─────────────────────────────────────────

_GREEN = "#2ECC71"
_RED = "#E74C3C"
_ORANGE = "#E67E22"
_BLUE = "#3498DB"
_TEXT_SEC = "#8899AA"
_SURFACE = "#1E2530"
_BORDER = "#2C3E6B"


# ── Internal Helpers ────────────────────────────────────────


def _format_value(value: Optional[float], unit: str = "Wh",
                  precision: int = 1) -> str:
    """Format a numeric value with human-readable unit scaling."""
    if value is None:
        return "N/A"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.{precision}f} M{unit}"
    if abs(value) >= 1_000:
        return f"{value / 1_000:,.{precision}f} k{unit}"
    return f"{value:,.{precision}f} {unit}"


def _format_delta(value: Optional[float], invert: bool = False) -> str:
    """
    Format a percentage delta with a coloured arrow.

    Parameters
    ----------
    value : float | None
        Percentage change value.
    invert : bool
        If ``True``, a *positive* change is bad (e.g. cooling energy increase).
    """
    if value is None:
        return f'<span style="color:{_TEXT_SEC}">N/A</span>'
    if abs(value) < 0.01:
        return f'<span style="color:{_TEXT_SEC}">— 0.00%</span>'

    is_positive = value > 0
    is_good = is_positive if not invert else not is_positive
    color = _GREEN if is_good else _RED
    arrow = "▲" if is_positive else "▼"

    return (
        f'<span style="color:{color}; font-weight:600">'
        f'{arrow} {abs(value):.2f}%</span>'
    )


def _metric_card(label: str, baseline: str, optimized: str,
                 delta_html: str) -> None:
    """Render a single Baseline → Optimized comparison card."""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {_SURFACE} 0%, #1B2A4A 100%);
        border: 1px solid {_BORDER};
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 12px;
    ">
        <div style="color: {_TEXT_SEC}; font-size: 0.8rem; text-transform: uppercase;
                    letter-spacing: 1px; margin-bottom: 14px; font-weight: 600;">
            {label}
        </div>
        <div style="display: flex; justify-content: space-between;
                    align-items: center; flex-wrap: wrap; gap: 8px;">
            <div style="min-width: 80px;">
                <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                            text-transform: uppercase;">BASELINE</div>
                <div style="color: #FAFAFA; font-size: 1.05rem;
                            font-weight: 500;">{baseline}</div>
            </div>
            <div style="color: {_BLUE}; font-size: 1.2rem;">→</div>
            <div style="min-width: 80px;">
                <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                            text-transform: uppercase;">OPTIMIZED</div>
                <div style="color: #FAFAFA; font-size: 1.05rem;
                            font-weight: 500;">{optimized}</div>
            </div>
            <div style="min-width: 80px;">
                <div style="color: {_TEXT_SEC}; font-size: 0.7rem;
                            text-transform: uppercase;">CHANGE</div>
                <div style="font-size: 1.05rem;">{delta_html}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Public API ──────────────────────────────────────────────


def render_comparison_cards(report: Dict[str, Any]) -> None:
    """Render styled comparison cards for all key metrics."""
    baseline = report.get("baseline", {})
    optimized = report.get("optimized", {})
    improvements = report.get("improvements", {})

    col1, col2 = st.columns(2)

    with col1:
        _metric_card(
            "Total HVAC Energy",
            _format_value(baseline.get("total_hvac_energy_wh")),
            _format_value(optimized.get("total_hvac_energy_wh")),
            _format_delta(improvements.get("total_hvac_energy_reduction_pct")),
        )
        _metric_card(
            "Heating Energy",
            _format_value(baseline.get("heating_energy_wh")),
            _format_value(optimized.get("heating_energy_wh")),
            _format_delta(improvements.get("heating_energy_reduction_pct")),
        )

        # Peak demand — compute from available data
        bph = baseline.get("peak_heating_rate_w")
        bpc = baseline.get("peak_cooling_rate_w")
        oph = optimized.get("peak_heating_rate_w")
        opc = optimized.get("peak_cooling_rate_w")

        peak_base = max(bph, bpc) if bph is not None and bpc is not None else None
        peak_opt = max(oph, opc) if oph is not None and opc is not None else None

        _metric_card(
            "Peak Demand",
            _format_value(peak_base, "W"),
            _format_value(peak_opt, "W"),
            _format_delta(
                improvements.get(
                    "peak_demand_reduction_pct",
                    improvements.get("peak_demand_change_pct"),
                )
            ),
        )

    with col2:
        _metric_card(
            "Cooling Energy",
            _format_value(baseline.get("cooling_energy_wh")),
            _format_value(optimized.get("cooling_energy_wh")),
            _format_delta(
                improvements.get("cooling_energy_change_pct"), invert=True
            ),
        )

        base_comfort = baseline.get("comfort_percentage")
        opt_comfort = optimized.get("comfort_percentage")
        _metric_card(
            "Comfort Percentage",
            f"{base_comfort:.1f}%" if base_comfort is not None else "N/A",
            f"{opt_comfort:.1f}%" if opt_comfort is not None else "N/A",
            _format_delta(improvements.get("comfort_change_pct")),
        )


def render_comparison_table(report: Dict[str, Any]) -> None:
    """Render a full comparison table with professional formatting."""
    baseline = report.get("baseline", {})
    optimized = report.get("optimized", {})
    improvements = report.get("improvements", {})

    def _fv(val: Optional[float], unit: str = "Wh") -> str:
        return _format_value(val, unit)

    def _fd(val: Optional[float]) -> str:
        if val is None:
            return "N/A"
        return f"{val:+.2f}%"

    rows = [
        ("Total HVAC Energy",
         _fv(baseline.get("total_hvac_energy_wh")),
         _fv(optimized.get("total_hvac_energy_wh")),
         _fd(improvements.get("total_hvac_energy_reduction_pct"))),
        ("Heating Energy",
         _fv(baseline.get("heating_energy_wh")),
         _fv(optimized.get("heating_energy_wh")),
         _fd(improvements.get("heating_energy_reduction_pct"))),
        ("Cooling Energy",
         _fv(baseline.get("cooling_energy_wh")),
         _fv(optimized.get("cooling_energy_wh")),
         _fd(improvements.get("cooling_energy_change_pct"))),
        ("Comfort",
         f"{baseline.get('comfort_percentage'):.1f}%"
         if baseline.get("comfort_percentage") is not None else "N/A",
         f"{optimized.get('comfort_percentage'):.1f}%"
         if optimized.get("comfort_percentage") is not None else "N/A",
         _fd(improvements.get("comfort_change_pct"))),
        ("Peak Heating Rate",
         _fv(baseline.get("peak_heating_rate_w"), "W"),
         _fv(optimized.get("peak_heating_rate_w"), "W"),
         "—"),
        ("Peak Cooling Rate",
         _fv(baseline.get("peak_cooling_rate_w"), "W"),
         _fv(optimized.get("peak_cooling_rate_w"), "W"),
         "—"),
    ]

    hdr = (
        "text-align: left; padding: 12px 16px; color: #8899AA; "
        "font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;"
    )
    table = f'<table style="width: 100%; border-collapse: collapse;"><thead><tr style="border-bottom: 2px solid {_BORDER};"><th style="{hdr}">Metric</th><th style="{hdr} text-align: right;">Baseline</th><th style="{hdr} text-align: right;">Optimized</th><th style="{hdr} text-align: right;">Difference</th></tr></thead><tbody>'
    for metric, bv, ov, diff in rows:
        table += f'<tr style="border-bottom: 1px solid {_SURFACE};"><td style="padding: 12px 16px; color: #FAFAFA; font-weight: 500;">{metric}</td><td style="padding: 12px 16px; color: #B0B8C8; text-align: right;">{bv}</td><td style="padding: 12px 16px; color: #FAFAFA; text-align: right; font-weight: 500;">{ov}</td><td style="padding: 12px 16px; color: {_BLUE}; text-align: right; font-weight: 600;">{diff}</td></tr>'
    table += "</tbody></table>"
    st.markdown(table, unsafe_allow_html=True)
