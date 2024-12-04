"""
Configuration loader utility.
"""
import json
from pathlib import Path

def load_config(env: str = 'dev'):
    config_path = Path(__file__).parent.parent.parent / 'configs' / f'{env}_config.json'
    with open(config_path) as f:
        return json.load(f)
