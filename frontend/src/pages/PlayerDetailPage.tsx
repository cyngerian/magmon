// frontend/src/pages/PlayerDetailPage.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios'; // Keep for type guard
import apiClient, { getDeckDetails, getDeckVersions, getDeckVersion } from '../apiClient'; // Import version functions
// Removed apiClient import
import { useParams, Link } from 'react-router-dom'; // Import Link

// --- Interfaces ---
// Public profile data expected from /api/users/:userId
interface PlayerProfile {
    id: number;
    username: string;
    avatar_url: string | null;
    favorite_color: string | null;
    retirement_plane: string | null;
    stats: {
        total_wins: number;
        // Add current_form here later if needed
    };
}

// Interface for the deck list items
interface DeckListItem {
    id: number;
    name: string;
    commander: string;
    colors: string;
    last_updated: string;
}

// Interface for full deck details (from /api/decks/:deckId)
interface DeckDetails extends DeckListItem {
    decklist_text: string | null;
    user_id: number;
    created_at: string;
    current_version_id: number | null; // Add current_version_id
}

// Interface for deck game history items (from /api/decks/:deckId/history)
interface DeckGameHistoryItem {
    game_id: number;
    game_date: string;
    placement: number | null;
    version_number: number | null; // Add version number
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
// TODO: Centralize API_BASE_URL
const API_BASE_URL = 'http://127.0.0.1:5004/api';

function PlayerDetailPage() {
    const { userId } = useParams<{ userId: string }>(); // Get userId from URL
    const [player, setPlayer] = useState<PlayerProfile | null>(null);
    const [isLoadingPlayer, setIsLoadingPlayer] = useState(true); // Renamed for clarity
    const [playerMessage, setPlayerMessage] = useState(''); // Renamed for clarity

    // State for decks
    const [playerDecks, setPlayerDecks] = useState<DeckListItem[]>([]);
    const [isLoadingDecks, setIsLoadingDecks] = useState(true);
    const [decksMessage, setDecksMessage] = useState('');

    // State for selected deck details and history
    const [selectedDeckId, setSelectedDeckId] = useState<number | null>(null);
    const [selectedDeckDetails, setSelectedDeckDetails] = useState<DeckDetails | null>(null); // Holds base details of selected deck
    const [selectedDeckHistory, setSelectedDeckHistory] = useState<DeckGameHistoryItem[]>([]);
    const [isLoadingDeckDetails, setIsLoadingDeckDetails] = useState(false); // Loading for right pane

    // State for version selection within the detail view
    const [detailVersions, setDetailVersions] = useState<DeckVersionSummary[]>([]);
    const [selectedDetailVersionId, setSelectedDetailVersionId] = useState<number | null>(null);
    const [selectedDetailVersion, setSelectedDetailVersion] = useState<DeckVersionDetail | null>(null);
    const [deckDetailsMessage, setDeckDetailsMessage] = useState('');

    useEffect(() => {
        const fetchPlayerProfileAndDecks = async () => {
            if (!userId) {
                setPlayerMessage("User ID not found in URL.");
                setIsLoadingPlayer(false);
                setIsLoadingDecks(false);
                return;
            }
            setIsLoadingPlayer(true);
            setIsLoadingDecks(true);
            setPlayerMessage('');
            setDecksMessage('');
            setPlayer(null); // Reset player on new fetch
            setPlayerDecks([]); // Reset decks on new fetch
            setSelectedDeckId(null); // Reset selected deck
            setSelectedDeckDetails(null);
            setSelectedDeckHistory([]);

            // Fetch Profile
            try {
                const profileResponse = await apiClient.get<PlayerProfile>(`/users/${userId}`); // Use apiClient, relative URL (Retry 2)
                setPlayer(profileResponse.data);
            } catch (error) {
                console.error(`Error fetching profile for user ${userId}:`, error);
                setPlayerMessage(axios.isAxiosError(error) && error.response ? `Failed to load player profile: ${error.response.data.error || error.message}` : `Failed to load player profile: ${(error as Error).message}`); // Use axios.isAxiosError
            } finally {
                setIsLoadingPlayer(false);
            }

            // Fetch Decks
            try {
                const decksResponse = await apiClient.get<DeckListItem[]>(`/users/${userId}/decks`); // Use apiClient, relative URL (Retry 2)
                setPlayerDecks(decksResponse.data);
            } catch (error) {
                console.error(`Error fetching decks for user ${userId}:`, error);
                setDecksMessage(axios.isAxiosError(error) && error.response ? `Failed to load decks: ${error.response.data.error || error.message}` : `Failed to load decks: ${(error as Error).message}`); // Use axios.isAxiosError
            } finally {
                setIsLoadingDecks(false);
            }
        };

        fetchPlayerProfileAndDecks();
    }, [userId]); // Re-fetch if userId changes

    // Combined loading state check
    if (isLoadingPlayer || isLoadingDecks) {
        return <p aria-busy="true">Loading player data...</p>;
    }

    // Display player-specific error first
    if (playerMessage) {
         return <p><small style={{ color: 'var(--pico-color-red-500)' }}>{playerMessage}</small></p>;
    }

    if (!player) {
        return <p>Player not found or could not load data.</p>;
    }

    // --- Deck Detail Fetching Logic ---
    const fetchDeckDetailsAndHistory = async (deckId: number) => {
        setIsLoadingDeckDetails(true);
        setDeckDetailsMessage('');
        setSelectedDeckDetails(null); // Reset details
        setSelectedDeckHistory([]); // Reset history
        setDetailVersions([]); // Reset versions list
        setSelectedDetailVersionId(null); // Reset selected version ID
        setSelectedDetailVersion(null); // Reset selected version details

        try {
            // Fetch base details, all versions, and history in parallel
            const [baseDetailsResponse, versionsResponse, historyResponse] = await Promise.all([
                getDeckDetails(deckId), // Fetches base info
                getDeckVersions(deckId), // Fetches list of all versions
                apiClient.get<DeckGameHistoryItem[]>(`/decks/${deckId}/history`) // History fetch remains
            ]);

            // Set base info (needed for name/commander display even while loading version)
            setSelectedDeckDetails(baseDetailsResponse); // Keep using selectedDeckDetails for base info display
            setDetailVersions(versionsResponse);
            setSelectedDeckHistory(historyResponse.data);

            // Determine which version to show initially
            let initialVersionId = baseDetailsResponse.current_version_id;
            if (!initialVersionId && versionsResponse.length > 0) {
                initialVersionId = versionsResponse[0].id; // Fallback to latest
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
                setDeckDetailsMessage("No versions found for this deck.");
            }

        } catch (error) {
            console.error("Error fetching deck details/versions/history:", error);
            setDeckDetailsMessage(axios.isAxiosError(error) && error.response ? `Failed to load deck data: ${error.response.data.error || error.message}` : `Failed to load deck data: ${(error as Error).message}`);
        } finally {
             setIsLoadingDeckDetails(false);
        }
    };

    const handleSelectDeck = (deckId: number) => {
        if (selectedDeckId === deckId) {
            // Deselect if clicking the same deck again
            setSelectedDeckId(null);
            setSelectedDeckDetails(null);
            setSelectedDeckHistory([]);
            setDeckDetailsMessage('');
        } else {
            setSelectedDeckId(deckId);
            fetchDeckDetailsAndHistory(deckId);
        }
    };

    // Handler for changing the selected version in the detail view
    const handleDetailVersionChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newVersionId = Number(event.target.value);
        // Use selectedDeckDetails?.id which holds the base deck info
        if (!selectedDeckDetails?.id || !newVersionId || newVersionId === selectedDetailVersionId) return;

        setIsLoadingDeckDetails(true); // Show loading for the detail section
        setDeckDetailsMessage('');
        setSelectedDetailVersionId(newVersionId);
        setSelectedDetailVersion(null); // Clear old details

        try {
            const versionDetails = await getDeckVersion(selectedDeckDetails.id, newVersionId);
            setSelectedDetailVersion(versionDetails);
        } catch (error) {
            console.error(`Error fetching details for version ${newVersionId}:`, error);
            setDeckDetailsMessage(axios.isAxiosError(error) && error.response ? `Failed to load version details: ${error.response.data.error || error.message}` : `Failed to load version details: ${(error as Error).message}`);
        } finally {
            setIsLoadingDeckDetails(false);
        }
    };

    return (
        <section>
            {/* Top Pane: Player Details */}
            <article>
                <header style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    {player.avatar_url ? (
                        <img src={`http://127.0.0.1:5004${player.avatar_url}`} alt={`${player.username}'s avatar`} style={{ width: '80px', height: '80px', borderRadius: '50%', objectFit: 'cover' }} />
                    ) : (
                        <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: '#ccc', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '2rem' }}>?</div>
                    )}
                    <hgroup>
                        <h2>{player.username}</h2>
                        {/* Display Stats */}
                        <p style={{ margin: 0 }}><small>Wins: {player.stats?.total_wins ?? 'N/A'}</small></p>
                    </hgroup>
                </header>
                <p><strong>Favorite Color:</strong> {player.favorite_color || 'N/A'}</p>
                <p><strong>Retirement Plane:</strong> {player.retirement_plane || 'N/A'}</p>
            </article>

            {/* Bottom Panes: Deck List & Deck Details */}
            <div className="grid">
                {/* Bottom Left Pane: Deck List (Placeholder) */}
                <article>
                    <h6>Decks</h6>
                    {decksMessage && <p><small style={{ color: 'var(--pico-color-red-500)' }}>{decksMessage}</small></p>}
                    {playerDecks.length > 0 ? (
                        <div style={{ maxHeight: '40vh', overflowY: 'auto' }}> {/* Scrollable list */}
                            <table role="grid" style={{ margin: 0 }}>
                                <thead><tr><th>Name</th><th>Commander</th><th>Colors</th><th>Action</th></tr></thead>
                                <tbody>
                                    {playerDecks.map(deck => (
                                        <tr key={deck.id} className={selectedDeckId === deck.id ? 'selected-row' : ''}>
                                            <td>{deck.name}</td>
                                            <td>{deck.commander}</td>
                                            <td>{deck.colors || 'C'}</td>
                                            <td>
                                                <button
                                                    onClick={() => handleSelectDeck(deck.id)}
                                                    className={`outline secondary ${selectedDeckId === deck.id ? 'contrast' : ''}`}
                                                    style={{ padding: '0.1em 0.5em', fontSize: '0.8em', margin: 0 }}
                                                    aria-busy={isLoadingDeckDetails && selectedDeckId === deck.id}
                                                    disabled={isLoadingDeckDetails && selectedDeckId === deck.id}
                                                >
                                                    {selectedDeckId === deck.id ? 'Selected' : 'View'}
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        !decksMessage && <p><i>This player has no decks.</i></p>
                    )}
                </article>

                {/* Bottom Right Pane: Deck Details (Placeholder) */}
                <article>
                    <h6>Deck Details & History</h6>
                    {isLoadingDeckDetails && <p aria-busy="true">Loading deck details...</p>}
                    {deckDetailsMessage && <p><small style={{ color: 'var(--pico-color-red-500)' }}>{deckDetailsMessage}</small></p>}

                    {!selectedDeckId && !isLoadingDeckDetails && !deckDetailsMessage && (
                        <p><i>Select a deck from the list to see details and history.</i></p>
                    )}

                    {selectedDeckDetails && !isLoadingDeckDetails && (
                        <>
                            <hgroup style={{ marginBottom: '0.5rem' }}>
                                <h5>{selectedDeckDetails.name}</h5>
                                <h6>{selectedDeckDetails.commander} ({selectedDeckDetails.colors || 'C'})</h6>
                            </hgroup>
                            {/* Version Selector Dropdown */}
                            {detailVersions.length > 0 && (
                                <select
                                    value={selectedDetailVersionId ?? ''}
                                    onChange={handleDetailVersionChange}
                                    aria-label="Select Deck Version"
                                    style={{ maxWidth: '500px', marginBottom: '1rem', display: 'inline-block', verticalAlign: 'middle' }} // Consistent width
                                    disabled={isLoadingDeckDetails}
                                >
                                    {detailVersions.map(v => (
                                        <option key={v.id} value={v.id}>
                                            Version {v.version_number} ({new Date(v.created_at).toLocaleDateString()}){v.is_current ? ' - Current' : ''}
                                        </option>
                                    ))}
                                </select>
                            )}
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
                            <details open={!selectedDetailVersion?.decklist_text}> {/* Keep open if no decklist */}
                                <summary>View Decklist (Version {selectedDetailVersion?.version_number ?? 'N/A'})</summary>
                                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: '300px', overflowY: 'auto', background: 'var(--pico-form-element-background-color)', padding: '0.5rem', border: '1px solid var(--pico-form-element-border-color)', borderRadius: 'var(--pico-border-radius)', fontSize: '0.85em' }}>
                                    <code>{selectedDetailVersion?.decklist_text || 'No decklist available for this version.'}</code>
                                </pre>
                            </details>

                            <hr style={{ margin: '1rem 0' }}/>
                            <h6>Game History (Overall for Deck)</h6>
                            {selectedDeckHistory.length > 0 ? (
                                <div style={{ maxHeight: '30vh', overflowY: 'auto' }}> {/* Scrollable history */}
                                    <table role="grid" style={{ margin: 0, fontSize: '0.9em' }}>
                                        <thead><tr><th>Date</th><th>Placement</th><th>Version #</th><th>Game</th></tr></thead> {/* Added Version # header */}
                                        <tbody>
                                            {selectedDeckHistory.map(hist => (
                                                <tr key={hist.game_id}>
                                                    <td>{new Date(hist.game_date + 'T00:00:00').toLocaleDateString()}</td>
                                                    <td>{hist.placement ?? 'N/A'}</td>
                                                    <td>{hist.version_number ?? 'N/A'}</td> {/* Display Version Number */}
                                                    <td><Link to={`/games?gameId=${hist.game_id}`}>View Game</Link></td> {/* Link to game (needs adjustment on GamesPage) */}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p><i>No game history found for this deck.</i></p>
                            )}
                        </>
                    )}
                </article>
            </div>
        </section>
    );
}

export default PlayerDetailPage;