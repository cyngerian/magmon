// frontend/src/pages/PlayersPage.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios'; // Keep for type guard
import apiClient from '../apiClient'; // Use configured apiClient (Retry 2)
// Removed apiClient import
import { Link } from 'react-router-dom';

// --- Interfaces ---
// Define a simpler User interface for the list, including profile fields
interface UserListItem {
    id: number;
    username: string;
    avatar_url: string | null;
    stats: {
        total_wins: number;
    };
}

// --- API Base URL ---
// TODO: Centralize API_BASE_URL
const API_BASE_URL = 'http://127.0.0.1:5004/api';

function PlayersPage() {
    const [players, setPlayers] = useState<UserListItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [message, setMessage] = useState('');

    useEffect(() => {
        const fetchPlayers = async () => {
            setIsLoading(true);
            setMessage('');
            try {
                // Use the updated /api/users endpoint which includes profile fields
                const response = await apiClient.get<UserListItem[]>(`/users`); // Use apiClient, relative URL (Retry 2)
                setPlayers(response.data);
            } catch (error) {
                console.error("Error fetching players:", error);
                setMessage(axios.isAxiosError(error) && error.response ? `Failed to load players: ${error.response.data.error || error.message}` : `Failed to load players: ${(error as Error).message}`); // Use axios.isAxiosError
                setPlayers([]); // Clear players on error
            } finally {
                setIsLoading(false);
            }
        };

        fetchPlayers();
    }, []); // Fetch only on component mount

    if (isLoading) {
        return <p aria-busy="true">Loading players...</p>;
    }

    if (message) {
         return <p><small style={{ color: 'var(--pico-color-red-500)' }}>{message}</small></p>;
    }

    return (
        <section>
            <h3>Players</h3>
            {players.length > 0 ? (
                // Use CSS Grid for 2 columns
                <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    {players.map(player => {
                        return (
                            // Player Tile as an article
                            <article key={player.id} className="player-tile">
                                {/* Avatar Div */}
                                <div className="player-tile-avatar">
                                    {player.avatar_url ? (
                                        <img
                                            src={`http://127.0.0.1:5004${player.avatar_url}`}
                                            alt={`${player.username} avatar`}
                                        />
                                    ) : (
                                        <div className="player-tile-avatar-placeholder">?</div>
                                    )}
                                </div>
                                {/* Player Info Div */}
                                <div className="player-tile-info">
                                    <h5> {/* Reduced heading size */}
                                        <Link to={`/players/${player.id}`}>{player.username}</Link>
                                    </h5>
                                    <p><small>Wins: {player.stats?.total_wins ?? 0}</small></p>
                                </div>
                            </article>
                        );
                    })}
                </div>
            ) : (
                <p>No players found.</p>
            )}
        </section>
    );
}

export default PlayersPage;