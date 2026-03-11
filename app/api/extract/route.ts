import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File | null;

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    const name = file.name.toLowerCase();
    const buffer = Buffer.from(await file.arrayBuffer());

    let text = '';

    if (name.endsWith('.txt')) {
      text = buffer.toString('utf-8');
    } else if (name.endsWith('.pdf')) {
      text = await extractPDF(buffer);
    } else if (name.endsWith('.docx')) {
      text = await extractDOCX(buffer);
    } else {
      return NextResponse.json(
        { error: 'Unsupported file type. Upload PDF, DOCX, or TXT.' },
        { status: 400 }
      );
    }

    return NextResponse.json({ text: text.trim() });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Extraction failed';
    console.error('Extract error:', message);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

async function extractPDF(buffer: Buffer): Promise<string> {
  // Import the library directly to avoid pdf-parse's debug-mode file read
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const pdfParse = (await import('pdf-parse/lib/pdf-parse.js')) as any;
  const parse = pdfParse.default ?? pdfParse;
  const data = await parse(buffer);
  return data.text;
}

async function extractDOCX(buffer: Buffer): Promise<string> {
  // mammoth is listed in package.json dependencies
  const mammoth = await import('mammoth');
  const result = await mammoth.extractRawText({ buffer });
  return result.value;
}
