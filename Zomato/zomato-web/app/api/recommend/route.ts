// app/api/recommend/route.ts
// POST /api/recommend — filters restaurants + calls Groq LLM
import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';
import Groq from 'groq-sdk';
import { filterRestaurants, getBudgetRange, MAX_LLM_CANDIDATES } from '@/lib/filter';
import { Restaurant, SearchQuery } from '@/lib/types';

// Load dataset once (cached at module level by Node.js)
let _restaurants: Restaurant[] | null = null;

function loadRestaurants(): Restaurant[] {
  if (_restaurants) return _restaurants;
  const filePath = path.join(process.cwd(), 'public', 'data', 'restaurants.json');
  const raw = fs.readFileSync(filePath, 'utf-8');
  _restaurants = JSON.parse(raw) as Restaurant[];
  return _restaurants;
}

function buildPrompt(query: SearchQuery, candidates: Restaurant[]): string {
  const budgetRange = getBudgetRange(query.budget);
  const restaurantList = candidates.slice(0, MAX_LLM_CANDIDATES)
    .map((r, i) => `
${i + 1}. ${r.name}
   - Cuisine      : ${r.cuisine}
   - Rating       : ${r.rating} / 5.0  (${r.votes} votes)
   - Cost for Two : ₹${r.cost_for_two}
   - Location     : ${r.location}
   - Online Order : ${r.online_order ? 'Yes' : 'No'}
   - Book Table   : ${r.book_table ? 'Yes' : 'No'}`)
    .join('\n');

  return `You are an expert restaurant recommendation assistant for Zomato.

A user is looking for a restaurant with the following preferences:
- Location     : ${query.location || 'Any'}
- Budget       : ${query.budget} (approx ${budgetRange} for two)
- Cuisine      : ${query.cuisine || 'No preference'}
- Min Rating   : ${query.min_rating} / 5.0
- Special Ask  : ${query.extras || 'None'}

Here are the top candidate restaurants filtered from the Zomato dataset:
${restaurantList}

Please do the following:
1. Select and rank the TOP 3 to 5 restaurants from the list above that BEST match the user's preferences.
2. For each recommended restaurant, provide:
   - Restaurant Name (bold)
   - Cuisine, Rating, and Cost for Two
   - A 2 to 3 sentence explanation of why it is a great fit.
3. End with a short 2 to 3 sentence overall summary.

Important: ONLY recommend restaurants from the list above. Do NOT invent any restaurant not listed. Be friendly and concise.`;
}

export async function POST(req: NextRequest) {
  try {
    const query: SearchQuery = await req.json();

    // Validate
    if (!query.location?.trim()) {
      return NextResponse.json({ error: 'Location is required' }, { status: 400 });
    }

    // Load & filter dataset
    const restaurants = loadRestaurants();
    const candidates = filterRestaurants(restaurants, query);

    if (candidates.length === 0) {
      return NextResponse.json({ error: 'No restaurants found. Try relaxing your filters.' }, { status: 404 });
    }

    // Call Groq LLM
    const groqClient = new Groq({ apiKey: process.env.GROQ_API_KEY });
    const prompt = buildPrompt(query, candidates);

    const completion = await groqClient.chat.completions.create({
      model: process.env.GROQ_MODEL || 'qwen/qwen3.8-27b',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful and knowledgeable restaurant recommendation assistant. Always base recommendations strictly on the data provided.',
        },
        { role: 'user', content: prompt },
      ],
      temperature: 0.5,
      max_tokens: 1200,
    });

    const llmResponse = completion.choices[0]?.message?.content?.trim() || '';

    return NextResponse.json({
      llm_response: llmResponse,
      candidates: candidates.slice(0, MAX_LLM_CANDIDATES),
      query,
    });
  } catch (err: unknown) {
    console.error('[/api/recommend]', err);
    const message = err instanceof Error ? err.message : 'Internal server error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
