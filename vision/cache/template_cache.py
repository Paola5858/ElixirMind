"""
Template Cache: Caches image templates for faster matching.
"""

import os
import pickle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TemplateCache:
    def __init__(self, cache_dir='data/templates'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.templates = {}

    def load_template(self, name):
        """Load template from cache or file."""
        if name in self.templates:
            return self.templates[name]

        cache_path = self.cache_dir / f"{name}.pkl"
        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                template = pickle.load(f)
                self.templates[name] = template
                return template

        return None

    def save_template(self, name, template):
        """Save template to cache and file."""
        self.templates[name] = template

        cache_path = self.cache_dir / f"{name}.pkl"
        with open(cache_path, 'wb') as f:
            pickle.dump(template, f)

    def preload_templates(self, template_names):
        """Preload multiple templates."""
        for name in template_names:
            self.load_template(name)

    def clear_cache(self):
        """Clear in-memory cache."""
        self.templates.clear()
