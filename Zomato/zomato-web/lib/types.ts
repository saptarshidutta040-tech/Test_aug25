// lib/types.ts
export interface Restaurant {
  name: string;
  location: string;
  cuisine: string;
  cost_for_two: number;
  rating: number;
  votes: number;
  online_order: boolean;
  book_table: boolean;
}

export interface SearchQuery {
  location: string;
  cuisine: string;
  budget: 'low' | 'medium' | 'high';
  min_rating: number;
  extras: string;
}

export interface RecommendResponse {
  llm_response: string;
  candidates: Restaurant[];
  query: SearchQuery;
  error?: string;
}
