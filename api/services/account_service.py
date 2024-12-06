import os
import yaml
from typing import List, Optional
from api.models import AccountInfo, AccountConfig
from datetime import datetime
import re
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

class AccountService:
    def __init__(self, accounts_dir: str):
        self.accounts_dir = accounts_dir
        if not os.path.exists(accounts_dir):
            os.makedirs(accounts_dir)

    async def list_accounts(self) -> List[AccountInfo]:
        """List all Instagram accounts with their configurations"""
        accounts = []
        if not os.path.exists(self.accounts_dir):
            return accounts

        for account_name in os.listdir(self.accounts_dir):
            account_dir = os.path.join(self.accounts_dir, account_name)
            if os.path.isdir(account_dir):
                try:
                    config = await self.get_account_config(account_name)
                    account_info = AccountInfo(
                        name=account_name,
                        config=config,
                        status="stopped",  # Default status
                        last_run=None,
                        total_interactions=0,
                        errors=None
                    )
                    accounts.append(account_info)
                except Exception as e:
                    # Log error but continue with other accounts
                    print(f"Error loading account {account_name}: {str(e)}")
                    continue
        return accounts

    async def get_account_config(self, account: str) -> Optional[AccountConfig]:
        """Get configuration for a specific account"""
        config_path = os.path.join(self.accounts_dir, account, "config.yml")
        if not os.path.exists(config_path):
            return None
        
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
                # Ensure required fields are present
                config_data.setdefault('username', account)
                config_data.setdefault('device', 'default')
                return AccountConfig(**config_data)
        except Exception as e:
            print(f"Error reading config for {account}: {str(e)}")
            return None

    async def update_account_config(self, account: str, config: AccountConfig) -> bool:
        """Update configuration for a specific account"""
        account_dir = os.path.join(self.accounts_dir, account)
        if not os.path.exists(account_dir):
            os.makedirs(account_dir)
        
        config_path = os.path.join(account_dir, "config.yml")
        try:
            with open(config_path, 'w') as f:
                yaml.dump(config.dict(exclude_none=True), f)
            return True
        except Exception as e:
            print(f"Error updating config for {account}: {str(e)}")
            return False

    async def patch_account_config(self, account: str, updates: dict) -> dict:
        """Partially update configuration for a specific account"""
        config_path = os.path.join(self.accounts_dir, account, "config.yml")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found for account {account}")

        try:
            # Initialize ruamel.yaml
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.width = 4096  # Prevent line wrapping
            yaml.indent(mapping=2, sequence=4, offset=2)

            # Read the current file content
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Update timestamp in header
            for i, line in enumerate(lines):
                if '# Last updated:' in line:
                    lines[i] = f'# Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n'
                    break

            # Find the index where the actual YAML content starts
            yaml_start_index = None
            for idx, line in enumerate(lines):
                if line.strip() == '##############################################################################':
                    if idx + 1 < len(lines) and lines[idx + 1].strip().startswith('# Actions'):
                        yaml_start_index = idx + 2  # YAML content starts after this line
                        break

            if yaml_start_index is None:
                raise Exception("Could not find the start of YAML content in config file.")

            # Extract the YAML content
            yaml_content = ''.join(lines[yaml_start_index:])

            # Parse the YAML content
            config_data = yaml.load(yaml_content) or CommentedMap()

            # Ensure config_data is a CommentedMap
            if not isinstance(config_data, CommentedMap):
                raise Exception("Parsed YAML content is not a valid CommentedMap.")

            # Process updates
            for key, value in updates.items():
                # Convert key to string if necessary
                if not isinstance(key, str):
                    key = str(key)

                if isinstance(value, list):
                    # Ensure list items are correctly handled
                    config_data[key] = [str(v) for v in value]
                else:
                    config_data[key] = value

            # Write back to file while preserving the scratchpad
            with open(config_path, 'w', encoding='utf-8') as f:
                # Write the scratchpad and header back to the file
                f.writelines(lines[:yaml_start_index])
                # Dump the updated YAML content
                yaml.dump(config_data, f)

            return config_data

        except Exception as e:
            print(f"Error updating config for account {account}: {str(e)}")
            raise Exception(f"Failed to update config: {str(e)}")
