'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles,
  TrendingUp,
  AlertCircle,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  Loader2,
  Activity,
  ArrowLeft,
  Globe,
  Clock,
  ShieldCheck,
  Copy,
  Check
} from "lucide-react";
import DraftViewer from '@/components/dashboard/DraftViewer';
import { rtiPredict, rtiImprove, getCase, startWatchdog } from '@/lib/api';
import { useRouter, useSearchParams } from 'next/navigation';
import useCaseStore from '@/store/caseStore';

interface RTIResultViewProps {
  caseId?: string;
  initialDraft?: string;
  initialDepartment?: string;
}

const getTwitterHandle = (dept: string) => {
  const d = (dept || '').toLowerCase();
  if (d.includes('pwd') || d.includes('road') || d.includes('highway') || d.includes('street')) return '@MORTHIndia @nitin_gadkari';
  if (d.includes('municipal') || d.includes('corporation') || d.includes('ward')) return '@MoHUA_India';
  if (d.includes('police') || d.includes('fir')) return '@HMOIndia';
  if (d.includes('consumer') || d.includes('e-commerce') || d.includes('flipkart') || d.includes('amazon')) return '@jagograhakjago @PiyushGoyal';
  if (d.includes('pension') || d.includes('epfo') || d.includes('pf')) return '@socialepfo @LabourMinistry';
  if (d.includes('railway') || d.includes('train')) return '@RailMinIndia @AshwiniVaishnaw';
  if (d.includes('bank') || d.includes('sbi') || d.includes('refund')) return '@FinMinIndia @RBI';
  return '@CPGRAMS @PMOIndia';
}

const buildOptimalTweet = (dept: string, city: string, problem: string): string => {
  const handles = getTwitterHandle(dept);
  const locationTag = city ? `in ${city}` : '';
  const prefix = `🚨 ${handles} Filed an RTI regarding an urgent issue ${locationTag}: `;
  const suffix = `\n\nNeeds immediate transparency. #RTI #Transparency @CIC_India`;

  const totalBudget = 280;
  const fixedLength = prefix.length + suffix.length;
  const availableLength = totalBudget - fixedLength;

  let cleanProblem = (problem || '').trim().replace(/\s+/g, ' ');

  if (cleanProblem.length <= availableLength) {
    return `${prefix}${cleanProblem}${suffix}`;
  }

  const truncated = cleanProblem.substring(0, availableLength);
  const lastSpace = truncated.lastIndexOf(' ');
  const finalProblem = lastSpace > 0 ? truncated.substring(0, lastSpace) : truncated;

  return `${prefix}${finalProblem}${suffix}`;
}

export default function RTIResultView({ initialDepartment }: RTIResultViewProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const {
    caseId: storeCaseId,
    rtiDraft,
    setRtiDraft,
    setStage,
    reset,
    formData,
    userProblem,
    hydrateState
  } = useCaseStore();

  const caseId = storeCaseId || searchParams.get('case_id') || '';

  const [subStep, setSubStep] = useState<1 | 2>(1); 
  const [prediction, setPrediction] = useState<any>(null);
  const [loadingPred, setLoadingPred] = useState(false);
  const [loadingImprove, setLoadingImprove] = useState(false);
  const [improvedDraft, setImprovedDraft] = useState<string | null>(null);
  const [copiedPasskey, setCopiedPasskey] = useState(false);
  const [watchdogActive, setWatchdogActive] = useState(true);

  // Auto-fetch case from backend if store state is empty
  useEffect(() => {
    const loadCaseIfNeeded = async () => {
      if (!rtiDraft && caseId) {
        setLoadingPred(true);
        try {
          const res = await getCase(caseId);
          if (res && res.data) {
            hydrateState(caseId, res.data);
            if (res.data.improved_draft || res.data.initial_draft) {
              setRtiDraft(res.data.improved_draft || res.data.initial_draft);
            }
          }
        } catch (err) {
          console.error("Failed to load case session:", err);
        } finally {
          setLoadingPred(false);
        }
      }
    };
    loadCaseIfNeeded();
  }, [caseId, rtiDraft, hydrateState, setRtiDraft]);

  // Activate watchdog automatically when case is created/viewed
  useEffect(() => {
    if (caseId) {
      startWatchdog(caseId).catch((err) => console.log('Watchdog startup check:', err));
    }
  }, [caseId]);

  useEffect(() => {
    const fetchPred = async () => {
      if (!rtiDraft || !caseId) return;
      setLoadingPred(true);
      try {
        const res = await rtiPredict(caseId, rtiDraft);
        setPrediction(res);
      } catch (err) {
        console.error('Prediction failed:', err);
      } finally {
        setLoadingPred(false);
      }
    };

    fetchPred();
  }, [caseId, rtiDraft]);

  const handleImprove = async () => {
    if (!caseId) return;
    setLoadingImprove(true);
    try {
      const res = await rtiImprove(caseId);
      if (res?.improved_draft || res?.draft_text) {
        setImprovedDraft(res.improved_draft || res.draft_text);
        setRtiDraft(res.improved_draft || res.draft_text);
      }
      setSubStep(2);
      // Ensure watchdog is initialized
      await startWatchdog(caseId);
    } catch (err) {
      console.error('Improvement failed:', err);
    } finally {
      setLoadingImprove(false);
    }
  };

  const handleCopyPasskey = () => {
    if (!caseId) return;
    navigator.clipboard.writeText(caseId);
    setCopiedPasskey(true);
    setTimeout(() => setCopiedPasskey(false), 2000);
  };

  const detectedRisks = Array.isArray(prediction?.detected_risks) ? prediction.detected_risks : [];
  const improvementSuggestions = Array.isArray(prediction?.improvement_suggestions) ? prediction.improvement_suggestions : [];

  const applicantCity = formData?.applicant_city || "Local Jurisdiction";
  const defaultProblem = userProblem || "Seeking information under Section 6(1) of RTI Act.";
  const tweetText = buildOptimalTweet(formData?.target_department, applicantCity, defaultProblem);
  const tweetUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}`;

  if (!rtiDraft && !loadingPred) {
    return (
      <div 
        className="min-h-screen flex flex-col items-center justify-center p-4 bg-cover bg-center bg-no-repeat relative text-slate-200"
        style={{ backgroundImage: "url('/bg.image.png')" }}
      >
        <div className="bg-white/95 backdrop-blur-sm border border-slate-300 rounded-3xl p-8 max-w-md text-center space-y-4 shadow-xl relative z-10">
          <AlertCircle className="text-amber-500 mx-auto" size={36}/>
          <h2 className="text-xl font-extrabold text-ashoka-navy tracking-tight">No Draft Found</h2>
          <p className="text-xs text-slate-600 font-medium">
            We couldn't locate an active RTI draft for analysis. Please start or select an existing case.
          </p>
          <button
            onClick={() => {
              setStage('RTI_GATHERING');
              router.push('/dashboard/intake');
            }}
            className="btn-primary text-xs py-2.5 px-6 mx-auto cursor-pointer bg-[#A32A02] hover:bg-[#138808] transition-colors text-white font-bold font-sans tracking-tight"
          >
            Go to RTI Form
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen flex flex-col items-center justify-center p-4 py-12 bg-cover bg-center bg-no-repeat relative text-ashoka-navy font-sans"
      style={{ backgroundImage: "url('/bg.image.png')" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-4xl relative z-10"
      >
        {subStep === 1 ? (
          <div>
            <div className="mb-3">
              <span className="text-xs font-bold uppercase font-sans tracking-tight text-court-maroon bg-rose-50 px-3 py-1 rounded-full border border-rose-200">
                STEP 3 · RTI Risk Analysis & Predictor
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-white mb-2 tracking-tight drop-shadow-md">
              RTI Rejection Risk Factors
            </h1>
            <p className="text-slate-200 mb-8 font-medium drop-shadow-sm">
              Our AI evaluates your RTI draft against Section 8/9 exemptions to predict approval likelihood and highlight potential risks.
            </p>

            <div className="bg-white/95 backdrop-blur-sm border border-slate-300 rounded-3xl p-6 sm:p-8 shadow-xl space-y-6 text-left">
              {loadingPred ? (
                <div className="py-12 text-center space-y-3">
                  <Loader2 className="animate-spin text-court-maroon mx-auto" size={32}/>
                  <p className="text-sm font-medium text-slate-500">
                    Analyzing RTI exemption risks and predictability...
                  </p>
                </div>
              ) : prediction ? (
                <>
                  <div className="flex items-center justify-between bg-[#FAF8F5] p-4 rounded-2xl border border-slate-200">
                    <div>
                      <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
                        Predicted Success Outlook
                      </h4>
                      <p className="text-lg font-black text-ashoka-navy mt-0.5 tracking-tight">
                        {prediction.prediction || prediction.status || 'HIGH LIKELIHOOD'}
                      </p>
                    </div>
                    <span className="px-3 py-1 bg-emerald-50 text-emerald-700 font-bold text-xs rounded-full border border-emerald-200 font-sans tracking-tight">
                      Optimized
                    </span>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                      Detected Risks & Pitfalls
                    </h4>
                    {detectedRisks.length > 0 ? (
                      <div className="space-y-2">
                        {detectedRisks.map((risk: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 font-medium flex items-start gap-2"
                          >
                            <AlertTriangle className="text-amber-600 flex-shrink-0 mt-0.5" size={15}/>
                            <span>{typeof risk === 'string' ? risk : risk.description || risk.risk}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic">
                        No major Section 8/9 exemption risks detected.
                      </p>
                    )}
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                      AI Improvement Suggestions
                    </h4>
                    {improvementSuggestions.length > 0 ? (
                      <ul className="space-y-2 text-xs text-slate-700 list-disc list-inside font-medium bg-[#FAF8F5] p-4 rounded-xl border border-slate-200">
                        {improvementSuggestions.map((sug: string, idx: number) => (
                          <li key={idx} className="leading-relaxed">
                            {sug}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-slate-500 italic bg-[#FAF8F5] p-4 rounded-xl border border-slate-200">
                        Draft is clear and well-structured for filing.
                      </p>
                    )}
                  </div>
                </>
              ) : (
                <p className="text-sm text-slate-500">Draft ready for optimization.</p>
              )}

              <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                <button
                  onClick={() => {
                    setStage('RTI_GATHERING');
                    router.push('/dashboard/intake');
                  }}
                  className="btn-ghost text-sm cursor-pointer bg-white border-slate-300 text-slate-700 hover:bg-slate-50 font-sans tracking-tight font-bold"
                >
                  <ArrowLeft size={16}/> Edit Applicant Form
                </button>
                <button
                  onClick={handleImprove}
                  disabled={loadingImprove}
                  className="btn-primary text-base py-3.5 px-8 cursor-pointer flex items-center gap-2 bg-[#A32A02] hover:bg-[#138808] transition-colors text-white font-bold tracking-tight shadow-md rounded-xl"
                >
                  {loadingImprove ? (
                    <>
                      <Loader2 className="animate-spin" size={18}/> Optimizing...
                    </>
                  ) : (
                    <>
                      Generate Final RTI Draft <ArrowRight size={18}/>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div>
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-bold uppercase font-sans tracking-tight text-court-maroon bg-rose-50 px-3 py-1 rounded-full border border-rose-200">
                STEP 4 · Final RTI Application (Form A)
              </span>
              <span className="text-xs font-mono font-bold text-slate-600 bg-white/95 backdrop-blur-sm px-3 py-1 rounded-xl border border-slate-300 shadow-xs">
                Case ID: #{caseId}
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-extrabold text-white mb-2 tracking-tight drop-shadow-md">
              Statutory RTI Application Ready
            </h1>
            <p className="text-slate-200 mb-6 font-medium drop-shadow-sm">
              Your application has been polished to withstand statutory rejections. Download the official PDF or copy the text.
            </p>

            {/* SLA WATCHDOG ACTIVATED PROMINENT CARD */}
            <div className="mb-6 bg-gradient-to-r from-emerald-950/90 to-ashoka-navy/95 border-2 border-emerald-500/40 rounded-3xl p-6 sm:p-8 text-white shadow-2xl backdrop-blur-md relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
              
              <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-3 w-3 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                    </span>
                    <span className="text-xs font-mono font-black uppercase tracking-widest text-emerald-300 bg-emerald-950/80 px-3 py-1 rounded-full border border-emerald-400/30">
                      🛡️ AUTOMATIC RTI SLA WATCHDOG ACTIVATED
                    </span>
                  </div>

                  <h3 className="text-xl sm:text-2xl font-black tracking-tight text-white">
                    JanAdhikar is now watching this case.
                  </h3>

                  <p className="text-xs sm:text-sm text-emerald-100/90 font-medium max-w-xl leading-relaxed">
                    You do not need to remember dates. JanAdhikar's serverless watchdog tracks your 30-day statutory deadline under Section 7(1), monitors Section 20 penalty exposure (₹250/day), and prepares First Appeals automatically if the PIO defaults.
                  </p>

                  <div className="flex flex-wrap items-center gap-3 pt-1">
                    <div className="bg-black/40 border border-emerald-500/40 px-4 py-2 rounded-xl flex items-center gap-3">
                      <span className="text-[11px] uppercase font-bold text-emerald-300 tracking-wider">Case Passkey:</span>
                      <span className="font-mono font-black text-amber-300 tracking-widest text-sm">{caseId}</span>
                      <button
                        type="button"
                        onClick={handleCopyPasskey}
                        className="text-slate-300 hover:text-white transition cursor-pointer p-1"
                        title="Copy Passkey"
                      >
                        {copiedPasskey ? <Check size={15} className="text-emerald-400" /> : <Copy size={15} />}
                      </button>
                    </div>
                    {copiedPasskey && (
                      <span className="text-xs text-emerald-400 font-bold animate-in fade-in">Copied to clipboard!</span>
                    )}
                  </div>
                </div>

                <div className="shrink-0 flex flex-col sm:flex-row md:flex-col gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      const currentCaseId = caseId;
                      router.push(`/track?case_id=${currentCaseId}`);
                    }}
                    className="inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-sm transition-all shadow-lg hover:shadow-emerald-500/25 cursor-pointer tracking-tight"
                  >
                    <Activity size={18} className="text-slate-950" />
                    <span>Track Case Down</span>
                    <ArrowRight size={18} />
                  </button>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <DraftViewer caseId={caseId} draft={improvedDraft || rtiDraft || ''} title="RTI Application (Section 6(1))"/>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white/95 backdrop-blur-sm border border-slate-300 rounded-2xl p-5 text-left shadow-xs flex flex-col justify-between h-full">
                  <div>
                    <h4 className="text-xs font-bold text-ashoka-navy uppercase tracking-wider flex items-center gap-1.5 mb-2">
                      <Clock className="w-4 h-4 text-court-maroon" /> Recommended Service Instructions
                    </h4>
                    <ul className="text-xs text-slate-600 space-y-1.5 pl-4 list-disc leading-relaxed font-medium">
                      <li>Send this application via <strong>Speed Post with Acknowledgment Due (AD)</strong> or submit online.</li>
                      <li>The PIO must respond within <strong>30 calendar days</strong> under Sec 7(1).</li>
                      <li>If unresolved or denied, you can file a First Appeal under Section 19(1).</li>
                    </ul>
                  </div>
                </div>

                <div className="bg-sky-50 border border-sky-200 rounded-2xl p-5 text-left shadow-sm flex flex-col justify-between h-full">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-sky-100 rounded-full">
                        <Globe className="text-sky-600" size={16} />
                      </div>
                      <h4 className="text-xs font-bold text-sky-900 uppercase tracking-wide">Social Media Visibility</h4>
                    </div>
                    <p className="text-xs text-sky-800 leading-relaxed font-medium mb-3">
                      Public visibility accelerates administrative action. Generate a pre-filled Twitter/X post tagging relevant authorities.
                    </p>
                  </div>
                  <a
                    href={tweetUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-[#000000] hover:bg-[#1f2937] text-white font-bold text-xs transition-colors shadow-md w-full sm:w-auto cursor-pointer tracking-tight"
                  >
                    <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.008 5.961h-1.91z"/></svg>
                    Post on X / Twitter
                  </a>
                </div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3 shadow-sm text-left">
                <div className="mt-0.5 text-amber-600 flex-shrink-0">
                  <AlertCircle size={18}/>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wide mb-1 font-sans">
                    Important Disclaimer
                  </h4>
                  <p className="text-xs text-amber-800 leading-relaxed font-medium">
                    This is an AI generated document, read well before submission. Please verify all facts, dates, and claims thoroughly before sending it to the concerned authority or court.
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-center justify-between pt-6 border-t border-slate-300 mt-6 gap-3">
                <button
                  onClick={() => { 
                    reset(); 
                    sessionStorage.removeItem('janadhikar_problem'); 
                    router.push('/'); 
                  }}
                  className="btn-ghost text-sm cursor-pointer w-full sm:w-auto justify-center bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 font-sans tracking-tight font-bold"
                >
                  <RefreshCw className="mr-1.5 inline" size={16}/> Start New Case
                </button>
                <button
                  onClick={() => {
                    const currentCaseId = caseId;
                    reset();
                    sessionStorage.removeItem('janadhikar_problem');
                    router.push(`/track?case_id=${currentCaseId}`);
                  }}
                  className="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-ashoka-navy hover:bg-[#1E293B] text-white font-bold text-sm transition-all shadow-md cursor-pointer w-full sm:w-auto tracking-tight font-sans"
                >
                  <Activity className="text-emerald-400" size={16}/>
                  <span>Track Case Down (SLA Watchdog)</span>
                  <ArrowRight size={16}/>
                </button>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
