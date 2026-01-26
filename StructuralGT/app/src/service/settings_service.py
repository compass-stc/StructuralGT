"""Settings service for StructuralGT GUI."""

import json
from pathlib import Path
from typing import Dict, Any


class SettingsService:
    """Service for StructuralGT GUI."""

    def __init__(self, settings_file: str = "settings.json"):
        """Initialize the settings service."""
        app_dir = Path(__file__).parent.parent
        self.settings_path = app_dir / settings_file
        self._settings: Dict[str, Any] = {}
        self._load_settings()

    def get(self, key: str, default: Any = None) -> Any:
        """Get the value for the given key."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set the value for the given key."""
        self._settings[key] = value
        self._save_settings()

    def _load_settings(self):
        """Load the settings from json file."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._settings = self._get_default_settings()
                self._save_settings()
        else:
            self._settings = self._get_default_settings()
            self._save_settings()

    def _save_settings(self):
        """Save the settings to json file."""
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def _get_default_settings(self) -> Dict[str, Any]:
        return {
            "theme": "dark"  # Default to dark theme
        }
