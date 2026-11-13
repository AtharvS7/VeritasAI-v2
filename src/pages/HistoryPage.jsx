import { useEffect, useState } from 'react';
import { getSearchHistory } from '../lib/api';

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    getSearchHistory().then(setItems).catch(err => setError(err.message)).finally(() => setLoading(false));
  }, []);
  return <div className="page-container history-page">
    <div className="page-header"><h1 className="page-title">Your Search History</h1><p className="page-subtitle">Private verification searches from your account</p></div>
    {loading ? <div className="loading-state">Loading your searches…</div> : error ? <div className="error-banner">{error}</div> : items.length === 0 ? <div className="empty-state"><h3>No searches yet</h3><p>Your verifications will appear here after you analyze a claim.</p></div> : <div className="history-list">
      {items.map(item => <article className="history-card" key={item.id}>
        <div className="history-card-top"><span className="history-verdict">{item.verdict || 'Analysis complete'}</span><time>{new Date(item.created_at).toLocaleString()}</time></div>
        <p>{item.input_text}</p>
        {item.confidence != null && <small>Confidence: {item.confidence}% · {item.source_type}</small>}
        {!!item.result?.claims?.length && <details><summary>View analysis details</summary><pre>{JSON.stringify(item.result, null, 2)}</pre></details>}
      </article>)}
    </div>}
  </div>;
}
