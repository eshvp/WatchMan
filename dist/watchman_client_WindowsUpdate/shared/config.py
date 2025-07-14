"""
Configuration management for WatchMan system.
"""
import json
import os
from typing import Dict, Any

class Config:
    """Configuration manager"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.data[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values"""
        self.data.update(updates)
