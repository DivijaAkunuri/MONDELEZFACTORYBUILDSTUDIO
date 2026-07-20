import React from "react";
import { Check } from "lucide-react";
import { TID } from "@/constants/testIds";

const STEPS = [
  "Project Details", "Building Geometry", "Structural & Site",
  "Utilities & Process", "Infra & External", "Output & Review",
];

export default function Stepper({ current = 5, onJump }) {
  return (
    <div data-testid={TID.stepper} className="flex items-center w-full mb-8 px-1">
      {STEPS.map((label, idx) => {
        const isDone = idx < current;
        const isActive = idx === current;
        const num = idx + 1;
        return (
          <React.Fragment key={label}>
            <button
              data-testid={TID.step(num)}
              onClick={() => onJump?.(idx)}
              className="flex items-center gap-2 flex-shrink-0"
            >
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                isDone ? "bg-emerald-100 text-emerald-600" :
                isActive ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-500"
              }`}>
                {isDone ? <Check className="w-4 h-4" /> : num}
              </div>
              <div className="text-left">
                <div className={`text-[13px] font-semibold ${
                  isDone ? "text-emerald-600" : isActive ? "text-blue-600" : "text-slate-500"
                }`}>{label}</div>
                <div className="text-[10px] text-slate-400">
                  {isDone ? "Complete" : isActive ? "In Progress" : "Pending"}
                </div>
              </div>
            </button>
            {idx < STEPS.length - 1 && (
              <div className="flex-1 h-px bg-slate-200 mx-3" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
