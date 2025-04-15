import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import apiClient from '../apiClient';
import { getDeckDetails, getDeckVersions, createDeckVersion } from '../apiClient';

// --- Interfaces ---
interface DeckVersion {
  id: number;
  version_number: number;
  created_at: string;
  notes: string;
  is_current: boolean;
}

interface Deck {
  id: number;
  name: string;
  commander: string;
  colors: string;
  decklist_text: string;
  user_id: number;
  created_at: string;
  last_updated: string;
  current_version_id: number;
}

interface User { 
  id: number; 
  username: string; 
  email: string; 
}

const DeckVersionsPage = ({ loggedInUser }: { loggedInUser: User | null }) => {
  const { deckId } = useParams<{ deckId: string }>();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [versions, setVersions] = useState<DeckVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openNewVersionDialog, setOpenNewVersionDialog] = useState(false);
  const [newVersionData, setNewVersionData] = useState({
    decklist_text: '',
    notes: ''
  });

  useEffect(() => {
    const fetchDeckAndVersions = async () => {
      try {
        setLoading(true);
        const deckData = await getDeckDetails(Number(deckId));
        setDeck(deckData);
        
        const versionsData = await getDeckVersions(Number(deckId));
        setVersions(versionsData);
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching deck versions:', err);
        setError(axios.isAxiosError(err) && err.response 
          ? `Failed to load deck versions: ${err.response.data.error || err.message}` 
          : `Failed to load deck versions: ${(err as Error).message}`);
        setLoading(false);
      }
    };

    fetchDeckAndVersions();
  }, [deckId]);

  const handleOpenNewVersionDialog = () => {
    if (deck) {
      setNewVersionData({
        decklist_text: deck.decklist_text,
        notes: ''
      });
    }
    setOpenNewVersionDialog(true);
  };

  const handleCloseNewVersionDialog = () => {
    setOpenNewVersionDialog(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setNewVersionData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreateVersion = async () => {
    try {
      await createDeckVersion(Number(deckId), newVersionData);
      
      // Refresh versions list
      const versionsData = await getDeckVersions(Number(deckId));
      setVersions(versionsData);
      
      // Refresh deck details to get updated current_version_id
      const deckData = await getDeckDetails(Number(deckId));
      setDeck(deckData);
      
      handleCloseNewVersionDialog();
    } catch (err) {
      console.error('Error creating new version:', err);
      setError(axios.isAxiosError(err) && err.response 
        ? `Failed to create new version: ${err.response.data.error || err.message}` 
        : `Failed to create new version: ${(err as Error).message}`);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // Basic authorization check
  if (!loggedInUser) {
    return <p>Please log in to view deck versions.</p>;
  }

  if (loading) {
    return <p aria-busy="true">Loading deck versions...</p>;
  }

  if (error) {
    return <p><small style={{ color: 'var(--pico-color-red-500)' }}>{error}</small></p>;
  }

  if (!deck) {
    return <p>Deck not found.</p>;
  }

  return (
    <article>
      <header>
        <Link to={`/decks/${deckId}`} role="button" className="outline secondary" style={{ padding: '0.2em 0.6em', fontSize: '0.8em', float: 'right' }}>
          Back to Deck
        </Link>
        <hgroup>
          <h3>Versions of {deck.name}</h3>
          <h4>Commander: {deck.commander} ({deck.colors || 'C'})</h4>
        </hgroup>
      </header>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
        <button onClick={handleOpenNewVersionDialog} className="primary">
          Create New Version
        </button>
      </div>

      {versions.length === 0 ? (
        <p><i>No versions found for this deck.</i></p>
      ) : (
        <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
          <table role="grid">
            <thead>
              <tr>
                <th>Version</th>
                <th>Created</th>
                <th>Notes</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {versions.map((version) => (
                <tr key={version.id} style={version.is_current ? { backgroundColor: 'var(--pico-primary-background)' } : {}}>
                  <td>{version.version_number}</td>
                  <td>{formatDate(version.created_at)}</td>
                  <td>{version.notes}</td>
                  <td>{version.is_current ? 'Current' : ''}</td>
                  <td>
                    <Link to={`/decks/${deckId}/versions/${version.id}`} role="button" className="outline secondary" style={{ padding: '0.2em 0.6em', fontSize: '0.8em' }}>
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* New Version Dialog - Using a modal */}
      {openNewVersionDialog && (
        <dialog open>
          <article>
            <header>
              <h3>Create New Version</h3>
            </header>
            <div>
              <label htmlFor="versionNotes">Version Notes</label>
              <textarea
                id="versionNotes"
                name="notes"
                placeholder="Describe what changes you made in this version"
                rows={2}
                value={newVersionData.notes}
                onChange={handleInputChange}
              ></textarea>
              
              <label htmlFor="decklistText">Decklist</label>
              <textarea
                id="decklistText"
                name="decklist_text"
                rows={15}
                value={newVersionData.decklist_text}
                onChange={handleInputChange}
              ></textarea>
            </div>
            <footer>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button onClick={handleCloseNewVersionDialog} className="secondary">
                  Cancel
                </button>
                <button onClick={handleCreateVersion} className="primary">
                  Create Version
                </button>
              </div>
            </footer>
          </article>
        </dialog>
      )}
    </article>
  );
};

export default DeckVersionsPage;
