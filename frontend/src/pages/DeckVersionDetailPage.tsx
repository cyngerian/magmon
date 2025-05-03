import { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, Link } from 'react-router-dom';
import { getDeckDetails, getDeckVersion } from '../apiClient';

// --- Interfaces ---
interface DeckVersion {
  id: number;
  version_number: number;
  created_at: string;
  notes: string;
  decklist_text: string;
  is_current: boolean;
}

interface Deck {
  id: number;
  name: string;
  commander: string;
  colors: string;
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

function DeckVersionDetailPage({ loggedInUser }: { loggedInUser: User | null }) {
  const { deckId, versionId } = useParams<{ deckId: string; versionId: string }>();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [version, setVersion] = useState<DeckVersion | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDeckAndVersion = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch deck details
        const deckData = await getDeckDetails(Number(deckId));
        setDeck(deckData);
        
        // Fetch version details
        const versionData = await getDeckVersion(Number(deckId), Number(versionId));
        setVersion(versionData);
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching deck version details:', err);
        setError(axios.isAxiosError(err) && err.response 
          ? `Failed to load version details: ${err.response.data.error || err.message}` 
          : `Failed to load version details: ${(err as Error).message}`);
        setLoading(false);
      }
    };

    fetchDeckAndVersion();
  }, [deckId, versionId]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // Basic authorization check
  if (!loggedInUser) {
    return <p>Please log in to view deck version details.</p>;
  }

  if (loading) {
    return <p aria-busy="true">Loading version details...</p>;
  }

  if (error) {
    return <p><small style={{ color: 'var(--pico-color-red-500)' }}>{error}</small></p>;
  }

  if (!deck || !version) {
    return <p>Deck version not found.</p>;
  }

  return (
    <article>
      <header>
        <div style={{ float: 'right' }}>
          <Link to={`/decks/${deckId}/versions`} role="button" className="outline secondary" style={{ padding: '0.2em 0.6em', fontSize: '0.8em', marginRight: '0.5em' }}>
            Back to Versions
          </Link>
          <Link to={`/decks/${deckId}`} role="button" className="outline secondary" style={{ padding: '0.2em 0.6em', fontSize: '0.8em' }}>
            Back to Deck
          </Link>
        </div>
        <hgroup>
          <h3>{deck.name} - Version {version.version_number}</h3>
          <h4>Commander: {deck.commander} ({deck.colors || 'C'})</h4>
        </hgroup>
      </header>

      <div style={{ marginBottom: '1rem' }}>
        <p>
          <strong>Created:</strong> {formatDate(version.created_at)}
          {version.is_current && <span style={{ marginLeft: '1rem', color: 'var(--pico-color-primary)', fontWeight: 'bold' }}>Current Version</span>}
        </p>
        {version.notes && (
          <div>
            <strong>Version Notes:</strong>
            <p style={{ 
              background: 'var(--pico-form-element-background-color)', 
              padding: '0.5rem 1rem', 
              borderRadius: 'var(--pico-border-radius)',
              border: '1px solid var(--pico-form-element-border-color)'
            }}>
              {version.notes}
            </p>
          </div>
        )}
      </div>

      <label htmlFor="decklistVersionViewFull">Decklist:</label>
      <pre id="decklistVersionViewFull" style={{ 
        textAlign: 'left', 
        whiteSpace: 'pre-wrap', 
        wordBreak: 'break-word', 
        maxHeight: '60vh', 
        overflowY: 'auto', 
        background: 'var(--pico-form-element-background-color)', 
        padding: '1rem', 
        border: '1px solid var(--pico-form-element-border-color)', 
        borderRadius: 'var(--pico-border-radius)' 
      }}>
        <code>{version.decklist_text || 'No decklist provided for this version.'}</code>
      </pre>
    </article>
  );
}

export default DeckVersionDetailPage;
