import os
import json
from typing import Dict, Any, List

CONFIG_DIR = os.environ.get("BITECLI_CONFIG_DIR", os.path.expanduser("~/.config/bitecli"))
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_FEEDS = [
    {"name": "Berkeley AIR", "url": "https://bair.berkeley.edu/blog/feed.xml"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "GitHub Engineering", "url": "https://github.blog/category/engineering/feed/"},
    {"name": "Netflix Tech", "url": "https://netflixtechblog.com/feed"},
]

DEFAULT_CONFIG = {
    "llm_provider": "gemini",
    "api_keys": {
        "gemini": "",
        "openai": "",
        "claude": "",
        "perplexity": ""
    },
    "feeds": DEFAULT_FEEDS,
    "max_buffered_summaries": 7
}

def load_config() -> Dict[str, Any]:
    """Loads the config or returns defaults."""
    if not os.path.exists(CONFIG_FILE):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    with open(CONFIG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_CONFIG

def save_config(config: Dict[str, Any]):
    """Saves the config dict to file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_api_key(provider: str) -> str:
    """Gets API key for the provider."""
    config = load_config()
    return config.get("api_keys", {}).get(provider, "")

def set_api_key(provider: str, key: str):
    """Sets an API key for a provider."""
    config = load_config()
    if "api_keys" not in config:
        config["api_keys"] = {}
    config["api_keys"][provider] = key
    save_config(config)

def set_llm_provider(provider: str):
    """Sets the default LLM provider."""
    config = load_config()
    config["llm_provider"] = provider
    save_config(config)

def get_feeds() -> List[Dict[str, str]]:
    """Gets configured feeds."""
    config = load_config()
    return config.get("feeds", DEFAULT_FEEDS)

def add_feed(name: str, url: str):
    config = load_config()
    if "feeds" not in config:
        config["feeds"] = []
    config["feeds"].append({"name": name, "url": url})
    save_config(config)
