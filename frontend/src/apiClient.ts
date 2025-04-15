import axios from 'axios';

// Use environment variable for API Base URL, with fallback for local dev outside Docker
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5004/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable sending cookies
  timeout: 10000, // 10 second timeout
});

// Log all requests and responses for debugging
apiClient.interceptors.request.use(request => {
  console.log('Starting Request:', {
    url: request.url,
    method: request.method,
    headers: request.headers,
    data: request.data
  });
  return request;
});

apiClient.interceptors.response.use(
  response => {
    console.log('Response:', {
      status: response.status,
      headers: response.headers,
      data: response.data
    });
    return response;
  },
  error => {
    console.error('Response Error:', {
      message: error.message,
      response: error.response ? {
        status: error.response.status,
        headers: error.response.headers,
        data: error.response.data
      } : null
    });
    return Promise.reject(error);
  }
);

// Request interceptor to add the auth token header (Retry)
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log("Interceptor: Sending token:", token); // DEBUG LOG
    } else {
      console.log("Interceptor: No token found in localStorage."); // DEBUG LOG
    }
    console.log("Interceptor: Sending headers:", config.headers); // DEBUG LOG
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling 401 errors (token expired)
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // If the error is 401 (Unauthorized) and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // For now, let's just redirect to login page since we don't have a refresh token endpoint
        console.log("Token expired. Redirecting to login...");
        localStorage.removeItem('accessToken');
        localStorage.removeItem('loggedInUser');
        window.location.href = '/login';
        return Promise.reject(error);
      } catch (refreshError) {
        console.error("Error refreshing token:", refreshError);
        // Clear auth data and redirect to login
        localStorage.removeItem('accessToken');
        localStorage.removeItem('loggedInUser');
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }
    
    return Promise.reject(error);
  }
);

// Helper function for making API requests
const apiRequest = async (method: string, url: string, data?: any) => {
  try {
    const response = await apiClient({
      method,
      url,
      data,
    });
    return response.data;
  } catch (error) {
    console.error(`API ${method} request to ${url} failed:`, error);
    throw error;
  }
};

// Auth-related API calls
export const registerUser = async (userData: any) => {
  return await apiRequest('POST', '/register', userData);
};

export const loginUser = async (credentials: any) => {
  return await apiRequest('POST', '/login', credentials);
};

// User-related API calls
export const getUsers = async () => {
  return await apiRequest('GET', '/users');
};

export const getUserProfile = async (userId: number) => {
  return await apiRequest('GET', `/users/${userId}`);
};

export const getMyProfile = async () => {
  return await apiRequest('GET', '/profile');
};

export const updateMyProfile = async (profileData: any) => {
  return await apiRequest('PATCH', '/profile', profileData);
};

export const uploadAvatar = async (formData: FormData) => {
  try {
    const token = localStorage.getItem('accessToken');
    const response = await axios.post(`${API_BASE_URL}/profile/avatar`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: token ? `Bearer ${token}` : '',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading avatar:', error);
    throw error;
  }
};

// Deck-related API calls
export const createDeck = async (deckData: any) => {
  return await apiRequest('POST', '/decks', deckData);
};

export const getUserDecks = async () => {
  return await apiRequest('GET', '/decks');
};

export const getUserDecksByUserId = async (userId: number) => {
  return await apiRequest('GET', `/users/${userId}/decks`);
};

export const getDeckDetails = async (deckId: number) => {
  return await apiRequest('GET', `/decks/${deckId}`);
};

export const getDeckHistory = async (deckId: number) => {
  return await apiRequest('GET', `/decks/${deckId}/history`);
};

// Deck version-related API calls
export const getDeckVersions = async (deckId: number) => {
  return await apiRequest('GET', `/decks/${deckId}/versions`);
};

export const getDeckVersion = async (deckId: number, versionId: number) => {
  return await apiRequest('GET', `/decks/${deckId}/versions/${versionId}`);
};

export const createDeckVersion = async (deckId: number, versionData: any) => {
  return await apiRequest('POST', `/decks/${deckId}/versions`, versionData);
};

// Game-related API calls
export const createGame = async (gameData: any) => {
  return await apiRequest('POST', '/games', gameData);
};

export const getGames = async (status?: string) => {
  const url = status ? `/games?status=${status}` : '/games';
  return await apiRequest('GET', url);
};

export const updateGameStatus = async (gameId: number, statusData: any) => {
  return await apiRequest('PATCH', `/games/${gameId}`, statusData);
};

export const registerForGame = async (gameId: number, registrationData: any) => {
  return await apiRequest('POST', `/games/${gameId}/registrations`, registrationData);
};

export const getGameRegistrations = async (gameId: number) => {
  return await apiRequest('GET', `/games/${gameId}/registrations`);
};

export const unregisterFromGame = async (gameId: number) => {
  return await apiRequest('DELETE', `/games/${gameId}/registrations`);
};

// Match-related API calls
export const submitMatch = async (matchData: any) => {
  return await apiRequest('POST', '/matches', matchData);
};

export const getMatches = async (status?: string) => {
  const url = status ? `/matches?status=${status}` : '/matches';
  return await apiRequest('GET', url);
};

export const getMatchDetails = async (matchId: number) => {
  return await apiRequest('GET', `/matches/${matchId}`);
};

export const approveMatch = async (matchId: number, approvalData: any) => {
  return await apiRequest('PATCH', `/matches/${matchId}/approve`, approvalData);
};

export const rejectMatch = async (matchId: number, rejectionData: any) => {
  return await apiRequest('PATCH', `/matches/${matchId}/reject`, rejectionData);
};

export default apiClient;
