# backend/tests/integration/conftest.py
import pytest
import requests
import uuid

# Assuming the backend service is accessible at this URL from the test runner container
BASE_URL = "http://backend:5004/api"

@pytest.fixture(scope="function") # Use function scope for isolation if tests modify user state
def auth_token():
    """
    Fixture to register a new user and return an authentication token.
    """
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"decktestuser_{unique_suffix}"
    email = f"decktest_{unique_suffix}@example.com"
    password = "password123"

    # --- Registration ---
    register_payload = {"username": username, "email": email, "password": password}
    register_url = f"{BASE_URL}/users/register"
    try:
        register_response = requests.post(register_url, json=register_payload, timeout=10)
        register_response.raise_for_status() # Ensure registration is successful
        if register_response.status_code != 201:
             pytest.fail(f"Fixture registration failed with status {register_response.status_code}: {register_response.text}")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Fixture registration request failed: {e}")

    # --- Login ---
    login_payload = {"username": username, "password": password}
    login_url = f"{BASE_URL}/auth/login"
    try:
        login_response = requests.post(login_url, json=login_payload, timeout=10)
        login_response.raise_for_status() # Ensure login is successful
        if login_response.status_code != 200:
             pytest.fail(f"Fixture login failed with status {login_response.status_code}: {login_response.text}")
        login_data = login_response.json()
        token = login_data.get("access_token")
        if not token:
            pytest.fail(f"Failed to get access token after login: {login_response.text}")
        return token # Yield the token for the test
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Fixture login request failed: {e}")

# You might add other fixtures here later, e.g., for database connections if needed
# for direct verification beyond API responses.