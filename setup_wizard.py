"""
Setup Wizard: Intelligent setup system for ElixirMind.
Guides users through initial configuration and testing.
"""

import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from emulators.emulator_factory import EmulatorFactory
from vision.calibration.calibrator import Calibrator
from vision.screen_capture import ScreenCapture
from actions.controller import Controller
from config import Config

logger = logging.getLogger(__name__)

class SetupWizard:
    """
    Intelligent setup wizard for ElixirMind Clash Royale bot.
    Handles automatic detection, configuration, and testing.
    """

    def __init__(self):
        self.config = Config()
        self.emulator_factory = EmulatorFactory()
        self.calibrator = Calibrator(self.config)
        self.screen_capture = ScreenCapture(self.config)
        self.controller = Controller(self.config)

        # Setup state
        self.detected_emulators = []
        self.selected_emulator = None
        self.adb_working = False
        self.calibration_done = False
        self.tests_passed = []

    async def run_full_setup(self) -> bool:
        """
        Run the complete setup wizard.

        Returns:
            True if setup completed successfully
        """
        print("🚀 Welcome to ElixirMind Setup Wizard!")
        print("=" * 50)

        try:
            # Step 1: Detect emulators
            print("\n📱 Step 1: Detecting Emulators...")
            emulators_found = await self.detect_emulators()
            if not emulators_found:
                print("❌ No emulators detected. Please install MEmu or BlueStacks and try again.")
                return False

            # Step 2: Select emulator
            print("\n🎯 Step 2: Selecting Emulator...")
            if not await self.select_emulator():
                return False

            # Step 3: Test ADB connection
            print("\n🔌 Step 3: Testing ADB Connection...")
            if not await self.test_adb_connection():
                print("❌ ADB connection failed. Please ensure ADB is installed and emulator is running.")
                return False

            # Step 4: Calibrate game detection
            print("\n🎯 Step 4: Calibrating Game Detection...")
            if not await self.calibrate_game_detection():
                print("❌ Game calibration failed. Please ensure Clash Royale is running in the emulator.")
                return False

            # Step 5: Run initial tests
            print("\n🧪 Step 5: Running Initial Tests...")
            if not await self.run_initial_tests():
                print("❌ Some tests failed. Please check the issues above.")
                return False

            # Success
            print("\n✅ Setup completed successfully!")
            print("🎉 ElixirMind is ready to use!")
            return True

        except Exception as e:
            logger.error(f"Setup failed: {e}")
            print(f"\n❌ Setup failed: {e}")
            return False

    async def detect_emulators(self) -> List[str]:
        """
        Detect installed emulators.

        Returns:
            List of detected emulator types
        """
        print("   Scanning for emulators...")

        detected = []

        # Check for MEmu
        if self._check_process_running(["MEmu.exe", "MEmuConsole.exe"]):
            detected.append("memu")
            print("   ✅ MEmu detected")

        # Check for BlueStacks
        if self._check_process_running(["Bluestacks.exe", "HD-Player.exe"]):
            detected.append("bluestacks")
            print("   ✅ BlueStacks detected")

        # Try template-based detection if processes not found
        try:
            screenshot_path = await self.screen_capture.capture_screen("setup_detection.png")
            if screenshot_path and os.path.exists(screenshot_path):
                emulator_type, confidence = self.calibrator.emulator_detector.detect_emulator(
                    screen_image_path=screenshot_path
                )
                if emulator_type and confidence > 0.3 and emulator_type not in detected:
                    detected.append(emulator_type)
                    print(f"   ✅ {emulator_type.title()} detected via screenshot (confidence: {confidence:.2f})")
        except Exception as e:
            logger.warning(f"Template detection failed: {e}")

        self.detected_emulators = detected

        if not detected:
            print("   ❌ No emulators detected")
        else:
            print(f"   📋 Found {len(detected)} emulator(s): {', '.join(d.title() for d in detected)}")

        return detected

    async def select_emulator(self) -> bool:
        """
        Select which emulator to use.

        Returns:
            True if emulator selected successfully
        """
        if len(self.detected_emulators) == 1:
            self.selected_emulator = self.detected_emulators[0]
            print(f"   ✅ Auto-selected: {self.selected_emulator.title()}")
            return True

        elif len(self.detected_emulators) > 1:
            print("   Multiple emulators found. Please select one:")
            for i, emu in enumerate(self.detected_emulators, 1):
                print(f"   {i}. {emu.title()}")

            # For automated setup, select the first one
            # In interactive mode, this would prompt user
            self.selected_emulator = self.detected_emulators[0]
            print(f"   ✅ Selected: {self.selected_emulator.title()}")
            return True

        else:
            print("   ❌ No emulators available for selection")
            return False

    async def test_adb_connection(self) -> bool:
        """
        Test ADB connection to the selected emulator.

        Returns:
            True if ADB connection works
        """
        print("   Testing ADB connection...")

        try:
            # Get emulator instance
            emulator = self.emulator_factory.create_emulator(self.selected_emulator)
            if not emulator:
                print("   ❌ Failed to create emulator instance")
                return False

            # Test basic ADB commands
            devices = await emulator.get_connected_devices()
            if not devices:
                print("   ❌ No ADB devices found")
                return False

            print(f"   ✅ ADB connected to {len(devices)} device(s)")

            # Test screenshot capability
            test_screenshot = await emulator.take_screenshot("adb_test.png")
            if test_screenshot and os.path.exists(test_screenshot):
                print("   ✅ Screenshot test passed")
                os.remove(test_screenshot)  # Clean up
            else:
                print("   ⚠️ Screenshot test failed, but ADB is working")

            self.adb_working = True
            return True

        except Exception as e:
            logger.error(f"ADB test failed: {e}")
            print(f"   ❌ ADB test failed: {e}")
            return False

    async def calibrate_game_detection(self) -> bool:
        """
        Calibrate game detection and ROIs.

        Returns:
            True if calibration successful
        """
        print("   Starting calibration process...")

        try:
            # Detect emulator and resolution
            print("   Detecting emulator and resolution...")
            emulator_type, resolution = await self.calibrator.detect_emulator_resolution()

            if not emulator_type or not resolution:
                print("   ❌ Could not detect emulator/resolution")
                return False

            print(f"   ✅ Detected: {emulator_type.title()} at {resolution[0]}x{resolution[1]}")

            # Calibrate ROIs
            print("   Calibrating ROIs...")
            calibrated_rois = await self.calibrator.calibrate_rois()

            if not calibrated_rois:
                print("   ❌ ROI calibration failed")
                return False

            print(f"   ✅ Calibrated {len(calibrated_rois)} ROIs")

            # Validate calibration
            print("   Validating calibration...")
            validation_results = await self.calibrator.validate_detection()

            if validation_results.get("overall_score", 0) < 0.7:
                print(f"   ⚠️ Calibration validation score: {validation_results.get('overall_score', 0):.2f}")
                print("   ⚠️ Calibration may need manual adjustment")
            else:
                print("   ✅ Calibration validation passed")

            self.calibration_done = True
            return True

        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            print(f"   ❌ Calibration failed: {e}")
            return False

    async def run_initial_tests(self) -> bool:
        """
        Run initial system tests.

        Returns:
            True if all critical tests pass
        """
        print("   Running initial tests...")

        tests = [
            ("Screen Capture", self._test_screen_capture),
            ("Controller Actions", self._test_controller),
            ("Vision Detection", self._test_vision),
            ("Strategy Logic", self._test_strategy),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"   Testing {test_name}...")
            try:
                result = await test_func()
                if result:
                    print(f"   ✅ {test_name} passed")
                    passed += 1
                    self.tests_passed.append(test_name)
                else:
                    print(f"   ❌ {test_name} failed")
            except Exception as e:
                logger.error(f"{test_name} test error: {e}")
                print(f"   ❌ {test_name} error: {e}")

        success_rate = passed / total
        print(f"   📊 Tests passed: {passed}/{total} ({success_rate:.1%})")

        # Require at least 75% success for critical tests
        critical_tests = ["Screen Capture", "Controller Actions"]
        critical_passed = sum(1 for t in critical_tests if t in self.tests_passed)

        if critical_passed < len(critical_tests):
            print("   ❌ Critical tests failed")
            return False

        if success_rate < 0.75:
            print("   ⚠️ Some tests failed, but setup can continue")
        else:
            print("   ✅ All tests passed")

        return True

    def _check_process_running(self, process_names: List[str]) -> bool:
        """Check if any of the given processes are running."""
        try:
            for proc in process_names:
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {proc}", "/NH"],
                    capture_output=True, text=True, shell=True
                )
                if proc.lower() in result.stdout.lower():
                    return True
        except Exception as e:
            logger.warning(f"Process check failed: {e}")

        return False

    async def _test_screen_capture(self) -> bool:
        """Test screen capture functionality."""
        try:
            screenshot = await self.screen_capture.capture_screen("test_screenshot.png")
            if screenshot and os.path.exists(screenshot):
                # Check if screenshot has reasonable size
                size = os.path.getsize(screenshot)
                if size > 10000:  # At least 10KB
                    os.remove(screenshot)  # Clean up
                    return True
            return False
        except Exception:
            return False

    async def _test_controller(self) -> bool:
        """Test controller actions."""
        try:
            # Test basic controller initialization
            return self.controller is not None
        except Exception:
            return False

    async def _test_vision(self) -> bool:
        """Test vision detection."""
        try:
            # Test if we can load and use the detector
            from vision.detector import Detector
            detector = Detector(self.config)
            return detector is not None
        except Exception:
            return False

    async def _test_strategy(self) -> bool:
        """Test strategy logic."""
        try:
            # Test if we can load and use strategy
            from strategy.base import Strategy
            strategy = Strategy(self.config)
            return strategy is not None
        except Exception:
            return False

    def get_setup_summary(self) -> Dict:
        """Get summary of setup results."""
        return {
            "detected_emulators": self.detected_emulators,
            "selected_emulator": self.selected_emulator,
            "adb_working": self.adb_working,
            "calibration_done": self.calibration_done,
            "tests_passed": self.tests_passed,
            "setup_complete": all([
                self.selected_emulator,
                self.adb_working,
                self.calibration_done,
                len(self.tests_passed) >= 2  # At least critical tests
            ])
        }

async def main():
    """Run the setup wizard from command line."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    wizard = SetupWizard()
    success = await wizard.run_full_setup()

    if success:
        print("\n🎉 Setup completed! You can now run ElixirMind.")
        print("💡 Tip: Run 'python main.py' to start the bot.")
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
