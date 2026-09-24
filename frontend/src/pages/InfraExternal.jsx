import React from "react";
import { useLocation } from "react-router-dom";
import { Wrench } from "lucide-react";
import { fmtMoney, fmtNumber } from "@/lib/format";
import Sidebar from "@/components/estimator/Sidebar";

const INFRA_ACTIVITIES = null;

export default function InfraExternal() {
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

  const infraRows = (result.boq || []).filter((row) => row.category === "Infra");
  const infraTotal = infraRows.reduce((sum, row) => sum + Number(row.amount || 0), 0);


  const builtUpArea = Number(
    result.totals?.built_up_area_sqm || 0
  );

  const plotArea = Number(
    result.totals?.plot_area_sqm ||
      inputs?.plot_area_sqm ||
      0
  );

  const infraCostPerSqm = builtUpArea
    ? infraTotal / builtUpArea
    : 0;

  const activeProject = {
    name: inputs?.project_name ?? "—",

    location: `${inputs?.location_city ?? ""}${
      inputs?.location_country
        ? `, ${inputs.location_country}`
        : ""
    }`,

    builtUp: `${fmtNumber(
      builtUpArea
    )} m²`,

    plot: `${fmtNumber(
      plotArea
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
        activeKey="infra-external"
        liveRateIndex={result?.live_rate_index}
        activeProject={activeProject}
      />

      {/* Main Content */}
      <div className="flex-1 min-w-0 overflow-y-auto">
        {/* Header */}
        <div className="bg-white border-b border-slate-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
              <Wrench className="w-5 h-5 text-orange-700" />
            </div>

            <div>
              <h1 className="text-xl font-bold text-slate-900 font-['Manrope']">
                Infra & External
              </h1>

              <p className="text-xs text-slate-500">
                Infrastructure and external works cost and BOQ
              </p>
            </div>
          </div>
        </div>

        <main className="p-6 space-y-5">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

            {/* Infra Cost */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                  <Wrench className="w-5 h-5 text-orange-700" />
                </div>

                <div className="min-w-0">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                    INFRA & EXTERNAL COST
                  </div>

                  <div className="text-xl font-bold text-slate-900 font-['Manrope']">
                    {fmtMoney(
                      infraTotal,
                      "USD",
                      fxRates
                    )}
                  </div>

                  <div className="text-sm text-slate-500">
                    {fmtMoney(
                      infraTotal,
                      currency,
                      fxRates
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Infra Cost / m² */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <Wrench className="w-5 h-5 text-blue-700" />
                </div>

                <div className="min-w-0">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                    INFRA COST / m²
                  </div>

                  <div className="text-xl font-bold text-slate-900 font-['Manrope']">
                    {fmtMoney(
                      infraCostPerSqm,
                      "USD",
                      fxRates
                    )}{" "}
                    / m²
                  </div>

                  <div className="text-sm text-slate-500">
                    {fmtMoney(
                      infraCostPerSqm,
                      currency,
                      fxRates
                    )}{" "}
                    / m²
                  </div>
                </div>
              </div>
            </div>

            {/* Plot Area */}
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                  <Wrench className="w-5 h-5 text-emerald-700" />
                </div>

                <div className="min-w-0">
                  <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                    PLOT AREA
                  </div>

                  <div className="text-xl font-bold text-slate-900 font-['Manrope']">
                    {fmtNumber(plotArea)} m²
                  </div>

                  <div className="text-sm text-slate-500">
                    External works area basis
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Infrastructure BOQ */}
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200">
              <h2 className="text-sm font-semibold text-slate-800 font-['Manrope']">
                Infrastructure & External BOQ
              </h2>

              <p className="text-xs text-slate-500 mt-1">
                Infrastructure and external works included in the estimate
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
                      % of Infra Cost
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {infraRows.map((row, index) => {
                    const pct = infraTotal
                      ? (
                          (Number(row.amount || 0) /
                            infraTotal) *
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
                          <div>
                            {fmtMoney(
                              row.rate,
                              "USD",
                              fxRates
                            )}
                          </div>

                          <div className="text-slate-500">
                            {fmtMoney(
                              row.rate,
                              currency,
                              fxRates
                            )}
                          </div>
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

                  {!infraRows.length && (
                    <tr>
                      <td
                        colSpan="7"
                        className="px-5 py-10 text-center text-slate-500"
                      >
                        No infrastructure items available for this estimate.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}