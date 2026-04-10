"""
Bot Manager: Manages the full bot lifecycle.

Improvements vs previous version:
- Validates poll_interval_seconds > 0 at construction time.
- Separates idle cadence from battle cadence (battle ticks faster).
- Exponential backoff on consecutive errors to avoid tight error loops.
- is_running() is a property for cleaner external access.
"""

import logging
import time

from .orchestrator import Orchestrator
from .state_machine import StateMachine

logger = logging.getLogger(__name__)

_MIN_POLL_INTERVAL = 0.01   # 10 ms floor
_MAX_BACKOFF       = 30.0   # seconds
_BATTLE_CADENCE    = 0.1    # 100 ms between battle ticks


class BotManager:
    def __init__(self, config: dict) -> None:
        poll = float(config.get("poll_interval_seconds", 0.25))
        if poll <= 0:
            raise ValueError(
                f"poll_interval_seconds must be > 0, got {poll!r}"
            )

        self.config = config
        self._poll_interval = max(poll, _MIN_POLL_INTERVAL)
        self.orchestrator = Orchestrator(config)
        self.state_machine = StateMachine()
        self.orchestrator.set_state_machine(self.state_machine)
        self._running = False
        self._consecutive_errors = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        logger.info("Starting ElixirMind Bot...")
        self.orchestrator.initialize()
        self.state_machine.set_state("idle")
        self._running = True
        logger.info("Bot started.")

    def run(self) -> None:
        """Main loop. Blocks until stopped or shutdown state reached."""
        logger.info("Entering main bot loop.")
        try:
            while self._running:
                state = self.state_machine.get_state()
                try:
                    if state == "idle":
                        self.orchestrator.check_for_battle()
                        time.sleep(self._poll_interval)
                    elif state == "battle":
                        self.orchestrator.handle_battle()
                        time.sleep(_BATTLE_CADENCE)
                    elif state == "shutdown":
                        logger.info("Shutdown state received.")
                        break
                    else:
                        logger.warning("Unknown state: %s", state)
                        time.sleep(self._poll_interval)

                    self._consecutive_errors = 0  # reset on success

                except Exception:
                    self._consecutive_errors += 1
                    backoff = min(
                        _BATTLE_CADENCE * (2 ** self._consecutive_errors),
                        _MAX_BACKOFF,
                    )
                    logger.exception(
                        "Error in bot loop (attempt %d), backing off %.1fs",
                        self._consecutive_errors, backoff,
                    )
                    time.sleep(backoff)
        finally:
            self.stop()

    def stop(self) -> None:
        if not self._running:
            logger.debug("Stop called but bot is already stopped.")
            return
        logger.info("Stopping ElixirMind Bot...")
        self._running = False
        self.orchestrator.shutdown()
        logger.info("Bot stopped.")
