import { useEffect, useState, useCallback } from 'react';
import { getSavedQueries } from '../context/api';
import './SavedQueriesPage.css';

/**
 * Screen 8 — Saved Queries
 * Spec: Section 6 Screen 8
 * Clicking a card runs its query through Processing.
 */
export default function SavedQueriesPage({ onRerun }) {
  const [cards, setCards]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    setLoading(true);
    // TODO: replace mock with real API call
    getSavedQueries()
      .then((data) => { setCards(data); setLoading(false); })
      .catch((e)   => { setError(e.message || 'Failed to load saved queries'); setLoading(false); });
  }, []);

  const handleCardClick = useCallback((card) => {
    if (typeof onRerun === 'function') {
      onRerun(card.query);
    } else {
      sessionStorage.setItem('qm_rerun_query', card.query);
      window.location.href = '/workspace';
    }
  }, [onRerun]);

  return (
    <div className="saved-viewport">
      <header className="saved-header">
        <h2>Saved Queries</h2>
        <p>Quick-access queries — click to run</p>
      </header>

      <div className="saved-grid">
        {loading && (
          <span style={{ color: 'rgba(224,224,230,0.32)', fontSize: 13, padding: '20px 0' }}>Loading…</span>
        )}
        {error && (
          <span style={{ color: '#e74c3c', fontSize: 13, padding: '20px 0' }}>{error}</span>
        )}
        {!loading && !error && cards.map((card, i) => (
          <button
            key={card.id}
            type="button"
            className="saved-card"
            style={{ animation: `slideUp 0.4s ease-out ${i * 0.06}s both` }}
            onClick={() => handleCardClick(card)}
          >
            <div className="saved-card-top">
              <span className="saved-card-name">{card.title}</span>
              <svg className="saved-card-arrow" viewBox="0 0 14 14" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 7h10M8 3l4 4-4 4" />
              </svg>
            </div>
            <p className="saved-card-query">{card.query}</p>
            <div className="saved-card-footer">
              <span className="saved-card-collection">{card.collection}</span>
              <span className="saved-card-date">{card.date}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
