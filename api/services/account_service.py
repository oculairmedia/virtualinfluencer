import os
import yaml
from typing import List, Optional
from api.models import AccountInfo, AccountConfig

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
