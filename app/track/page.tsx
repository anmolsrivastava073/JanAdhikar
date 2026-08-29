'use client';

import React, { useState, useEffect, Suspense, useMemo } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import {
  getCase,
  getWatchdogState,
  startWatchdog,
  recordWatchdogResponse,
  simulateWatchdog
} from '@/lib/api';
import {
  ArrowLeft,
  Search,
  Clock,
  Scale,
  FileText,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  Send,
  Sparkles,
  ChevronDown,
  ChevronUp,
  History,
  Info,
  Calendar,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  Sliders,
  ExternalLink
} from 'lucide-react';

interface WatchdogEvent {
  type: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

interface CaseMetrics {
  case_id: string;
  watchdog_enabled?: boolean;
  watchdog_status?: string;
  computed_status: string;
  is_overdue: boolean;
  days_overdue: number;
  days_remaining: number;
  section_20_penalty_inr: number;
  filing_date: string;
  response_due_date: string;
  first_appeal_due_date: string;
  time_remaining_seconds: number;
  appeal_eligible?: boolean;
  last_watchdog_check_at?: string;
  last_watchdog_event?: string;
  watchdog_events?: WatchdogEvent[];
  response_received_at?: string;
  pio_response_text?: string;
  exemption_cited?: string;
  legal_counter?: string;
  precedent_title?: string;
  first_appeal_draft?: string;
  department_info?: Record<string, any>;
  user_problem?: string;
}

function formatCountdown(totalSeconds: number) {
  if (totalSeconds <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0 };
  }
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return { days, hours, minutes, seconds };
}

function TrackPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const caseIdParam = searchParams.get('case_id') || '';

  const [inputCaseId, setInputCaseId] = useState(caseIdParam);
  const [caseData, setCaseData] = useState<CaseMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Live ticking countdown state
  const [secondsRemaining, setSecondsRemaining] = useState<number>(0);

  // PIO Response Tab / Form
  const [showResponseForm, setShowResponseForm] = useState(false);
  const [pioInputText, setPioInputText] = useState('');
  const [responseDate, setResponseDate] = useState(new Date().toISOString().split('T')[0]);
  const [analyzing, setAnalyzing] = useState(false);

  // Copy state
  const [copiedPasskey, setCopiedPasskey] = useState(false);

  // Dev simulation state
  const [showDevTools, setShowDevTools] = useState(false);
  const [simulating, setSimulating] = useState(false);

  const fetchCaseDetails = async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const cleanId = id.trim().toUpperCase();
      const data = await getWatchdogState(cleanId);
      if (!data || !data.case_id) throw new Error('Case not found');
      setCaseData(data);
      setSecondsRemaining(data.time_remaining_seconds || 0);
      if (data.pio_response_text) {
        setPioInputText(data.pio_response_text);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch case details');
      setCaseData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (caseIdParam) {
      setInputCaseId(caseIdParam);
      fetchCaseDetails(caseIdParam);
    }
  }, [caseIdParam]);

  // Live authoritative countdown timer
  useEffect(() => {
    if (secondsRemaining <= 0) return;
    const interval = setInterval(() => {
      setSecondsRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [secondsRemaining]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputCaseId.trim()) {
      router.push(`/track?case_id=${inputCaseId.trim().toUpperCase()}`);
    }
  };

  const handleCopyPasskey = () => {
    if (!caseData?.case_id) return;
    navigator.clipboard.writeText(caseData.case_id);
    setCopiedPasskey(true);
    setTimeout(() => setCopiedPasskey(false), 2000);
  };

  const handleRecordResponse = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!caseData?.case_id) return;

    setAnalyzing(true);
    try {
      const res = await recordWatchdogResponse(
        caseData.case_id,
        pioInputText,
        responseDate ? new Date(responseDate).toISOString() : new Date().toISOString()
      );
      await fetchCaseDetails(caseData.case_id);
      setShowResponseForm(true);
    } catch (err) {
      console.error('Failed to record PIO response:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSimulate = async (scenario: string, daysAgo?: number) => {
    if (!caseData?.case_id) return;
    setSimulating(true);
    try {
      await simulateWatchdog(caseData.case_id, scenario, daysAgo);
      await fetchCaseDetails(caseData.case_id);
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setSimulating(false);
    }
  };

  const countdown = useMemo(() => formatCountdown(secondsRemaining), [secondsRemaining]);

  // Calculate timeline milestone active indexes
  const timelineStages = useMemo(() => {
    const status = caseData?.watchdog_status || 'ACTIVE';
    const isOverdue = caseData?.is_overdue || false;
    const daysRemaining = caseData?.days_remaining ?? 30;
    const hasResponse = status === 'RESPONSE_RECEIVED' || !!caseData?.response_received_at;
    const appealReady = !!caseData?.first_appeal_draft || status === 'DEEMED_REFUSAL';

    return [
      {
        id: 1,
        title: 'RTI Filed',
        date: caseData?.filing_date ? new Date(caseData.filing_date).toLocaleDateString() : 'Filed',
        completed: true,
        current: false,
      },
      {
        id: 2,
        title: 'Watchdog Active',
        date: '24/7 Monitoring',
        completed: true,
        current: status === 'ACTIVE' && daysRemaining > 7,
      },
      {
        id: 3,
        title: '7 Days Remaining',
        date: 'Warning Window',
        completed: daysRemaining <= 7 || isOverdue || hasResponse,
        current: status === 'DUE_SOON' && daysRemaining <= 7 && daysRemaining > 0,
      },
      {
        id: 4,
        title: 'Statutory Limit (30d)',
        date: caseData?.response_due_date ? new Date(caseData.response_due_date).toLocaleDateString() : 'Day 30',
        completed: isOverdue || hasResponse,
        current: status === 'DUE_TODAY',
      },
      {
        id: 5,
        title: hasResponse ? 'Response Received' : 'Deemed Refusal',
        date: hasResponse ? 'Reply Logged' : 'Sec 7(2) Triggered',
        completed: isOverdue || hasResponse,
        current: status === 'DEEMED_REFUSAL' || status === 'OVERDUE' || (hasResponse && !appealReady),
      },
      {
        id: 6,
        title: 'First Appeal Eligible',
        date: 'Section 19(1)',
        completed: appealReady || isOverdue,
        current: appealReady,
      }
    ];
  }, [caseData]);

  return (
    <div 
      className="min-h-screen font-sans p-4 sm:p-6 lg:p-8 selection:bg-court-maroon selection:text-white pb-24 bg-cover bg-center bg-no-repeat relative text-slate-100"
      style={{ backgroundImage: "url('/bg.image.png')" }}
    >
      <div className="max-w-6xl mx-auto space-y-8 pt-4 relative z-10">
        
        {/* TOP NAVIGATION & SEARCH */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 border-b border-white/20 pb-6">
          <div className="flex items-start sm:items-center gap-4">
            <button 
              onClick={() => router.push('/')}
              className="p-2.5 rounded-xl bg-white border border-slate-300 text-slate-700 hover:text-ashoka-navy hover:bg-slate-100 transition shadow-sm cursor-pointer shrink-0 mt-1 sm:mt-0"
              title="Back to Landing Page"
            >
              <ArrowLeft size={18} />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse hidden sm:inline-block" />
                <span className="text-xs font-mono font-bold uppercase tracking-widest text-emerald-300 bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                  STATUTORY RTI SLA ENGINE
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-black tracking-tight text-white flex items-center gap-3 drop-shadow-md mt-1">
                JanAdhikar Legal Watchdog
              </h1>
              <p className="text-blue-100 text-xs sm:text-sm font-medium drop-shadow-sm">
                Deterministic statutory timeline enforcer & Section 20 penalty engine
              </p>
            </div>
          </div>

          <form onSubmit={handleSearchSubmit} className="flex gap-2 w-full md:w-auto pl-12 sm:pl-0">
            <input
              type="text"
              placeholder="Enter Case ID (CR-XXXX-XXXX)"
              value={inputCaseId}
              onChange={(e) => setInputCaseId(e.target.value.toUpperCase())}
              className="bg-white border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-ashoka-navy font-bold focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] w-full sm:w-60 uppercase tracking-widest shadow-sm placeholder:text-slate-400 placeholder:font-medium placeholder:tracking-normal placeholder:normal-case"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-[#A32A02] hover:bg-[#138808] transition-colors text-white font-bold text-sm px-6 py-2.5 rounded-xl cursor-pointer disabled:opacity-50 shadow-md shrink-0 tracking-tight"
            >
              {loading ? <RefreshCw className="animate-spin" size={16} /> : 'Track'}
            </button>
          </form>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-2xl text-sm font-medium shadow-sm backdrop-blur-sm flex items-center gap-3">
            <AlertCircle size={20} className="text-red-600 shrink-0" />
            <span>⚠️ {error}. Please verify your Case ID / Passkey and try again.</span>
          </div>
        )}

        {/* EMPTY SEARCH STATE */}
        {!caseData && !loading && !error && (
          <div className="mt-12 flex flex-col items-center justify-center text-center animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="w-20 h-20 bg-white/95 border border-slate-300 rounded-full flex items-center justify-center mb-6 shadow-md backdrop-blur-md">
              <Search className="w-10 h-10 text-slate-400" />
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-3 tracking-tight drop-shadow-md">
              Track Your RTI Case Down
            </h2>
            <p className="text-slate-200 max-w-lg mb-12 font-medium leading-relaxed text-sm sm:text-base drop-shadow-sm">
              Enter your 12-character Case ID above to check your statutory 30-day timeline, view accrued Section 20 penalties, and generate court-ready First Appeals.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full text-left">
              <div className="bg-white/95 backdrop-blur-md border border-slate-300 p-6 sm:p-8 rounded-3xl shadow-xl">
                <div className="w-12 h-12 bg-amber-50 rounded-2xl flex items-center justify-center mb-5 border border-amber-200">
                  <Clock className="w-6 h-6 text-amber-600" />
                </div>
                <h3 className="font-extrabold text-ashoka-navy mb-2 text-base tracking-tight">30-Day Statutory Limit</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  Under Section 7(1) of the RTI Act, 2005, the Public Information Officer (PIO) is legally mandated to provide the requested information within 30 calendar days.
                </p>
              </div>
              
              <div className="bg-white/95 backdrop-blur-md border border-slate-300 p-6 sm:p-8 rounded-3xl shadow-xl">
                <div className="w-12 h-12 bg-rose-50 rounded-2xl flex items-center justify-center mb-5 border border-rose-200">
                  <Scale className="w-6 h-6 text-court-maroon" />
                </div>
                <h3 className="font-extrabold text-ashoka-navy mb-2 text-base tracking-tight">Section 20 Penalty Engine</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  Unreasonable delays attract a personal statutory penalty on the PIO of ₹250 per day (up to ₹25,000). Our engine deterministically monitors this legal liability.
                </p>
              </div>
              
              <div className="bg-white/95 backdrop-blur-md border border-slate-300 p-6 sm:p-8 rounded-3xl shadow-xl">
                <div className="w-12 h-12 bg-emerald-50 rounded-2xl flex items-center justify-center mb-5 border border-emerald-200">
                  <FileText className="w-6 h-6 text-emerald-600" />
                </div>
                <h3 className="font-extrabold text-ashoka-navy mb-2 text-base tracking-tight">Automatic First Appeal</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  If the statutory deadline expires without a reply, or if an unlawful exemption is cited, JanAdhikar prepares a court-ready First Appeal under Section 19(1).
                </p>
              </div>
            </div>
          </div>
        )}

        {/* AUTHORITATIVE WATCHDOG DASHBOARD VIEW */}
        {caseData && (
          <div className="space-y-8 animate-in fade-in zoom-in-95 duration-300">
            
            {/* 1. TOP WATCHDOG HERO & PASSKEY BANNER */}
            <div className="bg-white/95 backdrop-blur-md border border-slate-300 rounded-3xl p-6 sm:p-8 shadow-xl text-ashoka-navy">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-slate-200">
                
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <span className="flex h-3 w-3 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-600"></span>
                    </span>
                    <span className="text-xs font-mono font-bold uppercase tracking-widest text-emerald-800 bg-emerald-100 px-3 py-1 rounded-full border border-emerald-300">
                      🛡️ CASE WATCHDOG ACTIVE
                    </span>
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-black text-ashoka-navy tracking-tight">
                    JanAdhikar is automatically monitoring your RTI deadline.
                  </h2>
                  <p className="text-xs sm:text-sm text-slate-600 font-medium max-w-2xl">
                    Every filed RTI is attached to a statutory state engine. Zero accounts required — save your Passkey to check status or appeal anytime.
                  </p>
                </div>

                {/* PASSKEY BOX */}
                <div className="bg-[#FAF8F5] border border-slate-300 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row lg:flex-col items-start sm:items-center lg:items-start justify-between gap-3 shrink-0 shadow-inner">
                  <div>
                    <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-500">
                      YOUR CASE PASSKEY
                    </span>
                    <div className="text-xl font-mono font-black text-ashoka-navy tracking-widest mt-0.5">
                      {caseData.case_id}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleCopyPasskey}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs shadow-sm transition cursor-pointer"
                  >
                    {copiedPasskey ? (
                      <>
                        <Check size={14} className="text-emerald-600" />
                        <span className="text-emerald-700">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy size={14} />
                        <span>Copy Passkey</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* 2. LIVE COUNTDOWN & STATUS BANNER */}
              <div className="pt-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
                
                {/* Countdown Section */}
                <div className="lg:col-span-6 bg-slate-900 text-white rounded-2xl p-5 sm:p-6 shadow-md">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400">
                    {caseData.is_overdue ? 'STATUTORY PERIOD EXPIRED' : 'PIO RESPONSE COUNTDOWN'}
                  </span>
                  
                  {caseData.is_overdue ? (
                    <div className="mt-2 text-court-maroon font-black text-2xl sm:text-3xl tracking-tight text-rose-400">
                      OVERDUE BY {caseData.days_overdue} DAY(S)
                    </div>
                  ) : (
                    <div className="grid grid-cols-4 gap-2 mt-2 text-center">
                      <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700">
                        <div className="text-2xl sm:text-3xl font-mono font-black text-amber-400">
                          {String(countdown.days).padStart(2, '0')}
                        </div>
                        <div className="text-[9px] uppercase font-bold text-slate-400 tracking-wider">Days</div>
                      </div>
                      <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700">
                        <div className="text-2xl sm:text-3xl font-mono font-black text-white">
                          {String(countdown.hours).padStart(2, '0')}
                        </div>
                        <div className="text-[9px] uppercase font-bold text-slate-400 tracking-wider">Hours</div>
                      </div>
                      <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700">
                        <div className="text-2xl sm:text-3xl font-mono font-black text-white">
                          {String(countdown.minutes).padStart(2, '0')}
                        </div>
                        <div className="text-[9px] uppercase font-bold text-slate-400 tracking-wider">Mins</div>
                      </div>
                      <div className="bg-slate-800/80 p-2.5 rounded-xl border border-slate-700">
                        <div className="text-2xl sm:text-3xl font-mono font-black text-emerald-400">
                          {String(countdown.seconds).padStart(2, '0')}
                        </div>
                        <div className="text-[9px] uppercase font-bold text-slate-400 tracking-wider">Secs</div>
                      </div>
                    </div>
                  )}

                  <p className="text-[11px] text-slate-400 mt-3 font-medium">
                    Statutory deadline: {caseData.response_due_date ? new Date(caseData.response_due_date).toLocaleDateString() : 'N/A'} (Section 7(1))
                  </p>
                </div>

                {/* Risk / Legal State Message */}
                <div className="lg:col-span-6 space-y-3">
                  {caseData.watchdog_status === 'DEEMED_REFUSAL' || caseData.is_overdue ? (
                    <div className="bg-rose-50 border border-rose-200 p-5 rounded-2xl text-court-maroon space-y-2">
                      <div className="flex items-center gap-2 font-bold text-sm">
                        <AlertTriangle size={18} className="text-court-maroon shrink-0" />
                        <span>Statutory Response Window Expired (Deemed Refusal)</span>
                      </div>
                      <p className="text-xs text-slate-700 leading-relaxed font-medium">
                        Under <strong>Section 7(2)</strong> of the RTI Act, failure to respond within 30 days is legally treated as a deemed refusal. You are now entitled to file a <strong>Section 19(1) First Appeal</strong> immediately.
                      </p>
                    </div>
                  ) : caseData.watchdog_status === 'RESPONSE_RECEIVED' ? (
                    <div className="bg-sky-50 border border-sky-200 p-5 rounded-2xl text-sky-900 space-y-2">
                      <div className="flex items-center gap-2 font-bold text-sm">
                        <CheckCircle2 size={18} className="text-sky-600 shrink-0" />
                        <span>Public Authority Response Recorded</span>
                      </div>
                      <p className="text-xs text-sky-800 leading-relaxed font-medium">
                        A response has been logged for this case. The statutory clock is halted. If the response was partial, evasive, or denied information, you can generate a First Appeal below.
                      </p>
                    </div>
                  ) : caseData.days_remaining <= 7 ? (
                    <div className="bg-amber-50 border border-amber-200 p-5 rounded-2xl text-amber-900 space-y-2">
                      <div className="flex items-center gap-2 font-bold text-sm">
                        <Clock size={18} className="text-amber-600 shrink-0" />
                        <span>Statutory Deadline Approaching ({caseData.days_remaining} Days Left)</span>
                      </div>
                      <p className="text-xs text-amber-800 leading-relaxed font-medium">
                        Your RTI is in the final week of its statutory window. If the PIO does not dispatch information by {new Date(caseData.response_due_date).toLocaleDateString()}, JanAdhikar will automatically prepare your First Appeal.
                      </p>
                    </div>
                  ) : (
                    <div className="bg-emerald-50 border border-emerald-200 p-5 rounded-2xl text-emerald-900 space-y-2">
                      <div className="flex items-center gap-2 font-bold text-sm">
                        <ShieldCheck size={18} className="text-emerald-600 shrink-0" />
                        <span>PIO Response Window Active</span>
                      </div>
                      <p className="text-xs text-emerald-800 leading-relaxed font-medium">
                        Your RTI application is within the normal statutory period. The concerned Public Information Officer is legally obligated to reply by {new Date(caseData.response_due_date).toLocaleDateString()}.
                      </p>
                    </div>
                  )}
                </div>

              </div>
            </div>

            {/* 3. METRIC CARDS */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              <div className="bg-white/95 backdrop-blur-md border border-slate-300 rounded-3xl p-6 sm:p-8 shadow-xl space-y-2 text-ashoka-navy">
                <span className="text-xs font-bold uppercase text-slate-500 tracking-wider font-sans">
                  Current Case Status
                </span>
                <div className="text-2xl font-black text-emerald-600 tracking-tight">
                  {caseData.watchdog_status?.replace(/_/g, ' ') || 'ACTIVE'}
                </div>
                <p className="text-xs text-slate-500 font-medium">
                  Filed on: {caseData.filing_date ? new Date(caseData.filing_date).toLocaleDateString() : 'N/A'}
                </p>
              </div>

              <div className="bg-white/95 backdrop-blur-md border border-slate-300 rounded-3xl p-6 sm:p-8 shadow-xl space-y-2 text-ashoka-navy">
                <span className="text-xs font-bold uppercase text-slate-500 tracking-wider font-sans">
                  30-Day SLA Milestone
                </span>
                <div className="text-2xl font-black tracking-tight">
                  {caseData.is_overdue ? (
                    <span className="text-court-maroon">Overdue by {caseData.days_overdue} Day(s)</span>
                  ) : (
                    <span className="text-amber-600">
                      {caseData.days_remaining} Days Remaining
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 font-medium">
                  Due: {caseData.response_due_date ? new Date(caseData.response_due_date).toLocaleDateString() : 'N/A'}
                </p>
              </div>

              <div
                className={`border rounded-3xl p-6 sm:p-8 space-y-2 shadow-xl transition-colors backdrop-blur-md ${
                  (caseData.section_20_penalty_inr || 0) > 0
                    ? 'bg-rose-50/95 border-rose-200 text-court-maroon'
                    : 'bg-white/95 border-slate-300 text-ashoka-navy'
                }`}
              >
                <span className="text-xs font-bold uppercase tracking-wider flex items-center justify-between">
                  <span>Section 20 Penalty Accrued</span>
                  <span className="text-[10px] bg-court-maroon text-white px-2.5 py-0.5 rounded-full font-sans tracking-tight font-bold">
                    ₹250 / Day
                  </span>
                </span>
                <div className={`text-3xl font-black tracking-tight ${(caseData.section_20_penalty_inr || 0) > 0 ? 'text-court-maroon' : 'text-ashoka-navy'}`}>
                  ₹{(caseData.section_20_penalty_inr || 0).toLocaleString('en-IN')}
                </div>
                <p className="text-[11px] text-slate-500 font-medium leading-relaxed">
                  Potential statutory exposure calculated under Sec 20(1) (Capped at ₹25,000). Formal penalty subject to Information Commission proceedings.
                </p>
              </div>
            </div>

            {/* 4. VISUAL PROGRESS TIMELINE */}
            <div className="bg-white/95 backdrop-blur-md border border-slate-300 rounded-3xl p-6 sm:p-8 shadow-xl text-ashoka-navy space-y-6">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-2 border-b border-slate-200 pb-4">
                <div>
                  <h3 className="text-lg font-black text-ashoka-navy tracking-tight flex items-center gap-2">
                    <History size={20} className="text-[#FF9933]" />
                    Statutory Progress Timeline
                  </h3>
                  <p className="text-xs text-slate-500 font-medium mt-0.5">
                    Live timeline based on deterministic server-side calculations under the RTI Act, 2005.
                  </p>
                </div>
              </div>

              {/* Step indicator pipeline */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
                {timelineStages.map((stage) => (
                  <div
                    key={stage.id}
                    className={`p-4 rounded-2xl border transition-all flex flex-col justify-between ${
                      stage.current
                        ? 'bg-amber-50/90 border-amber-300 shadow-md ring-2 ring-amber-400/40'
                        : stage.completed
                        ? 'bg-emerald-50/80 border-emerald-200'
                        : 'bg-[#FAF8F5] border-slate-200 opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-mono font-bold text-slate-400">
                        STEP {stage.id}
                      </span>
                      {stage.completed && !stage.current ? (
                        <CheckCircle2 size={16} className="text-emerald-600" />
                      ) : stage.current ? (
                        <span className="h-2.5 w-2.5 rounded-full bg-amber-500 animate-ping" />
                      ) : (
                        <div className="h-3 w-3 rounded-full border border-slate-300" />
                      )}
                    </div>
                    <div>
                      <div className="text-xs font-black text-ashoka-navy tracking-tight">
                        {stage.title}
                      </div>
                      <div className="text-[11px] text-slate-500 font-medium mt-1">
                        {stage.date}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 5. "I RECEIVED A RESPONSE" & PIO ANALYSIS SUITE */}
            <div className="bg-white/95 backdrop-blur-md border border-slate-300 rounded-3xl p-6 sm:p-8 shadow-xl text-ashoka-navy space-y-6">
              <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-200 pb-5">
                <div>
                  <h3 className="text-xl font-extrabold text-ashoka-navy tracking-tight flex items-center gap-2">
                    <Send size={20} className="text-court-maroon" />
                    Public Information Officer (PIO) Response Suite
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-600 font-medium mt-1">
                    Did you receive a reply letter or email from the authority? Log it here for automatic legal analysis.
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => {
                      setPioInputText('');
                      handleRecordResponse();
                    }}
                    disabled={analyzing}
                    className="bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-800 font-bold text-xs px-4 py-2.5 rounded-xl transition cursor-pointer shadow-sm tracking-tight"
                  >
                    ⚡ Flag Deemed Refusal (No Reply)
                  </button>
                </div>
              </div>

              <form onSubmit={handleRecordResponse} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="sm:col-span-1">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 font-sans">
                      Date Response Received
                    </label>
                    <input
                      type="date"
                      value={responseDate}
                      onChange={(e) => setResponseDate(e.target.value)}
                      className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-ashoka-navy font-bold focus:outline-none focus:border-[#FF9933]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5 font-sans">
                    Paste PIO Reply Letter / Email Text
                  </label>
                  <textarea
                    rows={4}
                    value={pioInputText}
                    onChange={(e) => setPioInputText(e.target.value)}
                    placeholder="Paste the official response text received from the PIO here (e.g. exemptions cited, refusal justifications, or partial information)..."
                    className="w-full bg-[#FAF8F5] border border-slate-300 rounded-2xl p-4 text-xs sm:text-sm text-ashoka-navy font-medium focus:outline-none focus:border-[#FF9933] resize-none leading-relaxed placeholder-slate-400"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={analyzing || !pioInputText.trim()}
                    className="py-3 px-6 cursor-pointer bg-[#A32A02] hover:bg-[#138808] transition-colors text-white flex items-center gap-2 shadow-md rounded-xl font-bold text-xs sm:text-sm disabled:opacity-50 tracking-tight"
                  >
                    {analyzing ? (
                      <>
                        <RefreshCw className="animate-spin" size={16} /> Analyzing with Legal AI...
                      </>
                    ) : (
                      <>
                        <Sparkles size={16} /> 🔍 Log & Analyze PIO Reply
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* Analysis Result & Counter Preview */}
              {caseData.exemption_cited && (
                <div className="mt-6 bg-[#FAF8F5] border border-slate-200 rounded-3xl p-6 sm:p-8 space-y-5 shadow-inner">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
                    <span className="text-xs uppercase text-slate-500 font-bold tracking-wider font-sans">
                      Detected Exemption Clause
                    </span>
                    <span className="bg-court-maroon/10 text-court-maroon border border-court-maroon/20 px-4 py-1.5 rounded-full text-xs font-bold shadow-sm font-sans tracking-tight">
                      Section {caseData.exemption_cited}
                    </span>
                  </div>

                  <div>
                    <h4 className="text-base font-extrabold text-ashoka-navy mb-2 tracking-tight">
                      {caseData.precedent_title || 'Legal Counter-Precedent'}
                    </h4>
                    <p className="text-xs sm:text-sm text-slate-700 bg-white border border-slate-300 p-5 rounded-2xl leading-relaxed font-medium shadow-sm">
                      {caseData.legal_counter || 'Information cannot be denied blanketly without establishing public harm.'}
                    </p>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <Link
                      href={`/rti/appeal?case_id=${caseData.case_id}&mode=appeal`}
                      className="bg-ashoka-navy hover:bg-slate-800 border border-slate-700 text-white font-bold text-xs sm:text-sm px-6 py-3.5 rounded-xl transition shadow-md flex items-center gap-2 tracking-tight"
                    >
                      <FileText size={16} className="text-[#FF9933]" />
                      <span>Generate Court-Ready First Appeal (Sec 19(1))</span>
                      <ArrowRight size={16} />
                    </Link>
                  </div>
                </div>
              )}

              {/* Appeal Callout if Deemed Refusal */}
              {(caseData.watchdog_status === 'DEEMED_REFUSAL' || caseData.is_overdue) && !caseData.exemption_cited && (
                <div className="mt-6 bg-rose-50 border border-rose-200 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h4 className="text-sm font-extrabold text-court-maroon">
                      First Appeal Available (Zero-Response / Deemed Refusal)
                    </h4>
                    <p className="text-xs text-slate-600 mt-0.5 font-medium">
                      Since the 30-day statutory window expired with no recorded reply, you are entitled to file a First Appeal before the Appellate Authority under Section 19(1).
                    </p>
                  </div>
                  <Link
                    href={`/rti/appeal?case_id=${caseData.case_id}&mode=appeal`}
                    className="bg-[#A32A02] hover:bg-[#138808] text-white font-bold text-xs px-5 py-3 rounded-xl transition shadow-md shrink-0 flex items-center gap-2 tracking-tight"
                  >
                    <span>Draft First Appeal</span>
                    <ArrowRight size={14} />
                  </Link>
                </div>
              )}
            </div>

          </div>
        )}

      </div>
    </div>
  );
}

export default function TrackPage() {
  return (
    <Suspense 
      fallback={
        <div className="min-h-screen flex flex-col items-center justify-center p-6 text-sm font-bold text-white tracking-wide bg-cover bg-center" style={{ backgroundImage: "url('/bg.image.png')" }}>
          <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin mb-4" />
          Loading JanAdhikar Watchdog...
        </div>
      }
    >
      <TrackPageContent />
    </Suspense>
  );
}
