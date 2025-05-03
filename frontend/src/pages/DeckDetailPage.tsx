import React, { useState, useEffect } from 'react';
import axios from 'axios';
import apiClient from '../apiClient';
import { useParams, Link, useLocation, useNavigate } from 'react-router-dom';

// Keyframes for loading spinner
const spinnerKeyframes = `
@keyframes spin {
    0% { transform: translateY(-50%) rotate(0deg); }
    100% { transform: translateY(-50%) rotate(360deg); }
}`;

// Add keyframes to document
const styleSheet = document.createElement("style");
styleSheet.textContent = spinnerKeyframes;
document.head.appendChild(styleSheet);

// --- Interfaces ---
interface DeckDetailData {
    id: number;
    name: string;
    commander: string;
    colors: string;
    last_updated: string;
    decklist_text?: string;
    user_id: number;
    created_at: string;
    current_version_id: number | null;
}

// Owner info interface
interface PlayerProfile {
    id: number;
    username: string;
    avatar_url: string | null;
    favorite_color: string | null;
    retirement_plane: string | null;
    stats: {
        total_wins: number;
    };
}

// Version interfaces
interface DeckVersionSummary {
    id: number;
    version_number: number;
    created_at: string;
    notes: string | null;
    is_current: boolean;
}

interface DeckVersionDetail extends DeckVersionSummary {
    decklist_text: string | null;
}

interface User { id: number; username: string; email: string; }

interface DeckGameHistoryItem {
    game_id: number;
    game_date: string;
    placement: number | null;
    version_number: number | null;
}

// --- API Base URL ---
function DeckDetailPage({ loggedInUser }: { loggedInUser: User | null }) {
    const { deckId } = useParams<{ deckId: string }>();
    const location = useLocation();
    const navigate = useNavigate();

    // State for deck details and owner info
    const [deckDetails, setDeckDetails] = useState<DeckDetailData | null>(null);
    const [ownerInfo, setOwnerInfo] = useState<PlayerProfile | null>(null);
    
    // State for versions
    const [allVersions, setAllVersions] = useState<DeckVersionSummary[]>([]);
    const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
    const [selectedVersionDetail, setSelectedVersionDetail] = useState<DeckVersionDetail | null>(null);
    
    // State for history
    const [deckHistory, setDeckHistory] = useState<DeckGameHistoryItem[]>([]);
    
    // Loading and error states
    const [isLoading, setIsLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState('');

    // Effect to clear navigation state after mount
    useEffect(() => {
        if (location.state?.targetVersionId) {
            navigate(location.pathname, { replace: true, state: {} });
        }
    }, [location.pathname, navigate]);

    // Effect to fetch initial data
    useEffect(() => {
        const fetchInitialData = async () => {
            setIsLoading(true);
            setErrorMessage('');
            
            if (!deckId) {
                setErrorMessage("No deck ID provided in URL.");
                setIsLoading(false);
                return;
            }

            const numericDeckId = Number(deckId);
            const targetVersionId = location.state?.targetVersionId;

            try {
                // Fetch base details, versions, and history in parallel
                const [baseDetailsResponse, versionsResponse, historyResponse] = await Promise.all([
                    apiClient.get<DeckDetailData>(`/decks/${numericDeckId}`),
                    apiClient.get<DeckVersionSummary[]>(`/decks/${numericDeckId}/versions`),
                    apiClient.get<DeckGameHistoryItem[]>(`/decks/${numericDeckId}/history`)
                ]);

                setDeckDetails(baseDetailsResponse.data);
                setAllVersions(versionsResponse.data);
                setDeckHistory(historyResponse.data);

                // Fetch owner info
                try {
                    const ownerResponse = await apiClient.get<PlayerProfile>(`/users/${baseDetailsResponse.data.user_id}`);
                    setOwnerInfo(ownerResponse.data);
                } catch (ownerError) {
                    console.error("Could not fetch owner details", ownerError);
                }

                // Determine which version to show initially
                let initialVersionId = targetVersionId;
                if (!initialVersionId || !versionsResponse.data.some((v: DeckVersionSummary) => v.id === initialVersionId)) {
                    initialVersionId = baseDetailsResponse.data.current_version_id ?? undefined;
                    if (!initialVersionId && versionsResponse.data.length > 0) {
                        initialVersionId = versionsResponse.data[0].id;
                    }
                }

                if (initialVersionId) {
                    setSelectedVersionId(initialVersionId);
                    const versionDetails = await apiClient.get<DeckVersionDetail>(`/decks/${numericDeckId}/versions/${initialVersionId}`);
                    setSelectedVersionDetail(versionDetails.data);
                }

            } catch (error) {
                console.error("Error fetching deck data:", error);
                setErrorMessage(axios.isAxiosError(error) && error.response ?
                    `Failed to load deck data: ${error.response.data.error || error.message}` :
                    `Failed to load deck data: ${(error as Error).message}`
                );
            } finally {
                setIsLoading(false);
            }
        };

        fetchInitialData();
    }, [deckId]); // Only re-fetch when deckId changes

    // Handle version selection change
    const handleVersionChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newVersionId = Number(event.target.value);
        if (!deckId || !newVersionId || newVersionId === selectedVersionId) return;

        setIsLoading(true);
        setErrorMessage('');
        setSelectedVersionId(newVersionId);
        setSelectedVersionDetail(null);

        try {
            const versionDetails = await apiClient.get<DeckVersionDetail>(`/decks/${Number(deckId)}/versions/${newVersionId}`);
            setSelectedVersionDetail(versionDetails.data);
        } catch (error) {
            console.error(`Error fetching version ${newVersionId}:`, error);
            setErrorMessage(axios.isAxiosError(error) && error.response ?
                `Failed to load version: ${error.response.data.error || error.message}` :
                `Failed to load version: ${(error as Error).message}`
            );
        } finally {
            setIsLoading(false);
        }
    };

    // Show loading state only for initial load
    if (isLoading && !deckDetails) {
        return <p aria-busy="true">Loading deck data...</p>;
    }

    if (errorMessage && !deckDetails) {
        return <p><small style={{ color: 'var(--pico-color-red-500)' }}>{errorMessage}</small></p>;
    }

    if (!deckDetails || !ownerInfo) {
        return <p>Deck or owner information not found.</p>;
    }

    // Basic authorization check
    if (!loggedInUser) {
        return <p>Please log in to view deck details.</p>;
    }
    // Optional: Check if loggedInUser.id === deck.user_id if only owners can view

    return (
        <article>
            <header style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                {/* Owner Info */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexBasis: '100%' }}>
                    {ownerInfo.avatar_url ? (
                        <img
                            src={`http://127.0.0.1:5004${ownerInfo.avatar_url}`}
                            alt={`${ownerInfo.username}'s avatar`}
                            style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }}
                        />
                    ) : (
                        <div style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '50%',
                            background: '#ccc',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#fff',
                            fontSize: '1.5rem'
                        }}>?</div>
                    )}
                    <Link to={`/players/${ownerInfo.id}`} style={{ fontWeight: 'bold' }}>
                        {ownerInfo.username}
                    </Link>
                </div>

                {/* Deck Info */}
                <div style={{ flexGrow: 1, minWidth: '200px' }}>
                    <hgroup style={{ margin: 0 }}>
                        <h4 style={{ marginBottom: '0.25rem' }}>{deckDetails.name}</h4>
                        <h5 style={{ margin: 0 }}>{deckDetails.commander} ({deckDetails.colors || 'C'})</h5>
                    </hgroup>
                </div>

                {/* Version Selector */}
                {allVersions.length > 0 && (
                    <div style={{ minWidth: '250px', marginLeft: 'auto' }}>
                        <label htmlFor="versionSelect" style={{ display: 'block', fontSize: '0.8em', marginBottom: '0.2rem' }}>
                            Select Version:
                        </label>
                        <div style={{ position: 'relative' }}>
                            <select
                                id="versionSelect"
                                value={selectedVersionId ?? ''}
                                onChange={handleVersionChange}
                                aria-label="Select Deck Version"
                                style={{ width: '100%' }}
                                disabled={isLoading}
                            >
                                {allVersions.map(v => (
                                    <option key={v.id} value={v.id}>
                                        V{v.version_number} ({new Date(v.created_at).toLocaleDateString()})
                                        {v.is_current ? ' - Current' : ''}
                                    </option>
                                ))}
                            </select>
                            {isLoading && (
                                <div style={{
                                    position: 'absolute',
                                    right: '8px',
                                    top: '50%',
                                    transform: 'translateY(-50%)',
                                    width: '16px',
                                    height: '16px',
                                    border: '2px solid var(--pico-primary)',
                                    borderTopColor: 'transparent',
                                    borderRadius: '50%',
                                    animation: 'spin 1s linear infinite'
                                }}/>
                            )}
                        </div>
                    </div>
                )}
            </header>

            {/* Version Info */}
            {selectedVersionDetail && (
                <p style={{ marginTop: '1rem' }}><small>
                    Version: {selectedVersionDetail.version_number}
                    {' | '}Created: {new Date(selectedVersionDetail.created_at).toLocaleString()}
                    {selectedVersionDetail.is_current && ' (Current)'}
                </small></p>
            )}

            {/* Version Notes */}
            {selectedVersionDetail?.notes && (
                <blockquote style={{
                    fontSize: '0.9em',
                    fontStyle: 'italic',
                    margin: '0 0 1rem 0',
                    paddingLeft: '1em',
                    borderLeft: '3px solid var(--pico-muted-border-color)'
                }}>
                    Notes: {selectedVersionDetail.notes}
                </blockquote>
            )}

            {/* Collapsible Decklist (Default Closed) */}
            <details open={false}>
                {isLoading && selectedVersionId && (
                    <div style={{ textAlign: 'center', padding: '1rem' }}>
                        <p aria-busy="true">Loading version...</p>
                    </div>
                )}
                <summary>View Decklist (Version {selectedVersionDetail?.version_number ?? 'N/A'})</summary>
                <pre style={{
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    maxHeight: '60vh',
                    overflowY: 'auto',
                    background: 'var(--pico-form-element-background-color)',
                    padding: '0.5rem',
                    border: '1px solid var(--pico-form-element-border-color)',
                    borderRadius: 'var(--pico-border-radius)',
                    fontSize: '0.85em',
                    marginTop: '0.5rem'
                }}>
                    <code>{selectedVersionDetail?.decklist_text || 'No decklist available for this version.'}</code>
                </pre>
            </details>

            {/* Game History */}
            <hr style={{ margin: '1.5rem 0' }}/>
            <h5>Game History (Overall for Deck)</h5>
            {/* Error handling */}
            {errorMessage && !deckHistory.length && (
                <p><small style={{ color: 'var(--pico-color-red-500)' }}>
                    {errorMessage.includes('history') ? errorMessage : 'Could not load game history.'}
                </small></p>
            )}
            {!errorMessage && deckHistory.length > 0 ? (
                <div style={{ maxHeight: '40vh', overflowY: 'auto' }}>
                    <table role="grid" style={{ margin: 0, fontSize: '0.9em' }}>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Placement</th>
                                <th>Version #</th>
                                <th>Game</th>
                            </tr>
                        </thead>
                        <tbody>
                            {deckHistory.map(hist => (
                                <tr key={hist.game_id}>
                                    <td>{new Date(hist.game_date + 'T00:00:00').toLocaleDateString()}</td>
                                    <td>{hist.placement ?? 'N/A'}</td>
                                    <td>{hist.version_number ?? 'N/A'}</td>
                                    <td><Link to={`/games?gameId=${hist.game_id}`}>View Game</Link></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                !errorMessage && <p><i>No game history found for this deck.</i></p>
            )}
        </article>
    );
}

export default DeckDetailPage;
