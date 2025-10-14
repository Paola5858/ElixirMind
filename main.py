"""
ElixirMind Main Entry Point
Refactored to use core modules for better architecture.
"""

import logging
import sys
from config import load_config
from core.bot_manager import BotManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for ElixirMind."""
    try:
        # Load configuration
        config = load_config()

        # Create and start bot manager
        bot_manager = BotManager(config)
        bot_manager.start()

        # Run the bot
        bot_manager.run()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        if 'bot_manager' in locals():
            bot_manager.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
