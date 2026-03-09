'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'motion/react';
import { 
  ArrowRight, 
  FileText, 
  PenTool, 
  Download, 
  Layers, 
  CheckCircle2,
  Github,
  Twitter
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-stone-900 rounded-xl flex items-center justify-center text-white font-bold text-xl">S</div>
          <span className="text-xl font-display font-bold tracking-tight">ScribeAI</span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-stone-600">
          <Link href="#features" className="hover:text-stone-900 transition-colors">Features</Link>
          <Link href="#how-it-works" className="hover:text-stone-900 transition-colors">How it Works</Link>
          <Link href="#pricing" className="hover:text-stone-900 transition-colors">Pricing</Link>
        </div>
        <Link 
          href="/create" 
          className="bg-stone-900 text-white px-5 py-2.5 rounded-full text-sm font-semibold hover:bg-stone-800 transition-all shadow-lg shadow-stone-200"
        >
          Get Started
        </Link>
      </nav>

      <main className="flex-grow pt-32">
        {/* Hero Section */}
        <section className="px-6 max-w-7xl mx-auto text-center mb-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-block px-4 py-1.5 rounded-full bg-stone-100 text-stone-600 text-xs font-bold uppercase tracking-widest mb-6">
              The Future of Assignments
            </span>
            <h1 className="text-5xl md:text-7xl font-display font-bold leading-[1.1] mb-8 max-w-4xl mx-auto">
              Turn Your Typed Work Into <span className="italic text-stone-500">Realistic</span> Handwritten Pages
            </h1>
            <p className="text-lg md:text-xl text-stone-600 max-w-2xl mx-auto mb-10 leading-relaxed">
              Convert PDFs, DOCX, or plain text into beautiful handwritten assignments. 
              Mimic your own style and print on realistic paper templates.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link 
                href="/create" 
                className="w-full sm:w-auto bg-stone-900 text-white px-8 py-4 rounded-2xl text-lg font-bold hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-xl shadow-stone-200"
              >
                Generate Assignment <ArrowRight className="w-5 h-5" />
              </Link>
              <button className="w-full sm:w-auto bg-white border border-stone-200 text-stone-900 px-8 py-4 rounded-2xl text-lg font-bold hover:bg-stone-50 transition-all">
                See Demo
              </button>
            </div>
          </motion.div>

          {/* Hero Preview */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mt-20 relative max-w-5xl mx-auto"
          >
            <div className="aspect-[16/9] bg-stone-200 rounded-3xl overflow-hidden shadow-2xl border-8 border-white">
              <img 
                src="https://picsum.photos/seed/handwriting/1200/800" 
                alt="App Preview" 
                className="w-full h-full object-cover opacity-80"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="glass p-8 rounded-2xl max-w-md text-left">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-3 h-3 rounded-full bg-red-400" />
                    <div className="w-3 h-3 rounded-full bg-yellow-400" />
                    <div className="w-3 h-3 rounded-full bg-green-400" />
                  </div>
                  <p className="font-mono text-sm text-stone-500 mb-2">Generating assignment...</p>
                  <div className="h-2 w-full bg-stone-100 rounded-full overflow-hidden">
                    <motion.div 
                      className="h-full bg-stone-900"
                      initial={{ width: 0 }}
                      animate={{ width: '100%' }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                  </div>
                </div>
              </div>
            </div>
            {/* Floating elements */}
            <div className="absolute -top-10 -right-10 glass p-4 rounded-2xl hidden lg:block animate-bounce">
              <PenTool className="w-8 h-8 text-stone-900" />
            </div>
            <div className="absolute -bottom-10 -left-10 glass p-4 rounded-2xl hidden lg:block animate-pulse">
              <FileText className="w-8 h-8 text-stone-900" />
            </div>
          </motion.div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-32 bg-white">
          <div className="px-6 max-w-7xl mx-auto">
            <div className="text-center mb-20">
              <h2 className="text-4xl font-display font-bold mb-4">Everything you need</h2>
              <p className="text-stone-500">Powerful features to make your assignments look authentic.</p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {[
                {
                  icon: <FileText className="w-6 h-6" />,
                  title: "Multi-format Support",
                  desc: "Upload PDF, DOCX or just paste your text directly."
                },
                {
                  icon: <PenTool className="w-6 h-6" />,
                  title: "Style Mimicry",
                  desc: "Upload samples to get a writing style that looks like yours."
                },
                {
                  icon: <Layers className="w-6 h-6" />,
                  title: "Paper Templates",
                  desc: "Choose from lined, grid, blank or custom exam sheets."
                },
                {
                  icon: <Download className="w-6 h-6" />,
                  title: "Instant Export",
                  desc: "Download as high-quality PDF or individual PNG images."
                }
              ].map((feature, i) => (
                <div key={i} className="p-8 rounded-3xl bg-stone-50 hover:bg-stone-100 transition-colors group">
                  <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center mb-6 shadow-sm group-hover:scale-110 transition-transform">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                  <p className="text-stone-600 text-sm leading-relaxed">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How it Works */}
        <section id="how-it-works" className="py-32">
          <div className="px-6 max-w-7xl mx-auto">
            <div className="flex flex-col lg:flex-row gap-20 items-center">
              <div className="lg:w-1/2">
                <h2 className="text-4xl font-display font-bold mb-8">How it works</h2>
                <div className="space-y-12">
                  {[
                    { step: "01", title: "Upload Content", desc: "Paste your text or upload your document files." },
                    { step: "02", title: "Customize Style", desc: "Select a handwriting font and paper template." },
                    { step: "03", title: "Download PDF", desc: "Get your realistic handwritten assignment in seconds." }
                  ].map((item, i) => (
                    <div key={i} className="flex gap-6">
                      <div className="text-4xl font-display font-black text-stone-200">{item.step}</div>
                      <div>
                        <h3 className="text-xl font-bold mb-2">{item.title}</h3>
                        <p className="text-stone-600">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="lg:w-1/2 relative">
                <div className="aspect-square bg-stone-200 rounded-[40px] overflow-hidden rotate-3 shadow-2xl">
                  <img src="https://picsum.photos/seed/process/800/800" alt="Process" className="w-full h-full object-cover" />
                </div>
                <div className="absolute -bottom-10 -right-10 glass p-6 rounded-3xl -rotate-3">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
                      <CheckCircle2 className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="font-bold">Ready to Print</p>
                      <p className="text-sm text-stone-500">PDF generated successfully</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-32 px-6">
          <div className="max-w-5xl mx-auto bg-stone-900 rounded-[48px] p-12 md:p-24 text-center text-white relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
              <div className="absolute top-0 left-0 w-64 h-64 bg-white rounded-full blur-[100px] -translate-x-1/2 -translate-y-1/2" />
              <div className="absolute bottom-0 right-0 w-64 h-64 bg-white rounded-full blur-[100px] translate-x-1/2 translate-y-1/2" />
            </div>
            <h2 className="text-4xl md:text-6xl font-display font-bold mb-8 relative z-10">Stop typing, start <span className="italic text-stone-400">writing</span>.</h2>
            <p className="text-stone-400 text-lg mb-12 max-w-xl mx-auto relative z-10">
              Join thousands of students who are saving hours every week with ScribeAI.
            </p>
            <Link 
              href="/create" 
              className="inline-flex items-center gap-2 bg-white text-stone-900 px-10 py-5 rounded-2xl text-xl font-bold hover:scale-105 transition-all relative z-10"
            >
              Get Started Now <ArrowRight className="w-6 h-6" />
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-stone-50 border-t border-stone-200 py-20 px-6">
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-12">
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-8 h-8 bg-stone-900 rounded-lg flex items-center justify-center text-white font-bold text-lg">S</div>
              <span className="text-xl font-display font-bold">ScribeAI</span>
            </div>
            <p className="text-stone-500 max-w-sm mb-8">
              The world's most realistic text-to-handwriting converter. Built for students, by students.
            </p>
            <div className="flex gap-4">
              <button className="w-10 h-10 rounded-full border border-stone-200 flex items-center justify-center hover:bg-stone-100 transition-colors">
                <Twitter className="w-5 h-5" />
              </button>
              <button className="w-10 h-10 rounded-full border border-stone-200 flex items-center justify-center hover:bg-stone-100 transition-colors">
                <Github className="w-5 h-5" />
              </button>
            </div>
          </div>
          <div>
            <h4 className="font-bold mb-6">Product</h4>
            <ul className="space-y-4 text-stone-500 text-sm">
              <li><Link href="#" className="hover:text-stone-900">Features</Link></li>
              <li><Link href="#" className="hover:text-stone-900">Templates</Link></li>
              <li><Link href="#" className="hover:text-stone-900">Pricing</Link></li>
              <li><Link href="#" className="hover:text-stone-900">API</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold mb-6">Company</h4>
            <ul className="space-y-4 text-stone-500 text-sm">
              <li><Link href="#" className="hover:text-stone-900">About</Link></li>
              <li><Link href="#" className="hover:text-stone-900">Privacy</Link></li>
              <li><Link href="#" className="hover:text-stone-900">Terms</Link></li>
              <li><Link href="#" className="hover:text-stone-900">Contact</Link></li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto mt-20 pt-8 border-t border-stone-200 text-center text-stone-400 text-sm">
          © 2024 ScribeAI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
