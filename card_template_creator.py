#!/usr/bin/env python3
"""
Card Template Creator for ElixirMind
Creates and manages card detection templates for Clash Royale.
"""

import cv2
import numpy as np
import os
import json
from pathlib import Path
import mss
import time
from PIL import Image

class CardTemplateCreator:
    def __init__(self):
        self.sct = mss.mss()
        self.templates_dir = Path("data/card_templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        self.card_templates = {}
        self.card_database = {}

        # Card positions in hand (adjust based on resolution)
        self.card_positions = [
            (240, 940, 400, 1000),   # Card 1
            (480, 940, 640, 1000),   # Card 2
            (720, 940, 880, 1000),   # Card 3
            (960, 940, 1120, 1000),  # Card 4
        ]

        # Known Clash Royale cards
        self.known_cards = [
            "Knight", "Archers", "Goblins", "Giant",
            "P.E.K.K.A", "Minions", "Balloon", "Witch",
            "Barbarians", "Golem", "Skeletons", "Valkyrie",
            "Skeleton Army", "Bomber", "Musketeer", "Baby Dragon",
            "Prince", "Wizard", "Mini P.E.K.K.A", "Giant Skeleton",
            "Hog Rider", "Minion Horde", "Ice Wizard", "Royal Giant",
            "Guards", "Princess", "Dark Prince", "Three Musketeers",
            "Lava Hound", "Ice Spirit", "Fire Spirit", "Goblins",
            "Spear Goblins", "Bats", "Zap", "Giant Snowball",
            "Arrows", "Rage", "Rocket", "Barbarian Barrel",
            "Lightning", "Poison", "Graveyard", "The Log",
            "Tornado", "Clone", "Earthquake", "Freeze",
            "Mirror", "Fireball", "Cannon", "Tesla",
            "Mortar", "Bomb Tower", "Inferno Tower", "Furnace",
            "Goblin Hut", "Barbarian Hut", "Elixir Collector", "Tombstone",
            "X-Bow", "Goblin Cage", "Fishing Hut", "Skeleton Barrel"
        ]

    def capture_screen(self):
        """Capture current screen"""
        monitor = self.sct.monitors[1]
        screenshot = self.sct.grab(monitor)
        return np.array(screenshot)

    def extract_card_region(self, frame, position_index):
        """Extract card region from screenshot"""
        if position_index >= len(self.card_positions):
            return None

        x, y, w, h = self.card_positions[position_index]
        card_region = frame[y:y+h, x:x+w]

        # Convert RGB to BGR for OpenCV
        return cv2.cvtColor(card_region, cv2.COLOR_RGB2BGR)

    def preprocess_card_image(self, card_img):
        """Preprocess card image for template matching"""
        if card_img is None:
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)

        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)

        # Apply threshold to get binary image
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return thresh

    def create_card_template(self, card_name, position_index=0):
        """Create template for a specific card"""
        print(f"📸 Creating template for: {card_name}")

        # Wait a moment for user to position card
        print(f"Position card '{card_name}' in slot {position_index + 1}")
        print("Press Enter when ready...")
        input()

        # Capture screen
        frame = self.capture_screen()

        # Extract card region
        card_img = self.extract_card_region(frame, position_index)
        if card_img is None:
            print(f"❌ Failed to extract card region for position {position_index}")
            return False

        # Preprocess
        processed = self.preprocess_card_image(card_img)
        if processed is None:
            print("❌ Failed to preprocess card image")
            return False

        # Save template
        template_path = self.templates_dir / f"{card_name.lower().replace(' ', '_')}.png"
        cv2.imwrite(str(template_path), processed)

        # Save metadata
        metadata = {
            "name": card_name,
            "position": position_index,
            "created_at": time.time(),
            "dimensions": processed.shape,
            "template_path": str(template_path)
        }

        metadata_path = self.templates_dir / f"{card_name.lower().replace(' ', '_')}_meta.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Template created: {template_path}")
        return True

    def batch_create_templates(self, cards_list=None):
        """Create templates for multiple cards"""
        if cards_list is None:
            cards_list = self.known_cards[:10]  # First 10 cards for demo

        print(f"🎯 Creating templates for {len(cards_list)} cards")
        print("Make sure Clash Royale is running and you're in a battle!")

        successful = 0
        for i, card_name in enumerate(cards_list):
            try:
                position = i % 4  # Cycle through 4 card positions
                if self.create_card_template(card_name, position):
                    successful += 1

                # Wait between captures
                time.sleep(2)

            except KeyboardInterrupt:
                print("\n🛑 Template creation interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error creating template for {card_name}: {e}")

        print(f"\n📊 Template Creation Complete: {successful}/{len(cards_list)} successful")

    def load_templates(self):
        """Load all available card templates"""
        self.card_templates = {}

        for template_file in self.templates_dir.glob("*_meta.json"):
            try:
                with open(template_file, 'r') as f:
                    metadata = json.load(f)

                # Load template image
                template_path = Path(metadata["template_path"])
                if template_path.exists():
                    template_img = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
                    self.card_templates[metadata["name"]] = {
                        "image": template_img,
                        "metadata": metadata
                    }

            except Exception as e:
                print(f"❌ Error loading template {template_file}: {e}")

        print(f"📚 Loaded {len(self.card_templates)} card templates")
        return self.card_templates

    def match_card(self, card_region, threshold=0.7):
        """Match card region against templates"""
        if not self.card_templates:
            self.load_templates()

        best_match = None
        best_score = 0

        processed_region = self.preprocess_card_image(card_region)

        for card_name, template_data in self.card_templates.items():
            try:
                template = template_data["image"]

                # Template matching
                result = cv2.matchTemplate(processed_region, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)

                if max_val > best_score and max_val >= threshold:
                    best_score = max_val
                    best_match = card_name

            except Exception as e:
                continue

        return best_match, best_score

    def detect_current_hand(self, frame=None):
        """Detect all cards in current hand"""
        if frame is None:
            frame = self.capture_screen()

        detected_cards = []

        for i in range(4):  # 4 card positions
            card_img = self.extract_card_region(frame, i)
            if card_img is not None:
                card_name, confidence = self.match_card(card_img)

                detected_cards.append({
                    "position": i,
                    "name": card_name,
                    "confidence": confidence,
                    "region": self.card_positions[i]
                })

        return detected_cards

    def test_template_matching(self):
        """Test template matching accuracy"""
        print("🧪 Testing template matching...")

        if not self.card_templates:
            print("❌ No templates loaded. Run batch_create_templates() first.")
            return

        # Capture current screen
        frame = self.capture_screen()

        # Detect cards
        detected = self.detect_current_hand(frame)

        print("\n🎴 Detection Results:")
        for card in detected:
            status = "✅" if card["name"] else "❌"
            name = card["name"] or "Unknown"
            conf = f"{card['confidence']:.2f}" if card["confidence"] else "0.00"
            print(f"  Position {card['position'] + 1}: {status} {name} (conf: {conf})")

        # Save detection visualization
        vis_img = frame.copy()
        for card in detected:
            x, y, w, h = card["region"]
            color = (0, 255, 0) if card["name"] else (0, 0, 255)
            cv2.rectangle(vis_img, (x, y), (x+w, y+h), color, 2)

            label = card["name"] or "Unknown"
            cv2.putText(vis_img, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.imwrite("card_detection_test.png", cv2.cvtColor(vis_img, cv2.COLOR_RGB2BGR))
        print("📸 Saved detection visualization: card_detection_test.png")

    def export_template_database(self):
        """Export template database for sharing"""
        database = {
            "version": "1.0",
            "created_at": time.time(),
            "cards": {}
        }

        for card_name, data in self.card_templates.items():
            metadata = data["metadata"]
            database["cards"][card_name] = {
                "name": metadata["name"],
                "dimensions": metadata["dimensions"],
                "created_at": metadata["created_at"]
            }

        with open("card_template_database.json", "w") as f:
            json.dump(database, f, indent=2)

        print(f"💾 Exported database with {len(database['cards'])} cards")

    def import_template_database(self, database_path):
        """Import template database"""
        try:
            with open(database_path, 'r') as f:
                database = json.load(f)

            print(f"📥 Importing database with {len(database['cards'])} cards")
            # Implementation would copy templates from database

        except Exception as e:
            print(f"❌ Error importing database: {e}")

def main():
    creator = CardTemplateCreator()

    print("🎴 ElixirMind Card Template Creator")
    print("=" * 40)

    while True:
        print("\nOptions:")
        print("1. Create templates for known cards")
        print("2. Test template matching")
        print("3. Load existing templates")
        print("4. Export template database")
        print("5. Detect current hand")
        print("6. Exit")

        choice = input("\nChoose option (1-6): ").strip()

        if choice == "1":
            creator.batch_create_templates()
        elif choice == "2":
            creator.test_template_matching()
        elif choice == "3":
            creator.load_templates()
        elif choice == "4":
            creator.export_template_database()
        elif choice == "5":
            hand = creator.detect_current_hand()
            print("\n🎴 Current Hand:")
            for card in hand:
                print(f"  {card['position'] + 1}: {card['name'] or 'Unknown'}")
        elif choice == "6":
            break
        else:
            print("❌ Invalid option")

if __name__ == "__main__":
    main()
