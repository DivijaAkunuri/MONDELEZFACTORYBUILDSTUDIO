import React from "react";
import { MapPin, Hammer, Wrench, Zap, HardHat } from "lucide-react";

/**
 * CityFactorsCard — shows the resolved city and per-discipline cost factors
 * (civil, mechanical, electrical, labour) that were applied in the calculation.
 * If the entered city was not recognized, we show a subtle notice so users
 * know the estimate is region-average, not city-specific.
 */
export default function CityFactorsCard({ cityFactors, requestedCity }) {
  if (!cityFactors) return null;
  const {
    matched, resolved, civil, mechanical, electrical, labour,
  } = cityFactors;

  const rows = [
    { key: "civil",      label: "Civil",      value: civil,      icon: Hammer,  color: "text-amber-700",  bg: "bg-amber-50" },
    { key: "mechanical", label: "Mechanical", value: mechanical, icon: Wrench,  color: "text-blue-700",   bg: "bg-blue-50" },
    { key: "electrical", label: "Electrical", value: electrical, icon: Zap,     color: "text-purple-700", bg: "bg-purple-50" },
    { key: "labour",     label: "Labour",     value: labour,     icon: HardHat, color: "text-emerald-700",bg: "bg-emerald-50" },
  ];

  return (
    <div data-testid="city-factors-card" className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-800 font-['Manrope']">City Cost Profile</h3>
        <div className="flex items-center gap-1.5 text-xs">
          <MapPin className="w-3.5 h-3.5 text-slate-500" />
          <span className={matched ? "text-slate-800 font-semibold" : "text-slate-500 italic"}>
            {matched ? resolved : (requestedCity || "Not recognized")}
          </span>
        </div>
      </div>
      {!matched && (
        <div data-testid="city-not-matched" className="mb-3 text-[11px] text-amber-700 bg-amber-50 border border-amber-100 rounded px-2 py-1.5">
          City not in database — using region average (all factors = 1.00).
          Try Mumbai, Delhi, Bangalore, Hamburg, London, New York, etc.
        </div>
      )}
      <div className="grid grid-cols-2 gap-2">
        {rows.map(({ key, label, value, icon: Icon, color, bg }) => {
          const pct = ((value - 1) * 100).toFixed(1);
          const isUp = value > 1;
          const isDown = value < 1;
          return (
            <div key={key} data-testid={`city-factor-${key}`} className="flex items-center gap-2 border border-slate-100 rounded-md p-2">
              <div className={`w-8 h-8 rounded-md ${bg} flex items-center justify-center flex-shrink-0`}>
                <Icon className={`w-4 h-4 ${color}`} />
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-[10px] uppercase text-slate-500 font-semibold tracking-wider">{label}</div>
                <div className="flex items-baseline gap-1">
                  <span className="text-sm font-bold text-slate-900">{value?.toFixed(2)}×</span>
                  <span className={`text-[10px] font-semibold ${isUp ? "text-rose-600" : isDown ? "text-emerald-600" : "text-slate-500"}`}>
                    {isUp ? "+" : ""}{pct}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
