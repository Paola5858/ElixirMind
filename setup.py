#!/usr/bin/env python3
"""
ElixirMind Setup Script
Automated installation and configuration.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Output: {e.output}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")

    # Upgrade pip first
    if not run_command("python -m pip install --upgrade pip", "Upgrading pip"):
        return False

    # Install core dependencies
    core_deps = [
        "opencv-python",
        "numpy",
        "pyautogui",
        "mss",
        "pillow",
        "streamlit",
        "plotly",
        "pandas"
    ]

    for dep in core_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False

    # Optional dependencies
    optional_deps = [
        "torch",
        "torchvision",
        "stable-baselines3",
        "psutil",
        "gputil"
    ]

    print("📦 Installing optional dependencies...")
    for dep in optional_deps:
        run_command(f"pip install {dep}", f"Installing {dep} (optional)")

    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")

    dirs = [
        "models",
        "data",
        "data/logs",
        "data/screenshots",
        "data/templates",
        "tests",
        "vision/cache",
        "strategy/models"
    ]

    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {dir_path}/")

    return True

def download_models():
    """Download pre-trained models"""
    print("🤖 Downloading AI models...")

    # This would normally download YOLOv5 models
    # For now, just create placeholder
    models_dir = Path("models")
    placeholder = models_dir / "yolov5s.pt"
    if not placeholder.exists():
        placeholder.write_text("# Placeholder - Download real model from ultralytics.com")
        print("✅ Created models placeholder")
        print("   Note: Download actual YOLOv5 weights from https://github.com/ultralytics/yolov5")

    return True

def create_config():
    """Create default configuration"""
    print("⚙️ Creating configuration...")

    config_content = '''# ElixirMind Configuration
REAL_MODE = True
EMULATOR_TYPE = "memu"
USE_RL_STRATEGY = False
AGGRESSION_LEVEL = 0.6
TARGET_FPS = 10
SAFE_MODE = True

# Emulator settings
EMULATOR_PORT = 21503
SCREEN_REGION = (0, 0, 1920, 1080)

# AI settings
YOLO_MODEL = "models/yolov5s.pt"
RL_MODEL = "strategy/models/ppo_clash"

# Performance settings
MAX_MEMORY_USAGE = 80  # percent
CPU_THREADS = 4
'''

    config_file = Path("config.py")
    if not config_file.exists():
        config_file.write_text(config_content)
        print("✅ Created config.py")

    return True

def run_tests():
    """Run basic functionality tests"""
    print("🧪 Running basic tests...")

    # Simple import test
    test_code = """
import sys
try:
    import cv2
    import numpy as np
    import pyautogui
    import mss
    print("✅ Core imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
"""

    try:
        result = subprocess.run([sys.executable, "-c", test_code],
                              capture_output=True, text=True, check=True)
        print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        print(e.output)
        return False

def main():
    print("🚀 ElixirMind Setup")
    print("=" * 50)
    print("This will install all dependencies and configure the system.")
    print()

    steps = [
        ("Installing Python dependencies", install_dependencies),
        ("Creating directory structure", create_directories),
        ("Downloading AI models", download_models),
        ("Creating configuration files", create_config),
        ("Running basic tests", run_tests),
    ]

    success_count = 0
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if step_func():
            success_count += 1
            print(f"✅ {step_name} completed")
        else:
            print(f"❌ {step_name} failed")
            break

    print(f"\n📊 Setup Results: {success_count}/{len(steps)} steps completed")

    if success_count == len(steps):
        print("\n🎉 Setup completed successfully!")
        print("\n🚀 Next steps:")
        print("1. Run: python auto_configurator.py")
        print("2. Run: python run_bot.bat")
        print("3. Run: python run_dashboard.bat (in new terminal)")
        print("\n📖 For detailed instructions, see README.md")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        print("You can try running individual steps manually.")

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
