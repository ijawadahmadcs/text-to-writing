'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
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
  RotateCcw,
  Plus,
  Palette,
  Type,
  Beaker
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
    thumbnail: '/templates/lined.png',
    bgClass: 'bg-white',
    lineColor: 'rgba(180, 210, 240, 0.6)',
    hasLines: true,
    lineSpacing: 88
  },
  { 
    id: 'blank', 
    name: 'Blank Paper', 
    thumbnail: '/templates/blank.png',
    bgClass: 'bg-white',
    lineColor: 'transparent',
    hasLines: false,
    lineSpacing: 0
  },
  { 
    id: 'exam', 
    name: 'Exam Sheet', 
    thumbnail: '/templates/exam.png',
    bgClass: 'bg-stone-50',
    lineColor: 'rgba(190, 190, 190, 0.5)',
    hasLines: true,
    lineSpacing: 88
  },
  // { 
  //   id: 'grid', 
  //   name: 'Grid Paper', 
  //   thumbnail: '/templates/grid.png',
  //   bgClass: 'bg-white',
  //   lineColor: 'rgba(200, 220, 240, 0.4)',
  //   hasLines: true,
  //   lineSpacing: 62
  // },
  // { 
  //   id: 'dotted', 
  //   name: 'Dot Grid', 
  //   thumbnail: '/templates/dotted.png',
  //   bgClass: 'bg-white',
  //   lineColor: 'rgba(180, 190, 200, 0.3)',
  //   hasLines: false,
  //   lineSpacing: 62
  // }
];

const HANDWRITING_FONTS = [
  { name: 'Dancing Script', family: "'Dancing Script', cursive", index: 0, preview: null },
  { name: 'Indie Flower', family: "'Indie Flower', cursive", index: 1, preview: null },
  { name: 'Caveat', family: "'Caveat', cursive", index: 2, preview: null },
  { name: 'Architects Daughter', family: "'Architects Daughter', cursive", index: 3, preview: null },
  { name: 'Antony Lark', family: 'QEAntonyLark', index: 4, preview: '/fonts/QEAntonyLark_preview.png' },
  { name: 'Beverly Smith', family: 'QEBEV', index: 5, preview: '/fonts/QEBEV_preview.png' },
  { name: 'Braden Hill', family: 'QEBradenHill', index: 6, preview: '/fonts/QEBradenHill_preview.png' },
  { name: 'Caroline Mutiboko', family: 'QECarolineMutiboko', index: 7, preview: '/fonts/QECarolineMutiboko_preview.png' },
  { name: 'Harriet DeLaughter (Cursive)', family: 'QECursiveVersion', index: 8, preview: '/fonts/QECursiveVersion_preview.png' },
  { name: 'David Mergens', family: 'QEDaveMergens', index: 9, preview: '/fonts/QEDaveMergens_preview.png' },
  { name: 'David Reid', family: 'QEDavidReid', index: 10, preview: '/fonts/QEDavidReid_preview.png' },
  { name: 'David Reid (Print)', family: 'QEDavidReidCAP', index: 11, preview: '/fonts/QEDavidReidCAP_preview.png' },
  { name: 'Donald Ross', family: 'QEDonaldRoss', index: 12, preview: '/fonts/QEDonaldRoss_preview.png' },
  { name: 'DS Font', family: 'QEDSFont', index: 13, preview: '/fonts/QEDSFont_preview.png' },
  { name: 'Garrett Moretz', family: 'QEGarrettWMoretz', index: 14, preview: '/fonts/QEGarrettWMoretz_preview.png' },
  { name: 'geeKzoid', family: 'QEgeeKzoid', index: 15, preview: '/fonts/QEgeeKzoid_preview.png' },
  { name: 'George Hughes', family: 'QEGHHughes', index: 16, preview: '/fonts/QEGHHughes_preview.png' },
  { name: 'Herbert Cooper', family: 'QEHerbertCooper', index: 17, preview: '/fonts/QEHerbertCooper_preview.png' },
  { name: 'Jeff Dungan', family: 'QEJeffDungan', index: 18, preview: '/fonts/QEJeffDungan_preview.png' },
  { name: 'Kate Rothrock', family: 'QEJER', index: 19, preview: '/fonts/QEJER_preview.png' },
  { name: 'John Caplin', family: 'QEJohnCaplin', index: 20, preview: '/fonts/QEJohnCaplin_preview.png' },
  { name: 'John Williams', family: 'QEJohnWilliams', index: 21, preview: '/fonts/QEJohnWilliams_preview.png' },
  { name: 'Julian Dean', family: 'QEJulianDean', index: 22, preview: '/fonts/QEJulianDean_preview.png' },
  { name: 'Kevin Knowles', family: 'QEKevinKnowles', index: 23, preview: '/fonts/QEKevinKnowles_preview.png' },
  { name: 'Kevin Shirley', family: 'QEKevinShirley', index: 24, preview: '/fonts/QEKevinShirley_preview.png' },
  { name: 'Kunjar Bhaduri', family: 'QEKunjarScript', index: 25, preview: '/fonts/QEKunjarScript_preview.png' },
  { name: 'Mamas and Papas', family: 'QEMamasAndPapas', index: 26, preview: '/fonts/QEMamasAndPapas_preview.png' },
  { name: 'Pamela Rosenberry', family: 'QEPamRosenberry', index: 27, preview: '/fonts/QEPamRosenberry_preview.png' },
  { name: 'Philip Bean', family: 'QEPhilipBean', index: 28, preview: '/fonts/QEPhilipBean_preview.png' },
  { name: 'William Phillips', family: 'QEPhillips', index: 29, preview: '/fonts/QEPhillips_preview.png' },
  { name: 'Harriet DeLaughter (Print)', family: 'QEPrintVersion', index: 30, preview: '/fonts/QEPrintVersion_preview.png' },
  { name: 'Royston Such', family: 'QERoystonSuch', index: 31, preview: '/fonts/QERoystonSuch_preview.png' },
  { name: 'Royston Such (Print)', family: 'QERoystonSuchCAP', index: 32, preview: '/fonts/QERoystonSuchCAP_preview.png' },
  { name: 'Rufus', family: 'QERufus', index: 33, preview: '/fonts/QERufus_preview.png' },
  { name: 'Ruth Stafford', family: 'QERuthStafford', index: 34, preview: '/fonts/QERuthStafford_preview.png' },
  { name: 'Sam Roberts', family: 'QESamRoberts', index: 35, preview: '/fonts/QESamRoberts_preview.png' },
  { name: 'Sam Roberts (2)', family: 'QESamRoberts2', index: 36, preview: '/fonts/QESamRoberts2_preview.png' },
  { name: 'Scott Williams', family: 'QEScottWilliams', index: 37, preview: '/fonts/QEScottWilliams_preview.png' },
  { name: 'Tim Doremus', family: 'QETimDoremus', index: 38, preview: '/fonts/QETimDoremus_preview.png' },
  { name: 'Tony Flores', family: 'QETonyFlores', index: 39, preview: '/fonts/QETonyFlores_preview.png' },
  { name: 'Valerie Read', family: 'QEVRead', index: 40, preview: '/fonts/QEVRead_preview.png' },
  { name: 'Vicky Caulfield', family: 'QEVickyCaulfield', index: 41, preview: '/fonts/QEVickyCaulfield_preview.png' },
];

// --- Components ---

export default function CreateAssignmentPage() {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [text, setText] = useState('');
  const [fileName, setFileName] = useState<string | null>(null);
  const [samples, setSamples] = useState<File[]>([]);
  const [customTemplates, setCustomTemplates] = useState<PaperTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<PaperTemplate>(TEMPLATES[0]);
  const [selectedFont, setSelectedFont] = useState(HANDWRITING_FONTS[0]);
  const [useExtractedStyle, setUseExtractedStyle] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPages, setGeneratedPages] = useState<string[]>([]);
  const [zoom, setZoom] = useState(1);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [inkColor, setInkColor] = useState('#1a1a2e');
  const [fontSize, setFontSize] = useState<number | null>(null); // null = auto
  const regenerateTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-regenerate when ink color or font size changes during preview
  useEffect(() => {
    if (currentStep !== 'preview' || isGenerating || generatedPages.length === 0) return;
    if (regenerateTimerRef.current) clearTimeout(regenerateTimerRef.current);
    regenerateTimerRef.current = setTimeout(() => {
      generateHandwriting();
    }, 600);
    return () => { if (regenerateTimerRef.current) clearTimeout(regenerateTimerRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inkColor, fontSize]);

  // Load fonts (simulated for MVP)
  useEffect(() => {
    const link = document.createElement('link');
    link.href = 'https://fonts.googleapis.com/css2?family=Dancing+Script&family=Indie+Flower&family=Caveat&family=Architects+Daughter&display=swap';
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
    setErrorMessage(null);
    setCurrentStep('preview');

    try {
      const isCustom = selectedTemplate.id.startsWith('custom-');
      const formData = new FormData();
      formData.append('text', text);
      formData.append('template', selectedTemplate.id);
      formData.append('fontIndex', String(selectedFont.index));
      formData.append('inkColor', inkColor);
      if (fontSize) formData.append('fontSize', String(fontSize));

      // Tell backend whether to use extracted style or a preset font
      const shouldUseExtracted = samples.length > 0 && useExtractedStyle;
      formData.append('useExtractedStyle', shouldUseExtracted ? '1' : '0');

      // For custom templates, fetch the blob from the object URL and attach it
      if (isCustom) {
        const resp = await fetch(selectedTemplate.thumbnail);
        const blob = await resp.blob();
        formData.append('customTemplate', blob, 'template.png');
      }

      // Attach handwriting sample images for style analysis
      for (let i = 0; i < samples.length; i++) {
        formData.append(`sample${i}`, samples[i], `sample${i}.png`);
      }

      const res = await fetch('/api/generate', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `Server error: ${res.status}`);

      setGeneratedPages(data.pages);
    } catch (err) {
      console.error('Generation failed:', err);
      const msg = err instanceof Error ? err.message : 'Generation failed. Please try again.';
      setErrorMessage(msg);
      setGeneratedPages([]);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadImages = () => {
    generatedPages.forEach((page, i) => {
      const link = document.createElement('a');
      link.href = page;
      link.download = `page-${i + 1}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    });
  };

  const downloadPDF = () => {
    // Detect dimensions from first generated page
    const img = new window.Image();
    img.src = generatedPages[0];
    const w = img.naturalWidth || 800;
    const h = img.naturalHeight || 1100;
    const pdf = new jsPDF('p', 'px', [w, h]);
    generatedPages.forEach((page, index) => {
      if (index > 0) pdf.addPage();
      pdf.addImage(page, 'PNG', 0, 0, w, h);
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

              <div className="relative rounded-3xl">
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white/60 backdrop-blur-sm rounded-3xl">
                  <div className="flex items-center gap-2 bg-amber-100 text-amber-800 px-4 py-2 rounded-full text-sm font-bold">
                    <Beaker className="w-4 h-4" /> In Testing Phase
                  </div>
                  <p className="text-xs text-stone-500 mt-2">Handwriting sample analysis coming soon</p>
                </div>
                <div className="grid md:grid-cols-3 gap-6 pointer-events-none select-none opacity-50">
                  <SampleUploader onUpload={() => {}} />
                </div>
              </div>

              <div className="bg-stone-100 p-6 rounded-3xl flex gap-4 items-start">
                <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center flex-shrink-0">
                  <PenTool className="w-5 h-5 text-stone-900" />
                </div>
                <div className="text-sm">
                  <p className="font-bold mb-1">Why upload samples?</p>
                  <p className="text-stone-500">Our AI analyzes your ink color, stroke thickness, slant, and spacing from your samples and applies that style when generating. Upload 1-3 clear photos for best results.</p>
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
                <h2 className="text-3xl font-display font-bold">Step 3: Paper & Style</h2>
                <p className="text-stone-500">Choose your paper template and handwriting style.</p>
              </div>

              <div className="space-y-6">
                <label className="text-sm font-bold text-stone-600 block">Select Paper Template</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[...TEMPLATES, ...customTemplates].map((t) => (
                    <button
                      key={t.id}
                      onClick={() => setSelectedTemplate(t)}
                      className={cn(
                        "p-4 rounded-3xl border-2 transition-all text-left space-y-3",
                        selectedTemplate.id === t.id ? "border-stone-900 bg-white shadow-lg" : "border-transparent bg-stone-100 hover:bg-stone-200"
                      )}
                    >
                      <div className="aspect-[3/4] rounded-xl overflow-hidden shadow-sm relative">
                        <Image src={t.thumbnail} alt={t.name} className="w-full h-full object-cover" fill unoptimized />
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold block">{t.name}</span>
                        {t.id.startsWith('custom-') && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setCustomTemplates(prev => prev.filter(ct => ct.id !== t.id));
                              if (selectedTemplate.id === t.id) setSelectedTemplate(TEMPLATES[0]);
                            }}
                            className="text-stone-400 hover:text-red-500 transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </button>
                  ))}
                  <div className="p-4 rounded-3xl border-2 border-dashed border-stone-300 bg-stone-50 text-left space-y-3">
                    <span className="text-sm font-bold block text-stone-700">Custom Template</span>
                    <div className="relative aspect-[3/4] rounded-xl overflow-hidden">
                      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white/60 backdrop-blur-sm">
                        <div className="flex items-center gap-1.5 bg-amber-100 text-amber-800 px-3 py-1.5 rounded-full text-xs font-bold">
                          <Beaker className="w-3 h-3" /> Coming Soon
                        </div>
                      </div>
                      <div className="w-full h-full flex flex-col items-center justify-center gap-2 pointer-events-none select-none opacity-50">
                        <div className="w-12 h-12 bg-stone-200 rounded-xl flex items-center justify-center">
                          <Plus className="w-6 h-6 text-stone-500" />
                        </div>
                        <span className="text-xs text-stone-400 text-center">Upload your own template</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                <label className="text-sm font-bold text-stone-600 block">Handwriting Style</label>

                {/* Extracted style — always shown, blurred as testing */}
                <div className="relative rounded-3xl">
                  <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white/60 backdrop-blur-sm rounded-3xl">
                    <div className="flex items-center gap-2 bg-amber-100 text-amber-800 px-4 py-2 rounded-full text-sm font-bold">
                      <Beaker className="w-4 h-4" /> In Testing Phase
                    </div>
                    <p className="text-xs text-stone-500 mt-2">Style extraction from samples coming soon</p>
                  </div>
                  <div className="p-6 rounded-3xl bg-white border border-stone-200 shadow-sm space-y-4 pointer-events-none select-none opacity-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
                          <PenTool className="w-5 h-5 text-green-700" />
                        </div>
                        <div>
                          <p className="font-bold text-sm">Extracted Handwriting Pattern</p>
                          <p className="text-xs text-stone-400">Analyzed from your samples</p>
                        </div>
                      </div>
                      <div className="w-14 h-8 rounded-full bg-green-500 relative">
                        <div className="w-6 h-6 bg-white rounded-full shadow-md absolute top-1 left-7" />
                      </div>
                    </div>
                    <p className="text-xs text-stone-500">Your handwriting pattern will be used — ink color, size, slant, and spacing from your samples.</p>
                  </div>
                </div>

                {/* Font selector — always visible */}
                <div className="space-y-3">
                  <p className="text-xs text-stone-500">Select a pre-made font </p>
                  <div className="max-h-[420px] overflow-y-auto pr-1">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {HANDWRITING_FONTS.map((f) => (
                      <button
                        key={f.name}
                        onClick={() => setSelectedFont(f)}
                        className={cn(
                          "p-3 rounded-2xl border-2 transition-all text-left space-y-2",
                          selectedFont.name === f.name ? "border-stone-900 bg-white shadow-md" : "border-transparent bg-stone-100 hover:bg-stone-200"
                        )}
                      >
                        {f.preview ? (
                          <div className="h-12 rounded-lg overflow-hidden bg-white relative">
                            <Image src={f.preview} alt={f.name} className="w-full h-full object-contain" fill unoptimized />
                          </div>
                        ) : (
                          <div className="h-12 flex items-center px-2" style={{ fontFamily: f.family }}>
                            <span className="text-lg truncate">Hello world</span>
                          </div>
                        )}
                        <span className="text-xs font-bold block truncate">{f.name}</span>
                      </button>
                    ))}
                  </div>
                  </div>
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
              ) : errorMessage ? (
                <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-6">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                    <X className="w-8 h-8 text-red-500" />
                  </div>
                  <div className="text-center max-w-md">
                    <h3 className="text-2xl font-bold text-red-600 mb-2">Generation Failed</h3>
                    <p className="text-stone-500 text-sm">{errorMessage}</p>
                  </div>
                  <div className="flex gap-4">
                    <button
                      onClick={() => { setErrorMessage(null); setCurrentStep('template'); }}
                      className="bg-stone-900 text-white px-8 py-3 rounded-2xl font-bold flex items-center gap-2 hover:scale-[1.02] active:scale-[0.98] transition-all"
                    >
                      <RotateCcw className="w-4 h-4" /> Try Again
                    </button>
                    <button
                      onClick={() => { setErrorMessage(null); setCurrentStep('upload'); }}
                      className="bg-white border border-stone-200 text-stone-900 px-8 py-3 rounded-2xl font-bold hover:bg-stone-50 transition-all"
                    >
                      Start Over
                    </button>
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
                          <div key={i} className="bg-white shadow-2xl rounded-sm overflow-hidden w-[600px] aspect-[1/1.414] relative">
                            <Image src={page} alt={`Page ${i + 1}`} className="w-full h-full object-contain" fill unoptimized />
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
                      <button
                        onClick={downloadImages}
                        className="w-full bg-white border border-stone-200 text-stone-900 py-4 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-stone-50 transition-all"
                      >
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

                    <div className="glass p-6 rounded-3xl space-y-5">
                      <h3 className="font-bold">Style Options</h3>
                      
                      <div className="space-y-2">
                        <label className="text-xs font-bold text-stone-600 flex items-center gap-2">
                          <Palette className="w-3.5 h-3.5" /> Ink Color
                        </label>
                        <div className="flex items-center gap-3">
                          <input
                            type="color"
                            value={inkColor}
                            onChange={(e) => setInkColor(e.target.value)}
                            className="w-10 h-10 rounded-xl border border-stone-200 cursor-pointer bg-transparent"
                          />
                          <div className="flex gap-1.5">
                            {['#1a1a2e', '#1a237e', '#0d47a1', '#1b5e20', '#4a148c', '#b71c1c'].map(c => (
                              <button
                                key={c}
                                onClick={() => setInkColor(c)}
                                className={cn(
                                  "w-7 h-7 rounded-lg border-2 transition-all",
                                  inkColor === c ? "border-stone-900 scale-110" : "border-transparent hover:scale-105"
                                )}
                                style={{ backgroundColor: c }}
                              />
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <label className="text-xs font-bold text-stone-600 flex items-center gap-2">
                          <Type className="w-3.5 h-3.5" /> Font Size
                        </label>
                        <div className="flex items-center gap-3">
                          <input
                            type="range"
                            min={20}
                            max={80}
                            value={fontSize ?? 42}
                            onChange={(e) => setFontSize(Number(e.target.value))}
                            className="flex-1 accent-stone-900"
                          />
                          <span className="text-xs font-mono w-8 text-center text-stone-500">{fontSize ?? 42}</span>
                        </div>
                        <button
                          onClick={() => setFontSize(null)}
                          className="text-xs text-stone-400 hover:text-stone-600 transition-colors"
                        >
                          Reset to auto
                        </button>
                      </div>

                      <p className="text-xs text-stone-400">Changes auto-apply after a brief delay.</p>
                    </div>

                    <div className="p-6 rounded-3xl bg-stone-100 space-y-4">
                      <h4 className="text-sm font-bold">Summary</h4>
                      <div className="space-y-2 text-xs text-stone-500">
                        <div className="flex justify-between"><span>Pages</span><span>{generatedPages.length}</span></div>
                        <div className="flex justify-between"><span>Template</span><span>{selectedTemplate.name}</span></div>
                        <div className="flex justify-between"><span>Font</span><span>{selectedFont.name}</span></div>
                        <div className="flex justify-between"><span>Ink</span><span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full inline-block" style={{backgroundColor: inkColor}} />{inkColor}</span></div>
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
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    multiple: false,
    onDrop: async (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setExtracting(true);
      setExtractError(null);

      try {
        const form = new FormData();
        form.append('file', file);

        const res = await fetch('/api/extract', {
          method: 'POST',
          body: form,
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Extraction failed');

        onFileSelect(file.name, data.text);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Could not extract text from file.';
        setExtractError(msg);
        console.error('Extraction error:', err);
      } finally {
        setExtracting(false);
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
        {extracting ? (
          <>
            <Loader2 className="w-5 h-5 text-stone-500 animate-spin mx-auto mb-1" />
            <p className="font-bold text-sm">Extracting text...</p>
          </>
        ) : (
          <>
            <p className="font-bold">Click or drag to upload</p>
            <p className="text-xs text-stone-400">PDF, DOCX, or TXT (Max 10MB)</p>
          </>
        )}
        {extractError && (
          <p className="text-xs text-red-500 mt-2">{extractError}</p>
        )}
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

function CustomTemplateUploader({ onUpload }: { onUpload: (template: PaperTemplate) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    const url = URL.createObjectURL(file);
    const name = file.name.replace(/\.[^/.]+$/, '');
    const template: PaperTemplate = {
      id: `custom-${Date.now()}`,
      name: name.charAt(0).toUpperCase() + name.slice(1),
      thumbnail: url,
      bgClass: 'bg-white',
      lineColor: 'transparent',
      hasLines: false,
      lineSpacing: 30,
    };
    onUpload(template);
  };

  return (
    <button
      onClick={() => inputRef.current?.click()}
      className="p-4 rounded-3xl border-2 border-dashed border-stone-300 bg-stone-50 hover:bg-stone-100 hover:border-stone-400 transition-all text-left space-y-3"
    >
      <div className="aspect-[3/4] rounded-xl flex flex-col items-center justify-center gap-2">
        <div className="w-12 h-12 bg-stone-200 rounded-xl flex items-center justify-center">
          <Plus className="w-6 h-6 text-stone-500" />
        </div>
        <span className="text-xs text-stone-400 text-center">Upload your own template</span>
      </div>
      <span className="text-sm font-bold block text-stone-500">Custom</span>
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = '';
        }}
      />
    </button>
  );
}
