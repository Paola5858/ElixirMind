#!/usr/bin/env python3
"""
ElixirMind Setup Script
Automated installation and configuration for ElixirMind bot.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import json


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ is required")
        print(f"Current version: {sys.version}")
        return False
    print(
        f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")

    try:
        # Upgrade pip first
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

        # Install requirements
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

        print("✅ Dependencies installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")

    directories = [
        "data/logs",
        "data/results",
        "data/reference/cards",
        "models",
        "dashboard/assets"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    print("✅ Directories created")


def create_default_config():
    """Create default configuration file."""
    print("⚙️ Creating default configuration...")

    default_config = {
        "REAL_MODE": False,
        "DEBUG_MODE": True,
        "EMULATOR_TYPE": "memu",
        "DEVICE_ID": "127.0.0.1:21503",
        "USE_RL_STRATEGY": False,
        "SAFE_MODE": True,
        "TARGET_FPS": 10,
        "AGGRESSION_LEVEL": 0.6,
        "LOG_LEVEL": "INFO"
    }

    config_path = Path("config.json")
    if not config_path.exists():
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=2)
        print("✅ Default configuration created")
    else:
        print("ℹ️ Configuration file already exists")


def check_system_requirements():
    """Check system requirements."""
    print("🔍 Checking system requirements...")

    # Check OS
    os_name = platform.system()
    if os_name == "Windows":
        print("✅ Windows detected - Full support available")
    elif os_name in ["Linux", "Darwin"]:
        print(f"⚠️ {os_name} detected - Limited PyAutoGUI support")
    else:
        print(f"❓ Unknown OS: {os_name}")

    # Check available memory
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb >= 8:
            print(f"✅ Memory: {memory_gb:.1f}GB (recommended: 8GB+)")
        else:
            print(f"⚠️ Memory: {memory_gb:.1f}GB (recommended: 8GB+)")
    except ImportError:
        print("ℹ️ Memory check skipped (psutil not available)")


def setup_git_hooks():
    """Setup git pre-commit hooks if in development mode."""
    print("🔧 Setting up development tools...")

    if Path(".git").exists():
        try:
            # Install development dependencies
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "pre-commit", "black", "flake8", "pytest"
            ])

            # Setup pre-commit
            subprocess.check_call(["pre-commit", "install"])
            print("✅ Git hooks configured")

        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ Git hooks setup skipped")
    else:
        print("ℹ️ Not a git repository - skipping hooks")


def verify_installation():
    """Verify installation by importing key modules."""
    print("🧪 Verifying installation...")

    try:
        # Test core imports
        import cv2
        import numpy as np
        import torch
        import streamlit

        print("✅ Core dependencies verified")

        # Test optional imports
        try:
            from stable_baselines3 import PPO
            print("✅ Reinforcement Learning available")
        except ImportError:
            print("⚠️ Reinforcement Learning not available (optional)")

        try:
            import pytesseract
            print("✅ OCR capabilities available")
        except ImportError:
            print("⚠️ OCR not available (optional)")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def print_next_steps():
    """Print next steps for user."""
    print("\n" + "="*60)
    print("🎉 ElixirMind installation completed!")
    print("="*60)
    print()
    print("📋 Next Steps:")
    print("1. Configure your emulator (MEmu/BlueStacks)")
    print("2. Install Clash Royale in the emulator")
    print("3. Edit config.json if needed")
    print("4. Start the bot:")
    print("   python main.py --mode test")
    print()
    print("5. Open dashboard:")
    print("   streamlit run dashboard/app.py")
    print()
    print("📚 Documentation:")
    print("- README.md - Complete guide")
    print("- config.json - Configuration options")
    print("- tests/ - Run tests with 'pytest'")
    print()
    print("⚠️ Important:")
    print("- Use only on test accounts")
    print("- Enable Safe Mode for first runs")
    print("- Check emulator connection with 'adb devices'")
    print()
    print("🆘 Need help? Check GitHub issues or documentation")


def main():
    """Main setup function."""
    print("🤖 ElixirMind Setup")
    print("=" * 40)
    print()

    # Check prerequisites
    if not check_python_version():
        sys.exit(1)

    # System requirements
    check_system_requirements()

    # Setup process
    setup_directories()

    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)

    create_default_config()
    setup_git_hooks()

    # Verify installation
    if not verify_installation():
        print("❌ Installation verification failed")
        sys.exit(1)

    # Success
    print_next_steps()


if __name__ == "__main__":
    main()
