'use client';

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Copy, Download, CheckCheck, FileText, Printer, Loader2, Globe } from 'lucide-react'
import { downloadGenericPdf, downloadRtiPdf, translateDocument } from '@/lib/api'

export default function DraftViewer({ title = 'Generated Document', draft, caseId }: any) {
  const [copied, setCopied] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [displayDraft, setDisplayDraft] = useState(draft)
  const [translating, setTranslating] = useState(false)
  const [selectedLang, setSelectedLang] = useState('English')

  useEffect(() => {
    setDisplayDraft(draft);
    setSelectedLang('English');
  }, [draft]);

  if (!draft) return null

  const cleanDraftText = (displayDraft || '').replace(/\*\*(.*?)\*\*/g, '$1').replace(/#{1,6}\s?/g, '');

  const handleCopy = () => {
    navigator.clipboard.writeText(cleanDraftText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownloadPdf = async () => {
    setDownloading(true)
    try {
      let blob;
      if (caseId && selectedLang === 'English') {
        blob = await downloadRtiPdf(caseId)
      } else {
        blob = await downloadGenericPdf(`${title} (${selectedLang})`, cleanDraftText)
      }
      
      const fileBlob = new Blob([blob], { type: 'application/octet-stream' })
      const url = URL.createObjectURL(fileBlob)
      
      const link = document.createElement('a')
      link.href = url
      link.download = `${caseId ? `Application_${caseId}_${selectedLang}` : 'Legal_Notice'}.pdf`
      document.body.appendChild(link)
      link.click()
      
      setTimeout(() => {
        if (link.parentNode) link.parentNode.removeChild(link)
        URL.revokeObjectURL(url)
      }, 5000)

    } catch (err) {
      console.error('Failed to download PDF:', err)
      alert('Failed to generate PDF. Please try again.')
    } finally {
      setDownloading(false)
    }
  }

  const handlePrint = () => {
    const iframe = document.createElement('iframe')
    iframe.style.position = 'fixed'
    iframe.style.right = '0'
    iframe.style.bottom = '0'
    iframe.style.width = '0'
    iframe.style.height = '0'
    iframe.style.border = '0'
    document.body.appendChild(iframe)
    
    const content = `
      <html>
        <head>
          <title>${title} - ${selectedLang}</title>
          <style>
            body { font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; padding: 40px; color: #000; }
            pre { white-space: pre-wrap; font-family: inherit; margin: 0; }
          </style>
        </head>
        <body>
          <h2>${title} (${selectedLang})</h2>
          <pre>${cleanDraftText.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
        </body>
      </html>
    `
    
    if (iframe.contentWindow) {
      iframe.contentWindow.document.open()
      iframe.contentWindow.document.write(content)
      iframe.contentWindow.document.close()
      
      iframe.contentWindow.focus()
      setTimeout(() => {
        if (iframe.contentWindow) {
          iframe.contentWindow.print()
        }
        setTimeout(() => {
          if (document.body.contains(iframe)) {
            document.body.removeChild(iframe)
          }
        }, 1000)
      }, 250)
    }
  }

  const handleTranslate = async (e: any) => {
    const lang = e.target.value;
    setSelectedLang(lang);
    if (lang === 'English') {
      setDisplayDraft(draft);
      return;
    }
    setTranslating(true);
    try {
      const res = await translateDocument(draft, lang);
      setDisplayDraft(res.translated_text);
    } catch (err) {
      console.error('Translation failed:', err);
      alert('Failed to translate document. Please try again.');
      setSelectedLang('English');
      setDisplayDraft(draft);
    } finally {
      setTranslating(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/95 backdrop-blur-sm border border-slate-300 rounded-3xl overflow-hidden shadow-xl"
    >
      <div className="flex flex-col md:flex-row items-center justify-between px-5 py-4 border-b border-slate-200 bg-[#FAF8F5] gap-3">
        <div className="flex items-center gap-2.5">
          <FileText size={16} className="text-[#FF9933] shrink-0" />
          <h3 className="text-sm font-extrabold text-ashoka-navy tracking-tight font-sans truncate max-w-[200px] sm:max-w-none">{title} ({selectedLang})</h3>
          {caseId && <span className="hidden sm:inline-block text-xs font-mono text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">#{caseId}</span>}
        </div>
        
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          {/* Translation Dropdown */}
          <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 shadow-sm">
            <Globe size={13} className="text-slate-500" />
            <select
              value={selectedLang}
              onChange={handleTranslate}
              disabled={translating}
              className="text-xs font-bold text-slate-600 bg-transparent focus:outline-none cursor-pointer tracking-tight"
            >
              <option value="English">English</option>
              <option value="Hindi">Hindi (हिन्दी)</option>
              <option value="Marathi">Marathi (मराठी)</option>
              <option value="Tamil">Tamil (தமிழ்)</option>
              <option value="Gujarati">Gujarati (ગુજરાતી)</option>
              <option value="Bengali">Bengali (বাংলা)</option>
              <option value="Telugu">Telugu (తెలుగు)</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <button onClick={handleCopy} className="btn-ghost flex-1 sm:flex-none text-xs py-1.5 px-3 gap-1.5 bg-white border border-slate-200 text-slate-600 hover:text-ashoka-navy hover:bg-slate-50">
              {copied ? <><CheckCheck size={13} className="text-emerald-500" /> Copied!</> : <><Copy size={13} /> Copy</>}
            </button>
            <button 
              onClick={handleDownloadPdf} 
              disabled={downloading}
              className="btn-ghost flex-1 sm:flex-none text-xs py-1.5 px-3 gap-1.5 bg-white border border-slate-200 text-slate-600 hover:text-ashoka-navy hover:bg-slate-50 disabled:opacity-50"
            >
              {downloading ? <><Loader2 size={13} className="animate-spin" /> Gen...</> : <><Download size={13} /> PDF</>}
            </button>
            <button onClick={handlePrint} className="btn-ghost flex-1 sm:flex-none text-xs py-1.5 px-3 gap-1.5 bg-white border border-slate-200 text-slate-600 hover:text-ashoka-navy hover:bg-slate-50">
              <Printer size={13} /> Print
            </button>
          </div>
        </div>
      </div>
      
      <div className="p-5 sm:p-6">
        <div className="relative bg-[#FAF8F5] border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-inner min-h-[300px] max-h-[500px] overflow-y-auto">
          {translating && (
            <div className="absolute inset-0 bg-white/50 backdrop-blur-[1px] flex items-center justify-center z-10 rounded-2xl">
              <div className="flex items-center gap-2 bg-white px-5 py-2.5 rounded-full shadow border border-slate-200">
                <Loader2 size={16} className="animate-spin text-[#FF9933]" />
                <span className="text-xs font-bold text-slate-600">Translating Document...</span>
              </div>
            </div>
          )}
          <pre className="text-sm text-ashoka-navy font-sans font-medium leading-relaxed whitespace-pre-wrap break-words">
            {cleanDraftText}
          </pre>
        </div>
      </div>
    </motion.div>
  )
}
