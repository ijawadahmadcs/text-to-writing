'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Upload, 
  FileText, 
  PenTool, 
  Layers, 
  ArrowRight, 
  ArrowLeft, 
  X, 
  Check, 
  Loader2,
  Image as ImageIcon,
  Download,
  ZoomIn,
  ZoomOut,
  RotateCcw
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { jsPDF } from 'jspdf';
import { cn } from '@/lib/utils';

// --- Types ---
type Step = 'upload' | 'samples' | 'template' | 'preview';

interface PaperTemplate {
  id: string;
  name: string;
  thumbnail: string;
  bgClass: string;
  lineColor: string;
  hasLines: boolean;
  lineSpacing: number;
}

const TEMPLATES: PaperTemplate[] = [
  { 
    id: 'lined', 
    name: 'Lined Notebook', 
    thumbnail: 'https://picsum.photos/seed/lined/200/300',
    bgClass: 'bg-white',
    lineColor: 'rgba(0, 100, 255, 0.1)',
    hasLines: true,
    lineSpacing: 30
  },
  { 
    id: 'blank', 
    name: 'Blank Paper', 
    thumbnail: 'https://picsum.photos/seed/blank/200/300',
    bgClass: 'bg-white',
    lineColor: 'transparent',
    hasLines: false,
    lineSpacing: 0
  },
  { 
    id: 'grid', 
    name: 'Grid Paper', 
    thumbnail: 'https://picsum.photos/seed/grid/200/300',
    bgClass: 'bg-white',
    lineColor: 'rgba(0, 0, 0, 0.05)',
    hasLines: true, // We'll handle grid differently in rendering
    lineSpacing: 25
  },
  { 
    id: 'exam', 
    name: 'Exam Sheet', 
    thumbnail: 'https://picsum.photos/seed/exam/200/300',
    bgClass: 'bg-stone-50',
    lineColor: 'rgba(255, 0, 0, 0.1)',
    hasLines: true,
    lineSpacing: 35
  }
];

const HANDWRITING_FONTS = [
  { name: 'Casual', family: "'Dancing Script', cursive" },
  { name: 'Neat', family: "'Indie Flower', cursive" },
  { name: 'Cursive', family: "'Great Vibes', cursive" },
  { name: 'Architect', family: "'Architects Daughter', cursive" }
];

// --- Components ---

export default function CreateAssignmentPage() {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [text, setText] = useState('');
  const [fileName, setFileName] = useState<string | null>(null);
  const [samples, setSamples] = useState<File[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<PaperTemplate>(TEMPLATES[0]);
  const [selectedFont, setSelectedFont] = useState(HANDWRITING_FONTS[0]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPages, setGeneratedPages] = useState<string[]>([]);
  const [zoom, setZoom] = useState(1);

  // Load fonts (simulated for MVP)
  useEffect(() => {
    const link = document.createElement('link');
    link.href = 'https://fonts.googleapis.com/css2?family=Dancing+Script&family=Indie+Flower&family=Great+Vibes&family=Architects+Daughter&display=swap';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
  }, []);

  const handleNext = () => {
    if (currentStep === 'upload') setCurrentStep('samples');
    else if (currentStep === 'samples') setCurrentStep('template');
    else if (currentStep === 'template') generateHandwriting();
  };

  const handleBack = () => {
    if (currentStep === 'samples') setCurrentStep('upload');
    else if (currentStep === 'template') setCurrentStep('samples');
    else if (currentStep === 'preview') setCurrentStep('template');
  };

  const generateHandwriting = async () => {
    setIsGenerating(true);
    setCurrentStep('preview');
    
    // Simulate generation delay
    await new Promise(resolve => setTimeout(resolve, 2500));

    // Simple multi-page generation logic
    const words = text.split(/\s+/);
    const wordsPerPage = 150; // Rough estimate
    const pagesCount = Math.ceil(words.length / wordsPerPage) || 1;
    
    const newPages = [];
    for (let i = 0; i < pagesCount; i++) {
      const canvas = document.createElement('canvas');
      canvas.width = 800;
      canvas.height = 1100;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        // Draw Background
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw Lines
        if (selectedTemplate.hasLines) {
          ctx.strokeStyle = selectedTemplate.lineColor;
          ctx.lineWidth = 1;
          for (let y = 100; y < canvas.height - 50; y += selectedTemplate.lineSpacing) {
            ctx.beginPath();
            ctx.moveTo(50, y);
            ctx.lineTo(canvas.width - 50, y);
            ctx.stroke();
          }
          // Vertical margin line
          ctx.strokeStyle = 'rgba(255, 0, 0, 0.1)';
          ctx.beginPath();
          ctx.moveTo(80, 0);
          ctx.lineTo(80, canvas.height);
          ctx.stroke();
        }

        // Draw Text
        ctx.fillStyle = '#1a1a1a';
        ctx.font = `24px ${selectedFont.family}`;
        
        const pageWords = words.slice(i * wordsPerPage, (i + 1) * wordsPerPage);
        let x = 100;
        let y = 100 + selectedTemplate.lineSpacing - 5;
        const maxWidth = canvas.width - 100;

        pageWords.forEach(word => {
          const metrics = ctx.measureText(word + ' ');
          if (x + metrics.width > maxWidth) {
            x = 100;
            y += selectedTemplate.lineSpacing;
          }
          
          // Add slight randomness to position and rotation for realism
          ctx.save();
          const jitterX = (Math.random() - 0.5) * 2;
          const jitterY = (Math.random() - 0.5) * 2;
          const rotation = (Math.random() - 0.5) * 0.02;
          
          ctx.translate(x + jitterX, y + jitterY);
          ctx.rotate(rotation);
          ctx.fillText(word, 0, 0);
          ctx.restore();
          
          x += metrics.width;
        });

        newPages.push(canvas.toDataURL('image/png'));
      }
    }
    
    setGeneratedPages(newPages);
    setIsGenerating(false);
  };

  const downloadPDF = () => {
    const pdf = new jsPDF('p', 'px', [800, 1100]);
    generatedPages.forEach((page, index) => {
      if (index > 0) pdf.addPage();
      pdf.addImage(page, 'PNG', 0, 0, 800, 1100);
    });
    pdf.save('assignment.pdf');
  };

  return (
    <div className="min-h-screen bg-stone-50 flex flex-col">
      {/* Header */}
      <header className="glass px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <Link href="/" className="w-8 h-8 bg-stone-900 rounded-lg flex items-center justify-center text-white font-bold">S</Link>
          <div className="h-4 w-px bg-stone-200" />
          <h1 className="font-bold text-stone-600">Create Assignment</h1>
        </div>
        
        <div className="flex items-center gap-2">
          {['upload', 'samples', 'template', 'preview'].map((step, i) => (
            <React.Fragment key={step}>
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all",
                currentStep === step ? "bg-stone-900 text-white scale-110" : 
                (i < ['upload', 'samples', 'template', 'preview'].indexOf(currentStep) ? "bg-green-500 text-white" : "bg-stone-200 text-stone-400")
              )}>
                {i < ['upload', 'samples', 'template', 'preview'].indexOf(currentStep) ? <Check className="w-4 h-4" /> : i + 1}
              </div>
              {i < 3 && <div className="w-4 h-px bg-stone-200" />}
            </React.Fragment>
          ))}
        </div>

        <button className="text-stone-400 hover:text-stone-900 transition-colors">
          <X className="w-6 h-6" />
        </button>
      </header>

      <main className="flex-grow p-6 md:p-12 max-w-5xl mx-auto w-full">
        <AnimatePresence mode="wait">
          {currentStep === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-display font-bold">Step 1: Upload Content</h2>
                <p className="text-stone-500">Paste your text or upload a document to get started.</p>
              </div>

              <div className="grid md:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <label className="text-sm font-bold text-stone-600 block">Paste Text</label>
                  <textarea 
                    className="w-full h-64 p-6 rounded-3xl border border-stone-200 focus:ring-2 focus:ring-stone-900 focus:border-transparent outline-none resize-none bg-white shadow-sm"
                    placeholder="Type or paste your assignment content here..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                  />
                </div>

                <div className="space-y-4">
                  <label className="text-sm font-bold text-stone-600 block">Upload Document</label>
                  <UploadZone onFileSelect={(name, content) => {
                    setFileName(name);
                    setText(content);
                  }} />
                  {fileName && (
                    <div className="p-4 rounded-2xl bg-stone-100 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-stone-500" />
                        <span className="text-sm font-medium truncate max-w-[200px]">{fileName}</span>
                      </div>
                      <button onClick={() => {setFileName(null); setText('');}} className="text-stone-400 hover:text-red-500">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-end pt-8">
                <button 
                  disabled={!text.trim()}
                  onClick={handleNext}
                  className="bg-stone-900 text-white px-10 py-4 rounded-2xl font-bold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98] transition-all"
                >
                  Next Step <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}

          {currentStep === 'samples' && (
            <motion.div
              key="samples"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-display font-bold">Step 2: Handwriting Samples</h2>
                <p className="text-stone-500">Upload 2-3 images of your handwriting for style analysis.</p>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                <SampleUploader onUpload={(file) => setSamples([...samples, file])} />
                {samples.map((file, i) => (
                  <div key={i} className="aspect-[3/4] rounded-3xl bg-white border border-stone-200 overflow-hidden relative group">
                    <img src={URL.createObjectURL(file)} alt="Sample" className="w-full h-full object-cover" />
                    <button 
                      onClick={() => setSamples(samples.filter((_, idx) => idx !== i))}
                      className="absolute top-4 right-4 w-8 h-8 rounded-full bg-black/50 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="bg-stone-100 p-6 rounded-3xl flex gap-4 items-start">
                <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center flex-shrink-0">
                  <PenTool className="w-5 h-5 text-stone-900" />
                </div>
                <div className="text-sm">
                  <p className="font-bold mb-1">Why upload samples?</p>
                  <p className="text-stone-500">Our AI analyzes your stroke patterns, pressure, and slant to generate a handwriting style that looks uniquely yours. (Currently in Beta)</p>
                </div>
              </div>

              <div className="flex justify-between pt-8">
                <button onClick={handleBack} className="text-stone-600 font-bold flex items-center gap-2">
                  <ArrowLeft className="w-5 h-5" /> Back
                </button>
                <button 
                  onClick={handleNext}
                  className="bg-stone-900 text-white px-10 py-4 rounded-2xl font-bold flex items-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all"
                >
                  Next Step <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}

          {currentStep === 'template' && (
            <motion.div
              key="template"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-8"
            >
              <div className="text-center space-y-2">
                <h2 className="text-3xl font-display font-bold">Step 3: Paper & Font</h2>
                <p className="text-stone-500">Choose how your assignment should look.</p>
              </div>

              <div className="space-y-6">
                <label className="text-sm font-bold text-stone-600 block">Select Paper Template</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {TEMPLATES.map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setSelectedTemplate(t)}
                      className={cn(
                        "p-4 rounded-3xl border-2 transition-all text-left space-y-3",
                        selectedTemplate.id === t.id ? "border-stone-900 bg-white shadow-lg" : "border-transparent bg-stone-100 hover:bg-stone-200"
                      )}
                    >
                      <div className="aspect-[3/4] rounded-xl overflow-hidden shadow-sm">
                        <img src={t.thumbnail} alt={t.name} className="w-full h-full object-cover" />
                      </div>
                      <span className="text-sm font-bold block">{t.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-6">
                <label className="text-sm font-bold text-stone-600 block">Select Handwriting Font</label>
                <div className="flex flex-wrap gap-3">
                  {HANDWRITING_FONTS.map((f) => (
                    <button
                      key={f.name}
                      onClick={() => setSelectedFont(f)}
                      className={cn(
                        "px-6 py-3 rounded-2xl border-2 transition-all font-bold",
                        selectedFont.name === f.name ? "border-stone-900 bg-white shadow-md" : "border-transparent bg-stone-100 hover:bg-stone-200"
                      )}
                      style={{ fontFamily: f.family }}
                    >
                      {f.name}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex justify-between pt-8">
                <button onClick={handleBack} className="text-stone-600 font-bold flex items-center gap-2">
                  <ArrowLeft className="w-5 h-5" /> Back
                </button>
                <button 
                  onClick={handleNext}
                  className="bg-stone-900 text-white px-10 py-4 rounded-2xl font-bold flex items-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all"
                >
                  Generate Assignment <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          )}

          {currentStep === 'preview' && (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-8"
            >
              {isGenerating ? (
                <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-6">
                  <div className="relative">
                    <Loader2 className="w-16 h-16 text-stone-900 animate-spin" />
                    <PenTool className="w-6 h-6 text-stone-900 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                  </div>
                  <div className="text-center">
                    <h3 className="text-2xl font-bold">Generating Assignment...</h3>
                    <p className="text-stone-500">Applying handwriting style and rendering pages.</p>
                  </div>
                </div>
              ) : (
                <div className="grid lg:grid-cols-[1fr_300px] gap-8">
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <h2 className="text-2xl font-bold">Preview</h2>
                      <div className="flex items-center gap-2 bg-white rounded-xl p-1 border border-stone-200">
                        <button onClick={() => setZoom(z => Math.max(0.5, z - 0.1))} className="p-2 hover:bg-stone-50 rounded-lg"><ZoomOut className="w-4 h-4" /></button>
                        <span className="text-xs font-mono w-12 text-center">{Math.round(zoom * 100)}%</span>
                        <button onClick={() => setZoom(z => Math.min(2, z + 0.1))} className="p-2 hover:bg-stone-50 rounded-lg"><ZoomIn className="w-4 h-4" /></button>
                      </div>
                    </div>

                    <div className="bg-stone-200 rounded-[40px] p-8 overflow-auto max-h-[70vh] flex justify-center">
                      <div className="space-y-8" style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}>
                        {generatedPages.map((page, i) => (
                          <div key={i} className="bg-white shadow-2xl rounded-sm overflow-hidden w-[600px] aspect-[1/1.414]">
                            <img src={page} alt={`Page ${i + 1}`} className="w-full h-full object-contain" />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="glass p-6 rounded-3xl space-y-6">
                      <h3 className="font-bold">Export Options</h3>
                      <button 
                        onClick={downloadPDF}
                        className="w-full bg-stone-900 text-white py-4 rounded-2xl font-bold flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all"
                      >
                        <Download className="w-5 h-5" /> Download PDF
                      </button>
                      <button className="w-full bg-white border border-stone-200 text-stone-900 py-4 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-stone-50 transition-all">
                        <ImageIcon className="w-5 h-5" /> Download Images
                      </button>
                      
                      <div className="h-px bg-stone-100" />
                      
                      <button 
                        onClick={() => setCurrentStep('template')}
                        className="w-full text-stone-500 py-2 text-sm font-bold flex items-center justify-center gap-2 hover:text-stone-900 transition-colors"
                      >
                        <RotateCcw className="w-4 h-4" /> Regenerate
                      </button>
                    </div>

                    <div className="p-6 rounded-3xl bg-stone-100 space-y-4">
                      <h4 className="text-sm font-bold">Summary</h4>
                      <div className="space-y-2 text-xs text-stone-500">
                        <div className="flex justify-between"><span>Pages</span><span>{generatedPages.length}</span></div>
                        <div className="flex justify-between"><span>Template</span><span>{selectedTemplate.name}</span></div>
                        <div className="flex justify-between"><span>Font</span><span>{selectedFont.name}</span></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

// --- Sub-components ---

function UploadZone({ onFileSelect }: { onFileSelect: (name: string, content: string) => void }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    multiple: false,
    onDrop: async (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (file) {
        // For MVP, we'll just simulate reading text
        // In a real app, we'd use pdf-parse or mammoth
        const reader = new FileReader();
        reader.onload = () => {
          onFileSelect(file.name, "This is simulated text extracted from your document. In a production environment, we would use libraries like pdf-parse or mammoth to extract the actual content from your PDF or DOCX files. For now, you can paste your own text in the left panel to see the handwriting generation in action!");
        };
        reader.readAsText(file);
      }
    }
  });

  return (
    <div 
      {...getRootProps()} 
      className={cn(
        "h-64 rounded-3xl border-2 border-dashed flex flex-col items-center justify-center gap-4 transition-all cursor-pointer",
        isDragActive ? "border-stone-900 bg-stone-100" : "border-stone-200 bg-white hover:border-stone-400"
      )}
    >
      <input {...getInputProps()} />
      <div className="w-16 h-16 bg-stone-100 rounded-2xl flex items-center justify-center">
        <Upload className="w-8 h-8 text-stone-500" />
      </div>
      <div className="text-center">
        <p className="font-bold">Click or drag to upload</p>
        <p className="text-xs text-stone-400">PDF, DOCX, or TXT (Max 10MB)</p>
      </div>
    </div>
  );
}

function SampleUploader({ onUpload }: { onUpload: (file: File) => void }) {
  const { getRootProps, getInputProps } = useDropzone({
    accept: { 'image/*': ['.png', '.jpg', '.jpeg'] },
    onDrop: (files) => files.forEach(file => onUpload(file))
  });

  return (
    <div 
      {...getRootProps()} 
      className="aspect-[3/4] rounded-3xl border-2 border-dashed border-stone-200 bg-white flex flex-col items-center justify-center gap-3 hover:border-stone-400 transition-all cursor-pointer"
    >
      <input {...getInputProps()} />
      <div className="w-12 h-12 bg-stone-50 rounded-xl flex items-center justify-center">
        <ImageIcon className="w-6 h-6 text-stone-400" />
      </div>
      <span className="text-xs font-bold text-stone-400">Add Sample</span>
    </div>
  );
}
