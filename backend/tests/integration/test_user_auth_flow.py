# backend/tests/integration/test_user_auth_flow.py
import pytest
import requests
import uuid
import time

# Assuming the backend service is accessible at this URL from the test runner container
BASE_URL = "http://localhost:5004/api"

@pytest.mark.integration
def test_user_registration_and_login_flow():
    """
    Tests the full user registration and login flow.
    1. Registers a new user.
    2. Logs in with the new user's credentials.
    """
    # Generate unique user data for isolation
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"testuser_{unique_suffix}"
    email = f"test_{unique_suffix}@example.com"
    password = "password123"

    # --- Registration Step ---
    register_payload = {
        "username": username,
        "email": email,
        "password": password
    }
    register_url = f"{BASE_URL}/users/register"
    print(f"Attempting registration for {username} at {register_url}") # Debug print

    try:
        register_response = requests.post(register_url, json=register_payload, timeout=10) # Added timeout
        print(f"Registration response status: {register_response.status_code}") # Debug print
        # print(f"Registration response body: {register_response.text}") # Debug print for detailed errors

        # Check for potential server errors or unexpected responses
        register_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        assert register_response.status_code == 201
        register_data = register_response.json()
        assert "user" in register_data
        assert register_data["user"]["username"] == username
        assert register_data["user"]["email"] == email
        assert "id" in register_data["user"]
        user_id = register_data["user"]["id"] # Store user_id if needed later

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Registration request failed: {e}")
    except Exception as e:
         pytest.fail(f"An unexpected error occurred during registration assertion: {e}\nResponse: {register_response.text if 'register_response' in locals() else 'No response object'}")


    # Add a small delay if needed, sometimes useful in integration tests
    # time.sleep(0.5)

    # --- Login Step ---
    login_payload = {
        "username": username,
        "password": password
    }
    login_url = f"{BASE_URL}/auth/login"
    print(f"Attempting login for {username} at {login_url}") # Debug print

    try:
        login_response = requests.post(login_url, json=login_payload, timeout=10) # Added timeout
        print(f"Login response status: {login_response.status_code}") # Debug print
        # print(f"Login response body: {login_response.text}") # Debug print

        login_response.raise_for_status()

        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert isinstance(login_data["access_token"], str)
        assert len(login_data["access_token"]) > 0 # Basic check for non-empty token

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Login request failed: {e}")
    except Exception as e:
         pytest.fail(f"An unexpected error occurred during login assertion: {e}\nResponse: {login_response.text if 'login_response' in locals() else 'No response object'}")

# Example of a separate test (could be combined or kept separate)
@pytest.mark.integration
def test_registration_duplicate_username():
    """Tests that registering with a duplicate username fails."""
    unique_suffix = uuid.uuid4().hex[:8]
    username = f"testdup_{unique_suffix}"
    email_1 = f"test1_{unique_suffix}@example.com"
    email_2 = f"test2_{unique_suffix}@example.com"
    password = "password123"

    # First registration (should succeed)
    register_payload_1 = {"username": username, "email": email_1, "password": password}
    register_url = f"{BASE_URL}/users/register"
    try:
        response1 = requests.post(register_url, json=register_payload_1, timeout=10)
        response1.raise_for_status() # Ensure first one works
        assert response1.status_code == 201
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Initial registration request failed unexpectedly: {e}")

    # Second registration with same username (should fail)
    register_payload_2 = {"username": username, "email": email_2, "password": password}
    try:
        response2 = requests.post(register_url, json=register_payload_2, timeout=10)
        assert response2.status_code == 409 # Conflict
        error_data = response2.json()
        assert "error" in error_data
        assert "username" in error_data["error"].lower() # Check if error message mentions username
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Duplicate registration request failed: {e}")
    except Exception as e:
         pytest.fail(f"An unexpected error occurred during duplicate registration assertion: {e}\nResponse: {response2.text if 'response2' in locals() else 'No response object'}")