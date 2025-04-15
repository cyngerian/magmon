import React, { useState, useEffect } from 'react';
import axios from 'axios';
import apiClient from './apiClient';
import { Routes, Route, Link, Navigate, Outlet, useNavigate } from 'react-router-dom';
import './App.css';
import './custom.css';

// Import page components
import GamesPage from './pages/GamesPage';
import DeckManagementPage from './pages/DeckManagementPage';
import DeckDetailPage from './pages/DeckDetailPage';
import DeckVersionsPage from './pages/DeckVersionsPage';
import DeckVersionDetailPage from './pages/DeckVersionDetailPage';
import ProfilePage from './pages/ProfilePage';
import PlayersPage from './pages/PlayersPage';
import PlayerDetailPage from './pages/PlayerDetailPage';
import AdminUsersPage from './pages/AdminUsersPage';
import AdminGameManagementPage from './pages/AdminGameManagementPage';
import ChangePasswordModal from './components/ChangePasswordModal';

// --- Interfaces ---
interface User {
    id: number;
    username: string;
    email: string;
    is_admin?: boolean;
    must_change_password?: boolean;
}

// --- API Base URL ---
const API_BASE_URL = 'http://127.0.0.1:5004/api';

// --- Authentication Hook ---
// --- Authentication Hook --- (Retry)
// TODO: Consider storing token in memory or HttpOnly cookie for better security
const useAuth = () => {
    const [loggedInUser, setLoggedInUser] = useState<User | null>(() => {
        const storedUser = localStorage.getItem('loggedInUser');
        return storedUser ? JSON.parse(storedUser) : null;
    });
    const [accessToken, setAccessToken] = useState<string | null>(() => {
        return localStorage.getItem('accessToken');
    });

    const login = (user: User, token: string) => {
        setLoggedInUser(user);
        setAccessToken(token);
        localStorage.setItem('loggedInUser', JSON.stringify(user));
        localStorage.setItem('accessToken', token);
    };

    const logout = () => {
        setLoggedInUser(null);
        setAccessToken(null);
        localStorage.removeItem('loggedInUser');
        localStorage.removeItem('accessToken');
    };

    // Return token as well
    return { loggedInUser, accessToken, login, logout };
};

// --- Page Components (Login/Register remain simple) ---
// Reverted LoginPage props and logic
// Update LoginPage props and logic (Retry)
function LoginPage({ onLoginSuccess }: { onLoginSuccess: (user: User, token: string) => void }) {
    const [loginUsername, setLoginUsername] = useState('');
    const [loginPassword, setLoginPassword] = useState('');
    const [loginMessage, setLoginMessage] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoginMessage('');
        console.log('Login attempt:', { username: loginUsername }); // Debug log

        try {
            console.log('Making login request with headers:', {
                'Content-Type': 'application/json'
            }); // Debug log

            const response = await apiClient.post<{ access_token: string, refresh_token: string, user: User }>(
                '/login',
                {
                    username: loginUsername,
                    password: loginPassword
                },
                {
                    headers: {
                        'Content-Type': 'application/json'
                    }
                }
            );

            console.log('Login response:', {
                status: response.status,
                headers: response.headers,
                data: response.data
            }); // Debug log

            onLoginSuccess(response.data.user, response.data.access_token);
            navigate('/');
        } catch (error) {
            console.error('Login error details:', {
                error,
                isAxiosError: axios.isAxiosError(error),
                response: axios.isAxiosError(error) ? {
                    status: error.response?.status,
                    statusText: error.response?.statusText,
                    headers: error.response?.headers,
                    data: error.response?.data
                } : null,
                message: error instanceof Error ? error.message : String(error)
            }); // Detailed error logging

            setLoginMessage(axios.isAxiosError(error) && error.response
                ? `Login failed: ${error.response.data.error || error.message}`
                : `Login failed: ${(error as Error).message}`
            );
        }
    };

    return (
        <article>
            <hgroup>
                <h2>Login</h2>
                <h3>Access your account</h3>
            </hgroup>
            <form onSubmit={handleLogin}>
                <label htmlFor="loginUsername">Username</label>
                <input
                    type="text"
                    id="loginUsername"
                    value={loginUsername}
                    onChange={(e) => setLoginUsername(e.target.value)}
                    required
                />
                <label htmlFor="loginPassword">Password</label>
                <input
                    type="password"
                    id="loginPassword"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                />
                <button type="submit">Login</button>
            </form>
            {loginMessage && (
                <p><small style={{ color: 'var(--pico-color-red-500)' }}>{loginMessage}</small></p>
            )}
            <small>Don't have an account? <Link to="/register">Register here</Link></small>
        </article>
    );
}
function RegisterPage() {
  const [regUsername, setRegUsername] = useState(''); const [regEmail, setRegEmail] = useState(''); const [regPassword, setRegPassword] = useState(''); const [regMessage, setRegMessage] = useState(''); const navigate = useNavigate();
  const handleRegister = async (e: React.FormEvent) => { e.preventDefault(); setRegMessage(''); try { const response = await apiClient.post(`/register`, { username: regUsername, email: regEmail, password: regPassword }); setRegMessage(response.data.message || 'Registration successful! Please login.'); setRegUsername(''); setRegEmail(''); setRegPassword(''); setTimeout(() => navigate('/login'), 1500); } catch (error) { setRegMessage(axios.isAxiosError(error) && error.response ? `Registration failed: ${error.response.data.error || error.message}` : `Registration failed: ${(error as Error).message}`); } }; // Use apiClient
  return ( <article> <hgroup><h2>Register</h2><h3>Create a new account</h3></hgroup> <form onSubmit={handleRegister}> <label htmlFor="regUsername">Username</label> <input type="text" id="regUsername" value={regUsername} onChange={(e) => setRegUsername(e.target.value)} required /> <label htmlFor="regEmail">Email</label> <input type="email" id="regEmail" value={regEmail} onChange={(e) => setRegEmail(e.target.value)} required /> <label htmlFor="regPassword">Password</label> <input type="password" id="regPassword" value={regPassword} onChange={(e) => setRegPassword(e.target.value)} required /> <button type="submit">Register</button> </form> {regMessage && <p><small style={{ color: regMessage.startsWith('Registration failed') ? 'var(--pico-color-red-500)' : 'var(--pico-color-green-500)' }}>{regMessage}</small></p>} <small>Already have an account? <Link to="/login">Login here</Link></small> </article> );
}

// --- Layout Components ---
function DashboardLayout({ user, onLogout }: { user: User, onLogout: () => void }) {
    return (
        <>
            <nav>
                <ul>
                    <li><strong>MagMon</strong></li>
                </ul>
                <ul>
                    <li><Link to="/">Dashboard</Link></li>
                    <li><Link to="/games">Games</Link></li>
                    <li><Link to="/decks">Decks</Link></li>
                    <li><Link to="/players">Players</Link></li>
                    {user.is_admin && (
                        <>
                            <li><Link to="/admin/users">Users</Link></li>
                            <li><Link to="/admin/games">Games</Link></li>
                        </>
                    )}
                </ul>
                <ul>
                    <li>Welcome, {user.username}</li>
                    <li><Link to="/profile" role="button" className="secondary outline">Profile</Link></li>
                    <li><button onClick={onLogout} className="secondary outline contrast">Logout</button></li>
                </ul>
            </nav>
            <main className="container">
                <Outlet />
            </main>
        </>
    );
}
function DashboardHome() { return <h2>Dashboard</h2>; }

// --- Main App Component (Routing Logic) ---
function App() {
    const { loggedInUser, login, logout } = useAuth();
    const [showPasswordChange, setShowPasswordChange] = useState(false);

    // Check if user needs to change password
    useEffect(() => {
        if (loggedInUser?.must_change_password) {
            setShowPasswordChange(true);
        }
    }, [loggedInUser]);

    const handlePasswordChangeSuccess = (newTokens: { access_token: string; refresh_token: string }) => {
        if (loggedInUser) {
            // Update tokens and user info
            localStorage.setItem('accessToken', newTokens.access_token);
            
            // Update user object to remove must_change_password flag
            const updatedUser = {
                ...loggedInUser,
                must_change_password: false
            };
            login(updatedUser, newTokens.access_token);
            setShowPasswordChange(false);
        }
    };

    return (
        <>
            {showPasswordChange && loggedInUser && (
                <ChangePasswordModal
                    onSuccess={handlePasswordChangeSuccess}
                    onClose={loggedInUser.must_change_password ? undefined : () => setShowPasswordChange(false)}
                />
            )}
            
            <Routes>
                {/* Logged-in Routes */}
                <Route path="/" element={loggedInUser ? <DashboardLayout user={loggedInUser} onLogout={logout} /> : <Navigate to="/login" replace />}>
                    <Route index element={<DashboardHome />} />
                    <Route path="games" element={loggedInUser ? <GamesPage loggedInUser={loggedInUser} /> : <Navigate to="/login" replace />} />
                    {/* Define more specific route first */}
                    <Route path="decks/:deckId" element={loggedInUser ? <DeckDetailPage loggedInUser={loggedInUser} /> : <Navigate to="/login" replace />} />
                    <Route path="decks" element={loggedInUser ? <DeckManagementPage loggedInUser={loggedInUser} /> : <Navigate to="/login" replace />} />
                    <Route path="decks/:deckId/versions" element={loggedInUser ? <DeckVersionsPage loggedInUser={loggedInUser} /> : <Navigate to="/login" replace />} />
                    <Route path="decks/:deckId/versions/:versionId" element={loggedInUser ? <DeckVersionDetailPage loggedInUser={loggedInUser} /> : <Navigate to="/login" replace />} />
                    <Route path="profile" element={loggedInUser ? <ProfilePage loggedInUser={loggedInUser} /> : <Navigate to="/login" replace />} />
                    <Route path="players" element={loggedInUser ? <PlayersPage /> : <Navigate to="/login" replace />} />
                    <Route path="players/:userId" element={loggedInUser ? <PlayerDetailPage /> : <Navigate to="/login" replace />} />
                    {/* Admin Routes */}
                    {loggedInUser?.is_admin && (
                        <>
                            <Route path="admin/users" element={<AdminUsersPage />} />
                            <Route path="admin/games" element={<AdminGameManagementPage />} />
                        </>
                    )}
                </Route>
                {/* Public Routes */}
                <Route path="/login" element={!loggedInUser ? <LoginPage onLoginSuccess={login} /> : <Navigate to="/" replace />} />
                <Route path="/register" element={!loggedInUser ? <RegisterPage /> : <Navigate to="/" replace />} />
                {/* Catch-all */}
                <Route path="*" element={<Navigate to={loggedInUser ? "/" : "/login"} replace />} />
            </Routes>
        </>
    );
}

export default App;
