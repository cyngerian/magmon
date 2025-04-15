import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../apiClient';

interface User {
    id: number;
    username: string;
    email: string;
    avatar_url: string | null;
    must_change_password: boolean;
    last_login: string | null;
    is_admin: boolean;
}

interface ResetPasswordResponse {
    temp_password: string;
    expires_at: string;
}

function AdminUsersPage() {
    const navigate = useNavigate();
    const [users, setUsers] = useState<User[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);
    const [showResetModal, setShowResetModal] = useState(false);
    const [resetResult, setResetResult] = useState<ResetPasswordResponse | null>(null);

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

    // Fetch users
    useEffect(() => {
        const fetchUsers = async () => {
            try {
                const response = await apiClient.get<User[]>('/admin/users');
                setUsers(response.data);
                setError(null);
            } catch (error) {
                setError('Failed to load users');
                console.error('Error fetching users:', error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchUsers();
    }, []);

    const handleResetPassword = async (user: User) => {
        setSelectedUser(user);
        setShowResetModal(true);
        setResetResult(null);
    };

    const confirmResetPassword = async () => {
        if (!selectedUser) return;

        try {
            const response = await apiClient.post<ResetPasswordResponse>(
                `/admin/users/${selectedUser.id}/reset-password`
            );
            setResetResult(response.data);
        } catch (error) {
            setError('Failed to reset password');
            console.error('Error resetting password:', error);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    if (isLoading) {
        return <p aria-busy="true">Loading users...</p>;
    }

    if (error && !users.length) {
        return <p><small style={{ color: 'var(--pico-color-red-500)' }}>{error}</small></p>;
    }

    return (
        <article>
            <header>
                <h2>User Management</h2>
            </header>

            {/* User List */}
            <div style={{ marginTop: '1rem' }}>
                {users.map(user => (
                    <article key={user.id} style={{ padding: '1rem', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            {/* Avatar */}
                            {user.avatar_url ? (
                                <img
                                    src={`http://127.0.0.1:5004${user.avatar_url}`}
                                    alt={`${user.username}'s avatar`}
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
                                    justifyContent: 'center'
                                }}>?</div>
                            )}

                            {/* User Info */}
                            <div style={{ flexGrow: 1 }}>
                                <strong>{user.username}</strong>
                                <br />
                                <small>{user.email}</small>
                                {user.is_admin && (
                                    <span style={{ 
                                        marginLeft: '0.5rem',
                                        background: 'var(--pico-primary)',
                                        color: 'white',
                                        padding: '0.2em 0.5em',
                                        borderRadius: '4px',
                                        fontSize: '0.8em'
                                    }}>Admin</span>
                                )}
                            </div>

                            {/* Status & Actions */}
                            <div style={{ textAlign: 'right' }}>
                                <small>
                                    Last Login: {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                                </small>
                                <br />
                                <button
                                    className="outline"
                                    onClick={() => handleResetPassword(user)}
                                    style={{ marginTop: '0.5rem' }}
                                >
                                    Reset Password
                                </button>
                            </div>
                        </div>
                    </article>
                ))}
            </div>

            {/* Reset Password Modal */}
            {showResetModal && selectedUser && (
                <dialog open>
                    <article style={{ maxWidth: '400px', margin: 0 }}>
                        <header>
                            <h3>Reset Password</h3>
                        </header>
                        {!resetResult ? (
                            <>
                                <p>
                                    Are you sure you want to reset the password for <strong>{selectedUser.username}</strong>?
                                </p>
                                <p>
                                    This will:
                                    <ul>
                                        <li>Generate a temporary password</li>
                                        <li>Force a password change on next login</li>
                                        <li>Expire in 24 hours</li>
                                    </ul>
                                </p>
                                <footer>
                                    <button 
                                        className="secondary" 
                                        onClick={() => setShowResetModal(false)}
                                    >
                                        Cancel
                                    </button>
                                    <button 
                                        onClick={confirmResetPassword}
                                    >
                                        Reset Password
                                    </button>
                                </footer>
                            </>
                        ) : (
                            <>
                                <p>Temporary password generated for <strong>{selectedUser.username}</strong>:</p>
                                <div style={{ 
                                    background: 'var(--pico-background-color)',
                                    padding: '1rem',
                                    borderRadius: 'var(--pico-border-radius)',
                                    marginBottom: '1rem',
                                    fontFamily: 'monospace'
                                }}>
                                    {resetResult.temp_password}
                                </div>
                                <p><small>Expires: {new Date(resetResult.expires_at).toLocaleString()}</small></p>
                                <footer>
                                    <button
                                        className="secondary"
                                        onClick={() => copyToClipboard(resetResult.temp_password)}
                                    >
                                        Copy to Clipboard
                                    </button>
                                    <button 
                                        onClick={() => setShowResetModal(false)}
                                    >
                                        Close
                                    </button>
                                </footer>
                            </>
                        )}
                    </article>
                </dialog>
            )}
        </article>
    );
}

export default AdminUsersPage;