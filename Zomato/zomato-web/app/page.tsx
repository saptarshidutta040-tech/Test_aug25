'use client';

import { useState, useRef } from 'react';
import { SearchQuery, RecommendResponse, Restaurant } from '@/lib/types';

// ── Budget pill ───────────────────────────────────────────────────────────────
function BudgetPill({ label, value, selected, onClick }: {
  label: string; value: string; selected: boolean; onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex-1 text-center py-xs rounded-lg text-label-md font-label transition-all ${
        selected
          ? 'glow-active'
          : 'text-on-surface-variant hover:text-on-surface'
      }`}
    >
      {label}
    </button>
  );
}

// ── Shimmer skeleton ──────────────────────────────────────────────────────────
function ResultsSkeleton() {
  return (
    <div className="w-full fade-in-up">
      <div className="flex items-center gap-sm mb-md">
        <div className="shimmer h-8 w-56 rounded-lg" />
        <div className="flex-grow h-px bg-primary/20" />
      </div>
      <div className="flex flex-col lg:flex-row gap-lg">
        <div className="flex-[3] glass-panel rounded-xl p-md flex flex-col gap-sm">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="shimmer h-5 rounded" style={{ width: `${85 - i * 8}%` }} />
          ))}
          <div className="mt-sm flex flex-col gap-sm">
            {[1, 2, 3].map(i => (
              <div key={i} className="pl-sm border-l-2 border-primary/30 p-sm rounded-r-lg flex flex-col gap-xs">
                <div className="shimmer h-5 w-40 rounded" />
                <div className="shimmer h-4 w-full rounded" />
                <div className="shimmer h-4 w-3/4 rounded" />
              </div>
            ))}
          </div>
        </div>
        <div className="flex-[2] glass-panel rounded-xl p-md">
          <div className="shimmer h-5 w-44 rounded mb-sm" />
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex gap-sm py-sm border-b border-white/5">
              <div className="shimmer h-4 w-6 rounded" />
              <div className="shimmer h-4 flex-1 rounded" />
              <div className="shimmer h-4 w-12 rounded" />
              <div className="shimmer h-4 w-16 rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Candidates table ──────────────────────────────────────────────────────────
function CandidatesTable({ candidates }: { candidates: Restaurant[] }) {
  return (
    <div className="flex-[2] glass-panel rounded-xl p-md overflow-hidden flex flex-col">
      <h3 className="text-label-md font-label text-on-surface mb-sm flex items-center gap-xs">
        <span className="material-symbols-outlined text-primary opacity-80" style={{ fontSize: 16 }}>list_alt</span>
        Filtered Candidates
      </h3>
      <div className="overflow-x-auto overflow-y-auto max-h-[420px]">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="text-label-sm font-label text-primary border-b border-primary/20 sticky top-0 bg-surface-container">
              <th className="py-xs pr-xs w-8">#</th>
              <th className="py-xs px-xs">Name</th>
              <th className="py-xs px-xs text-center">Rating</th>
              <th className="py-xs px-xs text-right">Cost/2</th>
              <th className="py-xs px-xs text-center hidden sm:table-cell">Order</th>
            </tr>
          </thead>
          <tbody className="text-label-md font-label text-on-surface">
            {candidates.map((r, i) => (
              <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                <td className="py-sm pr-xs text-on-surface-variant">{i + 1}</td>
                <td className="py-sm px-xs font-semibold">
                  {r.name.length > 22 ? r.name.slice(0, 20) + '…' : r.name}
                </td>
                <td className="py-sm px-xs text-center text-primary drop-shadow-[0_0_2px_rgba(125,211,252,0.5)]">
                  {r.rating.toFixed(1)} ⭐
                </td>
                <td className="py-sm px-xs text-right">₹{r.cost_for_two.toLocaleString()}</td>
                <td className="py-sm px-xs text-center hidden sm:table-cell">
                  {r.online_order ? '✅' : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── AI response renderer ──────────────────────────────────────────────────────
function AIResponse({ text }: { text: string }) {
  // Split into paragraphs and highlight restaurant names
  const highlighted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^(\d+\.\s)/gm, '<span class="text-primary font-bold">$1</span>');

  return (
    <div
      className="flex-[3] text-body-md leading-[1.8] text-on-surface-variant glass-panel rounded-xl p-md ai-response overflow-y-auto max-h-[520px]"
      dangerouslySetInnerHTML={{ __html: highlighted.split('\n').map(line =>
        line.trim() ? `<p>${line}</p>` : ''
      ).join('') }}
    />
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function HomePage() {
  const [location, setLocation]     = useState('');
  const [cuisine, setCuisine]       = useState('');
  const [budget, setBudget]         = useState<'low' | 'medium' | 'high'>('medium');
  const [minRating, setMinRating]   = useState(4.0);
  const [extras, setExtras]         = useState('');

  const [loading, setLoading]       = useState(false);
  const [result, setResult]         = useState<RecommendResponse | null>(null);
  const [error, setError]           = useState<string | null>(null);

  const resultsRef = useRef<HTMLDivElement>(null);

  async function handleSearch() {
    if (!location.trim()) {
      setError('Please enter a location to search.');
      return;
    }

    setLoading(true);
    setResult(null);
    setError(null);

    const query: SearchQuery = {
      location: location.trim(),
      cuisine: cuisine.trim(),
      budget,
      min_rating: minRating,
      extras: extras.trim(),
    };

    try {
      const res = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(query),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error || 'Something went wrong. Please try again.');
      } else {
        setResult(data);
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    } catch {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Radial glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-3xl h-96 bg-[radial-gradient(ellipse_at_top,rgba(125,211,252,0.1)_0%,transparent_70%)] pointer-events-none z-0" />

      {/* ── SECTION 1: HERO + SEARCH ──────────────────────────────────────── */}
      <section className="relative z-10 w-full flex flex-col items-center mb-xl">

        {/* Heading */}
        <div className="flex flex-col items-center mb-lg text-center">
          <span className="inline-flex items-center gap-xs px-sm py-xs rounded-full glass-panel text-primary text-label-sm font-label mb-md">
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>auto_awesome</span>
            AI-Powered
          </span>
          <h1 className="text-headline-lg-mobile md:text-headline-lg font-headline text-on-surface drop-shadow-md">
            Find Your Perfect Restaurant
          </h1>
          <p className="text-on-surface-variant text-body-md mt-sm max-w-lg">
            Describe what you want and our AI will recommend the best matches from 9,200+ Zomato restaurants.
          </p>
        </div>

        {/* Search Card */}
        <div className="w-full max-w-[780px] glass-panel rounded-xl p-md md:p-lg">
          <div className="flex flex-col gap-md">

            {/* Row 1: Location + Cuisine */}
            <div className="flex flex-col md:flex-row gap-md">
              <div className="flex-1 flex items-center glass-input rounded-xl px-sm py-base">
                <span className="material-symbols-outlined text-primary mr-xs opacity-70">location_on</span>
                <input
                  type="text"
                  value={location}
                  onChange={e => setLocation(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSearch()}
                  placeholder="e.g. Koramangala, Bangalore"
                  className="w-full bg-transparent border-none focus:ring-0 text-on-surface text-body-md placeholder-on-surface-variant/50 p-0"
                />
              </div>
              <div className="flex-1 flex items-center glass-input rounded-xl px-sm py-base">
                <span className="material-symbols-outlined text-primary mr-xs opacity-70">restaurant</span>
                <input
                  type="text"
                  value={cuisine}
                  onChange={e => setCuisine(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSearch()}
                  placeholder="e.g. Italian, Chinese (optional)"
                  className="w-full bg-transparent border-none focus:ring-0 text-on-surface text-body-md placeholder-on-surface-variant/50 p-0"
                />
              </div>
            </div>

            {/* Row 2: Budget + Rating */}
            <div className="flex flex-col md:flex-row gap-md items-center">
              <div className="flex-1 w-full flex justify-between glass-input rounded-xl p-xs">
                <BudgetPill label="LOW"    value="low"    selected={budget === 'low'}    onClick={() => setBudget('low')} />
                <BudgetPill label="MEDIUM" value="medium" selected={budget === 'medium'} onClick={() => setBudget('medium')} />
                <BudgetPill label="HIGH"   value="high"   selected={budget === 'high'}   onClick={() => setBudget('high')} />
              </div>
              <div className="flex-1 w-full flex flex-col gap-xs px-sm">
                <div className="flex justify-between items-center text-label-sm font-label text-on-surface-variant">
                  <span>Min Rating</span>
                  <span className="text-primary font-bold drop-shadow-[0_0_4px_rgba(125,211,252,0.3)]">
                    {minRating.toFixed(1)} ⭐
                  </span>
                </div>
                <input
                  type="range"
                  min="0" max="5" step="0.1"
                  value={minRating}
                  onChange={e => setMinRating(parseFloat(e.target.value))}
                />
              </div>
            </div>

            {/* Row 3: Special Requests */}
            <div className="w-full flex items-center glass-input rounded-xl px-sm py-base">
              <span className="material-symbols-outlined text-primary mr-xs opacity-70">auto_awesome</span>
              <input
                type="text"
                value={extras}
                onChange={e => setExtras(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                placeholder="e.g. rooftop, live music, family-friendly (optional)"
                className="w-full bg-transparent border-none focus:ring-0 text-on-surface text-body-md placeholder-on-surface-variant/50 p-0"
              />
            </div>

            {/* Error */}
            {error && (
              <div className="glass-panel border border-error/30 text-error text-label-md p-sm rounded-xl flex items-center gap-xs">
                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>warning</span>
                {error}
              </div>
            )}

            {/* CTA */}
            <button
              onClick={handleSearch}
              disabled={loading}
              className={`mt-sm w-full h-[56px] rounded-xl bg-primary-container/80 hover:bg-primary-container text-primary font-headline text-[18px] border border-primary/30 flex items-center justify-center gap-xs transition-all shadow-[0_4px_12px_rgba(14,77,110,0.3)] hover:shadow-[0_0_20px_rgba(125,211,252,0.2)] backdrop-blur-md active:scale-[0.98] ${loading ? 'loading-pulse' : ''}`}
            >
              <span className={`material-symbols-outlined ${loading ? 'animate-spin' : ''}`}>
                {loading ? 'autorenew' : 'search'}
              </span>
              {loading ? 'Searching…' : 'Find Restaurants'}
            </button>
          </div>
        </div>
      </section>

      {/* ── SECTION 2: RESULTS ────────────────────────────────────────────── */}
      <div ref={resultsRef}>
        {loading && <ResultsSkeleton />}

        {result && !loading && (
          <section className="w-full fade-in-up">
            <div className="flex items-center gap-sm mb-md">
              <h2 className="text-headline-md font-headline text-on-surface flex items-center gap-xs">
                <span className="material-symbols-outlined text-primary">robot_2</span>
                AI Recommendations
              </h2>
              <div className="flex-grow h-px bg-primary/20" />
              <span className="text-label-sm text-on-surface-variant/60">
                {result.candidates.length} matches found
              </span>
            </div>

            <div className="flex flex-col lg:flex-row gap-lg">
              <AIResponse text={result.llm_response} />
              <CandidatesTable candidates={result.candidates} />
            </div>

            <div className="mt-md text-center text-label-sm font-label text-on-surface-variant/50">
              Powered by Groq LLM · 9,200+ restaurants · Zomato Data
            </div>
          </section>
        )}
      </div>
    </>
  );
}
