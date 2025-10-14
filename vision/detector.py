    def detect_battle(self, screen, debug_mode=False):
        """Detect if battle is active using multiple indicators."""
        if not self.initialized or screen is None:
            return False

        # Check cache first
        cache_key = f"battle_detection_{hash(screen.tobytes()) if screen is not None else 'none'}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Multiple battle detection methods
        indicators = []

        # Method 1: Elixir detection
        elixir_present = self._detect_elixir_presence(screen)
        indicators.append(("elixir", elixir_present))

        # Method 2: Card hand detection
        cards_present = self._detect_card_hand(screen)
        indicators.append(("cards", cards_present))

        # Method 3: Tower detection
        towers_present = self._detect_towers(screen)
        indicators.append(("towers", towers_present))

        # Method 4: Template matching (if templates available)
        template_match = self._detect_battle_template(screen)
        indicators.append(("template", template_match))

        # Battle is active if at least 2 indicators are positive
        positive_indicators = sum(1 for _, present in indicators if present)
        battle_active = positive_indicators >= 2

        # Debug logging
        if debug_mode or not battle_active:
            logger.info(f"Battle detection: {positive_indicators}/4 indicators positive")
            for indicator_name, present in indicators:
                logger.info(f"  - {indicator_name}: {'YES' if present else 'NO'}")

        # Cache result
        self.cache_manager.put(cache_key, battle_active)

        return battle_active
=======
    def detect_battle(self, screen, debug_mode=False):
        """Detect if battle is active using multiple indicators."""
        if not self.initialized or screen is None:
            return False

        # Check cache first
        cache_key = f"battle_detection_{hash(screen.tobytes()) if screen is not None else 'none'}"
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Multiple battle detection methods
        indicators = []

        # Method 1: Elixir detection
        elixir_present = self._detect_elixir_presence(screen)
        indicators.append(("elixir", elixir_present))

        # Method 2: Card hand detection
        cards_present = self._detect_card_hand(screen)
        indicators.append(("cards", cards_present))

        # Method 3: Tower detection
        towers_present = self._detect_towers(screen)
        indicators.append(("towers", towers_present))

        # Method 4: Template matching (if templates available)
        template_match = self._detect_battle_template(screen)
        indicators.append(("template", template_match))

        # Battle is active if at least 2 indicators are positive
        positive_indicators = sum(1 for _, present in indicators if present)
        battle_active = positive_indicators >= 2

        # Debug logging
        if debug_mode or not battle_active:
            logger.info(f"Battle detection: {positive_indicators}/4 indicators positive")
            for indicator_name, present in indicators:
                logger.info(f"  - {indicator_name}: {'YES' if present else 'NO'}")

        # Cache result
        self.cache_manager.put(cache_key, battle_active)

        return battle_active
