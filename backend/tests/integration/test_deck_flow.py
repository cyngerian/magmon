# backend/tests/integration/test_deck_flow.py
import pytest
import requests
import uuid

# Assuming the backend service is accessible at this URL from the test runner container
BASE_URL = "http://localhost:5004/api"

@pytest.mark.integration
def test_deck_creation_and_retrieval_flow(auth_token):
    """
    Tests the full deck creation and retrieval flow.
    1. Creates a new deck using an authenticated user.
    2. Retrieves the list of decks for the user and verifies the new deck.
    3. Retrieves the specific deck by its ID.
    """
    headers = {"Authorization": f"Bearer {auth_token}"}
    unique_suffix = uuid.uuid4().hex[:8]
    deck_name = f"MyIntegrationTestDeck_{unique_suffix}"
    deck_format = "commander"
    deck_description = "A deck created during integration testing."
    deck_list = "1 Sol Ring\n1 Command Tower" # Simple example decklist

    # --- Deck Creation Step ---
    create_payload = {
        "name": deck_name,
        "format": deck_format,
        "description": deck_description,
        "decklist": deck_list,
        "is_public": True # Assuming default or required field
    }
    create_url = f"{BASE_URL}/decks"
    print(f"Attempting deck creation: {deck_name} at {create_url}") # Debug print

    created_deck_id = None
    try:
        create_response = requests.post(create_url, headers=headers, json=create_payload, timeout=10)
        print(f"Deck creation response status: {create_response.status_code}") # Debug print
        # print(f"Deck creation response body: {create_response.text}") # Debug print

        create_response.raise_for_status() # Raise HTTPError for bad responses

        assert create_response.status_code == 201
        create_data = create_response.json()
        assert "deck" in create_data
        assert create_data["deck"]["name"] == deck_name
        assert create_data["deck"]["format"] == deck_format
        assert "id" in create_data["deck"]
        created_deck_id = create_data["deck"]["id"] # Store the ID for later steps
        print(f"Deck created successfully with ID: {created_deck_id}")

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Deck creation request failed: {e}")
    except Exception as e:
         pytest.fail(f"An unexpected error occurred during deck creation assertion: {e}\nResponse: {create_response.text if 'create_response' in locals() else 'No response object'}")

    assert created_deck_id is not None, "Deck ID was not captured after creation"

    # --- Retrieve All Decks Step ---
    get_all_url = f"{BASE_URL}/decks"
    print(f"Attempting to retrieve all decks at {get_all_url}") # Debug print
    try:
        get_all_response = requests.get(get_all_url, headers=headers, timeout=10)
        print(f"Get all decks response status: {get_all_response.status_code}") # Debug print
        get_all_response.raise_for_status()

        assert get_all_response.status_code == 200
        get_all_data = get_all_response.json()
        assert "decks" in get_all_data
        assert isinstance(get_all_data["decks"], list)

        # Verify the created deck is in the list
        found_deck = next((deck for deck in get_all_data["decks"] if deck["id"] == created_deck_id), None)
        assert found_deck is not None, f"Created deck (ID: {created_deck_id}) not found in the user's deck list"
        assert found_deck["name"] == deck_name
        assert found_deck["format"] == deck_format

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Get all decks request failed: {e}")
    except Exception as e:
         pytest.fail(f"An unexpected error occurred during get all decks assertion: {e}\nResponse: {get_all_response.text if 'get_all_response' in locals() else 'No response object'}")


    # --- Retrieve Specific Deck Step ---
    get_specific_url = f"{BASE_URL}/decks/{created_deck_id}"
    print(f"Attempting to retrieve specific deck at {get_specific_url}") # Debug print
    try:
        get_specific_response = requests.get(get_specific_url, headers=headers, timeout=10)
        print(f"Get specific deck response status: {get_specific_response.status_code}") # Debug print
        get_specific_response.raise_for_status()

        assert get_specific_response.status_code == 200
        get_specific_data = get_specific_response.json()
        assert "deck" in get_specific_data
        assert get_specific_data["deck"]["id"] == created_deck_id
        assert get_specific_data["deck"]["name"] == deck_name
        assert get_specific_data["deck"]["format"] == deck_format
        # Optionally check description and decklist if the endpoint returns them
        # assert get_specific_data["deck"]["description"] == deck_description
        # assert get_specific_data["deck"]["decklist"] == deck_list

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Get specific deck request failed: {e}")
    except Exception as e:
         pytest.fail(f"An unexpected error occurred during get specific deck assertion: {e}\nResponse: {get_specific_response.text if 'get_specific_response' in locals() else 'No response object'}")

# Add more tests as needed, e.g., for updating, deleting decks, error cases (unauthorized access)