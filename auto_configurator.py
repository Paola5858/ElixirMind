#!/usr/bin/env python3
"""
Auto Configurator for ElixirMind
Automatically detects and configures emulator and game settings.
"""

import asyncio
import subprocess
import json
import time
import cv2
import numpy as np
import mss
from pathlib import Path
import psutil
import platform
import re

class AutoConfigurator:
    def __init__(self):
        self.sct = mss.mss()
        self.config = {}
        self.detected_settings = {}

        # Supported emulators
        self.supported_emulators = {
            "MEmu": {
                "process_names": ["MEmu.exe", "MEmuConsole.exe"],
                "window_titles": ["MEmu"],
                "adb_port": 21503
            },
            "BlueStacks": {
                "process_names": ["BlueStacks.exe", "HD-Player.exe"],
                "window_titles": ["BlueStacks"],
                "adb_port": 5555
            },
            "NoxPlayer": {
                "process_names": ["Nox.exe", "NoxVMHandle.exe"],
                "window_titles": ["NoxPlayer"],
                "adb_port": 62001
            },
            "LDPlayer": {
                "process_names": ["dnplayer.exe", "ldconsole.exe"],
                "window_titles": ["LDPlayer"],
                "adb_port": 5555
            }
        }

        # Game resolutions to detect
        self.game_resolutions = [
            (1920, 1080),  # Full HD
            (1600, 900),   # HD+
            (1280, 720),   # HD
            (1024, 576),   # SD
            (960, 540),    # qHD
        ]

    async def run_full_configuration(self):
        """Run complete auto-configuration"""
        print("🔧 Starting Auto Configuration")
        print("=" * 40)

        steps = [
            ("System Detection", self.detect_system_info),
            ("Emulator Detection", self.detect_emulator),
            ("ADB Setup", self.setup_adb_connection),
            ("Game Detection", self.detect_game_installation),
            ("Resolution Calibration", self.calibrate_resolution),
            ("ROI Detection", self.detect_regions_of_interest),
            ("Performance Tuning", self.optimize_performance),
        ]

        for step_name, step_func in steps:
            print(f"\n⚙️ {step_name}...")
            try:
                result = await step_func()
                self.config[step_name.lower().replace(" ", "_")] = result
                print(f"✅ {step_name}: {'SUCCESS' if result else 'FAILED'}")
            except Exception as e:
                print(f"❌ {step_name}: ERROR - {e}")
                self.config[step_name.lower().replace(" ", "_")] = False

        # Save configuration
        self.save_configuration()

        # Generate report
        self.generate_config_report()

        return self.config

    async def detect_system_info(self):
        """Detect system information"""
        system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "python_version": platform.python_version(),
        }

        # Check for GPU
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            system_info["gpu"] = {
                "name": gpus[0].name if gpus else "None",
                "memory_gb": round(gpus[0].memoryTotal / 1024, 1) if gpus else 0
            }
        except:
            system_info["gpu"] = {"name": "Unknown", "memory_gb": 0}

        self.detected_settings["system"] = system_info
        return True

    async def detect_emulator(self):
        """Detect running emulator"""
        print("   Scanning for emulators...")

        running_processes = {p.name().lower() for p in psutil.process_iter()}

        detected_emulator = None
        for emulator_name, emulator_info in self.supported_emulators.items():
            process_found = any(
                proc_name.lower() in running_processes
                for proc_name in emulator_info["process_names"]
            )

            if process_found:
                detected_emulator = emulator_name
                self.detected_settings["emulator"] = {
                    "name": emulator_name,
                    "process_found": True,
                    "adb_port": emulator_info["adb_port"]
                }
                break

        if not detected_emulator:
            # Try to detect by window titles
            try:
                import pygetwindow as gw
                windows = gw.getAllTitles()

                for emulator_name, emulator_info in self.supported_emulators.items():
                    window_found = any(
                        title.lower().startswith(window_title.lower())
                        for title in windows
                        for window_title in emulator_info["window_titles"]
                    )

                    if window_found:
                        detected_emulator = emulator_name
                        self.detected_settings["emulator"] = {
                            "name": emulator_name,
                            "window_found": True,
                            "adb_port": emulator_info["adb_port"]
                        }
                        break
            except ImportError:
                print("   Note: Install pygetwindow for better window detection")

        if detected_emulator:
            print(f"   ✅ Detected: {detected_emulator}")
            return True
        else:
            print("   ❌ No emulator detected")
            print("   Please start your Android emulator first")
            return False

    async def setup_adb_connection(self):
        """Setup ADB connection to emulator"""
        if "emulator" not in self.detected_settings:
            return False

        emulator = self.detected_settings["emulator"]
        adb_port = emulator["adb_port"]

        print(f"   Connecting to ADB on port {adb_port}...")

        try:
            # Connect to emulator
            result = subprocess.run(
                ["adb", "connect", f"127.0.0.1:{adb_port}"],
                capture_output=True, text=True, timeout=10
            )

            if "connected" in result.stdout.lower() or "already connected" in result.stdout.lower():
                print("   ✅ ADB connected")

                # Get device info
                device_result = subprocess.run(
                    ["adb", "devices"], capture_output=True, text=True, timeout=5
                )

                self.detected_settings["adb"] = {
                    "connected": True,
                    "port": adb_port,
                    "devices": device_result.stdout.strip()
                }
                return True
            else:
                print(f"   ❌ ADB connection failed: {result.stdout}")
                return False

        except FileNotFoundError:
            print("   ❌ ADB not found. Please install Android SDK Platform Tools")
            return False
        except subprocess.TimeoutExpired:
            print("   ❌ ADB connection timeout")
            return False

    async def detect_game_installation(self):
        """Detect if Clash Royale is installed"""
        if "adb" not in self.detected_settings or not self.detected_settings["adb"]["connected"]:
            return False

        print("   Checking for Clash Royale installation...")

        try:
            # List installed packages
            result = subprocess.run(
                ["adb", "shell", "pm", "list", "packages", "|", "grep", "clash"],
                capture_output=True, text=True, timeout=10, shell=True
            )

            clash_packages = [line for line in result.stdout.split('\n') if 'clash' in line.lower()]

            if clash_packages:
                print("   ✅ Clash Royale detected")
                self.detected_settings["game"] = {
                    "installed": True,
                    "packages": clash_packages
                }
                return True
            else:
                print("   ❌ Clash Royale not found")
                print("   Please install Clash Royale in your emulator")
                return False

        except Exception as e:
            print(f"   ❌ Game detection error: {e}")
            return False

    async def calibrate_resolution(self):
        """Calibrate screen resolution"""
        print("   Calibrating resolution...")

        # Capture screen
        frame = self.capture_screen()
        height, width = frame.shape[:2]

        detected_res = (width, height)
        print(f"   Detected resolution: {width}x{height}")

        # Find closest supported resolution
        closest_res = min(self.game_resolutions,
                         key=lambda res: abs(res[0] - width) + abs(res[1] - height))

        self.detected_settings["resolution"] = {
            "detected": detected_res,
            "recommended": closest_res,
            "scale_factor": (closest_res[0] / detected_res[0], closest_res[1] / detected_res[1])
        }

        print(f"   Recommended: {closest_res[0]}x{closest_res[1]}")
        return True

    async def detect_regions_of_interest(self):
        """Detect important regions of interest in the game"""
        print("   Detecting regions of interest...")

        # Capture game screen (assuming game is running)
        frame = self.capture_screen()

        # Convert to HSV for color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        # Detect elixir bar (purple color)
        lower_purple = np.array([140, 50, 50])
        upper_purple = np.array([160, 255, 255])
        purple_mask = cv2.inRange(hsv, lower_purple, upper_purple)

        # Find elixir region
        contours, _ = cv2.findContours(purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        elixir_roi = None
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            elixir_roi = (x, y, x+w, y+h)

        # Detect card area (bottom portion)
        height, width = frame.shape[:2]
        card_area = (0, int(height * 0.75), width, height)

        # Detect crown towers (red and blue colors)
        lower_red = np.array([0, 50, 50])
        upper_red = np.array([10, 255, 255])
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([130, 255, 255])

        red_mask = cv2.inRange(hsv, lower_red, upper_red)
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

        # Find tower positions
        red_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        blue_contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        towers = []
        for contour in red_contours + blue_contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Minimum tower size
                x, y, w, h = cv2.boundingRect(contour)
                towers.append((x, y, x+w, y+h))

        self.detected_settings["roi"] = {
            "elixir_bar": elixir_roi,
            "card_area": card_area,
            "towers": towers,
            "arena_center": (width // 2, height // 2)
        }

        print(f"   Detected {len(towers)} towers")
        return elixir_roi is not None

    async def optimize_performance(self):
        """Optimize performance settings"""
        print("   Optimizing performance...")

        system = self.detected_settings.get("system", {})

        # Performance recommendations based on hardware
        recommendations = {
            "cpu_threads": min(system.get("cpu_count", 4), 8),
            "memory_limit": min(system.get("memory_gb", 8) * 0.8, 16),
            "detection_fps": 10 if system.get("gpu", {}).get("memory_gb", 0) > 2 else 5,
            "batch_size": 4 if system.get("gpu", {}).get("memory_gb", 0) > 4 else 1,
        }

        # Adjust based on emulator
        emulator = self.detected_settings.get("emulator", {}).get("name")
        if emulator == "MEmu":
            recommendations["emulator_specific"] = {
                "render_mode": "OpenGL",
                "cpu_cores": min(system.get("cpu_count", 4) // 2, 4),
                "ram_gb": 4
            }
        elif emulator == "BlueStacks":
            recommendations["emulator_specific"] = {
                "engine": "Performance",
                "cpu_cores": min(system.get("cpu_count", 4) // 2, 4),
                "ram_gb": 4
            }

        self.detected_settings["performance"] = recommendations
        return True

    def capture_screen(self):
        """Capture screen using MSS"""
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        return np.array(screenshot)

    def save_configuration(self):
        """Save detected configuration to file"""
        config_data = {
            "auto_configured_at": time.time(),
            "version": "1.0",
            "settings": self.detected_settings,
            "config": self.config
        }

        with open("auto_config.json", "w") as f:
            json.dump(config_data, f, indent=2)

        print("💾 Configuration saved to auto_config.json")

    def generate_config_report(self):
        """Generate configuration report"""
        print("\n📊 Auto Configuration Report")
        print("=" * 40)

        success_count = sum(1 for result in self.config.values() if result)
        total_count = len(self.config)

        print(f"Configuration Steps: {success_count}/{total_count} successful")

        if "system" in self.detected_settings:
            sys = self.detected_settings["system"]
            print(f"System: {sys['os']} {sys['architecture']}, {sys['cpu_count']} CPU cores, {sys['memory_gb']}GB RAM")

        if "emulator" in self.detected_settings:
            emu = self.detected_settings["emulator"]
            print(f"Emulator: {emu['name']}")

        if "resolution" in self.detected_settings:
            res = self.detected_settings["resolution"]
            print(f"Resolution: {res['detected'][0]}x{res['detected'][1]} (recommended: {res['recommended'][0]}x{res['recommended'][1]})")

        if "performance" in self.detected_settings:
            perf = self.detected_settings["performance"]
            print(f"Performance: {perf['detection_fps']} FPS, {perf['cpu_threads']} threads")

        if success_count == total_count:
            print("✅ Configuration: COMPLETE - Ready to use!")
        elif success_count >= total_count * 0.7:
            print("⚠️ Configuration: MOSTLY COMPLETE - Minor issues")
        else:
            print("❌ Configuration: INCOMPLETE - Major issues found")

    def load_configuration(self):
        """Load saved configuration"""
        try:
            with open("auto_config.json", "r") as f:
                data = json.load(f)
            self.detected_settings = data.get("settings", {})
            self.config = data.get("config", {})
            print("📂 Configuration loaded from auto_config.json")
            return True
        except FileNotFoundError:
            print("❌ No saved configuration found")
            return False

async def main():
    configurator = AutoConfigurator()

    print("🤖 ElixirMind Auto Configurator")
    print("This will automatically detect and configure your setup")
    print("=" * 60)

    # Try to load existing config first
    if configurator.load_configuration():
        choice = input("Found existing configuration. Re-run auto-configuration? (y/N): ")
        if choice.lower() != 'y':
            configurator.generate_config_report()
            return

    # Run full configuration
    await configurator.run_full_configuration()

if __name__ == "__main__":
    asyncio.run(main())
