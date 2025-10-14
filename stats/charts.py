"""
ElixirMind Charts Generator
Creates performance visualization charts for the dashboard.
"""

import logging
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


class ChartsGenerator:
    """Generates various performance charts and visualizations."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Chart color scheme
        self.colors = {
            'primary': '#1f77b4',
            'success': '#2ca02c',
            'warning': '#ff7f0e',
            'danger': '#d62728',
            'info': '#17becf',
            'background': '#f8f9fa'
        }

    def create_performance_overview(self, stats: Dict[str, Any]) -> go.Figure:
        """Create overview performance chart."""
        try:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Win Rate', 'Action Success Rate',
                                'Decision Speed', 'Battles Played'),
                specs=[[{"type": "indicator"}, {"type": "indicator"}],
                       [{"type": "indicator"}, {"type": "indicator"}]]
            )

            # Win Rate Gauge
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=stats.get('win_rate', 0) * 100,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Win Rate %"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': self.colors['success']},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "gray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ),
                row=1, col=1
            )

            # Success Rate Gauge
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=stats.get('success_rate', 0) * 100,
                    title={'text': "Action Success %"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': self.colors['primary']},
                        'steps': [
                            {'range': [0, 60], 'color': "lightgray"},
                            {'range': [60, 85], 'color': "gray"}
                        ]
                    }
                ),
                row=1, col=2
            )

            # Decision Time Indicator
            avg_decision_time = stats.get(
                'average_decision_time', 0) * 1000  # Convert to ms
            fig.add_trace(
                go.Indicator(
                    mode="number+delta",
                    value=avg_decision_time,
                    title={'text': "Avg Decision Time (ms)"},
                    delta={'reference': 500, 'relative': True},
                    number={'suffix': ' ms'}
                ),
                row=2, col=1
            )

            # Total Battles Indicator
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=stats.get('total_battles', 0),
                    title={'text': "Total Battles"},
                    number={'font': {'color': self.colors['info']}}
                ),
                row=2, col=2
            )

            fig.update_layout(
                height=500,
                title_text="ElixirMind Performance Overview",
                title_x=0.5
            )

            return fig

        except Exception as e:
            self.logger.error(
                f"Performance overview chart creation failed: {e}")
            return self._create_error_chart("Performance Overview Error")

    def create_battle_results_chart(self, sessions: List[Dict]) -> go.Figure:
        """Create battle results pie chart."""
        try:
            if not sessions:
                return self._create_empty_chart("No battle data available")

            # Count battle results
            results = {'win': 0, 'loss': 0, 'draw': 0}
            for session in sessions:
                result = session.get('battle_result', 'unknown')
                if result in results:
                    results[result] += 1

            fig = go.Figure(data=[
                go.Pie(
                    labels=['Wins', 'Losses', 'Draws'],
                    values=[results['win'], results['loss'], results['draw']],
                    hole=0.3,
                    marker_colors=[self.colors['success'],
                                   self.colors['danger'], self.colors['warning']]
                )
            ])

            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                title_text="Battle Results Distribution",
                title_x=0.5,
                height=400
            )

            return fig

        except Exception as e:
            self.logger.error(f"Battle results chart creation failed: {e}")
            return self._create_error_chart("Battle Results Error")

    def create_performance_timeline(self, trends: Dict[str, List]) -> go.Figure:
        """Create performance timeline chart."""
        try:
            hourly_data = trends.get('hourly_performance', [])

            if not hourly_data:
                return self._create_empty_chart("No timeline data available")

            hours = [d['hour'] for d in hourly_data]
            win_rates = [d['win_rate'] * 100 for d in hourly_data]
            session_counts = [d['sessions'] for d in hourly_data]

            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Win Rate Over Time', 'Activity Level'),
                vertical_spacing=0.1
            )

            # Win rate line
            fig.add_trace(
                go.Scatter(
                    x=hours,
                    y=win_rates,
                    mode='lines+markers',
                    name='Win Rate %',
                    line=dict(color=self.colors['success'], width=3)
                ),
                row=1, col=1
            )

            # Session count bars
            fig.add_trace(
                go.Bar(
                    x=hours,
                    y=session_counts,
                    name='Battles Played',
                    marker_color=self.colors['primary']
                ),
                row=2, col=1
            )

            fig.update_xaxes(title_text="Hours Ago", row=2, col=1)
            fig.update_yaxes(title_text="Win Rate %", row=1, col=1)
            fig.update_yaxes(title_text="Battles", row=2, col=1)

            fig.update_layout(
                height=600,
                title_text="Performance Timeline (Last 24 Hours)",
                title_x=0.5,
                showlegend=False
            )

            return fig

        except Exception as e:
            self.logger.error(
                f"Performance timeline chart creation failed: {e}")
            return self._create_error_chart("Timeline Error")

    def create_elixir_efficiency_chart(self, elixir_data: List[Dict]) -> go.Figure:
        """Create elixir usage efficiency chart."""
        try:
            if not elixir_data:
                return self._create_empty_chart("No elixir data available")

            # Process elixir data
            timestamps = [datetime.fromtimestamp(
                d['timestamp']) for d in elixir_data]
            elixir_levels = [d['elixir'] for d in elixir_data]

            # Calculate moving average
            window_size = min(10, len(elixir_levels))
            if window_size > 1:
                moving_avg = pd.Series(elixir_levels).rolling(
                    window=window_size).mean()
            else:
                moving_avg = elixir_levels

            fig = go.Figure()

            # Raw elixir levels
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=elixir_levels,
                    mode='lines',
                    name='Elixir Level',
                    line=dict(color=self.colors['info'], width=1),
                    opacity=0.6
                )
            )

            # Moving average
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=moving_avg,
                    mode='lines',
                    name='Moving Average',
                    line=dict(color=self.colors['primary'], width=3)
                )
            )

            # Add optimal elixir zones
            fig.add_hline(y=10, line_dash="dash", line_color="red",
                          annotation_text="Max Elixir")
            fig.add_hline(y=5, line_dash="dash", line_color="orange",
                          annotation_text="Optimal Range")

            fig.update_layout(
                title="Elixir Usage Efficiency",
                xaxis_title="Time",
                yaxis_title="Elixir Level",
                height=400,
                yaxis=dict(range=[0, 10])
            )

            return fig

        except Exception as e:
            self.logger.error(f"Elixir efficiency chart creation failed: {e}")
            return self._create_error_chart("Elixir Chart Error")

    def create_strategy_comparison(self, strategy_stats: Dict[str, Dict]) -> go.Figure:
        """Create strategy performance comparison chart."""
        try:
            if not strategy_stats:
                return self._create_empty_chart("No strategy data available")

            strategies = list(strategy_stats.keys())
            success_rates = [stats['success_rate'] *
                             100 for stats in strategy_stats.values()]
            decision_times = [stats['avg_decision_time'] *
                              1000 for stats in strategy_stats.values()]

            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Success Rate Comparison',
                                'Decision Time Comparison'),
                specs=[[{"type": "bar"}, {"type": "bar"}]]
            )

            # Success rate comparison
            fig.add_trace(
                go.Bar(
                    x=strategies,
                    y=success_rates,
                    name='Success Rate %',
                    marker_color=self.colors['success']
                ),
                row=1, col=1
            )

            # Decision time comparison
            fig.add_trace(
                go.Bar(
                    x=strategies,
                    y=decision_times,
                    name='Avg Decision Time (ms)',
                    marker_color=self.colors['warning']
                ),
                row=1, col=2
            )

            fig.update_yaxes(title_text="Success Rate %", row=1, col=1)
            fig.update_yaxes(title_text="Decision Time (ms)", row=1, col=2)

            fig.update_layout(
                height=400,
                title_text="Strategy Performance Comparison",
                title_x=0.5,
                showlegend=False
            )

            return fig

        except Exception as e:
            self.logger.error(
                f"Strategy comparison chart creation failed: {e}")
            return self._create_error_chart("Strategy Comparison Error")

    def create_action_heatmap(self, action_data: List[Dict]) -> go.Figure:
        """Create action placement heatmap."""
        try:
            if not action_data:
                return self._create_empty_chart("No action data available")

            # Extract positions from actions
            x_positions = []
            y_positions = []

            for action in action_data:
                if 'target_position' in action:
                    pos = action['target_position']
                    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        x_positions.append(pos[0])
                        y_positions.append(pos[1])

            if not x_positions:
                return self._create_empty_chart("No valid position data")

            # Create heatmap
            fig = go.Figure(data=go.Histogram2d(
                x=x_positions,
                y=y_positions,
                colorscale='Blues',
                nbinsx=20,
                nbinsy=15
            ))

            fig.update_layout(
                title="Action Placement Heatmap",
                xaxis_title="X Position",
                yaxis_title="Y Position",
                height=500
            )

            return fig

        except Exception as e:
            self.logger.error(f"Action heatmap creation failed: {e}")
            return self._create_error_chart("Heatmap Error")

    def create_real_time_metrics(self, current_stats: Dict) -> go.Figure:
        """Create real-time metrics display."""
        try:
            fig = make_subplots(
                rows=1, cols=4,
                subplot_titles=('Current Elixir', 'Actions/Min',
                                'Success Rate', 'Session Time'),
                specs=[[{"type": "indicator"}] * 4]
            )

            # Current Elixir
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=current_stats.get('current_elixir', 0),
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Elixir"},
                    gauge={
                        'axis': {'range': [None, 10]},
                        'bar': {'color': self.colors['info']},
                        'steps': [
                            {'range': [0, 3], 'color': "lightgray"},
                            {'range': [3, 7], 'color': "gray"}
                        ]
                    }
                ),
                row=1, col=1
            )

            # Actions per minute
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=current_stats.get('actions_per_minute', 0),
                    title={'text': "Actions/Min"},
                    number={'font': {'color': self.colors['primary']}}
                ),
                row=1, col=2
            )

            # Success rate
            fig.add_trace(
                go.Indicator(
                    mode="number+delta",
                    value=current_stats.get('success_rate', 0) * 100,
                    title={'text': "Success %"},
                    delta={'reference': 75, 'relative': False},
                    number={'suffix': '%'}
                ),
                row=1, col=3
            )

            # Session time
            session_minutes = current_stats.get('duration_minutes', 0)
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=session_minutes,
                    title={'text': "Session (min)"},
                    number={'font': {'color': self.colors['warning']}}
                ),
                row=1, col=4
            )

            fig.update_layout(
                height=300,
                title_text="Real-Time Performance Metrics",
                title_x=0.5
            )

            return fig

        except Exception as e:
            self.logger.error(f"Real-time metrics chart creation failed: {e}")
            return self._create_error_chart("Real-Time Metrics Error")

    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create empty placeholder chart."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor='white',
            height=400
        )
        return fig

    def _create_error_chart(self, error_message: str) -> go.Figure:
        """Create error placeholder chart."""
        fig = go.Figure()
        fig.add_annotation(
            text=f"❌ {error_message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="red")
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor='#ffe6e6',
            height=300
        )
        return fig
