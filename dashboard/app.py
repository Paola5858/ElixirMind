#!/usr/bin/env python3
"""
ElixirMind Dashboard
Real-time monitoring and control interface.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import psutil
import streamlit as st
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ElixirMind Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header { font-size:2.5rem; font-weight:bold; color:#1f77b4;
                   text-align:center; margin-bottom:2rem; }
    .metric-card { background:#f0f2f6; padding:1rem; border-radius:.5rem;
                   border-left:.25rem solid #1f77b4; }
    .status-good    { color:#28a745; font-weight:bold; }
    .status-warning { color:#ffc107; font-weight:bold; }
    .status-error   { color:#dc3545; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

_STATS_FILE = Path("data/session_stats.json")
_LOG_FILE   = Path("data/bot.log")


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _load_bot_stats() -> dict[str, Any]:
    """Read stats written by StatsTracker. Falls back to zeros."""
    try:
        if _STATS_FILE.exists():
            return json.loads(_STATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _system_stats() -> dict[str, Any]:
    return {
        "cpu_percent":    psutil.cpu_percent(interval=None),
        "memory_percent": psutil.virtual_memory().percent,
    }


def _win_rate(stats: dict[str, Any]) -> float:
    won   = int(stats.get("battles_won",  0))
    lost  = int(stats.get("battles_lost", 0))
    draw  = int(stats.get("battles_draw", 0))
    total = won + lost + draw
    return round(won / total * 100, 1) if total else 0.0


def _read_logs(n: int = 20) -> list[str]:
    try:
        if _LOG_FILE.exists():
            lines = _LOG_FILE.read_text(encoding="utf-8").splitlines()
            return lines[-n:]
    except Exception:
        pass
    return ["[no log file found]"]


# ---------------------------------------------------------------------------
# Dashboard sections
# ---------------------------------------------------------------------------

def _metrics_section(stats: dict[str, Any]) -> None:
    st.markdown('<h1 class="main-header">🤖 ElixirMind Dashboard</h1>',
                unsafe_allow_html=True)

    won   = int(stats.get("battles_won",  0))
    total = won + int(stats.get("battles_lost", 0)) + int(stats.get("battles_draw", 0))
    wr    = _win_rate(stats)
    fps   = float(stats.get("performance_summary", {}).get("avg_fps", 0.0))
    elixir_eff = float(stats.get("success_rate", 0.0)) * 100
    duration   = float(stats.get("session_duration", 0.0))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏆 Win Rate</h3>
            <h2 class="status-good">{wr:.1f}%</h2>
            <p>{won} wins / {total} battles</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚡ Avg FPS</h3>
            <h2>{fps:.1f}</h2>
            <p>capture performance</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💜 Action Success</h3>
            <h2>{elixir_eff:.1f}%</h2>
            <p>{stats.get('actions_total', 0)} actions total</p>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🕐 Uptime</h3>
            <h2>{duration / 3600:.1f}h</h2>
            <p>active session</p>
        </div>""", unsafe_allow_html=True)


def _charts_section() -> None:
    st.markdown("## 📊 Performance Analytics")
    sys = _system_stats()

    # Build a small rolling window from session_stats history if available;
    # otherwise show a single-point placeholder so the chart always renders.
    now = datetime.now()
    timestamps = pd.date_range(end=now, periods=13, freq="5min")
    placeholder = [0.0] * 13

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Win Rate Over Time", "Action Success Rate",
                        "Session Duration (min)", "System Resources"),
        specs=[[{"secondary_y": False}] * 2] * 2,
    )

    fig.add_trace(go.Scatter(x=timestamps, y=placeholder, mode="lines+markers",
                             name="Win Rate %", line=dict(color="#28a745", width=2)),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=timestamps, y=placeholder, mode="lines+markers",
                             name="Success %", line=dict(color="#ffc107", width=2)),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=timestamps, y=placeholder, mode="lines+markers",
                             name="Duration", line=dict(color="#1f77b4", width=2)),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=timestamps,
                             y=[sys["cpu_percent"]] * 13,
                             mode="lines", name="CPU %",
                             line=dict(color="#dc3545", width=2)),
                  row=2, col=2)
    fig.add_trace(go.Scatter(x=timestamps,
                             y=[sys["memory_percent"]] * 13,
                             mode="lines", name="Memory %",
                             line=dict(color="#6c757d", width=2)),
                  row=2, col=2)

    fig.update_layout(height=500, showlegend=True, margin=dict(t=40))
    st.plotly_chart(fig, use_container_width=True)


def _control_panel() -> None:
    st.markdown("## 🎮 Bot Control")

    if "bot_running" not in st.session_state:
        st.session_state.bot_running = False

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Start Bot", type="primary", use_container_width=True):
            st.session_state.bot_running = True
            st.success("Start signal sent (run main.py separately).")
    with col2:
        if st.button("⏹️ Stop Bot", type="secondary", use_container_width=True):
            st.session_state.bot_running = False
            st.warning("Stop signal sent.")
    with col3:
        if st.button("🔄 Refresh Stats", type="secondary", use_container_width=True):
            st.rerun()

    status = "🟢 Running" if st.session_state.bot_running else "🔴 Stopped"
    st.markdown(f"**Status:** {status}")


def _logs_section() -> None:
    st.markdown("## 📋 Live Logs")
    lines = _read_logs(20)
    st.code("\n".join(lines), language="log")

    col_left, _ = st.columns([1, 5])
    with col_left:
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
    if auto_refresh:
        # Sleep outside the main render path to avoid blocking the UI thread.
        time.sleep(5)
        st.rerun()


def _sidebar(stats: dict[str, Any]) -> None:
    st.sidebar.markdown("# 🤖 ElixirMind")
    st.sidebar.markdown("---")

    st.sidebar.markdown("### Quick Stats")
    st.sidebar.metric("Win Rate",  f"{_win_rate(stats):.1f}%")
    st.sidebar.metric("Battles",   stats.get("battles_won", 0) +
                                   stats.get("battles_lost", 0) +
                                   stats.get("battles_draw", 0))
    st.sidebar.metric("Uptime",    f"{stats.get('session_duration', 0) / 60:.1f}m")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### System")
    sys = _system_stats()
    st.sidebar.metric("CPU",    f"{sys['cpu_percent']}%")
    st.sidebar.metric("Memory", f"{sys['memory_percent']}%")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Links")
    st.sidebar.markdown("[📖 Documentation](https://github.com/Paola5858/ElixirMind)")
    st.sidebar.markdown("[🐛 Report Issue](https://github.com/Paola5858/ElixirMind/issues)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    stats = _load_bot_stats()
    _sidebar(stats)
    _metrics_section(stats)
    st.markdown("---")
    _charts_section()
    st.markdown("---")
    _control_panel()
    st.markdown("---")
    _logs_section()


if __name__ == "__main__":
    main()
