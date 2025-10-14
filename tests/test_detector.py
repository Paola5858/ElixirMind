"""
ElixirMind Vision Detector Tests
Unit tests for the game state detection system.
"""

from config import Config
from vision.detector import GameStateDetector, GameState, ElixirDetector, BattleDetector
import pytest
import numpy as np
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class TestGameStateDetector:
    """Tests for GameStateDetector class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        config = Config()
        config.YOLO_MODEL_PATH = "test_model.pt"
        config.CARD_TEMPLATES_PATH = "test_templates/"
        return config

    @pytest.fixture
    def detector(self, config):
        """Create detector instance."""
        return GameStateDetector(config)

    def test_detector_initialization(self, detector):
        """Test detector initializes correctly."""
        assert detector is not None
        assert detector.config is not None
        assert detector.yolo_model is None  # Not loaded yet

    @pytest.mark.asyncio
    async def test_load_models(self, detector):
        """Test model loading."""
        # Mock torch.hub.load to avoid actual model download
        with patch('torch.hub.load') as mock_load:
            mock_load.return_value = Mock()
            result = await detector.load_models()
            assert result is True

    @pytest.mark.asyncio
    async def test_analyze_frame_empty(self, detector):
        """Test frame analysis with empty frame."""
        empty_frame = np.zeros((100, 100, 3), dtype=np.uint8)

        # Mock dependencies
        with patch.object(detector.battle_detector, 'is_in_battle', return_value=False):
            result = await detector.analyze_frame(empty_frame)

        assert isinstance(result, GameState)
        assert result.in_battle is False

    @pytest.mark.asyncio
    async def test_analyze_frame_in_battle(self, detector):
        """Test frame analysis during battle."""
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        # Mock all detector methods
        with patch.object(detector.battle_detector, 'is_in_battle', return_value=True), \
                patch.object(detector.elixir_detector, 'detect_elixir', return_value={'amount': 5, 'confidence': 0.8}), \
                patch.object(detector, '_detect_cards_in_hand', return_value=[]), \
                patch.object(detector, '_detect_troops_yolo', return_value={'enemy': [], 'friendly': []}), \
                patch.object(detector, '_detect_towers', return_value={}):

            result = await detector.analyze_frame(test_frame)

        assert isinstance(result, GameState)
        assert result.in_battle is True
        assert result.current_elixir == 5


class TestElixirDetector:
    """Tests for ElixirDetector class."""

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def elixir_detector(self, config):
        return ElixirDetector(config)

    @pytest.mark.asyncio
    async def test_detect_elixir_empty_region(self, elixir_detector):
        """Test elixir detection with empty region."""
        empty_region = np.array([])
        result = await elixir_detector.detect_elixir(empty_region)

        assert result['amount'] == 0
        assert result['confidence'] == 0.0

    @pytest.mark.asyncio
    async def test_detect_elixir_color_method(self, elixir_detector):
        """Test color-based elixir detection."""
        # Create purple-tinted region (simulating elixir)
        purple_region = np.full((100, 50, 3), [150, 0, 200], dtype=np.uint8)

        elixir_detector.config.ELIXIR_DETECTION_METHOD = "color"
        result = await elixir_detector.detect_elixir(purple_region)

        assert isinstance(result['amount'], int)
        assert 0 <= result['amount'] <= 10
        assert 0.0 <= result['confidence'] <= 1.0


class TestBattleDetector:
    """Tests for BattleDetector class."""

    @pytest.fixture
    def config(self):
        return Config()

    @pytest.fixture
    def battle_detector(self, config):
        return BattleDetector(config)

    @pytest.mark.asyncio
    async def test_battle_detection_empty_frame(self, battle_detector):
        """Test battle detection with empty frame."""
        empty_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = await battle_detector.is_in_battle(empty_frame)
        assert result is False

    @pytest.mark.asyncio
    async def test_battle_detection_with_elixir(self, battle_detector):
        """Test battle detection with elixir colors present."""
        # Create frame with purple region (simulating elixir bar)
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        # Add purple region where elixir should be
        roi = battle_detector.config.ROI_ELIXIR
        frame[roi[1]:roi[3], roi[0]:roi[2]] = [150, 0, 200]  # Purple color

        result = await battle_detector.is_in_battle(frame)
        # Result may vary based on exact color matching, but should not crash
        assert isinstance(result, bool)

# Integration tests


class TestDetectorIntegration:
    """Integration tests for detector components."""

    @pytest.fixture
    def config(self):
        config = Config()
        config.DEBUG_MODE = True
        return config

    @pytest.mark.asyncio
    async def test_full_detection_pipeline(self, config):
        """Test complete detection pipeline."""
        detector = GameStateDetector(config)

        # Create realistic test frame
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        # Mock model loading
        with patch('torch.hub.load'):
            await detector.load_models()

        # Run detection
        result = await detector.analyze_frame(test_frame)

        # Verify result structure
        assert isinstance(result, GameState)
        assert hasattr(result, 'in_battle')
        assert hasattr(result, 'current_elixir')
        assert hasattr(result, 'cards_in_hand')
        assert hasattr(result, 'enemy_troops')
        assert hasattr(result, 'friendly_troops')

    @pytest.mark.asyncio
    async def test_performance_metrics(self, config):
        """Test performance metrics collection."""
        detector = GameStateDetector(config)

        # Run several detections
        test_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

        for _ in range(5):
            await detector.analyze_frame(test_frame)

        # Check performance stats
        stats = detector.get_performance_stats()
        assert 'avg_detection_time' in stats
        assert 'detection_fps' in stats
        assert len(stats['recent_times']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
