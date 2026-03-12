import { NextRequest, NextResponse } from 'next/server';

/**
 * Proxy: forwards /api/generate to the Python backend.
 * Set BACKEND_URL env var in Vercel to your deployed backend URL
 * (e.g. https://your-app.onrender.com). Defaults to localhost for dev.
 */
const BACKEND = process.env.BACKEND_URL || 'http://127.0.0.1:5328';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();

    const res = await fetch(`${BACKEND}/api/generate`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const errBody = await res.text();
      return NextResponse.json(
        { error: `Backend error: ${res.status} — ${errBody}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Generation failed';
    console.error('Generate proxy error:', message);
    return NextResponse.json(
      { error: `Could not reach the generation backend. (${message})` },
      { status: 502 }
    );
  }
}
