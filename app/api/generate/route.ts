import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:5328';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();

    // Forward the multipart form data to the Flask backend
    const res = await fetch(`${BACKEND_URL}/api/generate`, {
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
      { error: `Could not reach the generation backend. Make sure the Python server is running. (${message})` },
      { status: 502 }
    );
  }
}
