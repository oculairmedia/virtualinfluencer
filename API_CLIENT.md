# Instagram API Client

This document contains the updated API client code for the Virtual Influencer API.

## Original vs New API Endpoints

| Action | Original Endpoint | New Endpoint |
|--------|------------------|--------------|
| List Accounts | GET /api/accounts | GET /accounts |
| Start Session | POST /api/accounts/{account}/session/start | POST /start_session |
| Stop Session | POST /api/accounts/{account}/session/stop | POST /stop_session |
| Status | GET /api/accounts/{account}/session/status | GET /session_status/{account} |
| Metrics | GET /api/accounts/{account}/session/metrics | GET /bot_stats/{account} |

## Updated API Client Code

```python
def manage_instagram_session(self: "Agent", action: str, account: str = "default") -> str:
    """
    Manage Instagram automation sessions through Virtual Influencer API.

    Args:
        self: The agent instance.
        action (str): Action to perform (list, start, stop, status, metrics).
        account (str): Instagram account name to manage. Defaults to 'default'.

    Returns:
        str: Response from the API formatted as a readable message.
    """
    import json
    import http.client
    import socket

    host = "localhost"  # Updated to use localhost since we're using Docker
    port = 8000
    conn = None

    try:
        conn = http.client.HTTPConnection(host, port, timeout=30)

        if action == "list":
            conn.request('GET', "/accounts")
            response = conn.getresponse()
            data = json.loads(response.read().decode())
            if response.status != 200:
                return f"Error listing accounts: {data.get('detail', 'Unknown error')}"
            accounts = data if isinstance(data, list) else []
            if not accounts:
                return "No Instagram accounts configured"
            return "Configured Instagram accounts:\n" + "\n".join(f"- {acc}" for acc in accounts)

        elif action == "start":
            headers = {'Content-Type': 'application/json'}
            body = json.dumps({"account": account})
            conn.request('POST', "/start_session", body=body, headers=headers)
            response = conn.getresponse()
            data = json.loads(response.read().decode())
            if response.status != 200:
                return f"Error starting session: {data.get('detail', 'Unknown error')}"
            return f"Started session for account {account}"

        elif action == "stop":
            headers = {'Content-Type': 'application/json'}
            body = json.dumps({"account": account})
            conn.request('POST', "/stop_session", body=body, headers=headers)
            response = conn.getresponse()
            data = json.loads(response.read().decode())
            if response.status != 200:
                return f"Error stopping session: {data.get('detail', 'Unknown error')}"
            return f"Stopped session for account {account}"

        elif action == "status":
            conn.request('GET', f"/session_status/{account}")
            response = conn.getresponse()
            data = json.loads(response.read().decode())
            if response.status != 200:
                return f"Error getting session status: {data.get('detail', 'Unknown error')}"
            
            status = data.get('status', 'unknown')
            start_time = data.get('start_time', 'Not started')
            duration = data.get('duration', '0:00:00')
            return (f"Session status for {account}:\n"
                   f"Status: {status}\n"
                   f"Started: {start_time}\n"
                   f"Duration: {duration}")

        elif action == "metrics":
            conn.request('GET', f"/bot_stats/{account}")
            response = conn.getresponse()
            data = json.loads(response.read().decode())
            if response.status != 200:
                return f"Error getting session metrics: {data.get('detail', 'Unknown error')}"
            
            stats = data.get('stats', {})
            return (f"Session metrics for {account}:\n"
                   f"Duration: {stats.get('duration', '0:00:00')}\n"
                   f"Likes: {stats.get('total_likes', 0)}\n"
                   f"Follows: {stats.get('total_follows', 0)}\n"
                   f"Unfollows: {stats.get('total_unfollows', 0)}\n"
                   f"Story Views: {stats.get('total_story_views', 0)}\n"
                   f"Total Interactions: {stats.get('total_interactions', 0)}\n"
                   f"Success Rate: {stats.get('success_rate', '0')}%\n"
                   f"Errors: {stats.get('total_errors', 0)}")
        else:
            return f"Unknown action: {action}. Available actions: list, start, stop, status, metrics"

    except socket.timeout:
        return f"Error: Could not connect to Virtual Influencer API at {host}:{port} (connection timed out after 30 seconds)"
    except ConnectionRefusedError:
        return f"Error: Could not connect to Virtual Influencer API at {host}:{port} (connection refused)"
    except json.JSONDecodeError:
        return f"Error: Invalid response from Virtual Influencer API"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if conn:
            conn.close()
```

## Key Changes

1. **Host Configuration**
   - Changed from hardcoded IP to `localhost` since we're using Docker
   - Port remains `8000`

2. **Endpoint Updates**
   - Removed `/api` prefix from all endpoints
   - Updated endpoint paths to match new API structure
   - Added proper JSON content type headers

3. **Request/Response Format**
   - Updated request body format for session management
   - Modified response parsing to match new API structure
   - Enhanced error handling with `detail` field

4. **Metrics Display**
   - Updated metrics fields to match new bot stats endpoint
   - Added new fields like success rate and total interactions
   - Removed unused fields (comments, DMs)

5. **Error Handling**
   - Increased timeout from 3 to 30 seconds
   - Added HTTP status code checks
   - Improved error messages with API response details

## Usage Example

```python
agent = Agent()  # Your agent class instance

# List configured accounts
print(agent.manage_instagram_session("list"))

# Start session for specific account
print(agent.manage_instagram_session("start", "quecreate"))

# Check session status
print(agent.manage_instagram_session("status", "quecreate"))

# Get metrics
print(agent.manage_instagram_session("metrics", "quecreate"))

# Stop session
print(agent.manage_instagram_session("stop", "quecreate"))
```
