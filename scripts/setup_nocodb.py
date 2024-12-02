import os
import requests
import time

def wait_for_nocodb():
    """Wait for NocoDB to be ready"""
    base_url = "http://localhost:8080"
    max_retries = 30
    retry_interval = 5

    print("Waiting for NocoDB to be ready...")
    for _ in range(max_retries):
        try:
            response = requests.get(f"{base_url}/api/v1/health")
            if response.status_code == 200:
                print("NocoDB is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(retry_interval)
        print("Still waiting for NocoDB...")
    
    raise Exception("NocoDB failed to start")

def create_project():
    """Create a new NocoDB project"""
    base_url = "http://localhost:8080"
    auth_token = input("Enter your NocoDB auth token: ")
    
    headers = {
        "xc-auth": auth_token,
        "Content-Type": "application/json"
    }
    
    # Create project
    project_data = {
        "title": "InstagramBot",
        "description": "Instagram Bot Database"
    }
    
    response = requests.post(
        f"{base_url}/api/v1/db/meta/projects/",
        headers=headers,
        json=project_data
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to create project: {response.text}")
    
    project_id = response.json()["id"]
    print(f"Created project with ID: {project_id}")
    return project_id, auth_token

def create_tables(project_id, auth_token):
    """Create the required tables"""
    base_url = "http://localhost:8080"
    headers = {
        "xc-auth": auth_token,
        "Content-Type": "application/json"
    }
    
    # Create history filters table
    history_filters_table = {
        "table_name": "history_filters",
        "title": "History Filters",
        "columns": [
            {"column_name": "id", "title": "ID", "uidt": "ID"},
            {"column_name": "filter_name", "title": "Filter Name", "uidt": "SingleLineText"},
            {"column_name": "last_interaction", "title": "Last Interaction", "uidt": "DateTime"},
        ]
    }
    
    # Create interacted users table
    interacted_users_table = {
        "table_name": "interacted_users",
        "title": "Interacted Users",
        "columns": [
            {"column_name": "id", "title": "ID", "uidt": "ID"},
            {"column_name": "username", "title": "Username", "uidt": "SingleLineText"},
            {"column_name": "interaction_type", "title": "Interaction Type", "uidt": "SingleLineText"},
            {"column_name": "interaction_date", "title": "Interaction Date", "uidt": "DateTime"},
        ]
    }
    
    tables = {
        "history_filters": history_filters_table,
        "interacted_users": interacted_users_table
    }
    
    table_ids = {}
    
    for table_name, table_data in tables.items():
        response = requests.post(
            f"{base_url}/api/v1/db/meta/projects/{project_id}/tables",
            headers=headers,
            json=table_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to create table {table_name}: {response.text}")
        
        table_id = response.json()["id"]
        print(f"Created table {table_name} with ID: {table_id}")
        table_ids[table_name] = table_id
    
    return table_ids

def main():
    try:
        # Wait for NocoDB to be ready
        wait_for_nocodb()
        
        # Create project
        project_id, auth_token = create_project()
        
        # Create tables
        table_ids = create_tables(project_id, auth_token)
        
        # Print configuration
        print("\nAdd these environment variables to your docker-compose.yml:")
        print(f"NOCODB_TOKEN={auth_token}")
        print(f"NOCODB_PROJECT_ID={project_id}")
        print(f"NOCODB_HISTORY_FILTERS_TABLE_ID={table_ids['history_filters']}")
        print(f"NOCODB_INTERACTED_USERS_TABLE_ID={table_ids['interacted_users']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
