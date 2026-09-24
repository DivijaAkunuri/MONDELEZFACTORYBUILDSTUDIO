import React from "react";
import { useLocation } from "react-router-dom";
import { Wrench, Zap } from "lucide-react";
import { fmtMoney, fmtNumber } from "@/lib/format";
import Sidebar from "@/components/estimator/Sidebar";

export default function UtilitiesProcess() {
  const location = useLocation();

  const result = location.state?.result;
  const inputs = location.state?.inputs;
  const currency = location.state?.currency ?? "USD";
  const fxRates = location.state?.fxRates ?? {};

  if (!result) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <Wrench className="w-10 h-10 mx-auto mb-3 text-slate-400" />
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

  const utilityRows = result.utilities || [];
  const utilityTotal = Number(result.utilities_total || 0);

  const builtUpArea = Number(
    result.totals?.built_up_area_sqm || 0
  );

  const utilityCostPerSqm = builtUpArea
    ? utilityTotal / builtUpArea
    : 0;

  const activeProject = {
    name: inputs?.project_name ?? "—",
    location: `${inputs?.location_city ?? ""}${
      inputs?.location_country
        ? `, ${inputs.location_country}`
        : ""
    }`,
    builtUp: `${fmtNumber(builtUpArea)} m²`,
    plot: `${fmtNumber(inputs?.plot_area_sqm || 0)} m²`,
    lastSaved: "—",
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar
        currency={currency}
        fxRates={fxRates}
        result={result}
        inputs={inputs}
        activeKey="utilities-process"
        liveRateIndex={result?.live_rate_index}
        activeProject={activeProject}
      />

      <div className="flex-1 min-w-0 overflow-y-auto">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Wrench className="w-5 h-5 text-blue-700" />
            </div>

            <div>
              <h1 className="text-xl font-bold text-slate-900 font-['Manrope']">
                Utilities & Process
              </h1>

              <p className="text-xs text-slate-500">
                Utilities and process systems cost and BOQ
              </p>
            </div>
          </div>
        </div>

        <main className="p-6 space-y-5">

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

            {/* Utilities Cost */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                  <Wrench className="w-5 h-5 text-orange-700" />
                </div>

                <div className="min-w-0">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                    UTILITIES & PROCESS COST
                  </div>

                  <div className="text-xl font-bold text-slate-900 font-['Manrope'] mt-1">
                    {fmtMoney(
                      utilityTotal,
                      "USD",
                      fxRates
                    )}
                  </div>

                  <div className="text-sm text-slate-500">
                    {fmtMoney(
                      utilityTotal,
                      currency,
                      fxRates
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Utilities Cost / m² */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <Wrench className="w-5 h-5 text-blue-700" />
                </div>

                <div className="min-w-0">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                    UTILITIES COST / m²
                  </div>

                  <div className="text-xl font-bold text-slate-900 font-['Manrope'] mt-1">
                    {fmtMoney(
                      utilityCostPerSqm,
                      "USD",
                      fxRates
                    )}{" "}
                    / m²
                  </div>

                  <div className="text-sm text-slate-500">
                    {fmtMoney(
                      utilityCostPerSqm,
                      currency,
                      fxRates
                    )}{" "}
                    / m²
                  </div>
                </div>
              </div>
            </div>

            {/* Utility Systems */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                  <Zap className="w-5 h-5 text-emerald-700" />
                </div>

                <div className="min-w-0">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                    UTILITY SYSTEMS
                  </div>

                  <div className="text-xl font-bold text-slate-900 font-['Manrope'] mt-1">
                    {utilityRows.length}
                  </div>

                  <div className="text-sm text-slate-500">
                    Included systems
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Utilities BOQ */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200">
              <h2 className="text-sm font-semibold text-slate-800 font-['Manrope']">
                Utilities & Process BOQ
              </h2>

              <p className="text-xs text-slate-500 mt-1">
                Utility and process systems included in the estimate
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-[11px] uppercase text-slate-500 font-semibold tracking-wider">
                  <tr>
                    <th className="text-left px-5 py-3">#</th>
                    <th className="text-left px-5 py-3">System</th>
                    <th className="text-left px-5 py-3">Discipline</th>
                    <th className="text-right px-5 py-3">
                      Amount ({currency})
                    </th>
                    <th className="text-right px-5 py-3">
                      % of Utilities Cost
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {utilityRows.map((row, index) => {
                    const pct = utilityTotal
                      ? (
                          (Number(row.amount || 0) /
                            utilityTotal) *
                          100
                        ).toFixed(2)
                      : "0.00";

                    return (
                      <tr
                        key={row.name || index}
                        className="border-t border-slate-100 hover:bg-slate-50"
                      >
                        <td className="px-5 py-3 text-slate-500">
                          {index + 1}
                        </td>

                        <td className="px-5 py-3 text-slate-800 font-medium">
                          {row.name}
                        </td>

                        <td className="px-5 py-3 text-slate-500">
                          {row.discipline}
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

                  {!utilityRows.length && (
                    <tr>
                      <td
                        colSpan="5"
                        className="px-5 py-10 text-center text-slate-500"
                      >
                        No utility systems available for this estimate.
                      </td>
                    </tr>
                  )}
                </tbody>

                <tfoot>
                  <tr className="border-t-2 border-slate-200">
                    <td
                      colSpan="3"
                      className="px-5 py-4 font-semibold text-slate-800"
                    >
                      Total Utilities & Process
                    </td>

                    <td className="px-5 py-4 text-right font-bold text-slate-900">
                      {fmtMoney(
                        utilityTotal,
                        currency,
                        fxRates
                      )}
                    </td>

                    <td className="px-5 py-4 text-right font-semibold">
                      100%
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

        </main>
      </div>
    </div>
  );
}