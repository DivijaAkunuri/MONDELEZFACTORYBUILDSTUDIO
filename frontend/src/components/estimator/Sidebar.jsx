import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard, Plus, Building2, Zap, Wrench, GitCompareArrows,
  FileOutput, Database, CheckSquare, Settings, HelpCircle,
} from "lucide-react";
import { TID } from "@/constants/testIds";

const items = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard, path: "/" },
  { key: "new-estimate", label: "New Estimate", icon: Plus, path: "/estimator" },
  { key: "civil-scope", label: "Civil Scope", icon: Building2, path: "/civil-scope" },
  { key: "utilities-process", label: "Utilities & Process", icon: Zap, path: "/utilities-process" },
  { key: "infra-external", label: "Infra & External", icon: Wrench, path: "/infra-external" },
  { key: "compare", label: "Compare Options", icon: GitCompareArrows, path: "/compare" },
  { key: "reports", label: "Reports & Export", icon: FileOutput, path: "/reports" },
  { key: "rates", label: "Rate Database", icon: Database, path: "/rates" },
  { key: "approvals", label: "Approvals", icon: CheckSquare, path: "/approvals" },
  { key: "admin", label: "Admin Settings", icon: Settings, path: "/admin" },
  { key: "help", label: "Help & Support", icon: HelpCircle, path: "/help" },
];

export default function Sidebar({ activeProject, fxRates, currency, result, inputs, liveRateIndex }) {
  const navigate = useNavigate();
  const location = useLocation();

  const active = items.find((item) => location.pathname === item.path)?.key || "new-estimate";

  const eurRate = fxRates?.EUR ?? 0.919;
  const eurUsd = (1 / eurRate).toFixed(4);

  const idx = liveRateIndex || {};
  const idxPct = idx.delta_pct;

  const idxColor = idxPct > 0 ? "text-amber-400" : idxPct < 0 ? "text-emerald-400" : "text-slate-300";

  const handleNavigation = (key) => {
    if (key === "new-estimate") {
      navigate("/estimator");
      return;
    }

    if (key === "civil-scope") {
      navigate("/civil-scope", { state: { result, inputs, currency, fxRates } });
      return;
    }

    if (key === "infra-external") {
      navigate("/infra-external", { state: { result, inputs, currency, fxRates } });
      return;
    }

    if (key === "utilities-process") {
      navigate("/utilities-process", { state: { result, inputs, currency, fxRates } });
      return;
    }

    if (key === "reports") {
      navigate("/reports", { state: { result, inputs, currency, fxRates } });
      return;
    }

    const item = items.find((i) => i.key === key);
    if (item?.path) navigate(item.path);
  };

  return (
    <aside data-testid={TID.sidebar} className="sidebar-scroll w-[260px] flex-shrink-0 flex flex-col h-full bg-[#0B1120] text-slate-300 overflow-y-auto">

      {/* Logo */}
      <div className="px-5 pt-5 pb-6 border-b border-slate-800/60 flex items-start gap-3">
        <div className="w-10 h-10 rounded-md bg-slate-800/80 flex items-center justify-center flex-shrink-0">
          <Building2 className="w-6 h-6 text-white" />
        </div>

        <div>
          <div className="text-white font-extrabold text-[15px] leading-tight tracking-tight font-['Manrope']">
            CONSTRUCTION COST<br />ESTIMATOR
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Civil | Utilities | Infra | Food Industry</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3">
        {items.map(({ key, label, icon: Icon }) => {
          const isActive = active === key;

          return (
            <button
              key={key}
              data-testid={TID.navItem(key)}
              onClick={() => handleNavigation(key)}
              className={`w-full flex items-center gap-3 px-5 py-2.5 text-sm font-medium ${isActive
                ? "bg-blue-600 text-white"
                : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-100"
                }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{label}</span>
            </button>
          );
        })}
      </nav>

      {/* Active Project Card */}
      <div className="mx-3 mb-3 p-3 rounded-md bg-slate-900/70 border border-slate-800 text-[12px] leading-snug">
        <div className="text-slate-500 font-semibold uppercase tracking-wider text-[10px] mb-1">Active Project</div>
        <div className="text-white font-semibold mb-2">{activeProject?.name ?? "—"}</div>

        <Row label="Location" value={activeProject?.location} />
        <Row label="Built-up Area" value={activeProject?.builtUp} />
        <Row label="Built-up Area (Length × Width × No. of Floors) (m²)" value={activeProject?.plot} />
        <Row label="Version" value="1.0" />
        <Row label="Last Saved" value={activeProject?.lastSaved ?? "—"} />
      </div>

      {/* Units / Currency / Live Rate Card */}
      <div className="mx-3 mb-4 p-3 rounded-md bg-slate-900/70 border border-slate-800 text-[12px]">
        <Row label="Units" value="All dimensions in mm" />
        <Row label="Currency" value={currency ?? "USD"} />
        <Row label="FX Rate (EUR/USD)" value={eurUsd} />

        <div className="text-[10px] text-slate-500 mt-1">
          ({new Date().toLocaleDateString("en-GB")})
        </div>

        {/* Live Rate Index */}
        {idx.material_index != null && (
          <div className="mt-2 pt-2 border-t border-slate-800">
            <div className="text-slate-500 font-semibold uppercase tracking-wider text-[10px] mb-1">Live Rate Index</div>

            <div className="flex justify-between items-baseline">
              <span className="text-slate-400 text-[11px]">Material Index</span>

              <span className={`font-bold ${idxColor}`}>
                {idx.material_index?.toFixed(3)} ({idxPct >= 0 ? "+" : ""}{idxPct}%)
              </span>
            </div>

            <div className="text-[9px] text-slate-500 mt-0.5">
              {idx.source === "fallback"
                ? "Fallback (baseline)"
                : `Live · ${idx.commodity ?? "commodity"} ${idx.price ?? ""} ${idx.price_unit ?? ""}`}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-2 py-0.5">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-200 text-right truncate max-w-[140px]">{value ?? "—"}</span>
    </div>
  );
}