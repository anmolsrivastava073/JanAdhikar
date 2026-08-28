'use client';
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, FileSearch, Loader2, KeyRound, Copy, Download, Lock, RefreshCw, FolderOpen, Check, ArrowLeft, Activity } from 'lucide-react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import useCaseStore from '@/store/caseStore'
import { initCase, getCase, classifyCase } from '@/lib/api'
import AudioRecorder from '@/components/dashboard/AudioRecorder'

export default function GatewayView() {
  const router = useRouter()
  const [text, setText] = useState('')
  const [passkey, setPasskey] = useState('')
  const [resumeMode, setResumeMode] = useState(false)
  const [localErr, setLocalErr] = useState<string | null>(null)
  
  const [isResumeNavigating, setIsResumeNavigating] = useState(false)
  const [showPasskeyModal, setShowPasskeyModal] = useState(false)
  const [copied, setCopied] = useState(false)
  const [hasAgreed, setHasAgreed] = useState(false)

  const { stage, setStage, caseId, setCaseId, setUserProblem, language, setLanguage, hydrateState, reset } = useCaseStore()

  const isProcessing = stage === 'INITIALIZING' || showPasskeyModal || isResumeNavigating
  
  const handleStartCase = async () => {
    if (!text.trim() || isProcessing) return
    setLocalErr(null)
    setHasAgreed(false)
    try {
      const currentText = text.trim();
      const currentLang = language || 'English';

      // Wipe old cache completely to prevent previous case data from leaking
      reset();
      sessionStorage.removeItem('janadhikar_problem');

      // Set current details
      setLanguage(currentLang);
      setStage('INITIALIZING')
      const { case_id } = await initCase()
      setCaseId(case_id)
      setUserProblem(currentText)
      setStage('IDLE')
      setShowPasskeyModal(true)

      classifyCase(case_id, currentText, currentLang).catch(() => {});
    } catch (err: any) {
      setLocalErr(err?.response?.data?.detail || err.message || 'Something went wrong.')
      setStage('IDLE')
    }
  }

  const handleProceedToIntake = () => {
    if (!hasAgreed) return
    setShowPasskeyModal(false)
    setLocalErr(null)
    router.push('/dashboard/intake')
  }

  const handleCopyId = () => {
    if (caseId) {
      navigator.clipboard.writeText(caseId)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleDownloadTxt = () => {
    if (!caseId) return
    const element = document.createElement("a")
    const file = new Blob([`JanAdhikar Private Case ID: ${caseId}\nKeep this key safe to resume your case anytime.`], {type: 'text/plain'})
    element.href = URL.createObjectURL(file)
    element.download = `${caseId}-Passkey.txt`
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const handleResume = async () => {
    if (!passkey.trim() || isProcessing) return
    setLocalErr(null)
    setStage('INITIALIZING')
    try {
      const res = await getCase(passkey.trim().toUpperCase())
      if (!res) throw new Error("Case not found.")
      
      setIsResumeNavigating(true) 
      
      hydrateState(res.case_id, res.data)
      const st = res.data?.status
      const rt = res.data?.route
      
      if (st === 'rti_completed' || st === 'rti_predicted' || st === 'rti_drafted') {
        router.push('/dashboard/rti/result')
      } else if (st === 'grievance_completed') {
        router.push('/dashboard/grievance/result')
      } else if (rt === 'RTI' || rt === 'Rights/Grievance' || st === 'classified' || st === 'initialized') {
        router.push('/dashboard/intake')
      } else {
        setResumeMode(false)
        setIsResumeNavigating(false)
        setStage('IDLE')
      }
    } catch (err) {
      setIsResumeNavigating(false)
      setLocalErr('Invalid Case ID or expired session. Please check and try again.')
      setStage('IDLE')
    }
  }

  return (
    <div 
      className="min-h-screen flex flex-col items-center justify-center p-4 relative overflow-hidden bg-cover bg-center bg-no-repeat font-sans"
      style={{ backgroundImage: "url('/bg.image.png')" }}
    >
      <div className="absolute top-6 left-6 z-20">
        <Link className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white/95 backdrop-blur-sm border border-slate-300 text-slate-700 text-xs font-bold shadow-sm hover:text-ashoka-navy hover:bg-slate-50 transition cursor-pointer tracking-tight" href="/">
          <ArrowLeft size={14} />
          <span>Back to Landing</span>
        </Link>
      </div>
      
      <AnimatePresence>
        {showPasskeyModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-ashoka-navy/60 backdrop-blur-sm p-4"
          >
            <motion.div
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              className="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-8 border border-slate-300 relative overflow-hidden text-center"
            >
              <div className="absolute top-0 left-0 w-full h-1.5 bg-court-maroon"></div>
              
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 text-ashoka-navy border border-slate-200 rounded-full text-xs font-bold mb-4 shadow-sm tracking-tight">
                <KeyRound size={13} />
                <span>Case Passkey Created</span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-extrabold text-ashoka-navy mb-2 tracking-tight">
                Save Your Private Case ID
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 mb-6 max-w-sm mx-auto font-medium">
                Save this key before we prepare your official legal form. You will need it to reopen your case anytime.
              </p>

              <div className="bg-[#FAF8F5] border border-slate-200 rounded-2xl p-6 shadow-inner mb-5">
                <span className="block text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3">
                  YOUR PRIVATE ACCESS IDENTIFIER
                </span>
                
                <div className="text-2xl sm:text-3xl font-mono font-black text-court-maroon tracking-widest mb-6 drop-shadow-sm">
                  {caseId}
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-2.5">
                  <button 
                    onClick={handleCopyId}
                    className="w-full sm:w-auto flex-1 bg-[#A32A02] hover:bg-[#138808] text-white font-bold py-2.5 px-4 rounded-xl transition-colors shadow-md flex items-center justify-center gap-2 text-xs cursor-pointer tracking-tight"
                  >
                    {copied ? <Check size={15} /> : <Copy size={15} />}
                    {copied ? 'Copied!' : 'Copy Case ID'}
                  </button>

                  <button 
                    onClick={handleDownloadTxt}
                    className="w-full sm:w-auto flex-1 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-bold py-2.5 px-4 rounded-xl transition-colors shadow-sm flex items-center justify-center gap-2 text-xs cursor-pointer tracking-tight"
                  >
                    <Download size={15} className="text-slate-500" />
                    <span>Download .txt Key</span>
                  </button>
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-3.5 text-left flex items-start gap-3 shadow-sm mb-4">
                <div className="mt-0.5 text-slate-500 flex-shrink-0">
                  <Lock size={15} />
                </div>
                <div>
                  <h4 className="text-[11px] font-bold text-ashoka-navy uppercase tracking-wide mb-0.5">Zero-Account Privacy:</h4>
                  <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                    Take a quick screenshot or write it down. Your case is stored locally and never linked to your phone number or email.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-2.5 mb-5 bg-white p-3.5 rounded-2xl border border-slate-200 text-left shadow-sm">
                <input
                  type="checkbox"
                  id="modal-agreement"
                  checked={hasAgreed}
                  onChange={(e) => setHasAgreed(e.target.checked)}
                  className="mt-0.5 w-4 h-4 text-[#A32A02] bg-white border-slate-300 rounded focus:ring-[#A32A02] cursor-pointer flex-shrink-0"
                />
                <label htmlFor="modal-agreement" className="text-xs text-slate-600 font-medium cursor-pointer leading-relaxed select-none">
                  I acknowledge that this <strong className="text-ashoka-navy">Passkey is solely responsible for retrieving my case data</strong>, and I confirm I have safely saved it.
                </label>
              </div>

              {localErr && <div className="p-3 bg-red-50 text-red-700 text-xs rounded-xl mb-4 text-left border border-red-200">{localErr}</div>}

              <button 
                onClick={handleProceedToIntake} 
                disabled={!hasAgreed}
                className="btn-primary w-full justify-center text-sm py-3 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed bg-[#A32A02] hover:bg-[#138808] text-white flex items-center gap-2 font-bold tracking-tight shadow-md"
              >
                <span>Generate Form & Continue</span>
                <ArrowRight size={16} />
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {!resumeMode && !isResumeNavigating ? (
          <motion.div key="main" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="w-full max-w-2xl text-center z-10">
            <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-3 tracking-tight drop-shadow-md">What is your problem?</h1>
            <p className="text-lg text-blue-100 mb-8 font-medium drop-shadow-sm">Write it in your own words. Our AI assistant will automatically structure it.</p>
            
            <div className="bg-white/95 backdrop-blur-sm border border-slate-300 rounded-3xl shadow-xl mb-6 text-left">
              <textarea
                rows={6}
                value={text}
                onChange={(e) => setText(e.target.value)}
                disabled={stage === 'INITIALIZING'}
                placeholder="e.g. My pension has not come for 3 months. My landlord refuses to return my deposit. The road in our ward is uncarpeted..."
                className="w-full bg-transparent p-6 text-lg text-ashoka-navy font-medium placeholder-slate-400 focus:outline-none resize-none rounded-t-3xl"
              />
              <div className="flex items-center justify-between px-6 pb-5">
                <AudioRecorder language={language} onTranscription={(t) => setText(prev => prev + (prev ? " " : "") + t)} />
                <span className="text-sm text-slate-400 font-medium">{text.length} chars</span>
              </div>
            </div>

            {localErr && <div className="p-3 bg-red-50 text-red-700 text-sm rounded-xl mb-4 text-left border border-red-200">{localErr}</div>}

            <button 
              onClick={handleStartCase} 
              disabled={!text.trim() || stage === 'INITIALIZING'} 
              className="btn-primary w-full justify-center text-lg py-4 cursor-pointer bg-[#A32A02] hover:bg-[#138808] transition-colors text-white flex items-center gap-2 shadow-md rounded-xl font-bold tracking-tight"
            >
              {stage === 'INITIALIZING' ? <><Loader2 size={20} className="animate-spin"/> Generating Your Case ID...</> : <>Start Analysis &amp; Form Fill <ArrowRight size={20} /></>}
            </button>

            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6 px-2">
              <button onClick={() => setResumeMode(true)} className="text-white font-bold text-sm hover:text-blue-200 transition cursor-pointer flex items-center gap-1.5 drop-shadow-sm">
                <FolderOpen size={16} /> Resume Draft
              </button>
              <span className="hidden sm:block text-slate-300">•</span>
              <Link className="text-white font-bold text-sm hover:text-emerald-300 transition cursor-pointer flex items-center gap-1.5 drop-shadow-sm" href="/track">
                <Activity size={16} /> Track Filed Case
              </Link>
              <span className="hidden sm:block text-slate-300">•</span>
              <button onClick={() => { reset(); setText(''); setPasskey(''); sessionStorage.removeItem('janadhikar_problem'); }} className="text-slate-300 flex items-center gap-1.5 text-sm font-medium hover:text-white transition cursor-pointer drop-shadow-sm">
                <RefreshCw size={14} /> Reset Form
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div key="resume" initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.98 }} className="w-full max-w-lg bg-white/95 backdrop-blur-sm p-8 rounded-3xl shadow-xl border border-slate-300 text-center z-10">
            <div className="w-14 h-14 bg-slate-50 text-court-maroon rounded-2xl flex items-center justify-center mx-auto mb-6 border border-slate-200">
              <FolderOpen size={28} />
            </div>
            <h2 className="text-3xl font-extrabold text-ashoka-navy mb-3 tracking-tight">Resume your case</h2>
            <p className="text-slate-500 mb-8 font-medium">Enter your 12-character Case ID to pick up where you left off.</p>
            
            <input 
              type="text" 
              value={passkey} 
              onChange={(e) => setPasskey(e.target.value.toUpperCase())}
              placeholder="E.G. CR-ABCD-1234"
              maxLength={12}
              className="w-full text-center bg-[#FAF8F5] border border-slate-300 rounded-xl p-4 text-lg font-mono font-bold text-ashoka-navy tracking-widest uppercase mb-6 placeholder-slate-400 focus:ring-2 focus:ring-court-maroon/20 focus:border-court-maroon focus:outline-none shadow-inner"
            />
            
            {localErr && <div className="p-3 bg-red-50 text-red-700 text-sm rounded-xl mb-4 text-left border border-red-200">{localErr}</div>}

            <button onClick={handleResume} disabled={!passkey.trim() || stage === 'INITIALIZING' || isResumeNavigating} className="btn-primary w-full justify-center text-lg py-4 mb-8 shadow-md cursor-pointer bg-[#A32A02] hover:bg-[#138808] transition-colors text-white rounded-xl font-bold tracking-tight">
              {stage === 'INITIALIZING' || isResumeNavigating ? <Loader2 size={20} className="animate-spin"/> : <>Open case <ArrowRight size={20} /></>}
            </button>
            
            <div className="flex items-center justify-between border-t border-slate-200 pt-6">
              <button onClick={() => setResumeMode(false)} className="text-slate-600 font-bold text-sm hover:text-ashoka-navy transition cursor-pointer tracking-tight">Start a new case instead</button>
              <button onClick={() => { reset(); setText(''); setPasskey(''); sessionStorage.removeItem('janadhikar_problem'); window.location.reload(); }} className="text-slate-400 flex items-center gap-1.5 text-sm font-medium hover:text-ashoka-navy transition cursor-pointer tracking-tight"><RefreshCw size={14} /> Reset Form</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
