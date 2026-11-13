import { useState } from 'react';
import ArticleInput from '../components/ArticleInput';
import ResultCard from '../components/ResultCard';
import CommunityFeed from '../components/CommunityFeed';
import { analyzeArticle, analyzeFile } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export default function DetectPage({ onSignIn }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { user } = useAuth();

  const handleAnalyze = async (text, file, inputType = 'text', contentType = 'auto') => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      let data;

      if (file) {
        // File upload mode
        data = await analyzeFile(file);
      } else {
        // Text/URL mode
        data = await analyzeArticle(text, inputType, contentType);
      }

      setResult(data);
    } catch (err) {
      setError(err.message || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="detect-page">
      <div className="detect-main">
        {user ? <ArticleInput onAnalyze={handleAnalyze} loading={loading} /> : <section className="guest-lock">
          <h1 className="hero-title">Veritas<span style={{ color: '#f87171' }}>AI</span></h1>
          <p className="hero-subtitle">Retrieval-augmented misinformation verification. Extract claims, retrieve evidence, and get explainable verdicts.</p>
          <h2>Sign in to verify claims</h2>
          <p>Create an account or sign in to use text, URL, and file verification. The global live detection feed remains visible.</p>
          <button className="btn-primary" onClick={onSignIn}>Sign in or create an account</button>
        </section>}
        {error && <div className="error-banner">⚠️ {error}</div>}
        {user && <ResultCard result={result} />}
      </div>
      <CommunityFeed />
    </div>
  );
}
