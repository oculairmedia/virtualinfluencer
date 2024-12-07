import os
import yaml
from typing import List, Optional, Dict, Any
from api.models import AccountInfo, AccountConfig, ConfigUpdate
from datetime import datetime
import re
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from fastapi import HTTPException

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

            # Convert kebab-case keys to snake_case
            converted_data = {}
            for key, value in config_data.items():
                if isinstance(key, str):
                    # Convert kebab-case to snake_case
                    snake_key = key.replace('-', '_')
                    converted_data[snake_key] = value

            # Create AccountConfig from the converted data
            return AccountConfig(**converted_data)
        except Exception as e:
            print(f"Error loading config for account {account}: {str(e)}")
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

    async def patch_account_config(self, account: str, config_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update account configuration."""
        config_path = os.path.join(self.accounts_dir, account, "config.yml")
        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail=f"Account {account} not found")

        try:
            # Load existing config while preserving comments
            yaml = YAML()
            yaml.preserve_quotes = True
            with open(config_path, 'r') as f:
                config_data = yaml.load(f)

            # Update timestamp in header comment
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(config_path, 'r') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                if line.startswith("# Last updated:"):
                    lines[i] = f"# Last updated: {timestamp}\n"
                    break

            # Convert snake_case to kebab-case for keys
            kebab_dict = {k.replace('_', '-'): v for k, v in config_update.items()}

            # Update config data
            config_data.update(kebab_dict)

            # Write back to file, preserving structure and comments
            with open(config_path, 'w') as f:
                # Write header with timestamp
                f.writelines(lines[:20])  # Write first 20 lines (header) as is
                
                # Write the rest of the config with special list handling
                for key, value in config_data.items():
                    if isinstance(value, list):
                        # Format lists with square brackets and quoted strings
                        quoted_items = [f'"{item}"' for item in value]
                        f.write(f'{key}: [{", ".join(quoted_items)}]\n')
                    else:
                        yaml.dump({key: value}, f)

            return config_data

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")
