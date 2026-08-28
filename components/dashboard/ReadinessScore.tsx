'use client';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

interface ReadinessScoreProps {
  score: number;
  label: string;
  missingFields?: string[];
}

export default function ReadinessScore({ score, label, missingFields = [] }: ReadinessScoreProps) {
  const color =
    score >= 90 ? '#059669' : score >= 60 ? '#2563EB' : score >= 30 ? '#D97706' : '#DC2626';

  const Icon = score >= 90 ? CheckCircle2 : score >= 30 ? AlertTriangle : XCircle;

  return (
    <div className="bg-[#FAF8F5] border border-slate-200 rounded-2xl p-5 shadow-inner">
      <div className="flex items-center justify-between mb-3 gap-3">
        <div className="flex items-center gap-2">
          <Icon size={18} style={{ color }} />
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Litigation-Readiness Score
          </span>
        </div>
        <span className="text-sm font-black tracking-tight shrink-0" style={{ color }}>
          {score}% — {label}
        </span>
      </div>

      <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden shadow-inner">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="h-full rounded-full"
          style={{ background: color }}
        />
      </div>

      {missingFields.length > 0 && (
        <div className="mt-3">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wide block mb-1.5">
            To reach 99% Court-Ready:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {missingFields.map((f) => (
              <span
                key={f}
                className="text-[11px] font-semibold text-amber-800 bg-amber-50 border border-amber-200 px-2 py-1 rounded-lg"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
