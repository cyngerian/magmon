import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react'; // Import within
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom'; // Use MemoryRouter for routing context
import DeckManagementPage from '../DeckManagementPage';
// Import both default and named exports needed for mocking
import apiClient, { createDeckVersion, getDeckDetails, getDeckVersions, getDeckVersion } from '../../apiClient'; // Import createDeckVersion

// --- Mocking ---
// Mock the entire apiClient module
// We need to explicitly define the mocks for both default and named exports
vi.mock('../../apiClient', () => ({
  // Mock the default export (the axios instance)
  default: {
    get: vi.fn(),
    post: vi.fn(),
    // Add other methods if the default export instance uses them directly
  },
  // Mock the named exports used directly
  getDeckDetails: vi.fn(),
  getDeckVersions: vi.fn(),
  getDeckVersion: vi.fn(),
  createDeckVersion: vi.fn(),
  // Add any other named exports from apiClient that are used
}));

// Mock react-router-dom hooks
const mockNavigate = vi.fn();
const mockLocation = { state: null, pathname: '/decks' }; // Default mock location
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
  };
});

// --- Test Suite ---
describe('DeckManagementPage', () => {
  const mockLoggedInUser = { id: 1, username: 'TestUser', email: 'test@example.com' };
  const mockDecks = [
    { id: 101, name: 'My First Deck', commander: 'Commander A', colors: 'WUB', last_updated: '2024-01-01T10:00:00Z', user_id: 1, created_at: '2024-01-01T10:00:00Z' },
    { id: 102, name: 'Another Deck', commander: 'Commander B', colors: 'RG', last_updated: '2024-01-02T11:00:00Z', user_id: 1, created_at: '2024-01-02T11:00:00Z' },
  ];

  beforeEach(() => {
    vi.clearAllMocks(); // Clear mocks before each test

    // Default successful mock for fetching user decks
    (apiClient.get as ReturnType<typeof vi.fn>).mockImplementation((url) => {
        if (url === `/users/${mockLoggedInUser.id}/decks`) {
            return Promise.resolve({ data: mockDecks });
        }
        // Add mocks for other GET requests if needed for detail view tests
        if (url.includes('/history')) {
             return Promise.resolve({ data: [] }); // Mock history
        }
        return Promise.reject(new Error(`Unhandled GET request: ${url}`));
    });

    // Default successful mock for creating a deck
    (apiClient.post as ReturnType<typeof vi.fn>).mockImplementation((url) => {
        if (url === '/decks') {
            return Promise.resolve({ data: { message: 'Deck created successfully!' } }); // Mock successful creation
        }
         if (url.includes('/change-password')) { // From previous test file, ensure it doesn't interfere
            return Promise.reject(new Error('Change password should not be called here'));
        }
        return Promise.reject(new Error(`Unhandled POST request: ${url}`));
    });

     // Mock detail/version fetches (needed for viewDeckDetails) - Use imported named functions
    (getDeckDetails as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 101, name: 'My First Deck', commander: 'Commander A', colors: 'WUB',
        last_updated: '2024-01-01T10:00:00Z', user_id: 1, created_at: '2024-01-01T10:00:00Z',
        decklist_text: '1 Sol Ring\n...', current_version_id: 1
    });
    (getDeckVersions as ReturnType<typeof vi.fn>).mockResolvedValue([
        { id: 1, version_number: 1, created_at: '2024-01-01T10:00:00Z', notes: null, is_current: true }
    ]);
     (getDeckVersion as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1, version_number: 1, created_at: '2024-01-01T10:00:00Z', notes: null, is_current: true,
        decklist_text: '1 Sol Ring\n...'
    });


    // Mock console.error to avoid polluting test output
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(console, 'log').mockImplementation(() => {}); // Also mock console.log if needed
  });

  afterEach(() => {
    vi.restoreAllMocks(); // Restore mocks after each test
  });

  // Helper to render with Router context
  const renderWithRouter = (ui: React.ReactElement, { route = '/decks' } = {}) => {
    window.history.pushState({}, 'Test page', route);
    return render(
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path="/decks" element={ui} />
          {/* Add other routes if navigation occurs */}
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders login message if user is not logged in', () => {
    renderWithRouter(<DeckManagementPage loggedInUser={null} />);
    expect(screen.getByText(/Please log in to manage decks./i)).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /Create New Deck/i })).not.toBeInTheDocument();
  });

  // --- Create New Deck Form Tests ---
  describe('Create New Deck Form', () => {
    it('renders the create deck form correctly', async () => {
      renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);
      await waitFor(() => expect(apiClient.get).toHaveBeenCalledWith(`/users/${mockLoggedInUser.id}/decks`)); // Wait for decks to load

      const createForm = screen.getByRole('heading', { name: /Create New Deck/i }).closest('article');
      expect(createForm).toBeInTheDocument(); // Ensure form is found

      expect(within(createForm!).getByLabelText(/Deck Name/i)).toBeInTheDocument();
      expect(within(createForm!).getByLabelText(/Commander/i)).toBeInTheDocument();
      expect(within(createForm!).getByRole('group', { name: /Colors/i })).toBeInTheDocument(); // Use getByRole for fieldset/legend
      // Use getByLabelText for Decklist textarea, scoped within the form
      expect(within(createForm!).getByLabelText(/Decklist/i)).toBeInTheDocument();
      expect(within(createForm!).getByRole('button', { name: /Create Deck/i })).toBeInTheDocument();
    });

    it('updates input fields on change', async () => {
        const user = userEvent.setup();
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);
        await waitFor(() => expect(apiClient.get).toHaveBeenCalled()); // Wait for initial load

        const createForm = screen.getByRole('heading', { name: /Create New Deck/i }).closest('article');
        expect(createForm).toBeInTheDocument();

        const nameInput = within(createForm!).getByLabelText(/Deck Name/i);
        const commanderInput = within(createForm!).getByLabelText(/Commander/i);
        // Use getByLabelText for Decklist textarea, scoped within the form
        const decklistInput = within(createForm!).getByLabelText(/Decklist/i);

        await user.type(nameInput, 'Test Deck Name');
        await user.type(commanderInput, 'Test Commander');
        await user.type(decklistInput, '1 Sol Ring\n1 Command Tower');

        expect(nameInput).toHaveValue('Test Deck Name');
        expect(commanderInput).toHaveValue('Test Commander');
        expect(decklistInput).toHaveValue('1 Sol Ring\n1 Command Tower');
    });

     it('updates color selection correctly', async () => {
        const user = userEvent.setup();
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);
        await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

        const whiteCheckbox = screen.getByLabelText('W', { selector: 'input[type="checkbox"]' });
        const blueCheckbox = screen.getByLabelText('U', { selector: 'input[type="checkbox"]' });
        const colorlessCheckbox = screen.getByLabelText('C', { selector: 'input[type="checkbox"]' });

        await user.click(whiteCheckbox);
        await user.click(colorlessCheckbox);
        await user.click(blueCheckbox); // WUC -> sorted WUC

        expect(whiteCheckbox).toBeChecked();
        expect(blueCheckbox).toBeChecked();
        expect(colorlessCheckbox).toBeChecked();

        // Uncheck white
        await user.click(whiteCheckbox);
        expect(whiteCheckbox).not.toBeChecked();
        expect(blueCheckbox).toBeChecked();
        expect(colorlessCheckbox).toBeChecked();
    });


    it('shows error if no color is selected on submit', async () => {
        const user = userEvent.setup();
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);
        await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

        await user.type(screen.getByLabelText(/Deck Name/i), 'No Color Deck');
        await user.type(screen.getByLabelText(/Commander/i), 'Colorless Cmdr');
        await user.click(screen.getByRole('button', { name: /Create Deck/i }));

        expect(await screen.findByText(/Please select at least one color/i)).toBeInTheDocument();
        expect(apiClient.post).not.toHaveBeenCalled();
    });

    it('submits the form and calls the API on successful creation', async () => {
        const user = userEvent.setup();
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);
        await waitFor(() => expect(apiClient.get).toHaveBeenCalledWith(`/users/${mockLoggedInUser.id}/decks`)); // Wait for initial deck load

        // Define createForm for this test scope
        const createForm = screen.getByRole('heading', { name: /Create New Deck/i }).closest('article');
        expect(createForm).toBeInTheDocument(); // Ensure form is found before proceeding

        // Mock the post call again specifically for this test if needed, or rely on beforeEach
        (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: { message: 'Deck created!' } });
        // Mock the deck fetch after creation
        (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: [...mockDecks, { id: 103, name: 'New Test Deck', commander: 'New Cmdr', colors: 'WU', user_id: 1, created_at: '...', last_updated: '...' }] });


        await user.type(screen.getByLabelText(/Deck Name/i), 'New Test Deck');
        await user.type(screen.getByLabelText(/Commander/i), 'New Cmdr');
        await user.click(screen.getByLabelText('W', { selector: 'input[type="checkbox"]' }));
        await user.click(within(createForm!).getByLabelText('U', { selector: 'input[type="checkbox"]' }));
        // Use getByLabelText for Decklist textarea, scoped within the form
        await user.type(within(createForm!).getByLabelText(/Decklist/i), '1 Island\n1 Plains');
        await user.click(within(createForm!).getByRole('button', { name: /Create Deck/i }));

        await waitFor(() => {
            expect(apiClient.post).toHaveBeenCalledTimes(1);
            expect(apiClient.post).toHaveBeenCalledWith('/decks', {
                name: 'New Test Deck',
                commander: 'New Cmdr',
                colors: 'WU', // Ensure colors are sent correctly
                decklist_text: '1 Island\n1 Plains',
            });
        });

        // Check for success message and form reset
        // Check for success message
        await waitFor(() => {
          // Use getByText inside waitFor
          expect(screen.getByText(/Deck created successfully!/i)).toBeInTheDocument();
        }, { timeout: 2000 }); // Increased timeout
        expect(screen.getByLabelText(/Deck Name/i)).toHaveValue('');
        expect(screen.getByLabelText(/Commander/i)).toHaveValue('');
        expect(screen.getByLabelText('W', { selector: 'input[type="checkbox"]' })).not.toBeChecked();
        expect(within(createForm!).getByLabelText('U', { selector: 'input[type="checkbox"]' })).not.toBeChecked();
        // Use getByLabelText for Decklist textarea, scoped within the form
        expect(within(createForm!).getByLabelText(/Decklist/i)).toHaveValue('');

        // Check if decks were refetched
        await waitFor(() => {
            expect(apiClient.get).toHaveBeenCalledTimes(2); // Initial load + refetch
            expect(apiClient.get).toHaveBeenLastCalledWith(`/users/${mockLoggedInUser.id}/decks`);
        });
         // Check if the new deck appears in the list
        expect(await screen.findByText('New Test Deck')).toBeInTheDocument();
    });

    it('shows an error message if API call fails during creation', async () => {
        const user = userEvent.setup();
        const errorMessage = 'Deck name already exists';
        // Reject with a standard Error object
        (apiClient.post as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error(errorMessage));

        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);
        await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

        await user.type(screen.getByLabelText(/Deck Name/i), 'Duplicate Deck');
        await user.type(screen.getByLabelText(/Commander/i), 'Cmdr');
        await user.click(screen.getByLabelText('B', { selector: 'input[type="checkbox"]' }));
        await user.click(screen.getByRole('button', { name: /Create Deck/i }));

        await waitFor(() => {
            expect(apiClient.post).toHaveBeenCalledTimes(1);
        });

        // Check for error message
        // Check for error message, matching the component's updated format
        await waitFor(() => {
            expect(screen.getByText(`Deck creation failed: ${errorMessage}`)).toBeInTheDocument();
        }, { timeout: 2000 }); // Keep increased timeout
    });
  });

  // --- Your Decks List Tests ---
  describe('Your Decks List', () => {
     it('shows loading state initially', () => {
        // Don't resolve the promise immediately
        (apiClient.get as ReturnType<typeof vi.fn>).mockImplementation((url) => {
            if (url === `/users/${mockLoggedInUser.id}/decks`) {
                return new Promise(() => {}); // Keep promise pending
            }
            return Promise.reject(new Error(`Unhandled GET request: ${url}`));
        });
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);
        expect(screen.getByText(/Loading decks.../i)).toBeInTheDocument();
    });

    it('renders the list of decks correctly after loading', async () => {
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);

        // Wait for loading to finish and decks to appear
        expect(await screen.findByText('My First Deck')).toBeInTheDocument();
        expect(screen.getByText('Commander A')).toBeInTheDocument();
        expect(screen.getByText('WUB')).toBeInTheDocument(); // Check colors

        expect(screen.getByText('Another Deck')).toBeInTheDocument();
        expect(screen.getByText('Commander B')).toBeInTheDocument();
        expect(screen.getByText('RG')).toBeInTheDocument(); // Check colors

        expect(screen.queryByText(/Loading decks.../i)).not.toBeInTheDocument();
        // Check that view/edit buttons are present for each deck
        expect(screen.getAllByRole('button', { name: /View/i })).toHaveLength(mockDecks.length);
        expect(screen.getAllByRole('button', { name: /Edit/i })).toHaveLength(mockDecks.length);
    });

    it('shows empty state if no decks are returned', async () => {
        (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: [] }); // Override to return empty array
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);

        expect(await screen.findByText(/No decks created yet./i)).toBeInTheDocument();
        expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('calls functions to fetch details when View button is clicked', async () => {
        const user = userEvent.setup();
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);

        // Wait for the initial list to load
        const viewButtons = await screen.findAllByRole('button', { name: /View/i });
        expect(viewButtons[0]).toBeInTheDocument(); // Ensure the first button exists

        // Click the "View" button for the first deck (ID 101)
        await user.click(viewButtons[0]);

        // Check that the necessary API calls for viewing details were made - Use imported named functions
        await waitFor(() => {
            expect(getDeckDetails).toHaveBeenCalledWith(101);
            expect(getDeckVersions).toHaveBeenCalledWith(101);
            // Check history fetch as well (using the mocked default apiClient.get)
            expect(apiClient.get).toHaveBeenCalledWith(`/decks/101/history`);
            // Check that the specific version details were fetched (assuming version ID 1 is current)
            expect(getDeckVersion).toHaveBeenCalledWith(101, 1); // Assuming version 1 is fetched initially
        });

        // Check if detail section appears (basic check)
        expect(await screen.findByRole('heading', { name: /Deck Details: My First Deck/i })).toBeInTheDocument();
    });

     it('shows loading indicator on the specific row when View is clicked', async () => {
        const user = userEvent.setup();
        // Make detail fetching slow - Use imported named functions
        (getDeckDetails as ReturnType<typeof vi.fn>).mockImplementationOnce(() => new Promise(resolve => setTimeout(() => resolve({
            id: 101, name: 'My First Deck', commander: 'Commander A', colors: 'WUB',
            last_updated: '2024-01-01T10:00:00Z', user_id: 1, created_at: '2024-01-01T10:00:00Z',
            decklist_text: '1 Sol Ring\n...', current_version_id: 1
        }), 100)));
        (getDeckVersions as ReturnType<typeof vi.fn>).mockImplementationOnce(() => new Promise(resolve => setTimeout(() => resolve([
            { id: 1, version_number: 1, created_at: '2024-01-01T10:00:00Z', notes: null, is_current: true }
        ]), 100)));
        (apiClient.get as ReturnType<typeof vi.fn>).mockImplementation((url) => {
             if (url === `/users/${mockLoggedInUser.id}/decks`) return Promise.resolve({ data: mockDecks });
             if (url === `/decks/101/history`) return new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100));
             return Promise.reject(new Error(`Unhandled GET: ${url}`));
        });
         (getDeckVersion as ReturnType<typeof vi.fn>).mockImplementationOnce(() => new Promise(resolve => setTimeout(() => resolve({
            id: 1, version_number: 1, created_at: '2024-01-01T10:00:00Z', notes: null, is_current: true,
            decklist_text: '1 Sol Ring\n...'
        }), 100)));


        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);
        const viewButtons = await screen.findAllByRole('button', { name: /View/i });
        const firstViewButton = viewButtons[0];
        const firstTableRow = firstViewButton.closest('tr'); // Find the row
        if (!firstTableRow) throw new Error("Could not find table row for the first view button");

        // Find the div within the last cell of that row.
        const actionCell = firstTableRow.querySelector('td:last-child');
        if (!actionCell) throw new Error("Could not find action cell (last td) in the table row");
        const buttonContainerDiv = actionCell.querySelector('div'); // Find the div inside the cell
        if (!buttonContainerDiv) throw new Error("Could not find button container div inside the action cell");

        // Check initial state on the div itself
        expect(buttonContainerDiv).toHaveAttribute('aria-busy', 'false');

        await user.click(firstViewButton);

        // Check for aria-busy=true on the SAME div, re-queried via stable row/cell
        await waitFor(() => {
          // Re-select the div using the stable row/cell context
          const currentActionCell = firstTableRow.querySelector('td:last-child');
          const currentButtonContainerDiv = currentActionCell?.querySelector('div');
          expect(currentButtonContainerDiv).toBeInTheDocument(); // Ensure the div is found
          expect(currentButtonContainerDiv).toHaveAttribute('aria-busy', 'true');
        });

        // Wait for details to load (find element rendered after load)
        await screen.findByRole('heading', { name: /Deck Details: My First Deck/i });

        // Check for aria-busy=false AFTER details have loaded, re-queried via stable row/cell
        await waitFor(() => {
          // Re-select the div again
          const finalActionCell = firstTableRow.querySelector('td:last-child');
          const finalButtonContainerDiv = finalActionCell?.querySelector('div');
          expect(finalButtonContainerDiv).toBeInTheDocument(); // Ensure the div is found
          expect(finalButtonContainerDiv).toHaveAttribute('aria-busy', 'false');
        });
    });

  });

  // --- Edit Deck Modal Tests ---
  describe('Edit Deck Modal', () => {
    const mockDeckToEdit = mockDecks[0]; // Edit 'My First Deck' (ID 101)
    const mockLatestVersionDetails = {
        id: 1, version_number: 1, created_at: '2024-01-01T10:00:00Z', notes: null, is_current: true,
        decklist_text: '1 Sol Ring\n10 Island' // Original decklist
    };
     const mockUpdatedDecklist = '1 Sol Ring\n10 Island\n1 Mana Crypt';
     const mockEditNotes = 'Added Mana Crypt';

    beforeEach(() => {
        // Mock getDeckDetails specifically for opening the edit modal
        (getDeckDetails as ReturnType<typeof vi.fn>).mockResolvedValue({
            ...mockDeckToEdit, // Spread base deck info
            decklist_text: mockLatestVersionDetails.decklist_text, // Add decklist
            current_version_id: mockLatestVersionDetails.id,
        });
        // Mock createDeckVersion for saving
        (createDeckVersion as ReturnType<typeof vi.fn>).mockResolvedValue({
             id: 2, // ID of the new version
             version_number: 2,
             created_at: new Date().toISOString(),
             notes: mockEditNotes,
             is_current: true, // Assume it becomes current
             decklist_text: mockUpdatedDecklist
        });
    });

    it('opens the edit modal with the latest decklist when Edit button is clicked', async () => {
        const user = userEvent.setup();
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);

        // Wait for list and find the Edit button for the first deck
        const editButtons = await screen.findAllByRole('button', { name: /Edit/i });
        await user.click(editButtons[0]);

        // Wait for getDeckDetails to be called for the modal
        await waitFor(() => {
            expect(getDeckDetails).toHaveBeenCalledWith(mockDeckToEdit.id);
        });

        // Check if modal is open and has the correct title
        const modal = await screen.findByRole('dialog');
        expect(modal).toBeInTheDocument();
        expect(within(modal).getByRole('heading', { name: /Edit Deck: My First Deck/i })).toBeInTheDocument();

        // Check if the decklist textarea within the modal is pre-filled using getByLabelText
        const decklistTextarea = within(modal).getByLabelText(/Decklist/i); // Already scoped by within(modal)
        expect(decklistTextarea).toHaveValue(mockLatestVersionDetails.decklist_text);
        expect(within(modal).getByLabelText(/Version Notes/i)).toHaveValue(''); // Notes should be empty
    });

    it('allows editing the decklist and notes within the modal', async () => {
        const user = userEvent.setup();
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);

        const editButtons = await screen.findAllByRole('button', { name: /Edit/i });
        await user.click(editButtons[0]);

        const modal = await screen.findByRole('dialog');
        // Use getByLabelText for Decklist textarea, already scoped by within(modal)
        const decklistTextarea = within(modal).getByLabelText(/Decklist/i);
        const notesTextarea = within(modal).getByLabelText(/Version Notes/i);

        await user.clear(decklistTextarea);
        await user.type(decklistTextarea, mockUpdatedDecklist);
        await user.type(notesTextarea, mockEditNotes);

        expect(decklistTextarea).toHaveValue(mockUpdatedDecklist);
        expect(notesTextarea).toHaveValue(mockEditNotes);
    });

     it('saves a new version and closes the modal on submit', async () => {
        const user = userEvent.setup();
        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);

        const editButtons = await screen.findAllByRole('button', { name: /Edit/i });
        await user.click(editButtons[0]);

        const modal = await screen.findByRole('dialog');
        // Use getByLabelText for Decklist textarea, already scoped by within(modal)
        const decklistTextarea = within(modal).getByLabelText(/Decklist/i);
        const notesTextarea = within(modal).getByLabelText(/Version Notes/i);
        const saveButton = within(modal).getByRole('button', { name: /Save New Version/i });

        await user.clear(decklistTextarea);
        await user.type(decklistTextarea, mockUpdatedDecklist);
        await user.type(notesTextarea, mockEditNotes);

        // Mock refetch after save
        (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ data: mockDecks }); // Mock the refetch of all decks

        await user.click(saveButton);

        // Check API call
        await waitFor(() => {
            expect(createDeckVersion).toHaveBeenCalledWith(mockDeckToEdit.id, {
                decklist_text: mockUpdatedDecklist,
                notes: mockEditNotes,
            });
        });

        // Check modal is closed
        await waitFor(() => {
             expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        });

        // Check success message
        // Check success message
        await waitFor(() => {
            // Use getByText inside waitFor
            expect(screen.getByText(`Successfully created new version for deck: ${mockDeckToEdit.name}`)).toBeInTheDocument();
        }, { timeout: 2000 }); // Increased timeout

        // Check if decks were refetched
        await waitFor(() => {
            // Initial load + refetch after save
            expect(apiClient.get).toHaveBeenCalledWith(`/users/${mockLoggedInUser.id}/decks`);
            // getDeckDetails was called once for modal open
            expect(getDeckDetails).toHaveBeenCalledTimes(1);
        });
     });

     it('shows aria-busy on save button while saving', async () => {
        const user = userEvent.setup();
         // Make save slow
        (createDeckVersion as ReturnType<typeof vi.fn>).mockImplementationOnce(() => new Promise(resolve => setTimeout(() => resolve({ id: 2 }), 100)));

        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);

        const editButtons = await screen.findAllByRole('button', { name: /Edit/i });
        await user.click(editButtons[0]);

        const modal = await screen.findByRole('dialog');
        const saveButton = within(modal).getByRole('button', { name: /Save New Version/i });

        expect(saveButton).not.toHaveAttribute('aria-busy', 'true');

        await user.click(saveButton);

        // Check aria-busy immediately after click
        await waitFor(() => {
            // Re-query inside waitFor
            const savingButton = within(modal).getByRole('button', { name: /Save New Version/i });
            expect(savingButton).toHaveAttribute('aria-busy', 'true');
        });

        // Wait for save to complete and modal to close
        await waitFor(() => {
             expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        }, { timeout: 500 });
     });

     it('shows error message in modal if saving fails', async () => {
        const user = userEvent.setup();
        const saveError = 'Invalid decklist format';
        // Reject with a standard Error object
        (createDeckVersion as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error(saveError));

        renderWithRouter(<DeckManagementPage loggedInUser={mockLoggedInUser} />);

        const editButtons = await screen.findAllByRole('button', { name: /Edit/i });
        await user.click(editButtons[0]);

        const modal = await screen.findByRole('dialog');
        const saveButton = within(modal).getByRole('button', { name: /Save New Version/i });

        await user.click(saveButton);

        // Check for error message within the modal
        // Check for error message within the modal, matching the component's updated format
        await waitFor(() => {
            expect(within(modal).getByText(`Failed to save: ${saveError}`)).toBeInTheDocument();
        }, { timeout: 2000 }); // Keep increased timeout

        // Check modal is still open
        expect(modal).toBeInTheDocument();
        // Check button is not busy anymore
        expect(saveButton).not.toHaveAttribute('aria-busy', 'true');
     });

  });
});