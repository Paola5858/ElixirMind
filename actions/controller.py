"""
Actions Controller: Handles bot actions and inputs.
"""
import pyautogui
import time
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self, config):
        self.config = config
        # Define card positions based on a standard 1920x1080 resolution
        # These should ideally come from config
        self.card_positions = [
            (780, 920),  # Card 1
            (960, 920),  # Card 2
            (1140, 920),  # Card 3
            (1320, 920)  # Card 4
        ]

    def initialize(self):
        """Initialize the controller."""
        logger.info("Actions Controller initialized.")
        # Configure pyautogui safety features
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

    def shutdown(self):
        """Shutdown the controller."""
        logger.info("Actions Controller shutdown.")

    def execute_actions(self, actions: List[Dict[str, Any]]):
        """
        Execute a list of actions.
        Supported action types:
        - 'play_card': {'type': 'play_card', 'card_index': 0-3, 'position': (x, y)}
        - 'use_spell': {'type': 'use_spell', 'card_index': 0-3, 'position': (x, y)}
        - 'upgrade_card': {'type': 'upgrade_card', 'card_index': 0-3}
        - 'wait': {'type': 'wait', 'duration': seconds}
        """
        if not actions:
            return

        for action in actions:
            action_type = action.get("type")
            logger.info(f"Executing action: {action}")

            try:
                if action_type == "play_card":
                    self._execute_play_card(action)
                elif action_type == "use_spell":
                    self._execute_use_spell(action)
                elif action_type == "upgrade_card":
                    self._execute_upgrade_card(action)
                elif action_type == "wait":
                    self._execute_wait(action)
                else:
                    logger.warning(f"Unknown action type: {action_type}")
            except Exception as e:
                logger.error(f"Failed to execute action {action}: {e}")

    def _execute_play_card(self, action: Dict[str, Any]):
        """Execute playing a card at a specific position."""
        card_index = action.get("card_index")
        target_pos = action.get("position")

        if card_index is not None and target_pos is not None and 0 <= card_index < len(self.card_positions):
            card_pos = self.card_positions[card_index]

            # Perform the drag and drop
            pyautogui.moveTo(card_pos[0], card_pos[1])
            pyautogui.dragTo(
                target_pos[0], target_pos[1], duration=0.25, tween=pyautogui.easeOutQuad)
            logger.info(f"Played card {card_index} at {target_pos}")
        else:
            logger.warning(f"Invalid card_index {card_index} or position {target_pos}")

    def _execute_use_spell(self, action: Dict[str, Any]):
        """Execute using a spell card at a specific position."""
        card_index = action.get("card_index")
        target_pos = action.get("position")

        if card_index is not None and target_pos is not None and 0 <= card_index < len(self.card_positions):
            card_pos = self.card_positions[card_index]

            # Spells are used by clicking and dragging like regular cards
            pyautogui.moveTo(card_pos[0], card_pos[1])
            pyautogui.dragTo(
                target_pos[0], target_pos[1], duration=0.3, tween=pyautogui.easeOutQuad)
            logger.info(f"Used spell {card_index} at {target_pos}")
        else:
            logger.warning(f"Invalid spell card_index {card_index} or position {target_pos}")

    def _execute_upgrade_card(self, action: Dict[str, Any]):
        """Execute upgrading a card."""
        card_index = action.get("card_index")

        if card_index is not None and 0 <= card_index < len(self.card_positions):
            card_pos = self.card_positions[card_index]

            # Upgrade is typically done by double-clicking the card
            pyautogui.moveTo(card_pos[0], card_pos[1])
            pyautogui.doubleClick()
            logger.info(f"Upgraded card {card_index}")
        else:
            logger.warning(f"Invalid card_index {card_index} for upgrade")

    def _execute_wait(self, action: Dict[str, Any]):
        """Execute a wait action."""
        duration = action.get("duration", 1.0)

        if duration > 0:
            time.sleep(duration)
            logger.info(f"Waited for {duration} seconds")
        else:
            logger.warning(f"Invalid wait duration: {duration}")
