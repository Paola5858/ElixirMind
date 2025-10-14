#!/usr/bin/env python3
"""
ElixirMind Dashboard
Real-time monitoring and control interface.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import time
import psutil
import json
from pathlib import Path
from datetime import datetime, timedelta
import threading
import queue

# Dashboard configuration
st.set_page_config(
    page_title="ElixirMind Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #1f77b4;
    }
    .status-good {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class DashboardApp:
    def __init__(self):
        self.data_queue = queue.Queue()
        self.is_running = False
        self.stats_history = []
        self.start_time = datetime.now()

        # Load configuration
        self.load_config()

    def load_config(self):
        """Load dashboard configuration"""
        try:
            with open("auto_config.json", "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {"settings": {}, "config": {}}

    def get_system_stats(self):
        """Get current system statistics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "timestamp": datetime.now()
        }

    def get_bot_stats(self):
        """Get bot performance statistics"""
        # This would normally connect to the running bot
        # For demo purposes, we'll simulate data
        return {
            "battles_played": 15,
            "battles_won": 10,
            "win_rate": 66.7,
            "avg_decision_time": 180,
            "cards_played": 127,
            "elixir_efficiency": 78.5,
            "current_fps": 12.5,
            "uptime_minutes": (datetime.now() - self.start_time).total_seconds() / 60
        }

    def create_metrics_section(self):
        """Create the main metrics display"""
        st.markdown('<h1 class="main-header">🤖 ElixirMind Dashboard</h1>', unsafe_allow_html=True)

        # Get current stats
        system_stats = self.get_system_stats()
        bot_stats = self.get_bot_stats()

        # Top row - Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🏆 Win Rate</h3>
                <h2 class="status-good">{:.1f}%</h2>
                <p>{} wins / {} battles</p>
            </div>
            """.format(
                bot_stats["win_rate"],
                bot_stats["battles_won"],
                bot_stats["battles_played"]
            ), unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>⚡ Performance</h3>
                <h2>{:.1f} FPS</h2>
                <p>{:.0f}ms avg decision</p>
            </div>
            """.format(
                bot_stats["current_fps"],
                bot_stats["avg_decision_time"]
            ), unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>💜 Elixir Efficiency</h3>
                <h2>{:.1f}%</h2>
                <p>{} cards played</p>
            </div>
            """.format(
                bot_stats["elixir_efficiency"],
                bot_stats["cards_played"]
            ), unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div class="metric-card">
                <h3>🕐 Uptime</h3>
                <h2>{:.1f}h</h2>
                <p>Active session</p>
            </div>
            """.format(
                bot_stats["uptime_minutes"] / 60
            ), unsafe_allow_html=True)

    def create_charts_section(self):
        """Create performance charts"""
        st.markdown("## 📊 Performance Analytics")

        # Create sample data for charts
        timestamps = pd.date_range(start=datetime.now() - timedelta(hours=1),
                                 end=datetime.now(), freq='5min')
        win_rates = [65, 67, 63, 70, 68, 72, 69, 71, 68, 73, 70, 75, 72]
        fps_data = [11.5, 12.1, 11.8, 12.3, 12.0, 12.5, 12.2, 12.4, 12.1, 12.6, 12.3, 12.7, 12.5]
        elixir_data = [75, 78, 76, 80, 77, 82, 79, 81, 78, 83, 80, 85, 82]

        # Performance over time chart
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Win Rate Over Time", "FPS Performance", "Elixir Efficiency", "System Resources"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": True}]]
        )

        # Win rate
        fig.add_trace(
            go.Scatter(x=timestamps, y=win_rates, mode='lines+markers', name='Win Rate %',
                      line=dict(color='#28a745', width=3)),
            row=1, col=1
        )

        # FPS
        fig.add_trace(
            go.Scatter(x=timestamps, y=fps_data, mode='lines+markers', name='FPS',
                      line=dict(color='#1f77b4', width=3)),
            row=1, col=2
        )

        # Elixir efficiency
        fig.add_trace(
            go.Scatter(x=timestamps, y=elixir_data, mode='lines+markers', name='Elixir %',
                      line=dict(color='#ffc107', width=3)),
            row=2, col=1
        )

        # System resources
        cpu_data = [45, 52, 48, 55, 51, 58, 54, 57, 53, 60, 56, 59, 55]
        memory_data = [68, 72, 70, 75, 73, 78, 76, 79, 74, 80, 77, 81, 78]

        fig.add_trace(
            go.Scatter(x=timestamps, y=cpu_data, mode='lines', name='CPU %',
                      line=dict(color='#dc3545', width=2)),
            row=2, col=2
        )

        fig.add_trace(
            go.Scatter(x=timestamps, y=memory_data, mode='lines', name='Memory %',
                      line=dict(color='#6c757d', width=2)),
            row=2, col=2, secondary_y=False
        )

        fig.update_layout(height=600, showlegend=True)
        fig.update_xaxes(title_text="Time", row=2, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=2)
        fig.update_yaxes(title_text="Percentage", row=1, col=1)
        fig.update_yaxes(title_text="FPS", row=1, col=2)
        fig.update_yaxes(title_text="Efficiency %", row=2, col=1)
        fig.update_yaxes(title_text="Usage %", row=2, col=2)

        st.plotly_chart(fig, use_container_width=True)

    def create_control_panel(self):
        """Create bot control panel"""
        st.markdown("## 🎮 Bot Control")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("▶️ Start Bot", type="primary", use_container_width=True):
                st.success("Bot started! (simulated)")
                self.is_running = True

        with col2:
            if st.button("⏹️ Stop Bot", type="secondary", use_container_width=True):
                st.warning("Bot stopped! (simulated)")
                self.is_running = False

        with col3:
            if st.button("🔄 Restart Bot", type="secondary", use_container_width=True):
                st.info("Bot restarted! (simulated)")
                self.is_running = True

        # Status indicator
        status_color = "🟢 Running" if self.is_running else "🔴 Stopped"
        st.markdown(f"**Status:** {status_color}")

    def create_logs_section(self):
        """Create live logs display"""
        st.markdown("## 📋 Live Logs")

        # Sample log entries
        log_entries = [
            "[2024-01-15 14:30:15] INFO: Battle detected! Starting autonomous play",
            "[2024-01-15 14:30:16] INFO: Cards detected: Knight, Archers, Giant, P.E.K.K.A",
            "[2024-01-15 14:30:17] INFO: Elixir at 8/10 - deploying Knight for defense",
            "[2024-01-15 14:30:18] SUCCESS: Card deployed successfully",
            "[2024-01-15 14:30:25] INFO: Elixir at 6/10 - waiting for regeneration",
            "[2024-01-15 14:30:32] INFO: Enemy tower damaged - maintaining pressure",
            "[2024-01-15 14:30:45] INFO: Elixir at 9/10 - deploying Giant",
            "[2024-01-15 14:30:46] SUCCESS: Card deployed successfully",
            "[2024-01-15 14:31:02] INFO: Battle won! +25 trophies",
            "[2024-01-15 14:31:03] INFO: Session stats updated"
        ]

        # Display logs in a scrollable container
        log_text = "\n".join(log_entries[-10:])  # Show last 10 entries

        st.code(log_text, language="log")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh logs", value=True)
        if auto_refresh:
            time.sleep(2)
            st.rerun()

    def create_sidebar(self):
        """Create sidebar with navigation and info"""
        st.sidebar.markdown("# 🤖 ElixirMind")
        st.sidebar.markdown("---")

        # Navigation
        st.sidebar.markdown("### Navigation")
        page = st.sidebar.radio(
            "Go to:",
            ["Dashboard", "Configuration", "Training", "Logs", "About"],
            label_visibility="collapsed"
        )

        st.sidebar.markdown("---")

        # Quick stats
        st.sidebar.markdown("### Quick Stats")
        bot_stats = self.get_bot_stats()

        st.sidebar.metric("Win Rate", f"{bot_stats['win_rate']}%")
        st.sidebar.metric("Battles", bot_stats['battles_played'])
        st.sidebar.metric("Uptime", f"{bot_stats['uptime_minutes']:.1f}m")

        st.sidebar.markdown("---")

        # System info
        st.sidebar.markdown("### System")
        system_stats = self.get_system_stats()

        st.sidebar.metric("CPU", f"{system_stats['cpu_percent']}%")
        st.sidebar.metric("Memory", f"{system_stats['memory_percent']}%")

        st.sidebar.markdown("---")

        # Links
        st.sidebar.markdown("### Links")
        st.sidebar.markdown("[📖 Documentation](https://github.com/your-username/ElixirMind)")
        st.sidebar.markdown("[🐛 Report Issue](https://github.com/your-username/ElixirMind/issues)")
        st.sidebar.markdown("[💬 Discord](https://discord.gg/elixirmind)")

    def run(self):
        """Main dashboard loop"""
        self.create_sidebar()

        # Main content based on page
        if st.session_state.get('page', 'Dashboard') == 'Dashboard':
            self.create_metrics_section()
            st.markdown("---")
            self.create_charts_section()
            st.markdown("---")
            self.create_control_panel()
            st.markdown("---")
            self.create_logs_section()

def main():
    dashboard = DashboardApp()
    dashboard.run()

if __name__ == "__main__":
    main()
