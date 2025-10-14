"""
ElixirMind Streamlit Dashboard
Real-time monitoring and control interface for the bot.
"""

import streamlit as st
import time
import json
from pathlib import Path
import sys
import asyncio
import threading
from datetime import datetime, timedelta

# Add parent directory to path to import bot modules
sys.path.append(str(Path(__file__).parent.parent))

try:
    from config import Config, get_config
    from stats.tracker import StatsTracker
    from stats.charts import ChartsGenerator
    from screen_capture import ScreenCapture
    from vision.detector import GameStateDetector
    import numpy as np
    import cv2
except ImportError as e:
    st.error(f"Failed to import bot modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="ElixirMind Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
}

.status-running {
    color: #28a745;
}

.status-stopped {
    color: #dc3545;
}

.status-warning {
    color: #ffc107;
}

.big-font {
    font-size: 2rem !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


class DashboardApp:
    """Main dashboard application class."""

    def __init__(self):
        self.config = None
        self.stats_tracker = None
        self.charts_generator = ChartsGenerator()

        # Initialize session state
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'bot_status' not in st.session_state:
            st.session_state.bot_status = 'Stopped'

        if 'last_update' not in st.session_state:
            st.session_state.last_update = time.time()

        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None

        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True

    def load_config(self):
        """Load bot configuration."""
        try:
            self.config = get_config()
            return True
        except Exception as e:
            st.error(f"Failed to load configuration: {e}")
            return False

    def load_stats(self):
        """Load statistics tracker."""
        try:
            if self.config:
                self.stats_tracker = StatsTracker(self.config)
                return True
            return False
        except Exception as e:
            st.error(f"Failed to load statistics: {e}")
            return False

    def render_sidebar(self):
        """Render dashboard sidebar."""
        with st.sidebar:
            st.title("🤖 ElixirMind")
            st.markdown("---")

            # Bot Status
            status = st.session_state.bot_status
            if status == 'Running':
                st.markdown('<p class="status-running">🟢 Bot is Running</p>',
                            unsafe_allow_html=True)
            elif status == 'Stopped':
                st.markdown('<p class="status-stopped">🔴 Bot is Stopped</p>',
                            unsafe_allow_html=True)
            else:
                st.markdown('<p class="status-warning">🟡 Bot Status Unknown</p>',
                            unsafe_allow_html=True)

            st.markdown("---")

            # Controls
            st.subheader("Controls")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ Start Bot", disabled=(status == 'Running')):
                    st.session_state.bot_status = 'Starting'
                    st.rerun()

            with col2:
                if st.button("⏹️ Stop Bot", disabled=(status == 'Stopped')):
                    st.session_state.bot_status = 'Stopping'
                    st.rerun()

            # Settings
            st.markdown("---")
            st.subheader("Settings")

            st.session_state.auto_refresh = st.checkbox("Auto Refresh",
                                                        value=st.session_state.auto_refresh)

            refresh_interval = st.slider(
                "Refresh Interval (seconds)", 1, 30, 5)

            # Configuration
            if st.button("Reload Configuration"):
                self.load_config()
                self.load_stats()
                st.success("Configuration reloaded!")

            # Export
            st.markdown("---")
            st.subheader("Export")

            if st.button("Export Statistics"):
                if self.stats_tracker:
                    export_file = self.stats_tracker.export_stats("json")
                    if export_file:
                        st.success(
                            f"Stats exported to: {Path(export_file).name}")
                    else:
                        st.error("Export failed")
                else:
                    st.error("Statistics not available")

    def render_main_dashboard(self):
        """Render main dashboard content."""
        # Header
        st.title("🎮 ElixirMind Dashboard")
        st.markdown("Real-time monitoring for your autonomous Clash Royale bot")

        # Auto refresh
        if st.session_state.auto_refresh:
            time.sleep(1)  # Small delay
            st.rerun()

        # Get current stats
        current_stats = self._get_current_stats()
        overall_stats = self._get_overall_stats()

        # Main metrics row
        self._render_metrics_row(current_stats, overall_stats)

        # Charts section
        self._render_charts_section(overall_stats)

        # Recent activity
        self._render_recent_activity()

        # Live game state (if bot is running)
        if st.session_state.bot_status == 'Running':
            self._render_live_game_state()

    def _render_metrics_row(self, current_stats: dict, overall_stats: dict):
        """Render main metrics row."""
        st.subheader("📊 Current Performance")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            win_rate = overall_stats.get('win_rate', 0) * 100
            st.metric(
                label="Win Rate",
                value=f"{win_rate:.1f}%",
                delta=f"+{win_rate - 50:.1f}%" if win_rate > 50 else f"{win_rate - 50:.1f}%"
            )

        with col2:
            success_rate = overall_stats.get('success_rate', 0) * 100
            st.metric(
                label="Action Success Rate",
                value=f"{success_rate:.1f}%",
                delta=f"+{success_rate - 75:.1f}%" if success_rate > 75 else f"{success_rate - 75:.1f}%"
            )

        with col3:
            total_battles = overall_stats.get('total_battles', 0)
            st.metric(
                label="Total Battles",
                value=str(total_battles)
            )

        with col4:
            avg_decision_time = overall_stats.get(
                'average_decision_time', 0) * 1000
            st.metric(
                label="Avg Decision Time",
                value=f"{avg_decision_time:.0f}ms"
            )

        # Session info
        if current_stats:
            st.markdown("---")
            st.subheader("🎯 Current Session")

            col1, col2, col3 = st.columns(3)

            with col1:
                session_duration = current_stats.get('duration_minutes', 0)
                st.metric("Session Duration", f"{session_duration:.1f} min")

            with col2:
                session_actions = current_stats.get('actions_taken', 0)
                st.metric("Actions Taken", str(session_actions))

            with col3:
                session_success = current_stats.get('success_rate', 0) * 100
                st.metric("Session Success Rate", f"{session_success:.1f}%")

    def _render_charts_section(self, overall_stats: dict):
        """Render charts section."""
        st.markdown("---")
        st.subheader("📈 Performance Analytics")

        # Performance overview
        try:
            overview_chart = self.charts_generator.create_performance_overview(
                overall_stats)
            st.plotly_chart(overview_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create overview chart: {e}")

        # Two column layout for additional charts
        col1, col2 = st.columns(2)

        with col1:
            # Battle results
            try:
                if self.stats_tracker:
                    sessions = [
                        s.__dict__ for s in self.stats_tracker.session_history]
                    battle_chart = self.charts_generator.create_battle_results_chart(
                        sessions)
                    st.plotly_chart(battle_chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to create battle results chart: {e}")

        with col2:
            # Strategy comparison
            try:
                strategy_stats = overall_stats.get('strategy_performance', {})
                strategy_chart = self.charts_generator.create_strategy_comparison(
                    strategy_stats)
                st.plotly_chart(strategy_chart, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to create strategy chart: {e}")

        # Performance timeline
        try:
            if self.stats_tracker:
                trends = self.stats_tracker.get_performance_trends(24)
                timeline_chart = self.charts_generator.create_performance_timeline(
                    trends)
                st.plotly_chart(timeline_chart, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create timeline chart: {e}")

    def _render_recent_activity(self):
        """Render recent activity section."""
        st.markdown("---")
        st.subheader("📋 Recent Activity")

        if self.stats_tracker and self.stats_tracker.session_history:
            # Show last 5 sessions
            recent_sessions = self.stats_tracker.session_history[-5:]

            for session in reversed(recent_sessions):
                with st.container():
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        session_time = datetime.fromtimestamp(
                            session.start_time)
                        st.write(f"**{session_time.strftime('%H:%M:%S')}**")

                    with col2:
                        result_emoji = {'win': '🏆', 'loss': '💔', 'draw': '🤝'}.get(
                            session.battle_result, '❓')
                        st.write(
                            f"{result_emoji} {session.battle_result.title()}")

                    with col3:
                        st.write(f"Actions: {session.actions_taken}")

                    with col4:
                        success_rate = (
                            session.successful_actions / max(1, session.actions_taken)) * 100
                        st.write(f"Success: {success_rate:.1f}%")

                    st.markdown("---")
        else:
            st.info("No recent activity data available")

    def _render_live_game_state(self):
        """Render live game state section."""
        st.markdown("---")
        st.subheader("🎮 Live Game State")

        # Placeholder for live game state
        # In a real implementation, this would show:
        # - Current screenshot
        # - Detected cards
        # - Elixir level
        # - Enemy troops
        # - Next planned action

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Game Screen**")
            # Placeholder for screenshot
            st.info("Screenshot capture would appear here")

        with col2:
            st.markdown("**Detected State**")

            # Mock game state data
            game_state_data = {
                "Current Elixir": "7/10",
                "Cards in Hand": "Knight, Archers, Fireball, Giant",
                "Enemy Troops": "2 detected",
                "Battle Phase": "Mid-game",
                "Next Action": "Place Knight at bridge"
            }

            for key, value in game_state_data.items():
                st.text(f"{key}: {value}")

    def _get_current_stats(self) -> dict:
        """Get current session statistics."""
        try:
            if self.stats_tracker:
                return self.stats_tracker.get_current_session_stats()
            return {}
        except Exception as e:
            st.error(f"Failed to get current stats: {e}")
            return {}

    def _get_overall_stats(self) -> dict:
        """Get overall statistics."""
        try:
            if self.stats_tracker:
                return self.stats_tracker.get_overall_stats()
            return {}
        except Exception as e:
            st.error(f"Failed to get overall stats: {e}")
            return {}

    def run(self):
        """Run the dashboard application."""
        # Load configuration and stats
        if not self.load_config():
            st.stop()

        if not self.load_stats():
            st.stop()

        # Render sidebar
        self.render_sidebar()

        # Render main dashboard
        self.render_main_dashboard()

        # Footer
        st.markdown("---")
        st.markdown("*ElixirMind Dashboard - Autonomous Clash Royale Bot*")

        # Update timestamp
        st.caption(
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# Main execution
if __name__ == "__main__":
    dashboard = DashboardApp()
    dashboard.run()
