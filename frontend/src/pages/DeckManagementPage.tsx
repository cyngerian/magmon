import React, { useState, useEffect } from 'react';
import axios from 'axios'; // Keep for type guard
import apiClient, { createDeckVersion, getDeckDetails, getDeckVersions, getDeckVersion } from '../apiClient'; // Use configured apiClient, import version functions
// Removed apiClient import
import { Link, useNavigate, useLocation } from 'react-router-dom'; // Import Link, useNavigate, useLocation

// --- Interfaces ---
interface Deck {
  id: number; name: string; commander: string; colors: string; last_updated: string; decklist_text?: string; user_id: number; created_at: string;
}
interface User { id: number; username: string; email: string; }

interface DeckVersion {
  id: number;
  version_number: number;
  created_at: string;
  notes: string | null; // Adjusted based on usage in the file (line 140 check)
  is_current: boolean;
}
// Interface for deck game history items
interface DeckGameHistoryItem {
    game_id: number;
    game_date: string;
    placement: number | null;
    version_number: number | null; // Changed to version_number
}
// Summary for dropdown
interface DeckVersionSummary {
  id: number;
  version_number: number;
  created_at: string;
  notes: string | null;
  is_current: boolean;
}
// Detail for selected version display
interface DeckVersionDetail extends DeckVersionSummary {
  decklist_text: string | null;
}

// --- API Base URL ---
function DeckManagementPage({ loggedInUser }: { loggedInUser: User | null }) {
  const [deckName, setDeckName] = useState('');
  const [deckCommander, setDeckCommander] = useState('');
  const [deckColors, setDeckColors] = useState('');
  const [decklistText, setDecklistText] = useState('');
  const [createStatusMessage, setCreateStatusMessage] = useState(''); // For create form status
  const [editSuccessMessage, setEditSuccessMessage] = useState(''); // For edit success outside modal
  const [userDecks, setUserDecks] = useState<Deck[]>([]);
  const [selectedDeck, setSelectedDeck] = useState<Deck | null>(null);
  const [deckHistory, setDeckHistory] = useState<DeckGameHistoryItem[]>([]); // State for history
  const [isLoading, setIsLoading] = useState(false); // Loading for deck list
  const [isLoadingDetails, setIsLoadingDetails] = useState(false); // Loading for details/history
  const [loadingDeckId, setLoadingDeckId] = useState<number | null>(null); // Track which deck's details are loading
  const [detailMessage, setDetailMessage] = useState(''); // Message for detail view

  // State for version selection within the detail view
  const [detailVersions, setDetailVersions] = useState<DeckVersionSummary[]>([]);
  const [selectedDetailVersionId, setSelectedDetailVersionId] = useState<number | null>(null);
  const [selectedDetailVersion, setSelectedDetailVersion] = useState<DeckVersionDetail | null>(null);

  // State for Edit Modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingDeck, setEditingDeck] = useState<Deck | null>(null); // Track which deck is being edited
  const [editDecklist, setEditDecklist] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [editError, setEditError] = useState('');
  const navigate = useNavigate(); // For potential navigation
  const location = useLocation(); // For reading navigation state

  const fetchUserDecks = async (userId: number) => {
    setIsLoading(true); // Messages are cleared by the functions that set them or trigger actions
    try {
      const response = await apiClient.get<Deck[]>(`/users/${userId}/decks`); // Use apiClient, relative URL (Retry 2)
      setUserDecks(response.data);
    } catch (error) { console.error("Error fetching decks:", error); setCreateStatusMessage("Failed to load decks."); } // Use createStatusMessage for general load errors too? Or add another state? For now, using createStatus.
    finally { setIsLoading(false); }
  };

  useEffect(() => {
    if (loggedInUser) { fetchUserDecks(loggedInUser.id); }
    else { setUserDecks([]); }
  }, [loggedInUser]); // Separate effect for fetching user decks

  // Effect to handle auto-selection based on navigation state
  useEffect(() => {
    const state = location.state as { autoSelectDeckId?: number, autoSelectVersionId?: number } | null; // Type assertion

    // Check if we have the required state and the user decks have loaded
    if (state?.autoSelectDeckId && userDecks.length > 0) {
        const deckToSelect = userDecks.find(d => d.id === state.autoSelectDeckId);
        // Only trigger if the deck exists and is not already selected (or details not loaded yet for it)
        if (deckToSelect && selectedDeck?.id !== state.autoSelectDeckId) {
            console.log("Auto-selecting deck/version from navigation state:", state);
            // Pass the target version ID directly to viewDeckDetails
            viewDeckDetails(state.autoSelectDeckId, state.autoSelectVersionId);
            // Clear the state immediately after triggering the load
            navigate(location.pathname, { replace: true, state: {} });
        }
    }
    // Dependencies: run when state changes, or when userDecks load
  }, [location.state, userDecks, navigate]); // Correct dependency array


  const handleCreateDeck = async (e: React.FormEvent) => {
    e.preventDefault(); setCreateStatusMessage(''); setEditSuccessMessage(''); // Clear messages
    if (!loggedInUser) return;
    if (!deckColors) { setCreateStatusMessage("Please select at least one color (or Colorless)."); return; }
    try {
      await apiClient.post(`/decks`, { name: deckName, commander: deckCommander, colors: deckColors, decklist_text: decklistText }); // Use apiClient, relative URL, remove user_id (Retry 2)
      console.log('[DEBUG] Setting create success message'); // DEBUG LOG
      setCreateStatusMessage('Deck created successfully!');
      // Add a microtask delay to allow React to render the message before refetching/clearing
      console.log('[DEBUG] Waiting for microtask before form clear/refetch'); // DEBUG LOG
      await new Promise(r => setTimeout(r, 0));
      console.log('[DEBUG] Microtask finished, refetching/clearing form'); // DEBUG LOG
      fetchUserDecks(loggedInUser.id); // Fetch decks first
      setDeckName(''); setDeckCommander(''); setDeckColors(''); setDecklistText(''); // Then clear form
    } catch (error) {
        let errorMsg = "Deck creation failed: An unknown error occurred";
        if (error instanceof Error) {
            errorMsg = `Deck creation failed: ${error.message}`;
        }
        // Attempt to get more specific error from Axios response if available
        if (axios.isAxiosError(error) && error.response?.data?.error) {
             errorMsg = `Deck creation failed: ${error.response.data.error}`;
        }
        console.log('[DEBUG] Setting create error message:', errorMsg); // DEBUG LOG
        setCreateStatusMessage(errorMsg);
    }
  };

  // Modified viewDeckDetails to accept an optional targetVersionId
  const viewDeckDetails = async (deckId: number, targetVersionId?: number) => {
      // setCreateStatusMessage(''); setEditSuccessMessage(''); // Clear main messages - REMOVED, let calling context manage
      setDetailMessage(''); // Clear detail message
      setLoadingDeckId(deckId); // Set loading ID *before* clearing selectedDeck
      setSelectedDeck(null); // Reset selected deck
      setDeckHistory([]); // Reset history
      setDetailVersions([]); // Reset versions list
      setSelectedDetailVersionId(null); // Reset selected version ID
      setSelectedDetailVersion(null); // Reset selected version details
      setIsLoadingDetails(true); // Start loading details (spinner appears based on loadingDeckId)

      console.log("Fetching details, versions, and history for deck ID:", deckId);

      try {
          // Fetch base details, all versions, and history in parallel
          const [baseDetailsResponse, versionsResponse, historyResponse] = await Promise.all([
              getDeckDetails(deckId), // Fetches base info
              getDeckVersions(deckId), // Fetches list of all versions
              apiClient.get<DeckGameHistoryItem[]>(`/decks/${deckId}/history`) // History fetch remains
          ]);

          // Set base info (needed for name/commander display even while loading version)
          setSelectedDeck(baseDetailsResponse); // Keep using selectedDeck for base info display
          console.log("Setting detailVersions:", versionsResponse); // Log versions being set
          setDetailVersions(versionsResponse);
          setDeckHistory(historyResponse.data);

          // Determine which version to show initially
          let initialVersionId = targetVersionId; // Prioritize targetVersionId from state/link
          // Validate targetVersionId exists in the fetched versions
          if (!initialVersionId || !versionsResponse.some((v: DeckVersion) => v.id === initialVersionId)) {
                console.log("Target version ID not found or not provided, using default logic.");
                initialVersionId = baseDetailsResponse.current_version_id; // Fallback to current
                if (!initialVersionId && versionsResponse.length > 0) {
                    initialVersionId = versionsResponse[0].id; // Fallback to latest if no current
                }
          }

          if (initialVersionId) {
              setSelectedDetailVersionId(initialVersionId);
              // Fetch details for the initial version
              const initialVersionDetails = await getDeckVersion(deckId, initialVersionId);
              setSelectedDetailVersion(initialVersionDetails);
          } else {
              // Handle case where there are no versions
              setSelectedDetailVersion({ // Placeholder detail
                  id: 0, version_number: 0, created_at: baseDetailsResponse.created_at,
                  notes: "No versions found.", is_current: false,
                  decklist_text: baseDetailsResponse.decklist_text || "No decklist available."
              });
              setDetailMessage("No versions found for this deck.");
          }

      } catch (error) {
          console.error("Error fetching deck details/versions/history:", error);
          let errorMsg = "Failed to load deck data: An unknown error occurred";
          if (error instanceof Error) {
              errorMsg = `Failed to load deck data: ${error.message}`;
          }
          if (axios.isAxiosError(error) && error.response?.data?.error) {
               errorMsg = `Failed to load deck data: ${error.response.data.error}`;
          }
          setDetailMessage(errorMsg);
      } finally {
          setIsLoadingDetails(false); // Stop loading details state
          setLoadingDeckId(null); // Clear loading ID
      }
  };

  // Handler for changing the selected version in the detail view
  const handleDetailVersionChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
      const newVersionId = Number(event.target.value);
      if (!selectedDeck || !newVersionId || newVersionId === selectedDetailVersionId) return;

      setIsLoadingDetails(true); // Show loading for the detail section
      setDetailMessage('');
      setSelectedDetailVersionId(newVersionId);
      setSelectedDetailVersion(null); // Clear old details

      try {
          const versionDetails = await getDeckVersion(selectedDeck.id, newVersionId);
          setSelectedDetailVersion(versionDetails);
      } catch (error) {
          console.error(`Error fetching details for version ${newVersionId}:`, error);
          let errorMsg = "Failed to load version details: An unknown error occurred";
           if (error instanceof Error) {
               errorMsg = `Failed to load version details: ${error.message}`;
           }
           if (axios.isAxiosError(error) && error.response?.data?.error) {
                errorMsg = `Failed to load version details: ${error.response.data.error}`;
           }
          setDetailMessage(errorMsg);
      } finally {
          setIsLoadingDetails(false);
      }
  };

  // --- Edit Modal Logic ---
  const openEditModal = async (deckToEdit: Deck) => {
      setEditingDeck(deckToEdit);
      setEditNotes(''); // Clear notes for new version
      setEditError('');
      setIsSaving(false); // Reset saving state

      // Fetch the latest deck details to ensure we have the current version's decklist
      try {
          const details = await getDeckDetails(deckToEdit.id);
          setEditDecklist(details.decklist_text || ''); // Pre-fill with current decklist
          setIsEditModalOpen(true); // Open modal only after fetching data
      } catch (error) {
          console.error("Error fetching deck details for edit:", error);
          let errorMsg = "Failed to load deck data for editing: An unknown error occurred.";
          if (error instanceof Error) {
              errorMsg = `Failed to load deck data for editing: ${error.message}`;
          }
          if (axios.isAxiosError(error) && error.response?.data?.error) {
               errorMsg = `Failed to load deck data for editing: ${error.response.data.error}`;
          }
          setEditError(errorMsg); // Show error in modal
      }
  };

  const closeEditModal = () => {
      setIsEditModalOpen(false);
      setEditingDeck(null); // Clear editing state
  };

  const handleSaveChanges = async () => {
      if (!editingDeck) return;
      setIsSaving(true);
      setEditError('');
      try {
          const newVersionData = {
              decklist_text: editDecklist,
              notes: editNotes,
          };
          const response = await createDeckVersion(editingDeck.id, newVersionData);
          console.log("New version created:", response); // Log success
          setIsEditModalOpen(false);
          setEditingDeck(null);
          // Show success message outside the modal
          console.log('[DEBUG] Setting edit success message'); // DEBUG LOG
          setEditSuccessMessage(`Successfully created new version for deck: ${editingDeck.name}`);
          setCreateStatusMessage(''); // Clear create status if any
          // Re-fetch decks to show updated last_updated timestamp? Or handle locally.
          console.log('[DEBUG] Triggering deck refetch/detail refresh after edit success'); // DEBUG LOG
          if (loggedInUser) fetchUserDecks(loggedInUser.id);
          // If the edited deck was being viewed, refresh its details?
          if (selectedDeck?.id === editingDeck.id) {
              viewDeckDetails(editingDeck.id); // Re-fetch details to show new version's list
          }

      } catch (error) {
            console.error("Error creating new version:", error);
            let errorMsg = "Failed to save: An unknown error occurred.";
            if (error instanceof Error) {
                errorMsg = `Failed to save: ${error.message}`;
            }
            // Attempt to get more specific error from Axios response if available
            if (axios.isAxiosError(error) && error.response?.data?.error) {
                 errorMsg = `Failed to save: ${error.response.data.error}`;
            }
            console.log('[DEBUG] Setting edit error message:', errorMsg); // DEBUG LOG
            setEditError(errorMsg); // Set the error state for the modal
        } finally {
            setIsSaving(false);
        }
  };

  if (!loggedInUser) { return <p>Please log in to manage decks.</p>; }

  console.log("Rendering DeckManagementPage"); // Log component render

  return (
    <> {/* Start fragment immediately inside return */}
    <section>
      <h3>Decks</h3>
      <div className="grid">
        <article>
          <h4>Create New Deck</h4>
          <form onSubmit={handleCreateDeck}>
            <div className="form-group">
              <label htmlFor="deckName">Deck Name</label>
              <input type="text" id="deckName" value={deckName} onChange={(e) => setDeckName(e.target.value)} required />
            </div>
            <div className="form-group">
              <label htmlFor="deckCommander">Commander</label>
              <input type="text" id="deckCommander" value={deckCommander} onChange={(e) => setDeckCommander(e.target.value)} required />
            </div>
            {/* Color Checkboxes - Use fieldset/legend for accessibility */}
            <fieldset className="form-group">
                 <legend>Colors</legend>
                 {/* Use Pico grid inside the fieldset */}
                 <div className="grid" style={{ gridTemplateColumns: 'repeat(3, auto)', gap: '0.5rem 1rem', justifyContent: 'start', margin: 0, padding: 0 }}>
                     {['W', 'U', 'B', 'R', 'G', 'C'].map(color => (
                         <label key={color} htmlFor={`color-${color}`} style={{ width: 'auto', margin: 0, padding: 0, textAlign: 'left' }}>
                             <input
                                 type="checkbox"
                                 id={`color-${color}`}
                                 name="colors"
                                 value={color}
                                 checked={deckColors.includes(color)}
                                 onChange={(e) => {
                                     const { value, checked } = e.target;
                                     setDeckColors(prev =>
                                         checked
                                             ? [...prev.split(''), value].sort((a, b) => "WUBRGC".indexOf(a) - "WUBRGC".indexOf(b)).join('')
                                             : prev.split('').filter(c => c !== value).join('')
                                     );
                                 }}
                             /> {color}
                         </label>
                     ))}
                 </div>
            </fieldset>
            <div className="form-group">
              <label htmlFor="decklistText">Decklist</label>
              <textarea id="decklistText" value={decklistText} onChange={(e) => setDecklistText(e.target.value)} rows={6} />
            </div>
            <button type="submit">Create Deck</button>
          </form>
          {createStatusMessage && <p><small style={{ color: createStatusMessage.startsWith('Deck creation failed') || createStatusMessage.startsWith('Failed to load') ? 'var(--pico-color-red-500)' : 'var(--pico-color-green-500)' }}>{createStatusMessage}</small></p>}
        </article>
        <article>
          <h4>Your Decks</h4>
          {/* Display edit success message here */}
          {editSuccessMessage && <p><small style={{ color: 'var(--pico-color-green-500)' }}>{editSuccessMessage}</small></p>}
          {isLoading ? <p aria-busy="true">Loading decks...</p> :
           userDecks.length > 0 ? (
            <table role="grid">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Commander</th>
                  <th>Colors</th>
                  <th style={{ minWidth: '130px' }}>Actions</th> {/* Wider column for two buttons */}
                </tr>
              </thead>
              <tbody>
              {userDecks.map((deck) => (
                <tr key={deck.id}>
                  <td>{deck.name}</td>
                  <td>{deck.commander}</td>
                  <td>{deck.colors || 'C'}</td>
                  {/* Wrap buttons in a div for stable layout during loading */}
                  <td>
                      <div
                          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-around', height: '30px', gap: '5px' }} /* Use gap for spacing */
                          aria-busy={loadingDeckId === deck.id} /* Use loadingDeckId for aria-busy */
                      >
                          {/* Removed problematic console.log */}
                          {loadingDeckId !== deck.id && ( /* Conditionally render buttons based on loadingDeckId */
                              <>
                                  {/* Removed console.log */}
                                  <button
                                      onClick={() => viewDeckDetails(deck.id)}
                                      className="outline secondary"
                                      style={{ padding: '0.1em 0.5em', fontSize: '0.8em', margin: 0, flexGrow: 1 }} /* Allow button to grow */
                                      disabled={loadingDeckId === deck.id} // Disable if loading this deck's details
                                  >
                                      View
                                  </button>
                                  <button
                                      onClick={() => openEditModal(deck)}
                                      className="outline contrast"
                                      style={{ padding: '0.1em 0.5em', fontSize: '0.8em', margin: 0, flexGrow: 1 }} /* Allow button to grow */
                                      disabled={loadingDeckId === deck.id} // Disable if loading this deck's details
                                  >
                                      Edit
                                  </button>
                              </>
                          )}
                          {/* Spinner/indicator will appear here due to aria-busy on parent */}
                      </div>
                  </td>
                </tr>
              ))}
              </tbody>
            </table>
          ) : ( <p><small>No decks created yet.</small></p> )}
        </article>
      </div>
      {selectedDeck && (
        <article style={{ marginTop: '1rem' }}>
           <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
             <hgroup style={{ marginBottom: '0.5rem' }}> {/* Reduced margin */}
               <h4>Deck Details: {selectedDeck.name}</h4>
               <h5>Commander: {selectedDeck.commander} ({selectedDeck.colors || 'C'})</h5>
             </hgroup>
             {/* Version Selector Dropdown */}
             {detailVersions.length > 0 && (
                <select
                    value={selectedDetailVersionId ?? ''}
                    onChange={handleDetailVersionChange}
                    aria-label="Select Deck Version"
                    style={{ maxWidth: '500px', margin: '0 1rem', verticalAlign: 'middle' }} /* Set maxWidth, removed flexGrow/minWidth */
                    disabled={isLoadingDetails}
                >
                    {detailVersions.map(v => (
                        <option key={v.id} value={v.id}>
                            Version {v.version_number} ({new Date(v.created_at).toLocaleDateString()}){v.is_current ? ' - Current' : ''}
                        </option>
                    ))}
                </select>
             )}
             <button className="outline secondary contrast" onClick={() => { setSelectedDeck(null); setDeckHistory([]); setDetailMessage(''); setDetailVersions([]); setSelectedDetailVersion(null); setSelectedDetailVersionId(null); }} style={{ padding: '0.2em 0.6em', fontSize: '0.8em' }}>Close</button> {/* Removed float */}
           </header>
           <div style={{ clear: 'both' }}></div> {/* Clear float */}
           {isLoadingDetails && <p aria-busy="true">Loading details...</p>}
           {detailMessage && <p><small style={{ color: 'var(--pico-color-red-500)' }}>{detailMessage}</small></p>}
           {!isLoadingDetails && !detailMessage && (
               <>
                   <div className="grid">
                       <section>
                           <p><strong>Owner:</strong> {loggedInUser?.username}</p>
                           {/* Display selected version info */}
                           {selectedDetailVersion && (
                               <p><small>
                                   Version: {selectedDetailVersion.version_number}
                                   {' | '}Created: {new Date(selectedDetailVersion.created_at).toLocaleString()}
                                   {selectedDetailVersion.is_current && ' (Current)'}
                               </small></p>
                           )}
                            {/* Display selected version notes if they exist */}
                            {selectedDetailVersion?.notes && (
                                <blockquote style={{ fontSize: '0.9em', fontStyle: 'italic', margin: '0 0 1rem 0', paddingLeft: '1em', borderLeft: '3px solid var(--pico-muted-border-color)' }}>
                                    Notes: {selectedDetailVersion.notes}
                                </blockquote>
                            )}
                           {/* Decklist Section */}
                           <label htmlFor="decklistDetailView" style={{ width: 'auto', textAlign: 'left', display: 'block', marginBottom: '0.25rem' }}>Decklist (Version {selectedDetailVersion?.version_number ?? 'N/A'}):</label>
                           <pre id="decklistDetailView" style={{ textAlign: 'left', whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '300px', overflowY: 'auto', background: 'var(--pico-form-element-background-color)', padding: '1rem', border: '1px solid var(--pico-form-element-border-color)', borderRadius: 'var(--pico-border-radius)', marginTop: 0 }}>
                               <code>{selectedDetailVersion?.decklist_text || 'Loading decklist or not available...'}</code>
                           </pre>
                       </section>
                       {/* History Section */}
                       <section>
                           <h6>Game History</h6>
                           {deckHistory.length > 0 ? (
                               <div style={{ maxHeight: '350px', overflowY: 'auto' }}> {/* Scrollable history */}
                                   <table role="grid" style={{ margin: 0, fontSize: '0.9em' }}>
                                       <thead><tr><th>Date</th><th>Placement</th><th>Version #</th><th>Game</th></tr></thead> {/* Changed column header */}
                                       <tbody>
                                           {deckHistory.map(hist => (
                                               <tr key={hist.game_id}>
                                                   <td>{new Date(hist.game_date + 'T00:00:00').toLocaleDateString()}</td>
                                                   <td>{hist.placement ?? 'N/A'}</td>
                                                   <td>{hist.version_number ?? 'N/A'}</td> {/* Display Version Number */}
                                                   <td><Link to={`/games?gameId=${hist.game_id}`}>View Game</Link></td>
                                               </tr>
                                           ))}
                                       </tbody>
                                   </table>
                               </div>
                           ) : (
                               <p><i>No game history found for this deck.</i></p>
                           )}
                       </section>
                   </div>
               </>
           )}
        </article>
      )}
    </section>

    {/* Edit Deck Modal */}
    <dialog open={isEditModalOpen}>
        <article>
            <header>
                <button aria-label="Close" rel="prev" onClick={closeEditModal}></button>
                <h5>Edit Deck: {editingDeck?.name} (Create New Version)</h5>
            </header>
            <p>Saving changes will create a new version of this deck.</p>
            <label htmlFor="editDecklist">Decklist:</label>
            <textarea
                id="editDecklist"
                value={editDecklist}
                onChange={(e) => setEditDecklist(e.target.value)}
                rows={15}
                style={{ fontFamily: 'monospace' }}
                aria-invalid={editError ? 'true' : undefined}
            />
            <label htmlFor="editNotes">Version Notes (Optional):</label>
            <textarea
                id="editNotes"
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                rows={3}
                aria-invalid={editError ? 'true' : undefined}
            />
             {editError && <small style={{ color: 'var(--pico-color-red-500)' }}>{editError}</small>}
            <footer>
                <button className="secondary" onClick={closeEditModal} disabled={isSaving}>Cancel</button>
                <button onClick={handleSaveChanges} aria-busy={isSaving} disabled={isSaving}>Save New Version</button>
            </footer>
        </article>
    </dialog>
    </> // End fragment immediately before closing parenthesis
  );
}

export default DeckManagementPage;
