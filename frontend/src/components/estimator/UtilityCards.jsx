
import React from "react";
import {
  Droplets,
  Flame,
  Snowflake,
  Zap,
  Wind,
  Recycle,
  ShieldAlert,
} from "lucide-react";
import { TID } from "@/constants/testIds";
import { fmtNumber } from "@/lib/format";

const CARDS = [
  {
    key: "water",
    label: "Water Demand",
    unit: "kilolitres/day (kL/day)",
    field: "water_kld",
    icon: Droplets,
    color: "text-sky-600",
    bg: "bg-sky-50",
  },
  {
    key: "steam",
    label: "Steam Demand",
    unit: "kilograms/hour (kg/hr)",
    field: "steam_kg_hr",
    icon: Flame,
    color: "text-rose-600",
    bg: "bg-rose-50",
  },
  {
    key: "chiller",
    label: "Chiller Load",
    unit: "tons of refrigeration (TR)",
    field: "chiller_tr",
    icon: Snowflake,
    color: "text-cyan-600",
    bg: "bg-cyan-50",
  },
  {
    key: "power",
    label: "Electrical Power Load",
    unit: "kilovolt-amperes (kVA)",
    field: "power_kva",
    icon: Zap,
    color: "text-amber-600",
    bg: "bg-amber-50",
  },
  {
    key: "air",
    label: "Compressed Air Demand",
    unit: "cubic feet/minute (CFM)",
    field: "compressed_air_cfm",
    icon: Wind,
    color: "text-slate-600",
    bg: "bg-slate-100",
  },
  {
    key: "etp",
    label: "Effluent Treatment Plant (ETP) Capacity",
    unit: "kilolitres/day (kL/day)",
    field: "etp_kld",
    icon: Recycle,
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  {
    key: "fire",
    label: "Fire Water Tank Capacity",
    unit: "cubic metres (m³)",
    field: "fire_water_m3",
    icon: ShieldAlert,
    color: "text-red-600",
    bg: "bg-red-50",
  },
];

export default function UtilityCards({ demand }) {
  if (!demand) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 w-full">
      {CARDS.map(({ key, label, unit, field, icon: Icon, color, bg }) => (
        <div
          key={key}
          data-testid={TID.utilityCard(key)}
          className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center gap-3"
        >
          <div
            className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center flex-shrink-0`}
          >
            <Icon className={`w-5 h-5 ${color}`} />
          </div>

          <div className="min-w-0">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold whitespace-normal leading-4">
              {label}
            </div>

            <div className="text-base font-bold text-slate-900 font-['Manrope']">
              {fmtNumber(demand[field])}
              <span className="block text-[11px] font-normal text-slate-500 leading-4">
                {unit}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

