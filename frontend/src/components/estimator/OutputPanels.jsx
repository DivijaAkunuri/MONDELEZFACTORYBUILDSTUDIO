
import React from "react";
import { CheckCircle2, AlertTriangle, Lightbulb } from "lucide-react";
import { TID } from "@/constants/testIds";
import { fmtMoney, fmtNumber } from "@/lib/format";

export function TabsBar({ tabs, active, onChange }) {
  return (
    <div className="flex space-x-6 border-b border-slate-200 px-2 mb-4 overflow-x-auto">
      {tabs.map((t) => (
        <button
          key={t.key}
          data-testid={TID.tab(t.key)}
          onClick={() => onChange(t.key)}
          className={`py-3 text-sm font-semibold whitespace-nowrap ${
            active === t.key
              ? "text-blue-600 border-b-2 border-blue-600"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function BoqTable({ rows, testid }) {
  if (!rows?.length) return <Empty text="No cost items" />;

  return (
    <div
      data-testid={testid}
      className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm"
    >
      <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 font-['Manrope']">
          Top {rows.length} Cost Items
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-[11px] uppercase text-slate-500 font-semibold tracking-wider">
            <tr>
              <th className="text-left px-4 py-2 w-10">#</th>
              <th className="text-left px-4 py-2">Activity</th>
              <th className="text-right px-4 py-2">Rate (USD)</th>
              <th className="text-right px-4 py-2">Amount (USD)</th>
              <th className="text-right px-4 py-2 w-24">% of Total</th>
            </tr>
          </thead>

          <tbody>
            {rows.map((r, i) => (
              <tr
                key={i}
                data-testid={TID.boqRow(i + 1)}
                className="border-t border-slate-100 hover:bg-slate-50"
              >
                <td className="px-4 py-2 text-slate-500">
                  {r.rank ?? i + 1}
                </td>

                <td className="px-4 py-2 text-slate-800 font-medium">
                  {r.activity}
                </td>

                <td className="px-4 py-2 text-right text-slate-700">
                  {fmtMoney(r.rate, "USD")}
                </td>

                <td className="px-4 py-2 text-right text-slate-900 font-semibold">
                  {fmtMoney(r.amount, "USD")}
                </td>

                <td className="px-4 py-2 text-right text-slate-600">
                  {r.pct_of_total ?? "—"}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function UtilitiesSummary({ utilities, total }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm h-full">
      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
        Utilities Cost Summary (USD $)
      </h3>

      <div className="space-y-2">
        {utilities.map((u) => (
          <div
            key={u.name}
            className="flex items-center justify-between text-sm border-b border-slate-100 pb-2"
          >
            <span className="text-slate-700">{u.name}</span>

            <span className="text-slate-900 font-semibold">
              {fmtMoney(u.amount, "USD")}
            </span>
          </div>
        ))}

        <div className="flex items-center justify-between pt-2 text-sm">
          <span className="text-blue-700 font-semibold">
            Total Utilities Cost
          </span>

          <span className="text-blue-700 font-bold">
            {fmtMoney(total, "USD")}
          </span>
        </div>
      </div>
    </div>
  );
}

export function ProjectOverview({ inputs, totals, onEdit }) {
  const rows = [
    ["Project Type", inputs.project_type],
    ["Industry Type", inputs.industry_type],
    ["Product Category", inputs.product_category],
    ["Building Type", inputs.building_type],
    [
      "Built-up Area (Length × Width × No. of Floors) (m²)",
      `${fmtNumber(totals.built_up_area_sqm)} m²`,
    ],
    ["Location", `${inputs.location_city}, ${inputs.location_country}`],
    ["Region / Tier", `${inputs.region} · ${inputs.location_tier}`],
    ["Seismic Zone", inputs.seismic_zone],
    ["Wind Zone", inputs.wind_zone],
    ["Wind Speed", `${inputs.wind_speed_ms} m/s`],
    ["Soil Type", inputs.soil_type],
    ["Safe Bearing Capacity (SBC) / Soil Type", inputs.sbc_soil_type],
    ["Foundation Type", inputs.foundation_type],
    ["Groundwater Table Depth", inputs.gwt_depth],
    ["Roof Type", inputs.roof_type],
    ["Number of Floors", inputs.num_floors],
    [
      "Production Capacity",
      `${inputs.production_capacity_tpd} tons per day`,
    ],
    ["Floor Height (m)", `${Number(inputs.height_m || 0)} m`],
    ["Bay Spacing (Column) (m)", `${Number(inputs.bay_spacing_m || 0)} m`],
    ["Annual Output", `${fmtNumber(inputs.annual_output_mt)} metric tons`],
    ["Water Availability", inputs.water_availability],
    ["Electrical Grid Reliability", inputs.grid_reliability],
    ["Ambient Temperature", inputs.ambient_temp_range],
    ["Relative Humidity", `${inputs.relative_humidity_pct}%`],
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-800 font-['Manrope']">
          Project Overview
        </h3>

        <button
          data-testid="edit-overview-btn"
          onClick={onEdit}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
        >
          <span className="inline-block">✎</span> Edit
        </button>
      </div>

      <div className="space-y-1.5 max-h-[520px] overflow-y-auto pr-1">
        {rows.map(([k, v]) => (
          <div key={k} className="flex text-[13px]">
            <div className="text-slate-500 w-[42%] flex-shrink-0">
              {k}
            </div>

            <div className="text-slate-500 mr-2">:</div>

            <div className="text-slate-800 font-medium flex-1 truncate">
              {v ?? "—"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AssumptionsBox({ items }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
        Key Assumptions
      </h3>

      <ul className="space-y-2">
        {items.map((t, i) => (
          <li
            key={i}
            className="flex items-start gap-2 text-[13px] text-slate-700"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RisksBox({ items }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
        Risk & Cost Drivers
      </h3>

      <ul className="space-y-2">
        {items.map((t, i) => (
          <li
            key={i}
            className="flex items-start gap-2 text-[13px] text-slate-700"
          >
            <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function OptimizationsBox({ items }) {
  if (!items?.length) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
        Optimization Suggestions
      </h3>

      <ul className="space-y-2">
        {items.map((t, i) => (
          <li
            key={i}
            className="flex items-start gap-2 text-[13px] text-slate-700"
          >
            <Lightbulb className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Empty({ text }) {
  return (
    <div className="text-sm text-slate-500 p-6 bg-white rounded-lg border border-slate-200">
      {text}
    </div>
  );
}
