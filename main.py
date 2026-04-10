"""
ElixirMind Main Entry Point
Refactored to use core modules for better architecture.
"""

import argparse
import logging
import sys

from config import load_config
from core.bot_manager import BotManager


logger = logging.getLogger(__name__)


def configure_logging(log_level: str) -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="ElixirMind main entry point")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to the JSON configuration file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode regardless of file configuration",
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point for ElixirMind."""
    bot_manager = None
    args = parse_args()

    try:
        config = load_config(args.config)
        if args.debug:
            config["debug"] = True
            config["log_level"] = "DEBUG"

        configure_logging(config.get("log_level", "INFO"))
        logger.info("Starting ElixirMind with config file: %s", args.config)

        bot_manager = BotManager(config)
        bot_manager.start()
        bot_manager.run()
        return 0

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        if bot_manager is not None:
            bot_manager.stop()
        return 0
    except Exception:
        logger.exception("Unexpected error during application execution")
        if bot_manager is not None and bot_manager.is_running():
            bot_manager.stop()
        return 1


if __name__ == "__main__":
    sys.exit(main())
