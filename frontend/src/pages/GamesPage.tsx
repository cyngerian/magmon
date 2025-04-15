import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios'; // Keep for type guard
import apiClient, { getDeckVersions, unregisterFromGame } from '../apiClient'; // Use configured apiClient, import getDeckVersions and unregisterFromGame
import { Link, useLocation } from 'react-router-dom'; // Import useLocation

// --- Interfaces ---
interface GameWithMatchInfo {
    id: number;
    game_date: string;
    status: 'Upcoming' | 'Completed' | 'Cancelled';
    is_pauper: boolean;
    details: string | null;
    match_id: number | null;
    match_status: 'pending' | 'approved' | null;
    submitted_by_id: number | null;
    registration_count: number; // Added registration count
    winner_id: number | null; // Winner user ID
    winner_username: string | null; // Winner username
}
interface Deck { id: number; name: string; commander: string; colors: string; }
interface User { id: number; username: string; email: string; }
interface Registration { registration_id: number; user_id: number; username: string; deck_id: number; deck_name: string; commander: string; colors: string; deck_version_id: number | null; version_number?: number; version_notes?: string; } // Added version fields
interface MatchDetails { /* ... same as before ... */
    match_id: number; game_id: number | null; game_date: string | null; status: 'pending' | 'approved';
    player_count: number; submitted_by_id: number; submitted_by_username: string | null; created_at: string;
    approved_by_id: number | null; approved_by_username: string | null; approved_at: string | null; approval_notes: string | null;
    start_time: string | null; end_time: string | null; notes_big_interaction: string | null; notes_rules_discussion: string | null; notes_end_summary: string | null;
    players: { user_id: number; username: string; deck_id: number; deck_name: string; commander: string; placement: number | null; }[];
}
interface PlacementInfo { user_id: number; placement: number; } // For submission payload

// Interface for version summary used in dropdowns
interface DeckVersionSummary {
  id: number;
  version_number: number;
  created_at: string;
  notes: string | null;
  is_current: boolean;
}

// --- API Base URL ---
const API_BASE_URL = 'http://127.0.0.1:5004/api'; // Use port 5004 (Corrected)

function GamesPage({ loggedInUser }: { loggedInUser: User | null }) {
    // Existing State
    const [games, setGames] = useState<GameWithMatchInfo[]>([]);
    const [userDecks, setUserDecks] = useState<Deck[]>([]);
    const [selectedGame, setSelectedGame] = useState<GameWithMatchInfo | null>(null);
    const [registrations, setRegistrations] = useState<Registration[]>([]);
    const [selectedDeckId, setSelectedDeckId] = useState<string>(''); // For registration
    const [availableVersions, setAvailableVersions] = useState<DeckVersionSummary[]>([]); // Versions for selected deck
    const [selectedRegVersionId, setSelectedRegVersionId] = useState<string>(''); // Version for registration
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingDetails, setIsLoadingDetails] = useState(false);
    const [regMessage, setRegMessage] = useState(''); // For registration/approval/submission messages
    const [listMessage, setListMessage] = useState(''); // For game list messages
    const [createDate, setCreateDate] = useState<string>('');
    const [createIsPauper, setCreateIsPauper] = useState(false);
    const [createDetails, setCreateDetails] = useState('');
    const [approvalNotes, setApprovalNotes] = useState('');
    const [matchDetails, setMatchDetails] = useState<MatchDetails | null>(null);

    // State for Submission Form (Integrated)
    const [showSubmissionForm, setShowSubmissionForm] = useState(false);
    const [placements, setPlacements] = useState<Record<string, string>>({});
    const [matchStartTime, setMatchStartTime] = useState<string>('');
    const [matchEndTime, setMatchEndTime] = useState<string>('');
    const [matchNotesInteraction, setMatchNotesInteraction] = useState('');
    const [matchNotesRules, setMatchNotesRules] = useState('');
    const [matchNotesSummary, setMatchNotesSummary] = useState('');
const location = useLocation(); // Get location object
// const navigate = useNavigate(); // Removed as unused
    // const navigate = useNavigate(); // Removed as unused

    // --- Data Fetching ---
    const fetchGames = useCallback(async () => { /* ... */
        setIsLoading(true); setListMessage('');
        try {
            console.log(`Attempting to fetch games from: ${API_BASE_URL}/games`); // Add log
            const response = await apiClient.get<GameWithMatchInfo[]>(`/games`); // Use apiClient, relative URL (Retry 2)
            console.log("Received games data:", response.data); // Log received data
            
            // Debug winner information
            response.data.forEach(game => {
                console.log(`Game ${game.id} (${game.game_date}) - Winner ID: ${game.winner_id}, Winner Username: ${game.winner_username}`);
            });
            
            const sortedGames = response.data.sort((a, b) => new Date(b.game_date).getTime() - new Date(a.game_date).getTime());
            console.log("Sorted games:", sortedGames); // Log sorted data
            setGames(sortedGames);
            console.log("Successfully set games state."); // Log success
        } catch (error) {
            console.error("Error caught in fetchGames:", error); // Log the specific error
            // Check if it's an Axios error or something else
            if (axios.isAxiosError(error)) { // Use axios.isAxiosError
                console.error("Axios error details:", error.response?.data, error.response?.status);
            }
            setListMessage('Failed to load games.'); // Keep this message for now
        }
        finally { setIsLoading(false); }
    }, []);

    const fetchUserDecks = useCallback(async (userId: number) => { /* ... */
        try {
            const response = await apiClient.get<Deck[]>(`/users/${userId}/decks`); // Use apiClient, relative URL (Retry 2)
            setUserDecks(response.data);
        } catch (error) { console.error("Error fetching logged-in user decks:", error); }
     }, []);

    const fetchGameDetails = useCallback(async (game: GameWithMatchInfo) => { /* ... */
        setIsLoadingDetails(true); setRegMessage(''); setMatchDetails(null); setApprovalNotes(''); setShowSubmissionForm(false);
        try {
            const regResponse = await apiClient.get<Registration[]>(`/games/${game.id}/registrations`); // Use apiClient, relative URL (Retry 2)
            setRegistrations(regResponse.data);
            const initialPlacements: Record<string, string> = {};
            regResponse.data.forEach(reg => { initialPlacements[reg.user_id.toString()] = ''; });
            setPlacements(initialPlacements);

            if (game.match_id) {
                const matchResponse = await apiClient.get<MatchDetails>(`/matches/${game.match_id}`); // Use apiClient, relative URL (Retry 2)
                setMatchDetails(matchResponse.data);
                if (matchResponse.data.status === 'pending' && matchResponse.data.approval_notes?.startsWith('Rejected by')) {
                    setApprovalNotes(matchResponse.data.approval_notes);
                } else if (matchResponse.data.status === 'approved' && matchResponse.data.approval_notes) {
                    setApprovalNotes(matchResponse.data.approval_notes);
                }
            }
        } catch (error) {
            console.error(`Error fetching details for game ${game.id}:`, error);
            setRegistrations([]); setMatchDetails(null); setRegMessage('Failed to load details.');
        } finally { setIsLoadingDetails(false); }
    }, []);

    useEffect(() => { /* ... */
        fetchGames();
        if (loggedInUser) { fetchUserDecks(loggedInUser.id); }
        else { setUserDecks([]); }
     }, [loggedInUser, fetchGames, fetchUserDecks]);

    // Effect to handle selecting a game based on URL query parameter
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const gameIdFromUrl = params.get('gameId');

        if (gameIdFromUrl && games.length > 0) {
            const gameIdNum = parseInt(gameIdFromUrl, 10);
            const gameToSelect = games.find(g => g.id === gameIdNum);
            if (gameToSelect && selectedGame?.id !== gameIdNum) { // Avoid re-selecting if already selected
                console.log(`Auto-selecting game ${gameIdNum} from URL parameter.`);
                handleSelectGame(gameToSelect);
            }
        }
        // Only run this effect when games list populates or location search changes
        // Note: Adding handleSelectGame to dependency array might cause infinite loops if not careful
    }, [games, location.search]); // Dependency: run when games array changes or URL search params change

    // --- Event Handlers ---
     const handleSelectGame = (game: GameWithMatchInfo) => { /* ... */
         if (selectedGame?.id === game.id) {
            setSelectedGame(null); setRegistrations([]); setMatchDetails(null); setShowSubmissionForm(false);
        } else {
            setSelectedGame(game);
            fetchGameDetails(game);
        }
    };

    const handleCreateGame = async () => { /* ... */
        setListMessage(''); setIsLoading(true);
        try {
            const payload: { game_date?: string; is_pauper: boolean; details?: string } = { is_pauper: createIsPauper, details: createDetails || undefined };
            if (createDate) { payload.game_date = createDate; }
            await apiClient.post(`/games`, payload); // Use apiClient, relative URL (Retry 2)
            setListMessage('Game created successfully!');
            setCreateDate(''); setCreateIsPauper(false); setCreateDetails('');
            fetchGames();
        } catch (error) { setListMessage(axios.isAxiosError(error) && error.response ? `Failed: ${error.response.data.error || error.message}` : `Failed: ${(error as Error).message}`); } // Use axios.isAxiosError
        finally { setIsLoading(false); }
    };

    // Handler for when the selected deck for registration changes
    const handleDeckSelectionChange = async (deckId: string) => {
        setSelectedDeckId(deckId);
        setAvailableVersions([]); // Clear old versions
        setSelectedRegVersionId(''); // Clear selected version
        if (deckId) {
            try {
                const versions = await getDeckVersions(Number(deckId));
                setAvailableVersions(versions);
                // Find and pre-select the current version
                const currentVersion = versions.find((v: DeckVersionSummary) => v.is_current);
                if (currentVersion) {
                    setSelectedRegVersionId(currentVersion.id.toString());
                } else if (versions.length > 0) {
                    // Fallback to the latest (first in descending list) if no current flag
                    setSelectedRegVersionId(versions[0].id.toString());
                }
            } catch (error) {
                console.error("Error fetching versions for selected deck:", error);
                setRegMessage("Failed to load versions for selected deck.");
            }
        }
    };

    const handleRegisterDeck = async (gameId: number) => { /* ... */
        setRegMessage('');
        // Ensure both deck and version are selected
        if (!selectedDeckId || !selectedRegVersionId || !loggedInUser) {
             setRegMessage("Please select both a deck and a version.");
             return;
        }
        setIsLoadingDetails(true);
        try {
            // Send both deck_id and deck_version_id
            const payload = {
                deck_id: parseInt(selectedDeckId, 10),
                deck_version_id: parseInt(selectedRegVersionId, 10)
            };
            await apiClient.post(`/games/${gameId}/registrations`, payload);
            setRegMessage('Registration successful!');
            setSelectedDeckId(''); // Reset deck selection
            setAvailableVersions([]); // Clear versions
            setSelectedRegVersionId(''); // Reset version selection
            if (selectedGame) fetchGameDetails(selectedGame); // Refresh details
        } catch (error) { setRegMessage(axios.isAxiosError(error) && error.response ? `Registration failed: ${error.response.data.error || error.message}` : `Registration failed: ${(error as Error).message}`); } // Use axios.isAxiosError
        finally { setIsLoadingDetails(false); }
    };

    const handleUnregister = async (gameId: number) => {
        if (!window.confirm("Are you sure you want to unregister from this game?")) return;
        setRegMessage('');
        setIsLoadingDetails(true); // Use detail loading indicator
        try {
            await unregisterFromGame(gameId);
            setRegMessage('Successfully unregistered.');
            // Refresh game details to show updated participant list / registration form
            if (selectedGame) {
                fetchGameDetails(selectedGame);
            }
        } catch (error) {
            console.error("Error unregistering:", error);
            setRegMessage(axios.isAxiosError(error) && error.response ? `Unregistration failed: ${error.response.data.error || error.message}` : `Unregistration failed: ${(error as Error).message}`);
        } finally {
            setIsLoadingDetails(false);
        }
    };

    const handleCancelGame = async (gameId: number) => { /* ... */
        if (!window.confirm("Cancel this game? This cannot be undone.")) return;
        setListMessage(''); setIsLoading(true);
        try {
            await apiClient.patch(`/games/${gameId}`, { status: 'Cancelled' }); // Use apiClient, relative URL (Retry 2)
            setListMessage('Game cancelled.');
            setSelectedGame(null); setRegistrations([]); setMatchDetails(null); setShowSubmissionForm(false);
            fetchGames();
        } catch (error) { setListMessage(axios.isAxiosError(error) && error.response ? `Cancellation failed: ${error.response.data.error || error.message}` : `Cancellation failed: ${(error as Error).message}`); } // Use axios.isAxiosError
        finally { setIsLoading(false); }
    };

    const handleApproveMatch = async (matchId: number) => { /* ... */
        setRegMessage(''); setIsLoadingDetails(true);
        if (!loggedInUser) return;
        try {
            // approved_by_id comes from token now
            await apiClient.patch(`/matches/${matchId}/approve`, { approval_notes: approvalNotes || null }); // Use apiClient, relative URL (Retry 2)
            setRegMessage('Game Approved!'); setApprovalNotes(''); fetchGames();
            if (selectedGame) {
                 const updatedSelectedGame = { ...selectedGame, match_status: 'approved' as const, status: 'Completed' as const };
                 setSelectedGame(updatedSelectedGame); fetchGameDetails(updatedSelectedGame);
            }
        } catch (error) { setRegMessage(axios.isAxiosError(error) && error.response ? `Approval failed: ${error.response.data.error || error.message}` : `Approval failed: ${(error as Error).message}`); } // Use axios.isAxiosError
        finally { setIsLoadingDetails(false); }
    };

    const handleRejectMatch = async (matchId: number) => { /* ... */
         if (!approvalNotes) { setRegMessage("Rejection notes are required."); return; }
         setRegMessage(''); setIsLoadingDetails(true);
         if (!loggedInUser) return;
         try {
            // rejected_by_id comes from token now
            await apiClient.patch(`/matches/${matchId}/reject`, { approval_notes: approvalNotes }); // Use apiClient, relative URL (Retry 2)
            setRegMessage('Game Rejected (kept as pending with notes).'); fetchGames();
            if (selectedGame) {
                 const updatedSelectedGame = { ...selectedGame, status: 'Upcoming' as const, match_status: 'pending' as const };
                 setSelectedGame(updatedSelectedGame); fetchGameDetails(updatedSelectedGame);
            }
         } catch (error) { setRegMessage(axios.isAxiosError(error) && error.response ? `Rejection failed: ${error.response.data.error || error.message}` : `Rejection failed: ${(error as Error).message}`); } // Use axios.isAxiosError
         finally { setIsLoadingDetails(false); }
    };

    // --- Submission Form Handlers (Integrated) ---
    const handlePlacementChange = (userId: string, placementValue: string) => { /* ... */
        setPlacements(prev => ({ ...prev, [userId]: placementValue }));
    };

    const handleMatchSubmit = async (e: React.FormEvent) => { /* ... */
        e.preventDefault(); setRegMessage('');
        if (!loggedInUser || !selectedGame) return;
        const participants = registrations;
        if (participants.length < 2) { setRegMessage("At least two players must be registered."); return; }
        const assignedPlacements = Object.values(placements).filter(p => p !== '');
        if (assignedPlacements.length !== participants.length) { setRegMessage("Please assign a placement to all registered players."); return; }
        const uniquePlacements = new Set(assignedPlacements);
        if (uniquePlacements.size !== participants.length) { setRegMessage("Each player must have a unique placement."); return; }
        const placementsPayload: PlacementInfo[] = Object.entries(placements).map(([userId, placement]) => ({ user_id: parseInt(userId, 10), placement: parseInt(placement, 10) }));

        setIsLoadingDetails(true);
        try {
            const payload = {
                submitted_by_id: loggedInUser.id, game_id: selectedGame.id, placements: placementsPayload,
                start_time: matchStartTime || null, end_time: matchEndTime || null,
                notes_big_interaction: matchNotesInteraction || null, notes_rules_discussion: matchNotesRules || null, notes_end_summary: matchNotesSummary || null,
            };
            await apiClient.post(`/matches`, payload); // Use apiClient, relative URL (Retry 2)
            setRegMessage('Game submitted successfully!');
            setPlacements({}); setMatchStartTime(''); setMatchEndTime(''); setMatchNotesInteraction(''); setMatchNotesRules(''); setMatchNotesSummary('');
            setShowSubmissionForm(false); fetchGames();
            const updatedSelectedGame = { ...selectedGame, status: 'Completed' as const, match_status: 'pending' as const };
            setSelectedGame(updatedSelectedGame); fetchGameDetails(updatedSelectedGame);
        } catch (error) { setRegMessage(axios.isAxiosError(error) && error.response ? `Game submission failed: ${error.response.data.error || error.message}` : `Game submission failed: ${(error as Error).message}`); } // Use axios.isAxiosError
        finally { setIsLoadingDetails(false); }
    };

    // --- Render Logic ---
    if (!loggedInUser) { return <p>Please log in to manage games.</p>; }

    const isUserRegistered = selectedGame !== null && registrations.some(r => r.user_id === loggedInUser.id);
    const canPerformApprovalAction = matchDetails?.status === 'pending' && loggedInUser?.id !== matchDetails?.submitted_by_id;

    const getDisplayStatus = (g: GameWithMatchInfo): string => { /* ... */
        if (g.match_status === 'pending') { return 'Pending Approval'; }
        if (g.match_status === 'approved') { return 'Approved'; }
        const today = new Date(); today.setHours(0, 0, 0, 0);
        const gameDate = new Date(g.game_date + 'T00:00:00');
        if (g.status === 'Upcoming' && gameDate.getTime() === today.getTime()) { return 'Current'; }
        // Add condition for past games that haven't been submitted
        if (g.status === 'Upcoming' && gameDate < today) { return 'Pending Submission'; }
        return g.status;
    };

    const placementOptions = Array.from({ length: registrations.length }, (_, i) => i + 1);

    return (
        <section>
            <h3>Games</h3>
            {listMessage && <p><small style={{ color: listMessage.startsWith('Failed') ? 'var(--pico-color-red-500)' : 'var(--pico-color-green-500)' }}>{listMessage}</small></p>}

            <div className="grid">
                {/* --- Left Column --- */}
                <section>
                    {/* Create Game Form - Final Layout */}
                    <article style={{ marginBottom: '1rem', paddingBottom: '0.5rem' }}>
                        <form onSubmit={(e) => { e.preventDefault(); handleCreateGame(); }}>
                            <h4>Create New Game</h4> {/* Removed hgroup/small text */}
                            {/* Grid for label/input alignment */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.5rem 1rem', alignItems: 'center' }}>
                                <label htmlFor="createDate" style={{ gridColumn: 1, textAlign: 'right', marginBottom: 0 }}>Game Date</label>
                                <input type="date" id="createDate" value={createDate || ''} onChange={(e) => setCreateDate(e.target.value)} required style={{ gridColumn: 2 }}/>

                                <label htmlFor="createIsPauper" style={{ gridColumn: 1, textAlign: 'right', marginBottom: 0 }}>Pauper</label>
                                <input type="checkbox" id="createIsPauper" role="switch" checked={createIsPauper} onChange={(e) => setCreateIsPauper(e.target.checked)} style={{ gridColumn: 2, marginRight: 'auto', marginBottom: 0 }}/>

                                <label htmlFor="createDetails" style={{ gridColumn: 1, textAlign: 'right', alignSelf: 'start', marginTop: '0.5rem' }}>Notes</label>
                                <textarea id="createDetails" value={createDetails} onChange={(e) => setCreateDetails(e.target.value)} rows={2} style={{ gridColumn: 2 }}></textarea>
                            </div>
                            <button type="submit" disabled={isLoading} aria-busy={isLoading} style={{ marginTop: '1rem' }}>Create Game</button>
                        </form>
                    </article>
                    {/* Game List - Updated Table */}
                    <article>
                        <h6>Game List</h6>
                        {isLoading && games.length === 0 && <p aria-busy="true">Loading...</p>}
                        {games.length > 0 ? (
                            <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
                                <table role="grid" style={{ margin: 0 }}>
                                    {/* 4) Added # Players Column */}
                                    <thead><tr><th>Date</th><th>Status</th><th># Players</th><th>Winner</th></tr></thead> {/* Changed Action to Winner */}
                                    <tbody>
                                        {games.map(g => (
                                            <tr key={g.id} className={selectedGame?.id === g.id ? 'selected-row' : ''}>
                                                {/* Make Date a link-like button */}
                                                <td><a href="#" onClick={(e) => { e.preventDefault(); handleSelectGame(g); }} className={selectedGame?.id === g.id ? 'contrast' : ''}>{new Date(g.game_date + 'T00:00:00').toLocaleDateString()}</a></td>
                                                <td>{getDisplayStatus(g)}</td>
                                                <td>{g.registration_count}</td>
                                                {/* Winner Column */}
                                                <td>{g.winner_id ? <Link to={`/players/${g.winner_id}`}>{g.winner_username ?? `User ${g.winner_id}`}</Link> : '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : ( !isLoading && <p>No games found.</p> )}
                    </article>
                </section>

                {/* --- Right Column (Details/Forms) --- */}
                <article style={{ textAlign: 'left' }}>
                    {!selectedGame && <p>Select a game from the list to see details.</p>}

                    {selectedGame && (
                        <>
                            <h4 style={{ textAlign: 'center' }}>{new Date(selectedGame.game_date + 'T00:00:00').toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</h4>
                            <p><strong>Status:</strong> {getDisplayStatus(selectedGame)}</p>
                            {selectedGame.is_pauper && <p><strong>Format:</strong> Pauper</p>}
                            {selectedGame.details && <p><strong>Notes:</strong> {selectedGame.details}</p>}

                            {/* Moved Match Details section up */}
                            {isLoadingDetails ? <p aria-busy="true">Loading details...</p> : (
                                <>
                                    {/* A: Show Match Details & Approval Form if match exists */}
                                    {matchDetails && !showSubmissionForm && (
                                        <>
                                            <hr /><h5>Participants</h5>
                                            {registrations.length > 0 ? (
                                                /* Ensured wrapper div for horizontal scrolling */
                                                <div style={{ overflowX: 'auto', marginBottom: '1rem' }}>
                                                    <table role="grid" className="participants-table" style={{ margin: 0, width: '100%' /* Ensure table tries to fit */ }}> {/* Removed inline font-size */}
                                                        <thead><tr><th>Player</th><th>Deck Name</th><th>Commander</th><th>Colors</th><th>Place</th></tr></thead>
                                                        <tbody>
                                                            {registrations.map(reg => {
                                                                // Find placement from matchDetails if available
                                                                const playerPlacement = matchDetails?.players?.find(p => p.user_id === reg.user_id)?.placement;
                                                                // Return the table row directly without extra whitespace/newlines
                                                                return (<tr key={reg.registration_id}>
                                                                    <td><Link to={`/players/${reg.user_id}`}>{reg.username}</Link></td>
                                                                    <td><Link to={`/decks/${reg.deck_id}`}>{reg.deck_name}</Link></td>
                                                                    <td>{reg.commander}</td>
                                                                    <td>{reg.colors || 'C'}</td>
                                                                    <td>{playerPlacement ?? (matchDetails ? 'N/A' : '')}</td>
                                                                </tr>);
                                                            })}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            ) : (<p><small>No players registered yet.</small></p>)}

                                            {/* Submitted Game Result Section */}
                                            <hr /><h5>Submitted Game Result ({matchDetails.status})</h5>
                                            <p><small>Submitted by: {matchDetails.submitted_by_id ? <Link to={`/players/${matchDetails.submitted_by_id}`}>{matchDetails.submitted_by_username ?? `User ${matchDetails.submitted_by_id}`}</Link> : 'N/A'} at {new Date(matchDetails.created_at).toLocaleString()}</small></p>
                                            {matchDetails.status === 'approved' && matchDetails.approved_by_id && ( <p><small>Approved by: <Link to={`/players/${matchDetails.approved_by_id}`}>{matchDetails.approved_by_username ?? `User ${matchDetails.approved_by_id}`}</Link> at {matchDetails.approved_at ? new Date(matchDetails.approved_at).toLocaleString() : 'N/A'}</small></p> )}
                                            {matchDetails.approval_notes && <p><strong>Approval/Rejection Notes:</strong> {matchDetails.approval_notes}</p>}

                                            {/* Submitted Notes Section */}
                                            {(matchDetails.notes_big_interaction || matchDetails.notes_rules_discussion || matchDetails.notes_end_summary) && <><hr/><h6>Submitted Notes</h6></>}
                                            {matchDetails.notes_big_interaction && <p><small><strong>Big Interaction:</strong> {matchDetails.notes_big_interaction}</small></p>}
                                            {matchDetails.notes_rules_discussion && <p><small><strong>Rules Discussion:</strong> {matchDetails.notes_rules_discussion}</small></p>}
                                            {matchDetails.notes_end_summary && <p><small><strong>End Summary:</strong> {matchDetails.notes_end_summary}</small></p>}

                                            {/* Approval/Rejection Form */}
                                            {matchDetails.status === 'pending' && (
                                                <>
                                                    <hr /><h6>Approve/Reject Submission</h6>
                                                    {!canPerformApprovalAction && <p><small><i>You cannot approve or reject a game you submitted.</i></small></p>}
                                                    <form onSubmit={(e) => e.preventDefault()}>
                                                        {/* Wrap label and textarea in a grid for better layout */}
                                                        {/* Changed grid columns to 2fr 3fr (40%/60%) */}
                                                        <div style={{ display: 'grid', gridTemplateColumns: '2fr 3fr', gap: '0 1rem', alignItems: 'start', marginBottom: '1rem' }}>
                                                            <label htmlFor="approvalNotes" style={{ gridColumn: 1, textAlign: 'right', marginTop: '0.5rem' }}>Approval/Rejection Notes (Required for Rejection)</label>
                                                            <textarea
                                                                id="approvalNotes"
                                                                /* Removed className */
                                                                value={approvalNotes}
                                                                onChange={(e) => setApprovalNotes(e.target.value)}
                                                                rows={3}
                                                                disabled={!canPerformApprovalAction || isLoadingDetails}
                                                                style={{ gridColumn: 2 }} /* No explicit width needed */
                                                            ></textarea>
                                                        </div>
                                                        <div className="grid">
                                                            {/* Approve button uses default (primary) style */}
                                                            <button onClick={() => handleApproveMatch(matchDetails.match_id)} disabled={!canPerformApprovalAction || isLoadingDetails} aria-busy={isLoadingDetails}>Approve</button>
                                                            <button type="button" onClick={() => handleRejectMatch(matchDetails.match_id)} className="secondary" disabled={!canPerformApprovalAction || isLoadingDetails || !approvalNotes} aria-busy={isLoadingDetails}>Reject</button>
                                                        </div>
                                                    </form>
                                                </>
                                            )}
                                        </>
                                    )}

                                    {/* B: Show Submission Form if Upcoming, no match yet, and button clicked */}
                                    {!matchDetails && selectedGame.status === 'Upcoming' && showSubmissionForm && (
                                        <>
                                            <hr/><h5>Submit Game Result</h5>
                                            <form onSubmit={handleMatchSubmit}>
                                                <h6>Participants & Placements</h6>
                                                {registrations.length < 2 ? <p><small>Need at least 2 registered players.</small></p> : (
                                                    <table role="grid" style={{marginBottom: '1.5rem'}}>
                                                        <thead><tr><th>Player</th><th>Deck</th><th>Placement</th></tr></thead>
                                                        <tbody>
                                                            {registrations.map(reg => (
                                                                <tr key={reg.registration_id}>
                                                                    <td>{reg.username}</td>
                                                                    <td>{reg.deck_name}</td>
                                                                    <td>
                                                                        <select value={placements[reg.user_id.toString()] || ''} onChange={(e) => handlePlacementChange(reg.user_id.toString(), e.target.value)} required style={{ minWidth: '100px', padding: '0.25rem 0.5rem', margin: 0 }}>
                                                                            <option value="" disabled>-- Place --</option>
                                                                            {placementOptions.map(p => (<option key={p} value={p}>{p}</option>))}
                                                                        </select>
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                )}
                                                <div className="grid">
                                                    <div><label htmlFor="startTime">Start Time</label><input type="datetime-local" id="startTime" value={matchStartTime} onChange={(e) => setMatchStartTime(e.target.value)} style={{ fontSize: '0.75rem' }} /></div>
                                                    <div><label htmlFor="endTime">End Time</label><input type="datetime-local" id="endTime" value={matchEndTime} onChange={(e) => setMatchEndTime(e.target.value)} style={{ fontSize: '0.75rem' }} /></div>
                                                </div>
                                                <fieldset style={{ marginTop: '1rem' }}>
                                                    <legend>Game Notes</legend>
                                                    <div><label htmlFor="notesInteraction">Big Interaction</label><textarea id="notesInteraction" value={matchNotesInteraction} onChange={(e) => setMatchNotesInteraction(e.target.value)} rows={2} /></div>
                                                    <div><label htmlFor="notesRules">Rules Discussion</label><textarea id="notesRules" value={matchNotesRules} onChange={(e) => setMatchNotesRules(e.target.value)} rows={2} /></div>
                                                    <div><label htmlFor="notesSummary">End Summary</label><textarea id="notesSummary" value={matchNotesSummary} onChange={(e) => setMatchNotesSummary(e.target.value)} rows={2} /></div>
                                                </fieldset>
                                                <button type="submit" style={{ marginTop: '1rem' }} disabled={isLoadingDetails || registrations.length < 2} aria-busy={isLoadingDetails}>Submit Result</button>
                                                <button type="button" className="secondary" onClick={() => setShowSubmissionForm(false)} style={{ marginTop: '1rem', marginLeft: '1rem' }} disabled={isLoadingDetails}>Cancel</button>
                                            </form>
                                        </>
                                    )}

                                    {/* C: Show Actions for Upcoming Game if no match details and submission form not shown */}
                                    {!matchDetails && selectedGame.status === 'Upcoming' && !showSubmissionForm && (
                                        <>
                                            <hr />
                                            {isUserRegistered ? (
                                                <>
                                                    <h6>Participants ({registrations.length})</h6> {/* Changed heading */}
                                                    {registrations.length > 0 ? (
                                                        <table role="grid" className="participants-table" style={{marginBottom: '1rem'}}>
                                                            <thead>
                                                                <tr>
                                                                    <th>Player</th>
                                                                    <th>Deck</th>
                                                                    <th>Commander</th> {/* Added Commander Header */}
                                                                    <th>Action</th> {/* Added Action column */}
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                {registrations.map(reg => (
                                                                    <tr key={reg.registration_id}>
                                                                        <td><Link to={`/players/${reg.user_id}`}>{reg.username}</Link> {reg.user_id === loggedInUser.id ? '(You)' : ''}</td>
                                                                        <td><Link to={`/decks/${reg.deck_id}`}>{reg.deck_name || `Deck ${reg.deck_id}`}</Link></td>
                                                                        <td>{reg.commander}</td> {/* Added Commander Data */}
                                                                        <td> {/* Action Cell */}
                                                                            {reg.user_id === loggedInUser.id && selectedGame.status === 'Upcoming' && (
                                                                                <button
                                                                                    onClick={() => handleUnregister(selectedGame.id)}
                                                                                    className="outline contrast"
                                                                                    style={{ padding: '0.1em 0.5em', fontSize: '0.8em', margin: 0 }}
                                                                                    disabled={isLoadingDetails}
                                                                                    aria-busy={isLoadingDetails}
                                                                                >
                                                                                    Unregister
                                                                                </button>
                                                                            )}
                                                                        </td>
                                                                    </tr>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    ) : <p><small>No participants registered yet.</small></p>}
                                                    {/* Display registration message here too */}
                                                    {regMessage && <p><small style={{ color: regMessage.startsWith('Failed') || regMessage.startsWith('Registration failed') || regMessage.startsWith('Unregistration failed') ? 'var(--pico-color-red-500)' : 'var(--pico-color-green-500)' }}>{regMessage}</small></p>}
                                                </>
                                            ) : (
                                                <>
                                                    <h6>Register Your Deck</h6>
                                                    {userDecks.length > 0 ? (
                                                        <form onSubmit={(e) => { e.preventDefault(); handleRegisterDeck(selectedGame.id); }}>
                                                            {/* Use grid for dropdown layout */}
                                                            {/* Swapped order: Deck first, then Version + Link */}
                                                            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '0.5rem', alignItems: 'end' }}> {/* Adjusted grid */}
                                                                {/* Deck Dropdown (First) */}
                                                                <div> {/* Wrap in div for label */}
                                                                    <label htmlFor="regDeckSelect" style={{marginBottom: '0.25rem'}}>Deck</label>
                                                                    <select id="regDeckSelect" value={selectedDeckId} onChange={(e) => handleDeckSelectionChange(e.target.value)} required>
                                                                        <option value="" disabled>-- Choose Deck --</option>
                                                                        {userDecks.map(deck => (<option key={deck.id} value={deck.id}>{deck.name} ({deck.commander})</option>))}
                                                                    </select>
                                                                </div>
                                                                {/* Version Dropdown & Link (Second) */}
                                                                <div> {/* Wrap in div for label */}
                                                                    <label htmlFor="regVersionSelect" style={{marginBottom: '0.25rem'}}>Version</label>
                                                                    <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}> {/* Flex for dropdown and link */}
                                                                        <select
                                                                            id="regVersionSelect"
                                                                            value={selectedRegVersionId}
                                                                            onChange={(e) => setSelectedRegVersionId(e.target.value)}
                                                                            required
                                                                            disabled={!selectedDeckId || availableVersions.length === 0} // Disable if no deck selected or no versions
                                                                            style={{flexGrow: 1}} // Allow dropdown to grow
                                                                        >
                                                                            <option value="" disabled>-- Choose Version --</option>
                                                                            {availableVersions.map(v => (
                                                                                <option key={v.id} value={v.id}>
                                                                                    V{v.version_number} ({new Date(v.created_at).toLocaleDateString()}){v.is_current ? ' - Current' : ''}
                                                                                </option>
                                                                            ))}
                                                                        </select>
                                                                        {/* View Details Link/Button */}
                                                                        {selectedDeckId && selectedRegVersionId && (
                                                                            <Link
                                                                                to={`/decks`} // Navigate to the main decks page
                                                                                state={{ autoSelectDeckId: Number(selectedDeckId), autoSelectVersionId: Number(selectedRegVersionId) }} // Pass state
                                                                                role="button"
                                                                                className="outline secondary"
                                                                                style={{ padding: '0.2em 0.6em', fontSize: '0.8em', margin: 0, flexShrink: 0 }} // Prevent shrinking
                                                                                title="View Version Details"
                                                                            >
                                                                                View
                                                                            </Link>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            {/* Button Below Dropdowns */}
                                                            <button type="submit" disabled={isLoadingDetails || !selectedDeckId || !selectedRegVersionId} aria-busy={isLoadingDetails}>Register Deck</button>
                                                        </form>
                                                    ) : (<p><small>Create a deck first!</small></p>)}
                                                    {regMessage && <p><small style={{ color: regMessage.startsWith('Failed') || regMessage.startsWith('Registration failed') ? 'var(--pico-color-red-500)' : 'var(--pico-color-green-500)' }}>{regMessage}</small></p>}
                                                </>
                                            )}

                                            <hr />
                                            {/* Submit Results Button */}
                                            <button onClick={() => setShowSubmissionForm(true)} className="outline" disabled={registrations.length < 2}>
                                                Submit Results {registrations.length < 2 ? `(Need ${Math.max(0, 2 - registrations.length)} more)` : ''}
                                            </button>
                                            {/* Cancel Game Button */}
                                            <button onClick={() => handleCancelGame(selectedGame.id)} className="secondary outline contrast" disabled={isLoading} style={{marginLeft: '1rem'}}>Cancel Game</button>
                                        </>
                                    )}
                                </>
                            )}
                            {/* Display general registration message if needed */}
                            {!isLoadingDetails && regMessage && !matchDetails && selectedGame.status !== 'Upcoming' && <p><small style={{ color: regMessage.startsWith('Failed') ? 'var(--pico-color-red-500)' : 'var(--pico-color-green-500)' }}>{regMessage}</small></p>}
                        </>
                    )}
                </article>
            </div>
        </section>
    );
}

export default GamesPage;
