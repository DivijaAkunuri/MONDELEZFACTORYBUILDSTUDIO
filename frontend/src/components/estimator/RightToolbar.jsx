import React from "react";
import { Edit3, DollarSign, Upload, Sparkles, StickyNote, FileText } from "lucide-react";
import { TID } from "@/constants/testIds";

const tools = [
  { key: "quick-inputs", label: "Quick Inputs", icon: Edit3 },
  { key: "rate-check", label: "Rate Check", icon: DollarSign },
  { key: "drawing-upload", label: "Drawing Upload", icon: Upload },
  { key: "take-off-ai", label: "Take-off (AI)", icon: Sparkles },
  { key: "notes", label: "Notes", icon: StickyNote },
  { key: "audit-log", label: "Audit Log", icon: FileText },
];

export default function RightToolbar({ onAction }) {
  return (
    <aside className="w-[76px] flex-shrink-0 bg-slate-50 border-l border-slate-200 flex flex-col items-center py-4 gap-3">
      {tools.map(({ key, label, icon: Icon }) => (
        <button
          key={key}
          data-testid={TID.rightToolBtn(key)}
          onClick={() => onAction?.(key)}
          className="w-14 h-14 rounded-lg bg-white border border-slate-200 hover:border-blue-400 hover:bg-blue-50 flex flex-col items-center justify-center gap-1 group shadow-sm"
          title={label}
        >
          <Icon className="w-4 h-4 text-slate-600 group-hover:text-blue-600" />
          <span className="text-[9px] leading-tight text-slate-500 group-hover:text-blue-700 text-center px-1">{label}</span>
        </button>
      ))}
    </aside>
  );
}
