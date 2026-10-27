import React from "react";
import { useLocation } from "react-router-dom";
import { Building2 } from "lucide-react";
import { fmtMoney, fmtNumber } from "@/lib/format";
import Sidebar from "@/components/estimator/Sidebar";

const CIVIL_ACTIVITIES = [
  "Excavation",
  "PCC (M10)",
  "RCC Foundation (Raft)",
  "Structural Steel (PEB)",
  "RCC Superstructure",
  "Roofing (Insulated Panel)",
  "Flooring (Epoxy + PU)",
  "Walls (Block + Plaster + Tile)",
  "Plumbing & Sanitary",
];

export default function CivilScope() {
  const location = useLocation();

  const result = location.state?.result;
  const inputs = location.state?.inputs;
  const currency = location.state?.currency ?? "USD";
  const fxRates = location.state?.fxRates ?? {};

  if (!result) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <Building2 className="w-10 h-10 mx-auto mb-3 text-slate-400" />

          <h2 className="text-lg font-semibold text-slate-800">
            No estimate loaded
          </h2>

          <p className="text-sm text-slate-500 mt-1">
            Please calculate an estimate first.
          </p>
        </div>
      </div>
    );
  }

  const civilRows = (result.boq || []).filter((row) =>
    CIVIL_ACTIVITIES.includes(row.activity)
  );

  const civilTotal = civilRows.reduce(
    (sum, row) => sum + Number(row.amount || 0),
    0
  );

  const builtUpArea = Number(
    result.totals?.built_up_area_sqm || 0
  );

  const civilCostPerSqm = builtUpArea
    ? civilTotal / builtUpArea
    : 0;

  const activeProject = {
    name: inputs?.project_name ?? "—",
    location: `${inputs?.location_city ?? ""}${
      inputs?.location_country
        ? `, ${inputs.location_country}`
        : ""
    }`,
    builtUp: `${fmtNumber(
      (inputs?.length_m || 0) *
        (inputs?.width_m || 0) *
        (inputs?.num_floors || 0)
    )} m²`,
    lastSaved: "—",
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <Sidebar
        currency={currency}
        fxRates={fxRates}
        result={result}
        inputs={inputs}
        activeKey="civil-scope"
        liveRateIndex={result?.live_rate_index}
        activeProject={activeProject}
      />

      {/* Main Content */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-blue-700" />
            </div>

            <div>
              <h1 className="text-xl font-bold text-slate-900 font-['Manrope']">
                Civil Scope
              </h1>

              <p className="text-xs text-slate-500">
                Civil construction cost and BOQ
              </p>
            </div>
          </div>
        </div>

        <main className="p-6 space-y-5">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Civil Cost */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-blue-700" />
                </div>

                <div className="min-w-0">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                    CIVIL COST
                  </div>

                  <div className="text-xl font-bold text-slate-900 font-['Manrope']">
                    {fmtMoney(
                      civilTotal,
                      "USD",
                      fxRates
                    )}
                  </div>

                  <div className="text-sm text-slate-500">
                    {fmtMoney(
                      civilTotal,
                      currency,
                      fxRates
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Civil Cost / m² */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-purple-700" />
                </div>

                <div className="min-w-0">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                    CIVIL COST / m²
                  </div>

                  <div className="text-xl font-bold text-slate-900 font-['Manrope']">
                    {fmtMoney(
                      civilCostPerSqm,
                      "USD",
                      fxRates
                    )}{" "}
                    / m²
                  </div>

                  <div className="text-sm text-slate-500">
                    {fmtMoney(
                      civilCostPerSqm,
                      currency,
                      fxRates
                    )}{" "}
                    / m²
                  </div>
                </div>
              </div>
            </div>

            {/* Built-up Area */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-emerald-700" />
                </div>

                <div className="min-w-0">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                    BUILT-UP AREA
                  </div>

                  <div className="text-xl font-bold text-slate-900 font-['Manrope']">
                    {fmtNumber(builtUpArea)} m²
                  </div>

                  <div className="text-sm text-slate-500">
                    Civil scope area basis
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Civil BOQ */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200">
              <h2 className="text-sm font-semibold text-slate-800 font-['Manrope']">
                Civil BOQ
              </h2>

              <p className="text-xs text-slate-500 mt-1">
                Civil construction activities included in the estimate
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-[11px] uppercase text-slate-500 font-semibold tracking-wider">
                  <tr>
                    <th className="text-left px-5 py-3">
                      #
                    </th>

                    <th className="text-left px-5 py-3">
                      Activity
                    </th>

                    <th className="text-right px-5 py-3">
                      Quantity
                    </th>

                    <th className="text-left px-5 py-3">
                      Unit
                    </th>

                    <th className="text-right px-5 py-3">
                      Rate (USD / {currency})
                    </th>

                    <th className="text-right px-5 py-3">
                      Amount ({currency})
                    </th>

                    <th className="text-right px-5 py-3">
                      % of Civil Cost
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {civilRows.map((row, index) => {
                    const pct = civilTotal
                      ? (
                          (Number(row.amount || 0) /
                            civilTotal) *
                          100
                        ).toFixed(2)
                      : "0.00";

                    return (
                      <tr
                        key={index}
                        className="border-t border-slate-100 hover:bg-slate-50"
                      >
                        <td className="px-5 py-3 text-slate-500">
                          {index + 1}
                        </td>

                        <td className="px-5 py-3 text-slate-800 font-medium">
                          {row.activity}
                        </td>

                        <td className="px-5 py-3 text-right text-slate-700">
                          {fmtNumber(
                            row.quantity,
                            2
                          )}
                        </td>

                        <td className="px-5 py-3 text-slate-500">
                          {row.unit}
                        </td>

                        <td className="px-5 py-3 text-right text-slate-700">
                          {fmtMoney(
                            row.rate,
                            "USD",
                            fxRates
                          )}
                          <br />
                          {fmtMoney(
                            row.rate,
                            currency,
                            fxRates
                          )}
                        </td>

                        <td className="px-5 py-3 text-right text-slate-900 font-semibold">
                          {fmtMoney(
                            row.amount,
                            currency,
                            fxRates
                          )}
                        </td>

                        <td className="px-5 py-3 text-right text-slate-600">
                          {pct}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}