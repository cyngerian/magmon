import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../apiClient';

interface Game {
    id: number;
    game_date: string;
    deleted_at: string | null;
    deleted_by: {
        id: number;
        username: string;
    } | null;
    last_admin_action: string | null;
    last_admin_action_at: string | null;
}

interface AuditLogEntry {
    id: number;
    admin: {
        id: number;
        username: string;
    };
    action_type: string;
    previous_state: any;
    new_state: any;
    reason: string;
    created_at: string;
}

function AdminGameManagementPage() {
    const navigate = useNavigate();
    const [games, setGames] = useState<Game[]>([]);
    const [deletedGames, setDeletedGames] = useState<Game[]>([]);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [selectedGame, setSelectedGame] = useState<Game | null>(null);
    const [deleteReason, setDeleteReason] = useState('');
    const [showAuditLog, setShowAuditLog] = useState(false);
    const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Check admin access
    useEffect(() => {
        const checkAdmin = async () => {
            try {
                const response = await apiClient.get('/admin/check');
                if (!response.data.is_admin) {
                    navigate('/');
                }
            } catch (error) {
                navigate('/');
            }
        };
        checkAdmin();
    }, [navigate]);

    // Fetch games
    useEffect(() => {
        const fetchGames = async () => {
            try {
                // Fetch active games
                const gamesResponse = await apiClient.get('/games');
                setGames(gamesResponse.data);

                // Fetch deleted games
                const deletedGamesResponse = await apiClient.get('/admin/games/deleted');
                setDeletedGames(deletedGamesResponse.data);

                setError(null);
            } catch (error) {
                setError('Failed to load games');
                console.error('Error fetching games:', error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchGames();
    }, []);

    const handleDelete = async (game: Game) => {
        setSelectedGame(game);
        setShowDeleteModal(true);
        setDeleteReason('');
    };

    const confirmDelete = async () => {
        if (!selectedGame || !deleteReason.trim()) return;

        try {
            await apiClient.delete(`/admin/games/${selectedGame.id}`, {
                data: { reason: deleteReason }
            });
            
            // Refresh games lists
            const gamesResponse = await apiClient.get('/games');
            setGames(gamesResponse.data);
            const deletedGamesResponse = await apiClient.get('/admin/games/deleted');
            setDeletedGames(deletedGamesResponse.data);
            
            setShowDeleteModal(false);
            setSelectedGame(null);
            setDeleteReason('');
        } catch (error) {
            setError('Failed to delete game');
            console.error('Error deleting game:', error);
        }
    };

    const handleRestore = async (game: Game) => {
        try {
            await apiClient.post(`/admin/games/${game.id}/restore`, {
                reason: 'Administrative restoration'
            });
            
            // Refresh games lists
            const gamesResponse = await apiClient.get('/games');
            setGames(gamesResponse.data);
            const deletedGamesResponse = await apiClient.get('/admin/games/deleted');
            setDeletedGames(deletedGamesResponse.data);
        } catch (error) {
            setError('Failed to restore game');
            console.error('Error restoring game:', error);
        }
    };

    const viewAuditLog = async (game: Game) => {
        try {
            const response = await apiClient.get(`/admin/games/${game.id}/audit-log`);
            setAuditLogs(response.data);
            setShowAuditLog(true);
            setSelectedGame(game);
        } catch (error) {
            setError('Failed to load audit log');
            console.error('Error loading audit log:', error);
        }
    };

    if (isLoading) {
        return <p aria-busy="true">Loading games...</p>;
    }

    return (
        <article>
            <header>
                <h2>Game Management</h2>
            </header>

            {error && (
                <p><small style={{ color: 'var(--pico-color-red-500)' }}>{error}</small></p>
            )}

            {/* Active Games */}
            <section>
                <h3>Active Games</h3>
                {games.map(game => (
                    <article key={game.id} style={{ padding: '1rem', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <strong>Game {game.id}</strong>
                                <br />
                                <small>{new Date(game.game_date).toLocaleDateString()}</small>
                            </div>
                            <div>
                                <button 
                                    className="outline"
                                    onClick={() => viewAuditLog(game)}
                                >
                                    View History
                                </button>
                                <button 
                                    className="outline"
                                    onClick={() => handleDelete(game)}
                                    style={{ marginLeft: '0.5rem' }}
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    </article>
                ))}
            </section>

            {/* Deleted Games */}
            <section>
                <h3>Deleted Games</h3>
                {deletedGames.map(game => (
                    <article key={game.id} style={{ padding: '1rem', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <strong>Game {game.id}</strong>
                                <br />
                                <small>
                                    {new Date(game.game_date).toLocaleDateString()}
                                    <br />
                                    Deleted by {game.deleted_by?.username} on {new Date(game.deleted_at!).toLocaleString()}
                                </small>
                            </div>
                            <div>
                                <button 
                                    className="outline"
                                    onClick={() => viewAuditLog(game)}
                                >
                                    View History
                                </button>
                                <button 
                                    className="outline"
                                    onClick={() => handleRestore(game)}
                                    style={{ marginLeft: '0.5rem' }}
                                >
                                    Restore
                                </button>
                            </div>
                        </div>
                    </article>
                ))}
            </section>

            {/* Delete Modal */}
            {showDeleteModal && selectedGame && (
                <dialog open>
                    <article style={{ maxWidth: '400px', margin: 0 }}>
                        <header>
                            <h3>Delete Game</h3>
                        </header>
                        <p>
                            Are you sure you want to delete Game {selectedGame.id} from {new Date(selectedGame.game_date).toLocaleDateString()}?
                        </p>
                        <label htmlFor="deleteReason">
                            Reason
                            <input
                                type="text"
                                id="deleteReason"
                                value={deleteReason}
                                onChange={(e) => setDeleteReason(e.target.value)}
                                required
                            />
                        </label>
                        <footer>
                            <button 
                                className="secondary" 
                                onClick={() => {
                                    setShowDeleteModal(false);
                                    setSelectedGame(null);
                                    setDeleteReason('');
                                }}
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={confirmDelete}
                                disabled={!deleteReason.trim()}
                            >
                                Delete
                            </button>
                        </footer>
                    </article>
                </dialog>
            )}

            {/* Audit Log Modal */}
            {showAuditLog && selectedGame && (
                <dialog open>
                    <article style={{ maxWidth: '600px', margin: 0 }}>
                        <header>
                            <h3>Game {selectedGame.id} History</h3>
                        </header>
                        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                            {auditLogs.map(log => (
                                <div key={log.id} className="audit-log-entry" style={{ marginBottom: '1rem' }}>
                                    <p>
                                        <strong>{log.action_type}</strong> by {log.admin.username}
                                        <br />
                                        <small>{new Date(log.created_at).toLocaleString()}</small>
                                    </p>
                                    <p>Reason: {log.reason}</p>
                                    {(log.previous_state || log.new_state) && (
                                        <details>
                                            <summary>View Changes</summary>
                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                                <div>
                                                    <strong>Before:</strong>
                                                    <pre style={{ whiteSpace: 'pre-wrap' }}>
                                                        {JSON.stringify(log.previous_state, null, 2)}
                                                    </pre>
                                                </div>
                                                <div>
                                                    <strong>After:</strong>
                                                    <pre style={{ whiteSpace: 'pre-wrap' }}>
                                                        {JSON.stringify(log.new_state, null, 2)}
                                                    </pre>
                                                </div>
                                            </div>
                                        </details>
                                    )}
                                </div>
                            ))}
                        </div>
                        <footer>
                            <button 
                                onClick={() => {
                                    setShowAuditLog(false);
                                    setSelectedGame(null);
                                    setAuditLogs([]);
                                }}
                            >
                                Close
                            </button>
                        </footer>
                    </article>
                </dialog>
            )}
        </article>
    );
}

export default AdminGameManagementPage;