'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Loader2, ArrowRight, ArrowLeft, CheckCircle2, ShieldCheck, Sparkles, Edit3, 
  User, Building2, FileCheck2, Clock, Banknote, Scale, Info, AlertCircle
} from 'lucide-react';
import useCaseStore from '@/store/caseStore';
import { classifyCase, rtiGenerate, grievanceGenerate } from '@/lib/api';
import FactsTriageCard from '@/components/dashboard/FactsTriageCard';
import ReadinessScore from '@/components/dashboard/ReadinessScore';

const formatAIText = (text?: string) => {
  if (!text) return null;
  const lines = text.split('\n');
  const result: JSX.Element[] = [];
  let currentList: JSX.Element[] = [];

  const pushList = () => {
    if (currentList.length > 0) {
      result.push(
        <ul key={`list-${result.length}`} className="list-disc pl-5 mb-3 space-y-2 marker:text-slate-400">
          {currentList}
        </ul>
      );
      currentList = [];
    }
  };

  const formatBold = (str: string) => {
    return str.split(/(\*\*.*?\*\*)/g).map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={j} className="font-extrabold text-ashoka-navy tracking-tight">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return <span key={j}>{part}</span>;
    });
  };

  lines.forEach((line, i) => {
    if (!line.trim()) {
      pushList();
      result.push(<div key={`space-${i}`} className="h-2" />);
      return;
    }

    const isBullet = /^(\-|\*|\d+\.)\s+(.*)/.exec(line.trim());
    
    if (isBullet) {
      const content = isBullet[2];
      currentList.push(
        <li key={`item-${i}`} className="leading-relaxed text-sm text-slate-700 font-medium">
          {formatBold(content)}
        </li>
      );
    } else {
      pushList();
      result.push(
        <div key={`line-${i}`} className="mb-2 last:mb-0 leading-relaxed text-sm text-slate-700 font-medium">
          {formatBold(line)}
        </div>
      );
    }
  });
  
  pushList();
  return result;
};

// ─── F.A.C.T.S. / Litigation-Readiness helpers (client-side, mirrors api/facts_engine.py) ───

const RTI_REQUIRED_FIELDS: [string, string][] = [
  ['applicant_name', 'Full Name'],
  ['applicant_address', 'Address'],
  ['applicant_city', 'City'],
  ['applicant_pincode', 'PIN Code'],
  ['target_department', 'Target Authority'],
  ['specific_records', 'Records Requested'],
];

const GRIEVANCE_REQUIRED_FIELDS: [string, string][] = [
  ['applicant_name', 'Full Name'],
  ['applicant_address', 'Address'],
  ['applicant_city', 'City'],
  ['target_department', 'Opposing Party'],
  ['incident_date', 'Incident Date'],
  ['desired_relief', 'Relief Sought'],
];

function computeReadiness(form: Record<string, any>, isRTI: boolean) {
  const fields = isRTI ? RTI_REQUIRED_FIELDS : GRIEVANCE_REQUIRED_FIELDS;
  const missing: string[] = [];
  let filledCount = 0;
  fields.forEach(([key, label]) => {
    if (form?.[key] && String(form[key]).trim()) {
      filledCount++;
    } else {
      missing.push(label);
    }
  });
  const score = fields.length ? Math.round((filledCount / fields.length) * 100) : 0;
  const label =
    score >= 90 ? 'Court Ready' : score >= 60 ? 'Filing Viable' : score >= 30 ? 'Needs Detail' : 'Weak';
  return { score, label, missing };
}

function resolvePecuniaryJurisdictionClient(amountRaw?: string) {
  if (!amountRaw) return null;
  const cleaned = String(amountRaw).replace(/[^\d.]/g, '');
  if (!cleaned) return null;
  const amount = parseFloat(cleaned);
  if (isNaN(amount)) return null;

  let forum = 'District Consumer Disputes Redressal Commission';
  if (amount > 20000000) forum = 'National Consumer Disputes Redressal Commission (NCDRC)';
  else if (amount > 5000000) forum = 'State Consumer Disputes Redressal Commission';

  return { amount, forum };
}

export default function IntakeFormView() {
  const router = useRouter();
  const { 
    caseId, userProblem, language, setClassifyResult, classifyResult, 
    formData, setFormData, setStage, setRtiDraft, setGrievanceResult, reset
  } = useCaseStore();

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [currentStep, setCurrentStep] = useState<0 | 1 | 2 | 3>(0);
  const [localForm, setLocalForm] = useState<Record<string, any>>({});

  useEffect(() => {
    const analyzeAndPreFill = async () => {
      if (!userProblem) {
        router.push('/');
        return;
      }
      try {
        setLoading(true);
        const res = await classifyCase(caseId || '', userProblem, language || 'English');
        setClassifyResult(res);

        const aiExtracted = res.extracted_data || {};
        setLocalForm({
          applicant_name: formData.applicant_name || aiExtracted.applicant_name || '',
          applicant_contact: formData.applicant_contact || aiExtracted.applicant_contact || '',
          applicant_city: formData.applicant_city || aiExtracted.applicant_city || '',
          applicant_state: formData.applicant_state || aiExtracted.applicant_state || '',
          applicant_address: formData.applicant_address || aiExtracted.applicant_address || '',
          applicant_pincode: formData.applicant_pincode || aiExtracted.applicant_pincode || '',
          target_department: formData.target_department || aiExtracted.target_department || '',
          specific_records: formData.specific_records || aiExtracted.specific_records || '',
          time_period: formData.time_period || aiExtracted.time_period || '',
          file_or_work_no: formData.file_or_work_no || aiExtracted.file_or_work_no || '',
          incident_date: formData.incident_date || aiExtracted.incident_date || '',
          financial_loss: formData.financial_loss || aiExtracted.financial_loss || '',
          evidence_available: formData.evidence_available || aiExtracted.evidence_available || '',
          desired_relief: formData.desired_relief || aiExtracted.desired_relief || '',
          statutory_fee: formData.statutory_fee || aiExtracted.statutory_fee || '',
          response_time: formData.response_time || aiExtracted.response_time || '',
        });
      } catch (err) {
        console.error(err);
        alert('Failed to analyze case. Please try again.');
        router.push('/');
      } finally {
        setLoading(false);
      }
    };

    if (!classifyResult) {
      analyzeAndPreFill();
    } else {
      setLocalForm(formData);
      setLoading(false);
    }
  }, [userProblem, caseId, language, classifyResult, formData, router, setClassifyResult, setStage]);

  const handleChange = (key: string, value: string) => {
    setLocalForm(prev => ({ ...prev, [key]: value }));
  };

  const handleNextStep = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setFormData(localForm);
    if (currentStep === 0) setCurrentStep(1);
    else if (currentStep === 1) setCurrentStep(2);
    else if (currentStep === 2) setCurrentStep(3);
  };

  const handleGenerate = async () => {
    if (!classifyResult) return;
    setGenerating(true);
    try {
      if (classifyResult.route === 'RTI') {
        const res = await rtiGenerate(caseId || '', localForm);
        setRtiDraft(res.initial_draft);
        setStage('PREDICTING');
        router.push('/dashboard/rti/result');
      } else if (classifyResult.route === 'Rights/Grievance') {
        const payload = {
          case_id: caseId,
          problem_text: userProblem,
          language: language || 'English',
          form_data: localForm,
        };
        const res = await grievanceGenerate(payload);
        setGrievanceResult(res);
        setStage('GRIEVANCE_COMPLETED');
        router.push('/dashboard/grievance/result');
      }
    } catch (err) {
      console.error(err);
      alert('Generation failed. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div 
        className="min-h-screen flex flex-col items-center justify-center bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/bg.image.png')" }}
      >
        <div className="bg-white/95 backdrop-blur-md p-8 rounded-3xl border border-slate-200 shadow-xl text-center space-y-3">
          <Loader2 className="animate-spin text-[#FF9933] mx-auto" size={40} />
          <h2 className="text-xl font-extrabold text-ashoka-navy tracking-tight">Analyzing Legal Merits...</h2>
          <p className="text-slate-500 text-sm font-medium">Running F.A.C.T.S. triage, resolving jurisdiction, and computing readiness.</p>
        </div>
      </div>
    );
  }

  const isRTI = classifyResult?.route === 'RTI';
  const isOther = classifyResult?.route === 'Other';
  const readiness = computeReadiness(localForm, isRTI);
  const factsChecklist = classifyResult?.facts_analysis?.checklist || [];
  const livePecuniary = !isRTI ? resolvePecuniaryJurisdictionClient(localForm.financial_loss) : null;

  return (
    <div 
      className="min-h-screen p-4 sm:p-6 lg:p-8 flex items-center justify-center font-sans bg-cover bg-center bg-no-repeat relative text-ashoka-navy"
      style={{ backgroundImage: "url('/bg.image.png')" }}
    >
      <div className="w-full max-w-3xl space-y-6 relative z-10">
        
        {!isOther && (
          <div className="bg-white/95 backdrop-blur-md border border-slate-200 rounded-2xl p-4 shadow-sm flex items-center justify-between overflow-x-auto gap-2">
            {[
              { num: 0, label: 'Assessment', icon: Scale },
              { num: 1, label: 'Applicant', icon: User },
              { num: 2, label: 'AI Strategy', icon: Sparkles },
              { num: 3, label: 'Confirm', icon: FileCheck2 },
            ].map((s) => {
              const active = currentStep === s.num;
              const done = currentStep > s.num;
              return (
                <div 
                  key={s.num} 
                  className={`flex items-center gap-2 text-xs sm:text-sm transition-all whitespace-nowrap font-sans tracking-tight font-bold ${
                    active ? 'text-court-maroon' : done ? 'text-statutory-green' : 'text-slate-400'
                  }`}
                >
                  <div className={`font-sans tracking-tight w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center text-[11px] sm:text-xs font-bold shrink-0 ${
                    active 
                      ? 'bg-court-maroon text-white shadow-sm border border-court-maroon/50' 
                      : done 
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-200' 
                      : 'bg-slate-100 text-slate-500 border border-slate-200'
                  }`}>
                    {done ? '✓' : s.num}
                  </div>
                  <span className="hidden sm:inline font-sans tracking-tight">{s.label}</span>
                </div>
              );
            })}
          </div>
        )}

        <div className="flex items-center justify-between px-2">
          <div>
            <span className={`text-xs font-bold uppercase font-sans tracking-tight px-3 py-1 rounded-full border ${isOther ? 'bg-slate-100 text-slate-600 border-slate-200' : 'text-[#FF9933] bg-[#A32A02]/20 border-[#A32A02]/30'}`}>
              Route: {isOther ? 'Out of Platform Scope' : (isRTI ? 'Right to Information (RTI)' : 'Administrative Grievance')}
            </span>
            <h2 className="text-xl sm:text-2xl font-extrabold text-white mt-2 tracking-tight drop-shadow-md">
              {currentStep === 0 && 'Legal Route & Case Assessment'}
              {currentStep === 1 && 'Step 1: Your Contact Information'}
              {currentStep === 2 && 'Step 2: Review AI Legal Strategy'}
              {currentStep === 3 && 'Step 3: Generate Statutory Document'}
            </h2>
          </div>
          {caseId && (
            <span className="text-xs font-mono font-bold text-slate-600 bg-white/95 backdrop-blur-md border border-slate-200 px-3 py-1.5 rounded-xl shadow-xs">
              #{caseId}
            </span>
          )}
        </div>

        <div className="bg-white/95 backdrop-blur-md rounded-3xl p-6 sm:p-8 border border-slate-300 shadow-xl text-left">
          
          {currentStep === 0 && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <div className="p-6 bg-[#FAF8F5] border border-slate-200 rounded-3xl flex flex-col gap-4 shadow-inner text-left">
                
                <div className="flex flex-col gap-1 border-b border-slate-200 pb-5">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1 font-sans">
                    AI Classification Result
                  </span>
                  <h3 className={`font-black text-3xl sm:text-4xl tracking-tight ${isOther ? 'text-slate-700' : isRTI ? 'text-blue-700' : 'text-emerald-700'}`}>
                    {isOther ? 'Out of Scope / Other' : isRTI ? 'Right to Information (RTI)' : 'Formal Legal Grievance'}
                  </h3>
                  <div className="mt-2">
                    <span className="text-sm font-bold font-sans tracking-tight text-court-maroon bg-rose-50 px-3 py-1.5 rounded-lg inline-block border border-rose-200">
                      Category: {classifyResult?.sub_category}
                    </span>
                  </div>
                </div>

                <div className="pt-2">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Detailed Legal Analysis</h4>
                  <div className="text-sm font-medium text-slate-700 leading-relaxed">
                    {formatAIText(classifyResult?.reasoning)}
                  </div>
                </div>
              </div>

              {factsChecklist.length > 0 && (
                <FactsTriageCard checklist={factsChecklist} />
              )}

              {isOther && (
                <div className="p-6 bg-blue-50 border border-blue-200 rounded-3xl text-left shadow-sm">
                  <h4 className="text-base font-bold text-blue-900 flex items-center gap-2 mb-4 pb-2 border-b border-blue-200 tracking-tight">
                    <Info className="text-blue-700" size={20} /> Recommended Action Plan For Your Case
                  </h4>
                  <div className="text-sm text-blue-800 leading-relaxed font-medium">
                    {formatAIText(classifyResult?.specific_advice || 'This case falls outside RTI or Consumer/Administrative grievance jurisdictions. Please consult a local legal professional or the relevant authority for this specific issue.')}
                  </div>
                </div>
              )}

              <div className="pt-6 border-t border-slate-200 flex items-center justify-between">
                <button 
                  onClick={() => { 
                    reset(); 
                    sessionStorage.removeItem('janadhikar_problem'); 
                    router.push('/'); 
                  }} 
                  className="btn-ghost py-3 px-5 border border-slate-300 text-slate-700 hover:bg-slate-50 cursor-pointer font-sans tracking-tight font-bold"
                >
                  <ArrowLeft size={16} /> Start New Case
                </button>
                {!isOther && (
                  <button onClick={() => handleNextStep()} className="btn-primary py-3.5 px-8 flex items-center gap-2 bg-[#A32A02] hover:bg-[#138808] transition-colors text-white rounded-xl shadow-md cursor-pointer font-bold tracking-tight">
                    Proceed to Form Fill <ArrowRight size={18} />
                  </button>
                )}
              </div>
            </div>
          )}

          {currentStep === 1 && (
            <form onSubmit={handleNextStep} className="space-y-5 animate-in fade-in duration-300">
              <p className="text-xs text-slate-600 leading-relaxed mb-4 font-medium">
                Official applications require the physical correspondence identity of the citizen. The AI will handle the technical legal details in the next step.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Your Full Name *</label>
                  <input
                    type="text"
                    required
                    value={localForm.applicant_name}
                    onChange={e => handleChange('applicant_name', e.target.value)}
                    placeholder="e.g. Rohan Sharma"
                    className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm font-medium transition-all"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Phone / Contact Email *</label>
                  <input
                    type="text"
                    required
                    value={localForm.applicant_contact}
                    onChange={e => handleChange('applicant_contact', e.target.value)}
                    placeholder="e.g. 9876543210 / rohan@email.com"
                    className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm font-medium transition-all"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">City / District *</label>
                  <input
                    type="text"
                    required
                    value={localForm.applicant_city}
                    onChange={e => handleChange('applicant_city', e.target.value)}
                    placeholder="e.g. Jaipur"
                    className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm font-medium transition-all"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">State / Union Territory *</label>
                  <input
                    type="text"
                    required
                    value={localForm.applicant_state}
                    onChange={e => handleChange('applicant_state', e.target.value)}
                    placeholder="e.g. Rajasthan"
                    className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm font-medium transition-all"
                  />
                </div>

                <div className="space-y-1.5 sm:col-span-2">
                  <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Postal Address for Response *</label>
                  <input
                    type="text"
                    required
                    value={localForm.applicant_address}
                    onChange={e => handleChange('applicant_address', e.target.value)}
                    placeholder="e.g. House No. 42, Sector 3, Main Road"
                    className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm font-medium transition-all"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">PIN Code *</label>
                  <input
                    type="text"
                    required
                    value={localForm.applicant_pincode}
                    onChange={e => handleChange('applicant_pincode', e.target.value)}
                    placeholder="e.g. 302001"
                    className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm font-medium transition-all"
                  />
                </div>

                <div className="space-y-1.5 sm:col-span-2">
                  <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Evidence / Reference on Record (Optional)</label>
                  <input
                    type="text"
                    value={localForm.evidence_available}
                    onChange={e => handleChange('evidence_available', e.target.value)}
                    placeholder="e.g. Receipt no. 4521, screenshot of chat, application ref no."
                    className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm font-medium transition-all"
                  />
                </div>
              </div>

              <div className="pt-6 border-t border-slate-200 flex items-center justify-between">
                <button type="button" onClick={() => setCurrentStep(0)} className="btn-ghost py-3 px-5 border border-slate-300 text-slate-700 hover:bg-slate-50 cursor-pointer font-sans tracking-tight font-bold">
                  <ArrowLeft size={16} /> Back
                </button>
                <button type="submit" className="btn-primary py-3.5 px-8 flex items-center gap-2 bg-[#A32A02] hover:bg-[#138808] transition-colors text-white rounded-xl shadow-md cursor-pointer font-bold tracking-tight">
                  Next: AI Legal Strategy <ArrowRight size={18} />
                </button>
              </div>
            </form>
          )}

          {currentStep === 2 && (
            <form onSubmit={handleNextStep} className="space-y-6 animate-in fade-in duration-300">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-2xl flex items-start gap-3 shadow-xs">
                <Sparkles className="text-blue-600 mt-0.5 shrink-0" size={18} />
                <p className="text-xs text-blue-900 font-medium leading-relaxed">
                  <strong className="text-ashoka-navy tracking-tight font-bold">AI Strategy Engine:</strong> We have automatically structured the technical legal clauses and target authority based on your problem. <br/><br/>
                  <span className="font-bold text-ashoka-navy tracking-tight">Note: All fields below are optional.</span> If you are unsure about any specifics, leave them blank—the Legal Engine will automatically handle defaults.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#FAF8F5] p-3 rounded-xl border border-slate-300 flex items-center gap-3">
                  <Banknote className="text-slate-500" size={16} />
                  <div>
                    <span className="block text-[10px] font-bold text-slate-500 uppercase">Statutory Fee</span>
                    <span className="text-sm font-bold text-ashoka-navy">{localForm.statutory_fee || (isRTI ? '₹10' : 'N/A')}</span>
                  </div>
                </div>
                <div className="bg-[#FAF8F5] p-3 rounded-xl border border-slate-300 flex items-center gap-3">
                  <Clock className="text-slate-500" size={16} />
                  <div>
                    <span className="block text-[10px] font-bold text-slate-500 uppercase">Mandated Response Time</span>
                    <span className="text-sm font-bold text-ashoka-navy">{localForm.response_time || (isRTI ? '30 Days' : '15 Days')}</span>
                  </div>
                </div>
              </div>

              {isRTI ? (
                <div className="space-y-5">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Target Public Authority / Department</label>
                    <input
                      type="text"
                      value={localForm.target_department}
                      onChange={e => handleChange('target_department', e.target.value)}
                      placeholder="e.g., Public Works Department / Unsure"
                      className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-court-maroon placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm font-bold tracking-tight transition-all"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Certified Legal Queries Generated by AI</label>
                    <textarea
                      rows={4}
                      value={localForm.specific_records}
                      onChange={e => handleChange('specific_records', e.target.value)}
                      placeholder="Leave blank to let AI formulate the exact records requested."
                      className="w-full bg-[#FAF8F5] border border-slate-300 rounded-2xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm resize-none leading-relaxed transition-all"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div className="space-y-1.5">
                      <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Time Period</label>
                      <input
                        type="text"
                        value={localForm.time_period}
                        onChange={e => handleChange('time_period', e.target.value)}
                        placeholder="Leave blank if unsure"
                        className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm transition-all"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Application / File Ref (If Known)</label>
                      <input
                        type="text"
                        value={localForm.file_or_work_no}
                        onChange={e => handleChange('file_or_work_no', e.target.value)}
                        placeholder="Leave blank if none"
                        className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm transition-all"
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-5">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Opposing Party / Authority</label>
                    <input
                      type="text"
                      value={localForm.target_department}
                      onChange={e => handleChange('target_department', e.target.value)}
                      placeholder="e.g., Landlord Name / Company / Unsure"
                      className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-court-maroon placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm font-bold tracking-tight transition-all"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Statutory Relief Demanded</label>
                    <textarea
                      rows={3}
                      value={localForm.desired_relief}
                      onChange={e => handleChange('desired_relief', e.target.value)}
                      placeholder="Leave blank to let AI formulate standard relief based on law."
                      className="w-full bg-[#FAF8F5] border border-slate-300 rounded-2xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm resize-none leading-relaxed transition-all"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div className="space-y-1.5">
                      <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Date of Incident</label>
                      <input
                        type="text"
                        value={localForm.incident_date}
                        onChange={e => handleChange('incident_date', e.target.value)}
                        placeholder="Leave blank if ongoing"
                        className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm transition-all"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-xs font-bold text-ashoka-navy uppercase tracking-wide">Financial Claim (₹)</label>
                      <input
                        type="text"
                        value={localForm.financial_loss}
                        onChange={e => handleChange('financial_loss', e.target.value)}
                        placeholder="Leave blank if not applicable"
                        className="w-full bg-[#FAF8F5] border border-slate-300 rounded-xl p-3.5 text-ashoka-navy placeholder-slate-400 focus:outline-none focus:border-[#FF9933] focus:ring-1 focus:ring-[#FF9933] text-sm transition-all"
                      />
                      {livePecuniary && (
                        <p className="text-[11px] font-bold text-blue-700 mt-1.5">
                          → Pecuniary Jurisdiction: {livePecuniary.forum}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={() => setCurrentStep(1)}
                  className="btn-ghost py-3 px-5 border border-slate-300 text-slate-700 hover:bg-slate-50 cursor-pointer w-full sm:w-auto justify-center font-sans tracking-tight font-bold"
                >
                  <ArrowLeft size={16} /> Back
                </button>
                <button
                  type="submit"
                  className="btn-primary py-3.5 px-8 flex items-center gap-2 bg-[#A32A02] hover:bg-[#138808] transition-colors text-white rounded-xl shadow-md cursor-pointer font-bold tracking-tight w-full sm:w-auto"
                >
                  Proceed to Final Review <ArrowRight size={18} />
                </button>
              </div>
            </form>
          )}

          {currentStep === 3 && (
            <div className="space-y-6 animate-in fade-in duration-300">

              <ReadinessScore label={readiness.label} missingFields={readiness.missing} score={readiness.score} />

              <div className="p-5 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-4 shadow-sm">
                <div className="p-2 bg-amber-100 rounded-full shrink-0 mt-0.5">
                  <AlertCircle className="text-amber-600" size={20} />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-amber-900 uppercase tracking-wide mb-1 font-sans">Important Legal Disclaimer</h4>
                  <p className="text-xs sm:text-sm text-amber-800 leading-relaxed font-medium">
                    JanAdhikar is an AI-assisted legal drafting tool, <strong>not a law firm</strong>. 
                    By clicking confirm, the AI will generate your formal document based on the facts provided above. 
                    <strong className="text-ashoka-navy"> You must personally verify all names, dates, amounts, and claims before officially filing or mailing this document.</strong>
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="bg-[#FAF8F5] p-5 rounded-2xl border border-slate-200 shadow-inner">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-200 mb-3">
                    <h4 className="text-xs font-bold text-court-maroon uppercase tracking-wider flex items-center gap-1.5 font-sans">
                      <User className="text-court-maroon" size={14} /> Identity Record
                    </h4>
                    <button onClick={() => setCurrentStep(1)} className="text-xs font-bold text-slate-500 hover:text-ashoka-navy flex items-center gap-1 transition-colors">
                      <Edit3 size={12} /> Edit
                    </button>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-500 font-bold block">NAME:</span>
                      <span className="font-semibold text-ashoka-navy">{localForm.applicant_name}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 font-bold block">CONTACT:</span>
                      <span className="font-semibold text-ashoka-navy">{localForm.applicant_contact}</span>
                    </div>
                    <div className="sm:col-span-2">
                      <span className="text-slate-500 font-bold block">POSTAL ADDRESS:</span>
                      <span className="font-semibold text-ashoka-navy">{localForm.applicant_address}, {localForm.applicant_city}, {localForm.applicant_state} - {localForm.applicant_pincode}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-[#FAF8F5] p-5 rounded-2xl border border-slate-200 shadow-inner">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-200 mb-3">
                    <h4 className="text-xs font-bold text-court-maroon uppercase tracking-wider flex items-center gap-1.5 font-sans">
                      <Building2 className="text-court-maroon" size={14} /> Legal Specifications
                    </h4>
                    <button onClick={() => setCurrentStep(2)} className="text-xs font-bold text-slate-500 hover:text-ashoka-navy flex items-center gap-1 transition-colors">
                      <Edit3 size={12} /> Edit
                    </button>
                  </div>
                  <div className="space-y-3 text-xs">
                    <div>
                      <span className="text-slate-500 font-bold block">{isRTI ? 'PUBLIC AUTHORITY:' : 'OPPOSING PARTY:'}</span>
                      <span className="font-semibold text-ashoka-navy text-sm tracking-tight">{localForm.target_department || 'Standard Default / As determined by Law'}</span>
                    </div>
                    {isRTI ? (
                      <>
                        <div>
                          <span className="text-slate-500 font-bold block">RECORDS SOUGHT:</span>
                          <p className="font-medium text-slate-700 whitespace-pre-wrap leading-relaxed mt-1">{localForm.specific_records || 'Standard certified records mapping to query'}</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <div>
                          <span className="text-slate-500 font-bold block">REMEDY DEMANDED:</span>
                          <p className="font-medium text-slate-700 leading-relaxed mt-1">{localForm.desired_relief || 'Standard statutory relief with interest'}</p>
                        </div>
                        {livePecuniary && (
                          <div>
                            <span className="text-slate-500 font-bold block">PECUNIARY JURISDICTION:</span>
                            <p className="font-medium text-slate-700 leading-relaxed mt-1">{livePecuniary.forum}</p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  disabled={generating}
                  className="btn-ghost py-3 px-5 border border-slate-300 text-slate-700 hover:bg-slate-50 cursor-pointer w-full sm:w-auto justify-center font-sans tracking-tight font-bold"
                >
                  <ArrowLeft size={16} /> Back
                </button>
                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={generating}
                  className="btn-primary py-4 px-10 flex items-center justify-center gap-2 bg-[#A32A02] hover:bg-[#138808] transition-colors text-white rounded-xl shadow-md cursor-pointer font-bold tracking-tight w-full sm:w-auto"
                >
                  {generating ? (
                    <>
                      <Loader2 className="animate-spin" size={18} />
                      <span>Drafting Statutory Petition...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 size={18} />
                      <span>Confirm & Generate Legal Draft</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
