"""
Model Downloader: Downloads and manages AI models for ElixirMind.
Handles automatic download of pre-trained models and setup of card templates.
"""

import requests
import os
import logging
from pathlib import Path
from typing import Dict, Optional, List
import zipfile
import hashlib
import json

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. Model verification will be limited.")

logger = logging.getLogger(__name__)

class ModelDownloader:
    """
    Downloads and manages AI models for the ElixirMind bot.
    Handles YOLOv5 models, card detection models, and template setup.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # Model URLs and metadata
        self.models_config = {
            "yolov5s": {
                "url": "https://github.com/ultralytics/yolov5/releases/download/v6.2/yolov5s.pt",
                "filename": "yolov5s.pt",
                "hash": None,  # We'll compute this
                "description": "YOLOv5 small model for object detection"
            },
            "yolov5m": {
                "url": "https://github.com/ultralytics/yolov5/releases/download/v6.2/yolov5m.pt",
                "filename": "yolov5m.pt",
                "hash": None,
                "description": "YOLOv5 medium model for better accuracy"
            },
            "card_detector": {
                "url": None,  # Will be trained locally
                "filename": "card_detector.pt",
                "hash": None,
                "description": "Custom trained card detector model"
            }
        }

        # Template URLs (placeholder - you'll need to create these)
        self.templates_config = {
            "card_templates": {
                "url": None,  # Local generation
                "filename": "card_templates.zip",
                "description": "Card template images for template matching"
            }
        }

        # Download status
        self.download_status = {}

    def download_file(self, url: str, filename: str, expected_hash: Optional[str] = None) -> bool:
        """
        Download a file with progress tracking and hash verification.

        Args:
            url: Download URL
            filename: Local filename
            expected_hash: Expected SHA256 hash for verification

        Returns:
            bool: True if download successful
        """
        try:
            filepath = self.models_dir / filename

            logger.info(f"Downloading {filename} from {url}")

            # Download with progress
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            logger.info(".1f")

            # Verify hash if provided
            if expected_hash:
                actual_hash = self._calculate_sha256(filepath)
                if actual_hash != expected_hash:
                    logger.error(f"Hash verification failed for {filename}")
                    os.remove(filepath)
                    return False

            logger.info(f"Successfully downloaded {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to download {filename}: {e}")
            return False

    def _calculate_sha256(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def download_base_models(self) -> bool:
        """
        Download base YOLOv5 models for object detection.

        Returns:
            bool: True if all downloads successful
        """
        logger.info("Starting download of base models...")

        success_count = 0
        total_models = len([m for m in self.models_config.values() if m['url'] is not None])

        for model_name, config in self.models_config.items():
            if config['url'] is None:
                logger.info(f"Skipping {model_name} - no URL provided")
                continue

            filepath = self.models_dir / config['filename']

            # Check if already exists
            if filepath.exists():
                logger.info(f"{model_name} already exists, skipping download")
                success_count += 1
                continue

            # Download the model
            if self.download_file(config['url'], config['filename'], config.get('hash')):
                success_count += 1
                self.download_status[model_name] = "downloaded"
            else:
                self.download_status[model_name] = "failed"

        logger.info(f"Downloaded {success_count}/{total_models} models")
        return success_count == total_models

    def setup_card_templates(self) -> bool:
        """
        Set up card templates for template matching fallback.
        Creates basic templates from game screenshots.

        Returns:
            bool: True if setup successful
        """
        logger.info("Setting up card templates...")

        templates_dir = self.models_dir / "templates"
        templates_dir.mkdir(exist_ok=True)

        # For now, create placeholder templates
        # In a real implementation, you'd extract these from game screenshots

        card_templates = [
            "knight.png", "archers.png", "fireball.png", "giant.png",
            "mini_pekka.png", "musketeer.png", "skeleton_army.png",
            "hog_rider.png", "valkyrie.png", "wizard.png"
        ]

        # Create placeholder template files (you'd replace with actual images)
        for template in card_templates:
            template_path = templates_dir / template
            if not template_path.exists():
                # Create a placeholder image (1x1 pixel)
                with open(template_path, 'wb') as f:
                    # Minimal PNG header for placeholder
                    f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82')

        logger.info(f"Created {len(card_templates)} placeholder card templates")
        return True

    def verify_models(self) -> Dict[str, bool]:
        """
        Verify that all required models are present and valid.

        Returns:
            Dict[str, bool]: Verification status for each model
        """
        verification_results = {}

        for model_name, config in self.models_config.items():
            filepath = self.models_dir / config['filename']

            if not filepath.exists():
                verification_results[model_name] = False
                continue

            # Try to load the model to verify it's valid
            try:
                if model_name.startswith('yolov5'):
                    # For YOLOv5 models, try to load with torch if available
                    if TORCH_AVAILABLE:
                        model = torch.load(filepath, map_location='cpu')
                        verification_results[model_name] = True
                    else:
                        # Fallback: check file size for basic verification
                        if filepath.stat().st_size > 1000000:  # > 1MB for YOLO models
                            verification_results[model_name] = True
                        else:
                            verification_results[model_name] = False
                elif model_name == 'card_detector':
                    # Custom model verification
                    if filepath.stat().st_size > 0:  # Basic size check
                        verification_results[model_name] = True
                    else:
                        verification_results[model_name] = False
                else:
                    verification_results[model_name] = True

            except Exception as e:
                logger.error(f"Failed to verify {model_name}: {e}")
                verification_results[model_name] = False

        return verification_results

    def get_model_path(self, model_name: str) -> Optional[Path]:
        """
        Get the path to a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Optional[Path]: Path to the model file, or None if not found
        """
        if model_name in self.models_config:
            filepath = self.models_dir / self.models_config[model_name]['filename']
            return filepath if filepath.exists() else None
        return None

    def list_available_models(self) -> List[str]:
        """
        List all available (downloaded) models.

        Returns:
            List[str]: Names of available models
        """
        available = []
        for model_name in self.models_config.keys():
            if self.get_model_path(model_name) is not None:
                available.append(model_name)
        return available

    def cleanup_old_models(self) -> int:
        """
        Clean up old or corrupted model files.

        Returns:
            int: Number of files cleaned up
        """
        cleaned = 0

        # Verify all files in models directory
        for filepath in self.models_dir.glob("*"):
            if filepath.is_file() and filepath.suffix in ['.pt', '.pth', '.onnx']:
                try:
                    # Try to load as PyTorch model
                    torch.load(filepath, map_location='cpu')
                except Exception:
                    logger.warning(f"Removing corrupted model file: {filepath}")
                    os.remove(filepath)
                    cleaned += 1

        return cleaned

    def update_model_hashes(self) -> None:
        """Update the expected hashes for downloaded models."""
        for model_name, config in self.models_config.items():
            filepath = self.get_model_path(model_name)
            if filepath:
                config['hash'] = self._calculate_sha256(filepath)
                logger.info(f"Updated hash for {model_name}")

    def save_config(self) -> None:
        """Save current model configuration to disk."""
        config_path = self.models_dir / "models_config.json"
        with open(config_path, 'w') as f:
            json.dump(self.models_config, f, indent=2)
        logger.info(f"Saved model configuration to {config_path}")

    def load_config(self) -> None:
        """Load model configuration from disk."""
        config_path = self.models_dir / "models_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.models_config.update(json.load(f))
            logger.info(f"Loaded model configuration from {config_path}")

    def setup_all(self) -> bool:
        """
        Complete setup: download models and setup templates.

        Returns:
            bool: True if setup successful
        """
        logger.info("Starting complete model setup...")

        # Load existing config
        self.load_config()

        # Download base models
        models_ok = self.download_base_models()

        # Setup templates
        templates_ok = self.setup_card_templates()

        # Verify everything
        verification = self.verify_models()
        all_verified = all(verification.values())

        # Save updated config
        self.save_config()

        success = models_ok and templates_ok and all_verified

        if success:
            logger.info("Model setup completed successfully!")
        else:
            logger.error("Model setup failed. Check logs for details.")

        return success
