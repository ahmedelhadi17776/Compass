"""
Configuration loader utility.
"""
import json
from pathlib import Path
from cryptography.fernet import Fernet


class SecureConfigLoader:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)

    def load_config(self, env: str = 'dev') -> dict:
        config_path = Path(__file__).parent.parent.parent / \
            'configs' / f'{env}_config.json'
        with open(config_path) as f:
            config = json.load(f)

        # Decrypt sensitive values
        for key, value in config.items():
            if key.endswith('_encrypted'):
                config[key[:-10]] = self.decrypt_value(value)

        return config

    def decrypt_value(self, encrypted_value: str) -> str:
        return self.cipher_suite.decrypt(encrypted_value.encode()).decode()
