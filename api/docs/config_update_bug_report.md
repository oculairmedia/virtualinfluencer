# Bug Report: Config Update API Endpoint Issues

## Issue Summary
The `/accounts/{account}/config` PATCH endpoint is not properly validating and transforming config parameters, leading to configuration format incompatibilities with the GramAddict bot.

## Environment
- API Version: Current
- Endpoint: PATCH `/accounts/{account}/config`
- Test Account: oculairmedia
- Date Discovered: 2024-12-12

## Description
When updating the configuration through the API endpoint, the saved config.yml file contains invalid parameter formatting that makes it incompatible with GramAddict's configuration parser. Specifically:

1. Parameter names are being wrapped in quotes, which GramAddict's YAML parser does not expect
   ```yaml
   # Current (Invalid):
   "username": "oculairmedia"
   "device": "192.168.50.202:42356"
   
   # Expected:
   username: oculairmedia
   device: 192.168.50.202:42356
   ```

2. Some numeric ranges are being saved with quotes when they should be raw values
   ```yaml
   # Current (Invalid):
   "truncate-sources": "2-3"
   
   # Expected:
   truncate-sources: 2-3
   ```

## Impact
- The bot fails to start when using a config file updated through the API
- Manual intervention is required to fix the config file format
- Potential for service disruption if configs are updated via API in production

## Steps to Reproduce
1. Send PATCH request to `/accounts/oculairmedia/config` with configuration updates
2. Observe the generated config.yml file
3. Attempt to run the bot using the updated config
4. Bot fails due to "Unknown arguments" error

## Root Cause Analysis
The API endpoint is:
1. Not stripping quotes from parameter names during serialization
2. Not properly handling data type conversion for numeric ranges
3. Missing validation for GramAddict's expected YAML format

## Recommendations

### Short-term Fix
1. Modify the config serialization in the API to:
   - Remove quotes from parameter names
   - Properly format numeric ranges without quotes
   - Validate against GramAddict's expected YAML schema

### Long-term Improvements
1. Add a config validation layer:
   ```python
   class ConfigValidator:
       def validate_and_transform(self, config: dict) -> dict:
           # Strip quotes from keys
           # Convert values to appropriate types
           # Validate against schema
           pass
   ```

2. Implement a proper schema for GramAddict configs:
   ```python
   CONFIG_SCHEMA = {
       "username": {"type": "str", "required": True},
       "device": {"type": "str", "required": True},
       "truncate-sources": {"type": "range", "format": "int-int"},
       # ... other fields
   }
   ```

3. Add comprehensive config validation tests:
   ```python
   def test_config_update_format():
       # Test parameter name formatting
       # Test numeric range handling
       # Test array formatting
       pass
   ```

4. Add a config migration system to handle format changes:
   ```python
   class ConfigMigration:
       def migrate(self, config: dict, from_version: str, to_version: str) -> dict:
           pass
   ```

### Prevention Measures
1. Add automated tests that verify:
   - Config file format after API updates
   - Compatibility with GramAddict's parser
   - Proper type conversion and validation

2. Implement a pre-save hook that validates configs:
   ```python
   @app.before_request
   def validate_config():
       if request.endpoint == 'update_config':
           validator = ConfigValidator()
           request.json = validator.validate_and_transform(request.json)
   ```

3. Add monitoring for config update failures:
   ```python
   def update_config():
       try:
           # Update config
           metrics.increment('config.update.success')
       except ValidationError:
           metrics.increment('config.update.validation_error')
           raise
   ```

## Additional Notes
- Consider adding a config format version field to track and manage format changes
- Add documentation specifically for config format requirements
- Consider implementing a config preview endpoint to validate before saving

## References
- GramAddict Configuration Documentation
- API Endpoint Documentation
- Related Issues: None found

## Status
- Priority: High
- Severity: Medium
- Status: Open
- Assigned to: API Development Team
