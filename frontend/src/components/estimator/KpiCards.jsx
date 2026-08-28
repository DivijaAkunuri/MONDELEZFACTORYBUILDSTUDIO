import React from "react";
import { DollarSign, Grid3x3, Calendar, ShieldCheck, PieChart, TrendingUp } from "lucide-react";
import { TID } from "@/constants/testIds";
import { fmtMoney, fmtNumber, CURRENCY_SYMBOLS } from "@/lib/format";

export default function KpiCards({ totals, currency, fxRates }) {
  if (!totals) return null;
  const t = totals;
  const cards = [
    {
      key: "total-cost", label: "TOTAL PROJECT COST",
      value: fmtMoney(t.total_project_cost, currency, fxRates),
      sub: "(Including all factors)",
      icon: DollarSign, iconBg: "bg-slate-900", iconClr: "text-white",
    },
    {
      key: "cost-per-sqm", label: "COST / m² (BUILT-UP)",
      value: `${fmtMoney(t.cost_per_sqm, "USD", fxRates)} /m²`,
      sub: `${fmtMoney(t.cost_per_sqm, currency, fxRates)} /m² • Built-up Area : ${fmtNumber(t.built_up_area_sqm)} m²`,
      icon: Grid3x3, iconBg: "bg-purple-100", iconClr: "text-purple-700",
    },
    {
      key: "duration", label: "PROJECT DURATION",
      value: `${t.duration_months} Months`,
      sub: "Estimated",
      icon: Calendar, iconBg: "bg-emerald-100", iconClr: "text-emerald-700",
    },
    {
      key: "confidence", label: "CONFIDENCE SCORE",
      value: `${t.confidence_score}%`,
      sub: t.confidence_label,
      icon: ShieldCheck, iconBg: "bg-amber-100", iconClr: "text-amber-700",
    },
    {
      key: "contingency", label: "CONTINGENCY",
      value: fmtMoney(t.contingency, currency, fxRates),
      sub: `${t.contingency_pct}% of Total Cost`,
      icon: PieChart, iconBg: "bg-rose-100", iconClr: "text-rose-700",
    },
    {
      key: "benchmark", label: "REGION BENCHMARK",
      value: `${t.region_benchmark_delta_pct >= 0 ? "+" : ""}${t.region_benchmark_delta_pct}%`,
      sub: "vs Global Average",
      icon: TrendingUp, iconBg: "bg-blue-100", iconClr: "text-blue-700",
    },
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
      {cards.map(({ key, label, value, sub, icon: Icon, iconBg, iconClr }) => (
        <div
          key={key}
          data-testid={TID.kpiCard(key)}
          className="flex items-center gap-3 p-4 bg-white border border-slate-200 rounded-lg shadow-sm"
        >
          <div className={`w-11 h-11 rounded-lg ${iconBg} flex items-center justify-center flex-shrink-0`}>
            <Icon className={`w-5 h-5 ${iconClr}`} />
          </div>
          <div className="min-w-0">
            <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">{label}</div>
            <div className="text-lg font-bold text-slate-900 truncate font-['Manrope']">{value}</div>
            <div className="text-[10px] text-slate-500 truncate">{sub}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
