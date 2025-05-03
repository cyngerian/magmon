// frontend/src/pages/ProfilePage.tsx
import React, { useState, useEffect, useCallback } from 'react'; // Import useCallback
import axios from 'axios'; // Keep for type guard
import apiClient from '../apiClient'; // Use configured apiClient (Retry 2)
// Removed apiClient import

// --- Interfaces ---
// Reuse User interface if defined globally, or redefine here
interface User { id: number; username: string; email: string; } // Basic User from App.tsx
interface UserProfile extends User {
    favorite_color: string | null;
    retirement_plane: string | null;
    avatar_url: string | null;
    registered_on: string;
}

// Interface for the PATCH response
interface ProfileUpdateResponse {
    message: string;
    profile: UserProfile;
}

// --- API Base URL ---
// TODO: Centralize API_BASE_URL
function ProfilePage({ loggedInUser }: { loggedInUser: User | null }) {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [message, setMessage] = useState(''); // For loading/error messages
    const [updateMessage, setUpdateMessage] = useState(''); // For update success/fail messages
    const [isUpdating, setIsUpdating] = useState(false);

    // Form state
    const [favoriteColor, setFavoriteColor] = useState('');
    const [retirementPlane, setRetirementPlane] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploadMessage, setUploadMessage] = useState('');
    const [isUploading, setIsUploading] = useState(false);

    // Define fetchProfile using useCallback *before* the useEffect that calls it
    const fetchProfile = useCallback(async () => {
        setIsLoading(true);
        setMessage('');
        setProfile(null); // Reset profile before fetching
        // TODO: Add proper authentication headers if/when JWT is implemented
        try {
            const response = await apiClient.get<UserProfile>(`/profile`); // Use apiClient, relative URL (Retry 2)
            // Only set the main profile state here
            const fetchedProfile = response.data;
            setProfile(fetchedProfile);
            // Initialize form state here again
            setFavoriteColor(fetchedProfile.favorite_color || '');
            setRetirementPlane(fetchedProfile.retirement_plane || '');
        } catch (error) {
            console.error("Error fetching profile:", error);
            setMessage(axios.isAxiosError(error) && error.response ? `Failed to load profile: ${error.response.data.error || error.message}` : `Failed to load profile: ${(error as Error).message}`); // Use axios.isAxiosError
            // setProfile(null); // Already reset above
        } finally {
            setIsLoading(false);
        }
    }, [/* No external dependencies needed here, API_BASE_URL is constant */]); // Add dependency array

    // Effect to fetch profile on load or when user changes
    useEffect(() => {
        // Only fetch if logged in (though route should protect this)
        if (loggedInUser) {
            fetchProfile(); // Call the memoized function
        } else {
            setIsLoading(false);
            setMessage("Please log in to view your profile.");
        }
    }, [loggedInUser, fetchProfile]); // Add fetchProfile to dependency array

    // Removed separate effect for form state initialization

    if (isLoading) {
        return <p aria-busy="true">Loading profile...</p>;
    }

    if (message) {
         return <p><small style={{ color: 'var(--pico-color-red-500)' }}>{message}</small></p>;
    }

    if (!profile) {
        // This case might happen briefly or if fetch fails silently
        return <p>Could not load profile data.</p>;
    }

    const handleProfileUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsUpdating(true);
        setUpdateMessage('');
        // TODO: Add proper authentication headers
        try {
            const payload = {
                favorite_color: favoriteColor || null, // Send null if empty
                retirement_plane: retirementPlane || null, // Send null if empty
            };
            // Use apiClient (Retry 2)
            const response = await apiClient.patch<ProfileUpdateResponse>(`/profile`, payload);
            // Access the profile data correctly
            setProfile(response.data.profile); // Update local profile state
            setFavoriteColor(response.data.profile.favorite_color || ''); // Re-sync form state
            setRetirementPlane(response.data.profile.retirement_plane || ''); // Re-sync form state
            setUpdateMessage('Profile updated successfully!');
        } catch (error) {
            console.error("Error updating profile:", error);
            setUpdateMessage(axios.isAxiosError(error) && error.response ? `Update failed: ${error.response.data.error || error.message}` : `Update failed: ${(error as Error).message}`); // Use axios.isAxiosError
        } finally {
            setIsUpdating(false);
        }
    };
    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files[0]) {
            setSelectedFile(event.target.files[0]);
            setUploadMessage(''); // Clear previous upload message
        } else {
            setSelectedFile(null);
        }
    };

    const handleAvatarUpload = async () => {
        if (!selectedFile) {
            setUploadMessage("Please select a file first.");
            return;
        }
        setIsUploading(true);
        setUploadMessage('');
        setUpdateMessage(''); // Clear profile update message

        const formData = new FormData();
        formData.append('avatar', selectedFile);

        // Auth headers added by interceptor
        try {
            const response = await apiClient.post<{ message: string, avatar_url: string }>(
                `/profile/avatar`, // Use apiClient, relative URL (Retry 2)
                formData,
                { headers: { 'Content-Type': 'multipart/form-data' } } // Keep multipart header
            );
            setUploadMessage(response.data.message);
            // Re-fetch profile data to get the updated URL and ensure consistency
            fetchProfile();
            setSelectedFile(null); // Clear file input selection
            // Clear the file input visually (find a better way if needed)
            const fileInput = document.getElementById('avatarUpload') as HTMLInputElement;
            if (fileInput) fileInput.value = '';

        } catch (error) {
            console.error("Error uploading avatar:", error);
            setUploadMessage(axios.isAxiosError(error) && error.response ? `Upload failed: ${error.response.data.error || error.message}` : `Upload failed: ${(error as Error).message}`); // Use axios.isAxiosError
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <section>
            <h3>Your Profile</h3>
            <article>
                <form onSubmit={handleProfileUpdate}>
                    <div className="grid">
                        {/* Left Column: Info */}
                        <section>
                            <p><strong>Username:</strong> {profile.username}</p>
                            <p><strong>Email:</strong> {profile.email}</p>
                            <p><strong>Registered:</strong> {new Date(profile.registered_on).toLocaleDateString()}</p>
                            <p><strong>Avatar:</strong> {profile.avatar_url ? <img src={`http://127.0.0.1:5004${profile.avatar_url}`} alt="Avatar" width="100" /> : 'Not set'}</p> {/* Use absolute URL */}
                            {/* Avatar Upload Section */}
                            <div className="form-group" style={{ marginTop: '1rem' }}>
                                <label htmlFor="avatarUpload">Upload New Avatar</label>
                                <input type="file" id="avatarUpload" accept="image/png, image/jpeg, image/gif" onChange={handleFileChange} />
                                <button type="button" onClick={handleAvatarUpload} disabled={!selectedFile || isUploading} aria-busy={isUploading} style={{ marginLeft: '1rem' }}>
                                    Upload Image
                                </button>
                                {uploadMessage && <p style={{marginTop: '0.5rem'}}><small style={{ color: uploadMessage.startsWith('Upload failed') ? 'var(--pico-color-red-500)' : 'var(--pico-color-green-500)' }}>{uploadMessage}</small></p>}
                            </div>
                        </section>
                        {/* Right Column: Editable Fields */}
                        <section>
                             <div className="form-group">
                                <label htmlFor="favoriteColor">Favorite Color</label>
                                <input
                                    type="text"
                                    id="favoriteColor"
                                    value={favoriteColor}
                                    onChange={(e) => setFavoriteColor(e.target.value)}
                                    placeholder="e.g., Blue, Izzet"
                                />
                            </div>
                             <div className="form-group">
                                <label htmlFor="retirementPlane">Retirement Plane</label>
                                <input
                                    type="text"
                                    id="retirementPlane"
                                    value={retirementPlane}
                                    onChange={(e) => setRetirementPlane(e.target.value)}
                                    placeholder="e.g., Zendikar, Ravnica"
                                />
                            </div>
                            <button type="submit" disabled={isUpdating} aria-busy={isUpdating}>Update Profile</button>
                            {updateMessage && <p style={{marginTop: '1rem'}}><small style={{ color: updateMessage.startsWith('Update failed') ? 'var(--pico-color-red-500)' : 'var(--pico-color-green-500)' }}>{updateMessage}</small></p>}
                        </section>
                    </div>
                </form>
            </article>
        </section>
    );
}

export default ProfilePage;