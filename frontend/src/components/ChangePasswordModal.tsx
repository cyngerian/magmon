import React, { useState } from 'react';
import apiClient from '../apiClient';

interface ChangePasswordModalProps {
    onSuccess: (newTokens: { access_token: string; refresh_token: string }) => void;
    onClose?: () => void;
}

function ChangePasswordModal({ onSuccess, onClose }: ChangePasswordModalProps) {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (newPassword !== confirmPassword) {
            setError('New passwords do not match');
            return;
        }

        if (newPassword.length < 8) {
            setError('New password must be at least 8 characters long');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await apiClient.post('/change-password', {
                current_password: currentPassword,
                new_password: newPassword
            });

            onSuccess({
                access_token: response.data.access_token,
                refresh_token: response.data.refresh_token
            });
        } catch (error: any) {
            setError(error.response?.data?.error || 'Failed to change password');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <dialog open>
            <article style={{ maxWidth: '400px', margin: 0 }}>
                <header>
                    <h3>Change Password Required</h3>
                </header>
                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '1rem' }}>
                        <label htmlFor="currentPassword">
                            Current Password
                            <input
                                type="password"
                                id="currentPassword"
                                value={currentPassword}
                                onChange={(e) => setCurrentPassword(e.target.value)}
                                required
                                autoComplete="current-password"
                            />
                        </label>
                    </div>
                    <div style={{ marginBottom: '1rem' }}>
                        <label htmlFor="newPassword">
                            New Password
                            <input
                                type="password"
                                id="newPassword"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                required
                                autoComplete="new-password"
                                minLength={8}
                            />
                        </label>
                    </div>
                    <div style={{ marginBottom: '1rem' }}>
                        <label htmlFor="confirmPassword">
                            Confirm New Password
                            <input
                                type="password"
                                id="confirmPassword"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                                autoComplete="new-password"
                            />
                        </label>
                    </div>
                    {error && (
                        <p style={{ color: 'var(--pico-color-red-500)' }}>
                            <small>{error}</small>
                        </p>
                    )}
                    <footer>
                        {onClose && (
                            <button
                                type="button"
                                className="secondary"
                                onClick={onClose}
                                disabled={isLoading}
                            >
                                Cancel
                            </button>
                        )}
                        <button
                            type="submit"
                            aria-busy={isLoading}
                            disabled={isLoading}
                        >
                            Change Password
                        </button>
                    </footer>
                </form>
            </article>
        </dialog>
    );
}

export default ChangePasswordModal;