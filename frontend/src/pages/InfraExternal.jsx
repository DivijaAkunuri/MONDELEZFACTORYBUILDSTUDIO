
import React from "react";
import { useLocation } from "react-router-dom";
import { Wrench, Route, Trees, Fence } from "lucide-react";
import { fmtMoney, fmtNumber } from "@/lib/format";
import Sidebar from "@/components/estimator/Sidebar";

const INFRA_ACTIVITIES = [
  "External Works & Roads",
  "Roads",
  "Pathways",
  "Parking Bays",
  "Compound Wall / Fence",
  "Compound Wall",
  "Fence",
  "Landscaping",
  "External / Site Development",
];

function isInfraRow(row) {
  const activity = String(row.activity || "").toLowerCase();
  const category = String(row.category || "").toLowerCase();

  return (
    category.includes("infra") ||
    category.includes("external") ||
    INFRA_ACTIVITIES.some((name) =>
      activity.includes(name.toLowerCase())
    )
  );
}

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

  const infraRows = (result.boq || []).filter(isInfraRow);

  const infraBreakdownTotal = Number(
    (result.breakdown || []).find((item) => {
      const name = String(item.name || "").toLowerCase();
      return (
        name.includes("infra") ||
        name.includes("external") ||
        name.includes("site development")
      );
    })?.value || 0
  );

  const infraBoqTotal = infraRows.reduce(
    (sum, row) => sum + (Number(row.amount) || 0),
    0
  );

  const infraTotal =
    infraBreakdownTotal > 0 ? infraBreakdownTotal : infraBoqTotal;

  const builtUpArea = Number(
    result.totals?.built_up_area_sqm || 0
  );

  const landArea = Number(inputs?.land_area_sqm || 0);

  const infraCostPerSqm =
    builtUpArea > 0 ? infraTotal / builtUpArea : 0;

  const activeProject = {
    name: inputs?.project_name ?? "—",
    location: `${inputs?.location_city ?? ""}${inputs?.location_country
        ? `, ${inputs.location_country}`
        : ""
      }`,
    builtUp: `${fmtNumber(builtUpArea)} m²`,
    lastSaved: "—",
  };

  const activityGroups = [
    {
      title: "Roads, Pathways & Parking",
      description:
        "External roads, internal pathways and parking areas.",
      icon: Route,
      keywords: ["external works & roads", "roads", "pathways", "parking"],
    },
    {
      title: "Compound Wall / Fence",
      description:
        "Perimeter wall and fencing works.",
      icon: Fence,
      keywords: ["compound wall", "fence"],
    },
    {
      title: "Landscaping",
      description:
        "Landscaping and external green areas.",
      icon: Trees,
      keywords: ["landscaping"],
    },
  ];

  const getGroupRows = (group) =>
    infraRows.filter((row) => {
      const activity = String(row.activity || "").toLowerCase();
      return group.keywords.some((keyword) =>
        activity.includes(keyword)
      );
    });

  const combinedRows = infraRows.filter((row) =>
    String(row.activity || "")
      .toLowerCase()
      .includes("external / site development")
  );

  const formatAmount = (value) =>
    fmtMoney(Number(value || 0), currency, fxRates);

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar
        currency={currency}
        fxRates={fxRates}
        result={result}
        inputs={inputs}
        activeKey="infra-external"
        liveRateIndex={result?.live_rate_index}
        activeProject={activeProject}
      />

      <div className="flex-1 min-w-0 overflow-y-auto">
        {/* Page Header */}
        <div className="bg-white border-b border-slate-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
              <Wrench className="w-5 h-5 text-orange-700" />
            </div>

            <div>
              <h1 className="text-xl font-bold text-slate-900 font-['Manrope']">
                Infra &amp; External
              </h1>
              <p className="text-xs text-slate-500">
                Infrastructure and external works cost breakdown
              </p>
            </div>
          </div>
        </div>

        <main className="p-6 space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SummaryCard
              title="EXTERNAL & SITE DEVELOPMENT COST"
              value={formatAmount(infraTotal)}
              subtitle={`USD ${fmtNumber(infraTotal)}`}
              icon={Wrench}
              color="orange"
            />

            <SummaryCard
              title="INFRA COST / m²"
              value={`${formatAmount(infraCostPerSqm)} / m²`}
              subtitle={
                builtUpArea > 0
                  ? `Based on ${fmtNumber(builtUpArea)} m² built-up area`
                  : "Built-up area unavailable"
              }
              icon={Wrench}
              color="blue"
            />

            <SummaryCard
              title="LAND AREA"
              value={`${fmtNumber(landArea)} m²`}
              subtitle="External works area basis"
              icon={Trees}
              color="green"
            />
          </div>

          {/* Individual Activity Sections */}
          {activityGroups.map((group) => {
            const Icon = group.icon;
            const rows = getGroupRows(group);
            const groupTotal = rows.reduce(
              (sum, row) => sum + Number(row.amount || 0),
              0
            );

            return (
              <section
                key={group.title}
                className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden"
              >
                <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-orange-700" />
                    </div>
                    <div>
                      <h2 className="text-sm font-semibold text-slate-800">
                        {group.title}
                      </h2>
                      <p className="text-xs text-slate-500 mt-1">
                        {group.description}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <p className="text-xs text-slate-500">Subtotal</p>
                    <p className="font-semibold text-slate-900">
                      {formatAmount(groupTotal)}
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 text-[11px] uppercase text-slate-500 font-semibold tracking-wider">
                      <tr>
                        <th className="text-left px-5 py-3">Activity</th>
                        <th className="text-right px-5 py-3">Quantity</th>
                        <th className="text-left px-5 py-3">Unit</th>
                        <th className="text-right px-5 py-3">Rate (USD)</th>
                        <th className="text-right px-5 py-3">
                          Amount ({currency})
                        </th>
                        <th className="text-right px-5 py-3">
                          % of Infra Cost
                        </th>
                      </tr>
                    </thead>

                    <tbody>
                      {rows.map((row, index) => {
                        const amount = Number(row.amount || 0);
                        const percentage =
                          infraTotal > 0
                            ? ((amount / infraTotal) * 100).toFixed(2)
                            : "0.00";

                        return (
                          <tr
                            key={`${row.activity}-${index}`}
                            className="border-t border-slate-100 hover:bg-slate-50"
                          >
                            <td className="px-5 py-3 font-medium text-slate-800">
                              {row.activity}
                            </td>
                            <td className="px-5 py-3 text-right text-slate-700">
                              {fmtNumber(Number(row.quantity || 0), 2)}
                            </td>
                            <td className="px-5 py-3 text-slate-500">
                              {row.unit || "—"}
                            </td>
                            <td className="px-5 py-3 text-right text-slate-700">
                              {fmtMoney(row.rate, "USD", fxRates)}
                            </td>
                            <td className="px-5 py-3 text-right font-semibold text-slate-900">
                              {formatAmount(amount)}
                            </td>
                            <td className="px-5 py-3 text-right text-slate-600">
                              {percentage}%
                            </td>
                          </tr>
                        );
                      })}

                      {rows.length === 0 && (
                        <tr>
                          <td
                            colSpan={6}
                            className="px-5 py-6 text-center text-slate-500"
                          >
                            No separate costed activities returned for this
                            section by the current estimate.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            );
          })}

          {/* Combined external cost, if the backend returns it */}
          {combinedRows.length > 0 && (
            <section className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-200">
                <h2 className="text-sm font-semibold text-slate-800">
                  Combined External / Site Development
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Existing combined amount returned by the estimator.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-[11px] uppercase text-slate-500 font-semibold">
                    <tr>
                      <th className="text-left px-5 py-3">Activity</th>
                      <th className="text-right px-5 py-3">Quantity</th>
                      <th className="text-left px-5 py-3">Unit</th>
                      <th className="text-right px-5 py-3">Rate (USD)</th>
                      <th className="text-right px-5 py-3">
                        Amount ({currency})
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {combinedRows.map((row, index) => (
                      <tr
                        key={`${row.activity}-${index}`}
                        className="border-t border-slate-100"
                      >
                        <td className="px-5 py-3 font-medium text-slate-800">
                          {row.activity}
                        </td>
                        <td className="px-5 py-3 text-right">
                          {fmtNumber(Number(row.quantity || 0), 2)}
                        </td>
                        <td className="px-5 py-3">{row.unit || "—"}</td>
                        <td className="px-5 py-3 text-right">
                          {fmtMoney(row.rate, "USD", fxRates)}
                        </td>
                        <td className="px-5 py-3 text-right font-semibold">
                          {formatAmount(row.amount)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* Full matching BOQ */}
          <section className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200">
              <h2 className="text-sm font-semibold text-slate-800">
                Complete Infrastructure &amp; External BOQ
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                All matching infrastructure and external items from the estimate.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-[11px] uppercase text-slate-500 font-semibold tracking-wider">
                  <tr>
                    <th className="text-left px-5 py-3">#</th>
                    <th className="text-left px-5 py-3">Activity</th>
                    <th className="text-left px-5 py-3">Category</th>
                    <th className="text-right px-5 py-3">Quantity</th>
                    <th className="text-left px-5 py-3">Unit</th>
                    <th className="text-right px-5 py-3">Rate (USD)</th>
                    <th className="text-right px-5 py-3">
                      Amount ({currency})
                    </th>
                    <th className="text-right px-5 py-3">% of Infra Cost</th>
                  </tr>
                </thead>

                <tbody>
                  {infraRows.map((row, index) => {
                    const amount = Number(row.amount || 0);
                    const percentage =
                      infraTotal > 0
                        ? ((amount / infraTotal) * 100).toFixed(2)
                        : "0.00";

                    return (
                      <tr
                        key={`${row.activity}-${index}`}
                        className="border-t border-slate-100 hover:bg-slate-50"
                      >
                        <td className="px-5 py-3 text-slate-500">
                          {index + 1}
                        </td>
                        <td className="px-5 py-3 font-medium text-slate-800">
                          {row.activity}
                        </td>
                        <td className="px-5 py-3 text-slate-500">
                          {row.category || "—"}
                        </td>
                        <td className="px-5 py-3 text-right">
                          {fmtNumber(Number(row.quantity || 0), 2)}
                        </td>
                        <td className="px-5 py-3">{row.unit || "—"}</td>
                        <td className="px-5 py-3 text-right">
                          {fmtMoney(row.rate, "USD", fxRates)}
                        </td>
                        <td className="px-5 py-3 text-right font-semibold">
                          {formatAmount(amount)}
                        </td>
                        <td className="px-5 py-3 text-right">
                          {percentage}%
                        </td>
                      </tr>
                    );
                  })}

                  {infraRows.length === 0 && (
                    <tr>
                      <td
                        colSpan={8}
                        className="px-5 py-10 text-center text-slate-500"
                      >
                        No infrastructure or external BOQ items were returned
                        by the current estimate.
                      </td>
                    </tr>
                  )}
                </tbody>

                {infraRows.length > 0 && (
                  <tfoot className="bg-slate-50 border-t border-slate-200">
                    <tr>
                      <td
                        colSpan={6}
                        className="px-5 py-4 text-right font-semibold"
                      >
                        Total Infrastructure &amp; External
                      </td>
                      <td className="px-5 py-4 text-right font-bold">
                        {formatAmount(infraTotal)}
                      </td>
                      <td className="px-5 py-4 text-right font-semibold">
                        100%
                      </td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

function SummaryCard({ title, value, subtitle, icon: Icon, color }) {
  const styles = {
    orange: "bg-orange-100 text-orange-700",
    blue: "bg-blue-100 text-blue-700",
    green: "bg-emerald-100 text-emerald-700",
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div
          className={`w-10 h-10 rounded-lg flex items-center justify-center ${styles[color] || styles.orange
            }`}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
            {title}
          </div>
          <div className="text-xl font-bold text-slate-900 font-['Manrope']">
            {value}
          </div>
          <div className="text-sm text-slate-500">{subtitle}</div>
        </div>
      </div>
    </div>
  );
}

