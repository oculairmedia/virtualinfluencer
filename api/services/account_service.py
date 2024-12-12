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

    def _transform_value(self, value: Any) -> Any:
        """Transform values to proper format for YAML"""
        if isinstance(value, list):
            # Convert all list items to strings and maintain flow style
            return [str(item) for item in value]
        elif isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            # Check if it's a numeric range (e.g., "2-3" or "15-25")
            if re.match(r'^\d+\-\d+$', value):
                return value.strip('"\'')  # Remove any quotes
            return value
        return value

    def _get_default_header(self, timestamp: str) -> str:
        """Get the default header template with given timestamp"""
        return f"""##############################################################################
# SCRATCHPAD - IMPORTANT NOTES FOR LLMs
##############################################################################
# Last updated: {timestamp}
# 
# FORMATTING RULES:
# 1. All lists/arrays must use proper YAML syntax with square brackets and commas
#    Example: blogger-followers: [ "user1", "user2", "user3" ]
# 2. Usernames should be in quotes to handle special characters
# 3. Time ranges use hyphens without spaces: "12-18" not "12 - 18"
#
# CURRENT STRATEGY:
# - Target: Followers of established 3D artists and motion designers
# - Speed: Moderate interactions (speed-multiplier: 0.4) for stability
# - Session Timing: 6-12 minute breaks between sessions
# - Moderate interaction limits to maintain stability
# - No mandatory word requirements
#
# INSTRUCTIONS FOR FUTURE LLMs:
# 1. When modifying this file, update the "Last updated" timestamp above"""

    def _extract_config_section(self, content: str) -> str:
        """Extract just the YAML config section (non-comment lines)"""
        lines = content.split('\n')
        config_lines = []
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                config_lines.append(line)
        return '\n'.join(config_lines)

    async def patch_account_config(self, account: str, config_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update account configuration."""
        config_path = os.path.join(self.accounts_dir, account, "config.yml")
        if not os.path.exists(config_path):
            raise HTTPException(status_code=404, detail=f"Account {account} not found")

        try:
            # Read existing file
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Extract just the config section
            config_section = self._extract_config_section(content)
            
            # Initialize YAML handler
            yaml = YAML()
            yaml.preserve_quotes = False  # Don't preserve quotes to avoid quoted parameter names
            yaml.default_flow_style = True  # Use flow style for lists [item1, item2]
            yaml.indent(mapping=2, sequence=4, offset=2)
            
            # Load existing config
            config_data = yaml.load(config_section) or {}

            # Convert snake_case to kebab-case and transform values
            updates = {}
            for key, value in config_update.items():
                kebab_key = key.replace('_', '-')
                updates[kebab_key] = self._transform_value(value)

            # Update config data
            config_data.update(updates)

            # Write back to file
            with open(config_path, 'w') as f:
                # Write header with current timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                header = self._get_default_header(timestamp)
                f.write(header)
                f.write('\n\n')  # Add separator between header and content
                
                # Write config data
                yaml.dump(config_data, f)

            return config_data

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")
