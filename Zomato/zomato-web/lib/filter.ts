// lib/filter.ts — TypeScript port of the Python FilterEngine
import { Restaurant, SearchQuery } from './types';

const BUDGET_MAP: Record<string, [number, number]> = {
  low:    [0, 500],
  medium: [500, 1500],
  high:   [1500, Infinity],
};

export const TOP_K_CANDIDATES = 15;
export const MAX_LLM_CANDIDATES = 8;

export function filterRestaurants(
  restaurants: Restaurant[],
  query: SearchQuery
): Restaurant[] {
  let results = [...restaurants];

  // Step 1: Location (case-insensitive partial match)
  if (query.location?.trim()) {
    const loc = query.location.trim().toLowerCase();
    results = results.filter(r => r.location.toLowerCase().includes(loc));
  }

  // Step 2: Cuisine (case-insensitive partial match)
  if (query.cuisine?.trim()) {
    const cui = query.cuisine.trim().toLowerCase();
    results = results.filter(r => r.cuisine.toLowerCase().includes(cui));
  }

  // Step 3: Budget range
  if (query.budget && BUDGET_MAP[query.budget]) {
    const [low, high] = BUDGET_MAP[query.budget];
    results = results.filter(r => r.cost_for_two >= low && r.cost_for_two <= high);
  }

  // Step 4: Minimum rating
  if (query.min_rating != null) {
    results = results.filter(r => r.rating >= query.min_rating);
  }

  // Step 5: Fallback — relax constraints progressively
  if (results.length === 0) {
    results = fallback(restaurants, query);
  }

  // Step 6: Score = rating × log(1 + votes), sort descending
  const scored = results.map(r => ({
    ...r,
    _score: r.rating * Math.log1p(r.votes),
  }));
  scored.sort((a, b) => b._score - a._score);

  return scored.slice(0, TOP_K_CANDIDATES);
}

function fallback(restaurants: Restaurant[], query: SearchQuery): Restaurant[] {
  let relaxed = [...restaurants];

  // Try: location only + relaxed rating
  if (query.location?.trim()) {
    const loc = query.location.trim().toLowerCase();
    const locationMatch = relaxed.filter(r => r.location.toLowerCase().includes(loc));
    if (locationMatch.length > 0) {
      if (query.min_rating) {
        const relaxedRating = locationMatch.filter(r => r.rating >= query.min_rating - 0.5);
        if (relaxedRating.length > 0) return relaxedRating;
      }
      return locationMatch;
    }
  }

  // Global top-K by score
  return relaxed
    .map(r => ({ ...r, _score: r.rating * Math.log1p(r.votes) }))
    .sort((a, b) => b._score - a._score)
    .slice(0, TOP_K_CANDIDATES);
}

export function getBudgetRange(budget: string): string {
  const map: Record<string, string> = {
    low:    '₹0–₹500',
    medium: '₹500–₹1,500',
    high:   '₹1,500+',
  };
  return map[budget] || '₹500–₹1,500';
}
