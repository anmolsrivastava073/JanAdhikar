'use client';
import { CheckCircle2, AlertTriangle, Info, ListChecks } from 'lucide-react';

interface FactsItem {
  id: string;
  label: string;
  status: 'OK' | 'WARNING' | 'NEEDS_INPUT';
  detail: string;
}

interface FactsTriageCardProps {
  checklist: FactsItem[];
}

const STATUS_STYLES: Record<string, { bg: string; border: string; text: string; icon: any }> = {
  OK: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', icon: CheckCircle2 },
  WARNING: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', icon: AlertTriangle },
  NEEDS_INPUT: { bg: 'bg-slate-50', border: 'border-slate-200', text: 'text-slate-600', icon: Info },
};

export default function FactsTriageCard({ checklist }: FactsTriageCardProps) {
  if (!checklist || checklist.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 sm:p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-200">
        <ListChecks size={16} className="text-court-maroon" />
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          F.A.C.T.S. Legal Triage
        </h3>
      </div>
      <div className="space-y-2.5">
        {checklist.map((item) => {
          const s = STATUS_STYLES[item.status] || STATUS_STYLES.NEEDS_INPUT;
          const Icon = s.icon;
          return (
            <div key={item.id} className={`p-3.5 rounded-xl border ${s.bg} ${s.border}`}>
              <div className="flex items-start gap-2.5">
                <Icon size={15} className={`${s.text} mt-0.5 shrink-0`} />
                <div className="min-w-0">
                  <span className={`text-xs font-bold ${s.text}`}>{item.label}</span>
                  <p className="text-xs text-slate-600 font-medium leading-relaxed mt-0.5">
                    {item.detail}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
