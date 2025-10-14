"""
ElixirMind Heuristic Strategy
Rule-based strategy using game knowledge and heuristics.
"""

import asyncio
import logging
import time
import random
from typing import Optional, Dict, Any, List, Tuple
import numpy as np

from .base import BaseStrategy, StrategyDecision, StrategyContext
from actions.controller import GameAction, ActionType
from config import Config


class HeuristicStrategy(BaseStrategy):
    """Rule-based strategy using Clash Royale game knowledge."""

    def __init__(self, config: Config):
        super().__init__(config)
        self.context = StrategyContext()

        # Strategy parameters
        self.aggression_level = 0.6  # 0.0 = defensive, 1.0 = aggressive
        self.elixir_management_threshold = 0.8  # When to be conservative

        # Card priorities and costs (approximations)
        self.card_priorities = {
            'knight': {'cost': 3, 'priority': 0.7, 'type': 'ground_tank'},
            'archers': {'cost': 3, 'priority': 0.6, 'type': 'ranged'},
            'fireball': {'cost': 4, 'priority': 0.8, 'type': 'spell'},
            'giant': {'cost': 5, 'priority': 0.9, 'type': 'heavy_tank'},
            'wizard': {'cost': 5, 'priority': 0.7, 'type': 'ranged_aoe'},
            'dragon': {'cost': 4, 'priority': 0.8, 'type': 'air'},
            'skeleton_army': {'cost': 3, 'priority': 0.5, 'type': 'swarm'},
            'arrows': {'cost': 3, 'priority': 0.6, 'type': 'spell'},
            'barbarians': {'cost': 5, 'priority': 0.7, 'type': 'ground_swarm'},
            'minions': {'cost': 3, 'priority': 0.6, 'type': 'air_swarm'}
        }

        # Tactical rules
        self.tactical_rules = [
            self._rule_counter_push,
            self._rule_defend_towers,
            self._rule_elixir_advantage,
            self._rule_offensive_push,
            self._rule_spell_value,
            self._rule_cycle_cards
        ]

    async def initialize(self) -> bool:
        """Initialize heuristic strategy."""
        try:
            self.logger.info("Initializing heuristic strategy")

            # Load any pre-configured rules or parameters
            await self._load_strategy_parameters()

            self.logger.info("Heuristic strategy initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Heuristic strategy initialization failed: {e}")
            return False

    async def _load_strategy_parameters(self):
        """Load strategy parameters from config or defaults."""
        try:
            # Could load from file or use config values
            self.aggression_level = getattr(
                self.config, 'AGGRESSION_LEVEL', 0.6)
            self.elixir_management_threshold = getattr(
                self.config, 'ELIXIR_THRESHOLD', 0.8)

        except Exception as e:
            self.logger.warning(f"Could not load strategy parameters: {e}")

    async def decide_action(self, game_state) -> Optional[GameAction]:
        """Make strategic decision using heuristic rules."""
        try:
            if not self.should_make_decision():
                return None

            # Update strategy context
            self.context.update_context(game_state)

            # Check if we have enough elixir to do anything
            if game_state.current_elixir < self.config.MIN_ELIXIR_TO_PLAY:
                return None

            # Apply tactical rules in priority order
            best_decision = None
            highest_priority = 0

            for rule in self.tactical_rules:
                decision = await rule(game_state)

                if decision and decision.priority > highest_priority:
                    best_decision = decision
                    highest_priority = decision.priority

            # Execute best decision
            if best_decision:
                self.last_decision_time = time.time()
                self.log_decision(best_decision)
                return best_decision.action

            return None

        except Exception as e:
            self.logger.error(f"Heuristic decision making failed: {e}")
            return None

    async def _rule_counter_push(self, game_state) -> Optional[StrategyDecision]:
        """Rule: Counter enemy pushes defensively."""
        try:
            if self.context.threat_level not in ['high', 'critical']:
                return None

            # Find best defensive card
            available_cards = self._get_available_cards(game_state)
            if not available_cards:
                return None

            # Prioritize defensive cards
            defensive_cards = [
                card for card in available_cards
                if self._is_defensive_card(card['name'])
            ]

            if not defensive_cards:
                # Use any available card for defense
                defensive_cards = available_cards

            # Select best defensive option
            best_card = max(defensive_cards,
                            key=lambda x: x.get('priority', 0))

            # Find best defensive position
            defensive_position = self._calculate_defensive_position(game_state)

            if defensive_position:
                action = self._create_place_card_action(
                    best_card['position'], defensive_position
                )

                return StrategyDecision(
                    action=action,
                    reasoning=f"Defensive counter with {best_card['name']}",
                    confidence=0.8,
                    priority=9  # High priority for defense
                )

            return None

        except Exception as e:
            self.logger.error(f"Counter push rule failed: {e}")
            return None

    async def _rule_defend_towers(self, game_state) -> Optional[StrategyDecision]:
        """Rule: Protect towers under immediate threat."""
        try:
            # Check for enemies near our towers
            critical_threats = [
                threat for threat in self.context.current_threats
                if threat['severity'] == 'high'
            ]

            if not critical_threats:
                return None

            available_cards = self._get_available_cards(game_state)
            if not available_cards:
                return None

            # Find closest threat
            closest_threat = min(critical_threats,
                                 # Lowest Y (closest to our towers)
                                 key=lambda x: x['position'][1])

            # Select appropriate counter
            counter_card = self._select_counter_card(
                available_cards, closest_threat)

            if counter_card:
                # Place counter near threat
                threat_pos = closest_threat['position']
                counter_pos = self._calculate_counter_position(threat_pos)

                action = self._create_place_card_action(
                    counter_card['position'], counter_pos
                )

                return StrategyDecision(
                    action=action,
                    reasoning=f"Tower defense against {closest_threat['troop'].get('class', 'enemy')}",
                    confidence=0.9,
                    priority=10  # Highest priority
                )

            return None

        except Exception as e:
            self.logger.error(f"Tower defense rule failed: {e}")
            return None

    async def _rule_elixir_advantage(self, game_state) -> Optional[StrategyDecision]:
        """Rule: Push when we have elixir advantage."""
        try:
            if game_state.current_elixir < 8:  # Need substantial elixir
                return None

            # Only push if no immediate threats
            if self.context.threat_level in ['high', 'critical']:
                return None

            available_cards = self._get_available_cards(game_state)
            if not available_cards:
                return None

            # Prefer tank cards for pushes
            tank_cards = [
                card for card in available_cards
                if self._is_tank_card(card['name'])
            ]

            push_card = None
            if tank_cards:
                push_card = max(tank_cards, key=lambda x: x.get('priority', 0))
            else:
                # Use strongest available card
                push_card = max(available_cards,
                                key=lambda x: x.get('priority', 0))

            # Select push lane (prefer lane with fewer enemy troops)
            push_position = self._select_push_lane(game_state)

            if push_card and push_position:
                action = self._create_place_card_action(
                    push_card['position'], push_position
                )

                return StrategyDecision(
                    action=action,
                    reasoning=f"Elixir advantage push with {push_card['name']}",
                    confidence=0.7,
                    priority=6
                )

            return None

        except Exception as e:
            self.logger.error(f"Elixir advantage rule failed: {e}")
            return None

    async def _rule_offensive_push(self, game_state) -> Optional[StrategyDecision]:
        """Rule: Create offensive pushes when appropriate."""
        try:
            # Only push during appropriate phases and elixir levels
            if (self.context.current_phase == "early" and game_state.current_elixir < 6) or \
               (game_state.current_elixir < 4):
                return None

            if self.context.threat_level == 'critical':
                return None  # Too dangerous

            available_cards = self._get_available_cards(game_state)
            if not available_cards:
                return None

            # Build push based on aggression level
            if random.random() < self.aggression_level:
                # Aggressive push
                offensive_cards = [
                    card for card in available_cards
                    if self._is_offensive_card(card['name'])
                ]

                if offensive_cards:
                    push_card = random.choice(offensive_cards)
                    push_position = self._select_aggressive_position(
                        game_state)

                    action = self._create_place_card_action(
                        push_card['position'], push_position
                    )

                    return StrategyDecision(
                        action=action,
                        reasoning=f"Offensive push with {push_card['name']}",
                        confidence=0.6,
                        priority=4
                    )

            return None

        except Exception as e:
            self.logger.error(f"Offensive push rule failed: {e}")
            return None

    async def _rule_spell_value(self, game_state) -> Optional[StrategyDecision]:
        """Rule: Use spells for high-value targets."""
        try:
            available_cards = self._get_available_cards(game_state)
            spell_cards = [
                card for card in available_cards
                if self._is_spell_card(card['name'])
            ]

            if not spell_cards:
                return None

            # Look for high-value spell targets
            enemy_troops = getattr(game_state, 'enemy_troops', [])
            if len(enemy_troops) < 2:  # Need multiple targets for value
                return None

            # Find clustered enemies
            clusters = self._find_troop_clusters(enemy_troops)

            for cluster in clusters:
                if len(cluster['troops']) >= 2:  # Good spell value
                    spell_card = random.choice(spell_cards)
                    target_pos = cluster['center']

                    # Convert to battlefield position
                    spell_position = self._convert_to_battlefield_position(
                        target_pos)

                    action = self._create_place_card_action(
                        spell_card['position'], spell_position
                    )

                    return StrategyDecision(
                        action=action,
                        reasoning=f"High-value spell targeting {len(cluster['troops'])} enemies",
                        confidence=0.8,
                        priority=7
                    )

            return None

        except Exception as e:
            self.logger.error(f"Spell value rule failed: {e}")
            return None

    async def _rule_cycle_cards(self, game_state) -> Optional[StrategyDecision]:
        """Rule: Cycle cheap cards when needed."""
        try:
            # Only cycle if we have excess elixir and no immediate needs
            if game_state.current_elixir < 8 or self.context.threat_level != 'low':
                return None

            available_cards = self._get_available_cards(game_state)
            cheap_cards = [
                card for card in available_cards
                if self._get_card_cost(card['name']) <= 3
            ]

            if not cheap_cards:
                return None

            # Use cheapest available card
            cycle_card = min(
                cheap_cards, key=lambda x: self._get_card_cost(x['name']))

            # Place in safe position
            safe_position = self._get_safe_cycle_position()

            action = self._create_place_card_action(
                cycle_card['position'], safe_position
            )

            return StrategyDecision(
                action=action,
                reasoning=f"Card cycle with {cycle_card['name']}",
                confidence=0.5,
                priority=2  # Low priority
            )

        except Exception as e:
            self.logger.error(f"Card cycle rule failed: {e}")
            return None

    def _get_available_cards(self, game_state) -> List[Dict[str, Any]]:
        """Get list of available cards that can be played."""
        try:
            available = []
            cards_in_hand = getattr(game_state, 'cards_in_hand', [])

            for card in cards_in_hand:
                card_name = card.get('name', 'unknown')
                card_cost = self._get_card_cost(card_name)

                if card.get('available', False) and game_state.current_elixir >= card_cost:
                    card_info = {
                        'name': card_name,
                        'position': card.get('position', 0),
                        'cost': card_cost,
                        'priority': self.card_priorities.get(card_name, {}).get('priority', 0.5)
                    }
                    available.append(card_info)

            return available

        except Exception as e:
            self.logger.error(f"Available cards detection failed: {e}")
            return []

    def _get_card_cost(self, card_name: str) -> int:
        """Get elixir cost of a card."""
        return self.card_priorities.get(card_name, {}).get('cost', 4)

    def _is_defensive_card(self, card_name: str) -> bool:
        """Check if card is primarily defensive."""
        defensive_types = ['ground_tank', 'ranged', 'swarm']
        card_type = self.card_priorities.get(card_name, {}).get('type', '')
        return card_type in defensive_types

    def _is_tank_card(self, card_name: str) -> bool:
        """Check if card is a tank unit."""
        tank_types = ['ground_tank', 'heavy_tank']
        card_type = self.card_priorities.get(card_name, {}).get('type', '')
        return card_type in tank_types

    def _is_offensive_card(self, card_name: str) -> bool:
        """Check if card is primarily offensive."""
        offensive_types = ['heavy_tank', 'ranged_aoe', 'air']
        card_type = self.card_priorities.get(card_name, {}).get('type', '')
        return card_type in offensive_types

    def _is_spell_card(self, card_name: str) -> bool:
        """Check if card is a spell."""
        card_type = self.card_priorities.get(card_name, {}).get('type', '')
        return card_type == 'spell'

    def _calculate_defensive_position(self, game_state) -> Optional[Tuple[int, int]]:
        """Calculate best defensive position."""
        try:
            # Find the most threatening enemy
            threats = self.context.current_threats
            if not threats:
                return None

            closest_threat = min(threats, key=lambda x: x['position'][1])
            threat_x, threat_y = closest_threat['position']

            # Place defense slightly in front of threat
            defense_x = threat_x
            defense_y = min(threat_y + 100, 700)  # Don't place too far back

            return (defense_x, defense_y)

        except Exception as e:
            self.logger.error(f"Defensive position calculation failed: {e}")
            return (960, 650)  # Default center-back position

    def _select_counter_card(self, available_cards: List[Dict], threat: Dict) -> Optional[Dict]:
        """Select appropriate counter card for specific threat."""
        try:
            if not available_cards:
                return None

            # Simple counter logic - use cheapest effective counter
            # In a real implementation, this would have more sophisticated logic
            return min(available_cards, key=lambda x: x['cost'])

        except Exception as e:
            self.logger.error(f"Counter card selection failed: {e}")
            return available_cards[0] if available_cards else None

    def _calculate_counter_position(self, threat_position: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate position to counter a threat."""
        try:
            threat_x, threat_y = threat_position

            # Place counter slightly ahead of threat
            counter_x = threat_x
            counter_y = max(threat_y - 50, 550)  # Don't place too far forward

            return (counter_x, counter_y)

        except Exception as e:
            self.logger.error(f"Counter position calculation failed: {e}")
            return (960, 600)

    def _select_push_lane(self, game_state) -> Tuple[int, int]:
        """Select which lane to push."""
        try:
            # Count enemies in each lane
            enemy_troops = getattr(game_state, 'enemy_troops', [])

            left_lane_enemies = sum(1 for troop in enemy_troops
                                    if troop.get('center', [960, 0])[0] < 800)
            right_lane_enemies = sum(1 for troop in enemy_troops
                                     if troop.get('center', [960, 0])[0] > 1120)

            # Push in lane with fewer enemies
            if left_lane_enemies <= right_lane_enemies:
                return self.config.BATTLEFIELD_GRID["my_left"]
            else:
                return self.config.BATTLEFIELD_GRID["my_right"]

        except Exception as e:
            self.logger.error(f"Push lane selection failed: {e}")
            return self.config.BATTLEFIELD_GRID["my_left"]

    def _select_aggressive_position(self, game_state) -> Tuple[int, int]:
        """Select aggressive position for offensive plays."""
        try:
            # Randomly choose between aggressive positions
            aggressive_positions = [
                (700, 500),   # Left bridge
                (1220, 500),  # Right bridge
                (960, 450)    # Center aggressive
            ]

            return random.choice(aggressive_positions)

        except Exception as e:
            self.logger.error(f"Aggressive position selection failed: {e}")
            return (960, 500)

    def _find_troop_clusters(self, troops: List[Dict]) -> List[Dict]:
        """Find clusters of enemy troops for spell targeting."""
        try:
            clusters = []
            cluster_radius = 150  # pixels

            processed = set()

            for i, troop in enumerate(troops):
                if i in processed:
                    continue

                troop_pos = troop.get('center', [0, 0])
                if len(troop_pos) < 2:
                    continue

                cluster_troops = [troop]
                processed.add(i)

                # Find nearby troops
                for j, other_troop in enumerate(troops):
                    if j in processed:
                        continue

                    other_pos = other_troop.get('center', [0, 0])
                    if len(other_pos) < 2:
                        continue

                    distance = np.sqrt((troop_pos[0] - other_pos[0]) ** 2 +
                                       (troop_pos[1] - other_pos[1]) ** 2)

                    if distance <= cluster_radius:
                        cluster_troops.append(other_troop)
                        processed.add(j)

                if len(cluster_troops) >= 2:
                    # Calculate cluster center
                    center_x = sum(t.get('center', [0, 0])[
                                   0] for t in cluster_troops) / len(cluster_troops)
                    center_y = sum(t.get('center', [0, 0])[
                                   1] for t in cluster_troops) / len(cluster_troops)

                    clusters.append({
                        'troops': cluster_troops,
                        'center': (int(center_x), int(center_y)),
                        'size': len(cluster_troops)
                    })

            return clusters

        except Exception as e:
            self.logger.error(f"Troop clustering failed: {e}")
            return []

    def _convert_to_battlefield_position(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Convert detection position to battlefield placement position."""
        # Simple conversion - in reality this might need coordinate transformation
        return position

    def _get_safe_cycle_position(self) -> Tuple[int, int]:
        """Get safe position for cycling cards."""
        # Behind our king tower
        return (960, 750)

    def _create_place_card_action(self, card_position: int, target_position: Tuple[int, int]) -> GameAction:
        """Create a place card action."""
        try:
            if 0 <= card_position < len(self.config.CARD_POSITIONS):
                card_coords = self.config.CARD_POSITIONS[card_position]

                return GameAction(
                    action_type=ActionType.PLACE_CARD,
                    parameters={
                        'card_position': card_coords,
                        'target_position': target_position
                    }
                )
            else:
                self.logger.error(f"Invalid card position: {card_position}")
                return None

        except Exception as e:
            self.logger.error(f"Action creation failed: {e}")
            return None

    async def update_from_feedback(self, action: GameAction, success: bool):
        """Update strategy based on action feedback."""
        try:
            if success:
                self.successful_decisions += 1

            # Adjust aggression based on success rate
            if self.decisions_made > 20:  # Have enough data
                current_success_rate = self.successful_decisions / self.decisions_made

                if current_success_rate < 0.4:  # Low success rate
                    self.aggression_level = max(
                        0.2, self.aggression_level - 0.05)
                elif current_success_rate > 0.7:  # High success rate
                    self.aggression_level = min(
                        0.9, self.aggression_level + 0.02)

        except Exception as e:
            self.logger.error(f"Strategy update from feedback failed: {e}")
