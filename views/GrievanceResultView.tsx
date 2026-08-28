'use client';
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Scale, ArrowRight, ArrowLeft, ShieldAlert, CheckCircle2, Globe, ExternalLink, AlertCircle, FileText, Landmark, Clock, BookOpen, Download, Copy, Printer, Check } from 'lucide-react'
import { useRouter } from 'next/navigation'
import useCaseStore from '@/store/caseStore'
import DraftViewer from '@/components/dashboard/DraftViewer'

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
  const prefix = `🚨 ${handles} Urgent civic issue ${locationTag}: `;
  const suffix = `\n\nNeeds immediate resolution! #CitizenRights #Grievance @CPGRAMS`;

  // Twitter standard limit is 280 characters
  const maxAllowedProblemLength = 280 - prefix.length - suffix.length;
  let cleanProblem = (problem || '').trim().replace(/\s+/g, ' ');

  if (cleanProblem.length > maxAllowedProblemLength) {
    // Truncate at word boundary to avoid breaking words
    const slice = cleanProblem.slice(0, maxAllowedProblemLength - 3);
    const lastSpace = slice.lastIndexOf(' ');
    cleanProblem = (lastSpace > 0 ? slice.slice(0, lastSpace) : slice) + '...';
  }

  return `${prefix}${cleanProblem}${suffix}`;
}

export default function GrievanceResultView() {
  const router = useRouter()
  const { caseId, userProblem, formData, grievanceResult, setGrievanceResult, setStage, reset } = useCaseStore()
  const [subStep, setSubStep] = useState(1)

  const defaultProblem = userProblem || "Unlawful withholding of security deposit / consumer deficiency of service"
  const applicantName = formData?.applicant_name || "Applicant"
  const applicantCity = formData?.applicant_city || "Local Jurisdiction"

  const tweetText = buildOptimalTweet(formData?.target_department, applicantCity, defaultProblem);
  const tweetUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}`;

  const activeResult = grievanceResult && grievanceResult.violated_rights && grievanceResult.violated_rights.length > 0
    ? grievanceResult
    : {
        violated_rights: [
          "Transfer of Property Act, 1882 (Section 108 — Lessor's Statutory Liabilities)",
          "Model Tenancy Act & State Rent Control Directives (Unlawful Retention of Security Corpus)",
          "Indian Contract Act, 1872 (Section 73 — Compensation for Breach of Contract)",
          "Consumer Protection Act, 2019 (Section 2(11) Deficiency in Service & Section 2(47) Unfair Trade Practice)"
        ],
        legal_explanation: `Under Indian tenancy law and the Indian Contract Act, 1872, a refundable security deposit is held in fiduciary trust by the property owner/service provider. Upon peaceful handover and clearance of electricity/maintenance dues, the owner is statutorily obligated to refund the principal amount within 30 days. Unilateral retention without producing certified inspection logs, photographic proof of damage, and actual repair receipts constitutes an actionable breach of contract and criminal breach of trust. Under Section 73 of the Indian Contract Act and Consumer Protection jurisprudence, the complainant is entitled to 100% refund along with 18% per annum statutory penal interest from the date of handover.`,
        target_portal_name: "State Rent Authority / e-Daakhil National Consumer Commission",
        target_portal_url: "https://edaakhil.nic.in",
        evidence_analysis: `1. Tenancy Agreement & Security Deposit Receipts: Conclusive proof of financial consideration and terms of refund.\n2. Key Handover Acknowledgment / Move-out Communication: Establishes timely surrender of peaceful possession.\n3. Bank Statements & Transaction Proofs: Confirms complete clearance of all legitimate dues and proves unilateral retention.`,
        demand_notice_draft: `FORMAL LEGAL DEMAND NOTICE
(Under Section 80 CPC read with Consumer Protection Act, 2019 & Indian Contract Act, 1872)

BY SPEED POST WITH ACKNOWLEDGMENT DUE / EMAIL

Date: ${new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
Case Ref: ${caseId || 'CR-GRV-8821'}

To:
The Opposite Party / Respondent,
${applicantCity}

From:
${applicantName}
Address: ${formData?.applicant_address || applicantCity}
Contact: ${formData?.applicant_contact || 'On Record'}

SUBJECT: FINAL STATUTORY DEMAND NOTICE FOR IMMEDIATE RESOLUTION / REFUND WITH 18% STATUTORY INTEREST

Sir/Madam,

Under instructions and on behalf of my client/myself, ${applicantName}, I hereby serve upon you this formal statutory Legal Demand Notice:

1. FACTUAL MATRIX:
   That you entered into a binding contractual arrangement with the undersigned regarding: "${defaultProblem}". The undersigned fulfilled all contractual covenants and paid the agreed consideration in full.

2. STATUTORY DEFICIENCY & BREACH:
   That contrary to statutory obligations and established Indian jurisprudence, you have failed and neglected to refund the legitimate dues / remedy the service defect, causing severe financial loss, mental harassment, and distress.

3. LEGAL LIABILITY:
   Take notice that under Section 73 of the Indian Contract Act, 1872, and Section 2(11) read with Section 2(47) of the Consumer Protection Act, 2019, you are personally and commercially liable for the principal amount, compensation for mental agony, and statutory interest @ 18% per annum.

NOW THEREFORE, you are hereby called upon to:
(a) Effect 100% refund / resolution of the outstanding dispute within FIFTEEN (15) DAYS from the receipt of this notice.
(b) Pay statutory interest @ 18% p.a. from the date the amount became due until final realization.
(c) Pay Rs. 25,000/- towards litigation expenses and legal notice charges.

Failure to comply shall constrain the undersigned to initiate formal proceedings before the Competent Consumer Commission (e-Daakhil) / Civil Court entirely at your risk, cost, and legal consequences.

Yours faithfully,

${applicantName}
(Complainant / Aggrieved Party)`,
        pecuniary_jurisdiction: null,
        statute_of_limitations: null,
      }

  const {
    violated_rights = [],
    legal_explanation = '',
    target_portal_name = '',
    target_portal_url = '',
    evidence_analysis = '',
    demand_notice_draft = '',
    pecuniary_jurisdiction = null,
    statute_of_limitations = null,
  } = activeResult

  return (
    <div 
      className="min-h-screen flex flex-col items-center justify-center p-4 py-12 bg-cover bg-center bg-no-repeat relative font-sans tracking-tight"
      style={{ backgroundImage: "url('/bg.image.png')" }}
    >
      <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-4xl relative z-10">
        
        {subStep === 1 ? (
          <div className="space-y-6">
            <div className="text-center sm:text-left">
              <div className="mb-3">
                <span className="text-xs font-bold uppercase font-sans tracking-tight text-court-maroon bg-rose-50 px-3 py-1 rounded-full border border-rose-200 shadow-sm">
                  STEP 3 · Institutional Legal Analysis
                </span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-extrabold text-white mb-2 tracking-tight drop-shadow-md">
                Identified Rights & Statutory Violations
              </h1>
              <p className="text-blue-100 text-sm sm:text-base leading-relaxed font-medium drop-shadow-sm">
                Based on your statement, our legal engine has analyzed the specific Indian statutory provisions, consumer protections, and case law precedents applicable to your case.
              </p>
            </div>

            <div className="bg-white/95 backdrop-blur-sm border border-slate-300 rounded-2xl p-4 sm:p-5 text-left flex items-start gap-3 shadow-sm">
              <BookOpen className="w-5 h-5 text-court-maroon mt-0.5 shrink-0" />
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">Citizen Matter on Record:</span>
                <p className="text-sm font-semibold text-ashoka-navy mt-0.5">{defaultProblem}</p>
              </div>
            </div>

            <div className="bg-white/95 backdrop-blur-sm border border-slate-300 rounded-3xl p-6 sm:p-8 shadow-xl space-y-6 text-left">
              
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <ShieldAlert className="w-4 h-4 text-court-maroon" />
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Applicable Acts & Violated Legal Provisions</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {violated_rights.map((right: string, idx: number) => (
                    <div key={idx} className="p-4 bg-rose-50/70 border border-rose-200/80 rounded-2xl flex items-start gap-3 shadow-sm">
                      <span className="w-6 h-6 rounded-full bg-court-maroon text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <div>
                        <p className="text-xs font-bold text-court-maroon leading-snug">{right}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-slate-200 pt-6">
                <div className="flex items-center gap-2 mb-3">
                  <Scale className="w-4 h-4 text-statutory-green" />
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Legal Analysis & Fiduciary Rights</h3>
                </div>
                <div className="bg-[#FAF8F5] p-5 sm:p-6 rounded-2xl border border-slate-200 text-sm text-ashoka-navy leading-relaxed font-medium shadow-inner">
                  {legal_explanation}
                </div>
              </div>

              <div className="border-t border-slate-200 pt-6">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Evidentiary Audit & Key Proofs Required</h3>
                </div>
                <div className="bg-[#FAF8F5] p-5 sm:p-6 rounded-2xl border border-slate-200 text-sm text-ashoka-navy leading-relaxed whitespace-pre-line font-medium shadow-inner">
                  {evidence_analysis}
                </div>
              </div>

              {(pecuniary_jurisdiction?.amount_parsed != null || (statute_of_limitations?.status && statute_of_limitations.status !== 'UNKNOWN' && statute_of_limitations.status !== 'NOT_APPLICABLE')) && (
                <div className="border-t border-slate-200 pt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {pecuniary_jurisdiction?.amount_parsed != null && (
                    <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-blue-800 bg-blue-100 px-2 py-0.5 rounded">
                        Pecuniary Jurisdiction
                      </span>
                      <h4 className="text-sm font-bold text-slate-900 mt-2 tracking-tight">{pecuniary_jurisdiction.forum_name}</h4>
                      <p className="text-xs text-slate-600 mt-1 font-medium leading-relaxed">{pecuniary_jurisdiction.reasoning}</p>
                    </div>
                  )}
                  {statute_of_limitations?.status && statute_of_limitations.status !== 'UNKNOWN' && statute_of_limitations.status !== 'NOT_APPLICABLE' && (
                    <div className={`rounded-2xl p-5 border ${statute_of_limitations.status === 'EXPIRED' ? 'bg-rose-50 border-rose-200' : 'bg-emerald-50 border-emerald-200'}`}>
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${statute_of_limitations.status === 'EXPIRED' ? 'text-rose-800 bg-rose-100' : 'text-emerald-800 bg-emerald-100'}`}>
                        Statute of Limitations
                      </span>
                      <h4 className="text-sm font-bold text-slate-900 mt-2 tracking-tight">
                        {statute_of_limitations.status === 'EXPIRED' ? 'Filing Window Elapsed' : 'Within Filing Window'}
                      </h4>
                      <p className="text-xs text-slate-600 mt-1 font-medium leading-relaxed">{statute_of_limitations.message}</p>
                    </div>
                  )}
                </div>
              )}

              {target_portal_name && (
                <div className="border-t border-slate-200 pt-6">
                  <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded">
                        Statutory Forum
                      </span>
                      <h4 className="text-base font-bold text-slate-900 mt-1 tracking-tight">{target_portal_name}</h4>
                      <p className="text-xs text-slate-600 mt-0.5 font-medium">Recommended statutory appellate authority & online filing portal</p>
                    </div>
                    {target_portal_url && (
                      <a
                        href={target_portal_url}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-ghost text-xs py-2 px-4 gap-1.5 bg-white border border-emerald-300 text-emerald-800 hover:bg-emerald-100 shrink-0 self-start sm:self-auto font-bold tracking-tight shadow-sm"
                      >
                        <Globe size={14} /> Open Portal <ExternalLink size={12} />
                      </a>
                    )}
                  </div>
                </div>
              )}

              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-6 border-t border-slate-200">
                <button
                  onClick={() => router.push('/dashboard/intake')}
                  className="btn-ghost text-sm py-3 px-5 border border-slate-300 cursor-pointer w-full sm:w-auto justify-center bg-white text-slate-700 hover:bg-slate-50 font-bold tracking-tight"
                >
                  <ArrowLeft size={16} /> Edit Applicant Details
                </button>
                <button
                  onClick={() => setSubStep(2)}
                  className="btn-primary text-base py-3.5 px-8 cursor-pointer w-full sm:w-auto justify-center shadow-md bg-[#A32A02] hover:bg-[#138808] transition-colors text-white font-bold"
                >
                  View Ready-to-File Notice <ArrowRight size={18} />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <span className="text-xs font-bold uppercase font-sans tracking-tight text-court-maroon bg-rose-50 px-3 py-1 rounded-full border border-rose-200 shadow-sm">
                  STEP 4 · Formal Legal Demand Notice
                </span>
                <h1 className="text-3xl sm:text-4xl font-extrabold text-white mt-2 tracking-tight drop-shadow-md">
                  Ready-to-File Legal Notice
                </h1>
              </div>
              {caseId && (
                <span className="text-xs font-mono font-bold text-slate-600 bg-white/95 backdrop-blur-sm px-3 py-1 rounded-xl border border-slate-300 shadow-xs self-start sm:self-auto">
                  Case ID: #{caseId}
                </span>
              )}
            </div>

            <p className="text-blue-100 text-sm leading-relaxed text-left font-medium drop-shadow-sm">
              Your formal legal demand notice has been drafted in compliance with <strong>Section 80 CPC</strong> and the <strong>Consumer Protection Act, 2019</strong>.
            </p>

            <div className="space-y-6 text-left">
              <DraftViewer caseId={caseId} draft={demand_notice_draft} title="Statutory Legal Demand Notice" />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white/95 backdrop-blur-sm border border-slate-300 rounded-2xl p-5 text-left shadow-xs flex flex-col justify-between h-full">
                  <div>
                    <h4 className="text-xs font-bold text-ashoka-navy uppercase tracking-wider flex items-center gap-1.5 mb-2">
                      <Clock className="w-4 h-4 text-court-maroon" /> Recommended Service Instructions
                    </h4>
                    <ul className="text-xs text-slate-600 space-y-1.5 pl-4 list-disc leading-relaxed font-medium">
                      <li>Send this notice via <strong>Speed Post with Acknowledgment Due (AD)</strong> or Registered Email.</li>
                      <li>Give the opposite party <strong>15 calendar days</strong> to comply from receipt.</li>
                      <li>If unresolved, submit the postal receipt and this notice to <strong>{target_portal_name || 'e-Daakhil'}</strong>.</li>
                    </ul>
                  </div>
                </div>

                <div className="bg-sky-50 border border-sky-200 rounded-2xl p-5 text-left shadow-sm flex flex-col justify-between h-full">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1.5 bg-sky-100 rounded-full">
                        <Globe className="text-sky-600" size={16} />
                      </div>
                      <h4 className="text-xs font-bold text-sky-900 uppercase tracking-wide">Social Media Escalation</h4>
                    </div>
                    <p className="text-xs text-sky-800 leading-relaxed font-medium mb-3">
                      Public visibility accelerates administrative action. Generate a pre-filled Twitter/X post tagging relevant authorities based on your grievance.
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

              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3 text-left shadow-sm">
                <AlertCircle className="text-amber-600 mt-0.5 shrink-0" size={18} />
                <p className="text-xs text-amber-900 leading-relaxed font-medium">
                  <strong>Statutory Notice Disclaimer:</strong> This legal notice has been generated by JanAdhikar's institutional AI engine. Please verify all party names, addresses, and transaction amounts before service.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
                <button
                  onClick={() => setSubStep(1)}
                  className="btn-ghost text-sm py-3 px-5 border border-slate-300 cursor-pointer w-full sm:w-auto justify-center bg-white text-slate-700 hover:bg-slate-50 font-bold tracking-tight"
                >
                  <ArrowLeft size={16} /> Back to Rights Analysis
                </button>
                <button
                  onClick={() => { 
                    reset(); 
                    sessionStorage.removeItem('janadhikar_problem');
                    router.push('/'); 
                  }}
                  className="btn-primary text-sm py-3 px-6 cursor-pointer w-full sm:w-auto justify-center bg-[#A32A02] hover:bg-[#138808] transition-colors text-white font-bold shadow-md"
                >
                  Start Another Case
                </button>
              </div>
            </div>
          </div>
        )}

      </motion.div>
    </div>
  )
}
