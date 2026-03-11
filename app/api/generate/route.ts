import { NextRequest, NextResponse } from 'next/server';

/**
 * Proxy for /api/generate — works in both environments:
 * - Local dev: forwards to Flask dev server at localhost:5328
 * - Vercel: forwards to the Python serverless function at /api/index
 *   (since Next.js routes take priority over vercel.json rewrites)
 */

export async function POST(req: NextRequest) {
  let backendUrl: string;

  if (process.env.VERCEL_URL) {
    // On Vercel: call the Python serverless function directly
    const proto = process.env.VERCEL_ENV === 'development' ? 'http' : 'https';
    backendUrl = `${proto}://${process.env.VERCEL_URL}/api/index`;
  } else if (process.env.BACKEND_URL) {
    backendUrl = `${process.env.BACKEND_URL}/api/generate`;
  } else {
    backendUrl = 'http://127.0.0.1:5328/api/generate';
  }

  try {
    const formData = await req.formData();

    const res = await fetch(backendUrl, {
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
