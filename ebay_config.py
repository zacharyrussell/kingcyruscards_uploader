import json
import os
from pathlib import Path

# Store config in user's home directory
CONFIG_DIR = Path.home() / ".kingcyruscards"
CONFIG_FILE = CONFIG_DIR / "ebay_config.json"
DEFAULTS_FILE = CONFIG_DIR / "defaults.json"

def ensure_config_dir():
    """Create config directory if it doesn't exist"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    """Load eBay API configuration"""
    ensure_config_dir()
    
    if not CONFIG_FILE.exists():
        return {
            "app_id": "",
            "dev_id": "",
            "cert_id": "",
            "environment": "sandbox"  # or "production"
        }
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def save_config(config):
    """Save eBay API configuration"""
    ensure_config_dir()
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def is_configured():
    """Check if eBay credentials are configured"""
    config = load_config()
    return all([
        config.get("app_id"),
        config.get("dev_id"),
        config.get("cert_id")
    ])

def load_defaults():
    """Load listing defaults"""
    ensure_config_dir()
    
    if not DEFAULTS_FILE.exists():
        return {
            "category_id": "",
            "condition": "NEW",
            "quantity": 1
        }
    
    try:
        with open(DEFAULTS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading defaults: {e}")
        return {}

def save_defaults(defaults):
    """Save listing defaults"""
    ensure_config_dir()
    
    try:
        with open(DEFAULTS_FILE, 'w') as f:
            json.dump(defaults, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving defaults: {e}")
        return False