import React, { useEffect } from "react";
import { useLocation } from "react-router-dom";
import html2pdf from "html2pdf.js";
import { FileOutput, Download, Printer } from "lucide-react";
import { fmtMoney, fmtNumber } from "@/lib/format";
import Sidebar from "@/components/estimator/Sidebar";

export default function ReportsExport() {
    const location = useLocation();

    const result = location.state?.result;
    const inputs = location.state?.inputs;
    const currency = location.state?.currency ?? "USD";
    const fxRates = location.state?.fxRates ?? {};

    useEffect(() => {
        if (location.state?.autoPrint && result) {
            const timer = setTimeout(() => printReport(), 500);
            return () => clearTimeout(timer);
        }
    }, [location.state?.autoPrint, result]);

    if (!result) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <div className="text-center">
                    <FileOutput className="w-10 h-10 mx-auto mb-3 text-slate-400" />
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

    const totals = result.totals || {};
    const breakdown = result.breakdown || [];
    const boq = result.boq || [];
    const utilities = result.utilities || [];
    const insights = result.insights || {};
    const cityFactors = result.city_factors || {};
    const multipliers = result.multipliers || {};

    const activeProject = {
        name: inputs?.project_name ?? "—",
        location: `${inputs?.location_city ?? ""}${inputs?.location_country ? `, ${inputs.location_country}` : ""
            }`,
        builtUp: `${fmtNumber(totals.built_up_area_sqm || 0)} m²`,
        plot: `${fmtNumber(totals.plot_area_sqm || 0)} m²`,
        lastSaved: "—",
    };

    const printReport = async () => {
        const element = document.getElementById("estimate-report");
        if (!element) return;

        const projectName = inputs?.project_name || "Project Estimate";
        const filename = `${projectName.replace(/[^a-z0-9]/gi, "_")}_Estimate.pdf`;

        const options = {
            margin: 8,
            filename,
            image: { type: "jpeg", quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
            jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
            pagebreak: { mode: ["css", "legacy"] },
        };

        await html2pdf().set(options).from(element).save();
    };

    return (
        <div className="min-h-screen bg-slate-50 flex">
            <div>
                <Sidebar
                    currency={currency}
                    fxRates={fxRates}
                    result={result}
                    inputs={inputs}
                    activeKey="reports"
                    liveRateIndex={result?.live_rate_index}
                    activeProject={activeProject}
                />
            </div>

            <div className="flex-1 min-w-0 overflow-y-auto">
                {/* Header */}
                <div className="bg-white border-b border-slate-200 px-6 py-4">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                                <FileOutput className="w-5 h-5 text-blue-700" />
                            </div>

                            <div>
                                <h1 className="text-xl font-bold text-slate-900 font-['Manrope']">
                                    Reports & Export
                                </h1>
                                <p className="text-xs text-slate-500">
                                    Complete project estimate report
                                </p>
                            </div>
                        </div>

                        <button
                            onClick={printReport}
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700"
                        >
                            <Download className="w-4 h-4" />
                            Save PDF
                        </button>
                    </div>
                </div>

                {/* Report */}
                <main className="p-6 print:p-0">
                    <div id="estimate-report" className="max-w-6xl mx-auto bg-white border border-slate-200 rounded-lg shadow-sm print:border-0 print:shadow-none">
                        {/* Report Header */}
                        <div className="p-10 border-b border-slate-200">
                            <div className="flex justify-end mb-6 pr-2">
                                <img
                                    src="/mondelez-logo.png"
                                    alt="Mondelez International"
                                    className="h-20 w-auto object-contain"
                                />
                            </div>
                            <div className="flex justify-between gap-6">
                                <div>
                                    <div className="text-xs font-semibold text-blue-600 uppercase tracking-wider">
                                        Construction Cost Estimate
                                    </div>

                                    <h1 className="text-2xl font-bold text-slate-900 mt-2">
                                        {inputs?.project_name || "Project Estimate"}
                                    </h1>

                                    <p className="text-sm text-slate-500 mt-1">
                                        {inputs?.location_city || "—"}
                                        {inputs?.location_country
                                            ? `, ${inputs.location_country}`
                                            : ""}
                                    </p>
                                </div>

                                <div className="text-right text-sm">
                                    <div className="text-slate-500">Project Type</div>
                                    <div className="font-semibold text-slate-800">
                                        {inputs?.project_type || "—"}
                                    </div>

                                    <div className="text-slate-500 mt-2">Industry</div>
                                    <div className="font-semibold text-slate-800">
                                        {inputs?.industry_type || "—"}
                                    </div>

                                    <div className="text-slate-500 mt-2">Generated On</div>
                                    <div className="font-semibold text-slate-800">
                                        {new Date().toLocaleString()}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Executive Summary */}
                        <section className="p-8 border-b border-slate-200">
                            <h2 className="text-lg font-bold text-slate-900">
                                Executive Summary
                            </h2>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
                                <ReportCard
                                    label="Total Project Cost"
                                    value={fmtMoney(
                                        totals.total_project_cost || 0,
                                        currency,
                                        fxRates
                                    )}
                                />

                                <ReportCard
                                    label="Cost / m²"
                                    value={`${fmtMoney(
                                        totals.cost_per_sqm || 0,
                                        currency,
                                        fxRates
                                    )} / m²`}
                                />

                                <ReportCard
                                    label="Built-up Area"
                                    value={`${fmtNumber(
                                        totals.built_up_area_sqm || 0
                                    )} m²`}
                                />

                                <ReportCard
                                    label="Duration"
                                    value={`${totals.duration_months || 0} months`}
                                />
                            </div>
                        </section>

                        {/* Project Information */}
                        <section className="p-8 border-b border-slate-200">
                            <SectionTitle title="Project Information" />

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-4 mt-5">
                                <Info label="Project Name" value={inputs?.project_name} />
                                <Info label="Project Type" value={inputs?.project_type} />
                                <Info label="Industry" value={inputs?.industry_type} />
                                <Info label="Product" value={inputs?.product_category} />
                                <Info label="City" value={inputs?.location_city} />
                                <Info label="Country" value={inputs?.location_country} />
                                <Info label="Region" value={inputs?.region} />
                                <Info label="Location Tier" value={inputs?.location_tier} />
                                <Info label="Building Type" value={inputs?.building_type} />
                                <Info label="Length" value={`${inputs?.length_m || 0} m`} />
                                <Info label="Width" value={`${inputs?.width_m || 0} m`} />
                                <Info label="Height" value={`${inputs?.height_m || 0} m`} />
                                <Info label="Floors" value={inputs?.num_floors} />
                                <Info label="Plot Area" value={`${inputs?.plot_area_sqm || 0} m²`} />
                                <Info label="Ground Coverage" value={`${inputs?.ground_coverage_pct || 0}%`} />
                                <Info label="FAR / FSI" value={inputs?.far_fsi} />
                            </div>
                        </section>

                        {/* Cost Breakdown */}
                        <section className="p-8 border-b border-slate-200">
                            <SectionTitle title="Cost Breakdown" />

                            <ReportTable
                                headers={["Category", "Amount", "% of Total"]}
                                rows={breakdown.map((b) => [
                                    b.name,
                                    fmtMoney(b.value || 0, currency, fxRates),
                                    `${b.pct || 0}%`,
                                ])}
                            />

                            <div className="flex justify-end mt-4">
                                <div className="text-right">
                                    <div className="text-xs text-slate-500 uppercase">
                                        Total Project Cost
                                    </div>
                                    <div className="text-xl font-bold text-slate-900">
                                        {fmtMoney(
                                            totals.total_project_cost || 0,
                                            currency,
                                            fxRates
                                        )}
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Civil / Infra / Utilities Summary */}
                        <section className="p-8 border-b border-slate-200">
                            <SectionTitle title="Major Cost Categories" />

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
                                <CategoryCard
                                    title="Civil Building"
                                    data={breakdown.find(
                                        (b) => b.name === "Civil Building"
                                    )}
                                    currency={currency}
                                    fxRates={fxRates}
                                />

                                <CategoryCard
                                    title="Utilities & Process"
                                    data={breakdown.find(
                                        (b) => b.name === "Utilities & Process"
                                    )}
                                    currency={currency}
                                    fxRates={fxRates}
                                />

                                <CategoryCard
                                    title="Infra & External"
                                    data={breakdown.find(
                                        (b) => b.name === "Infra & External"
                                    )}
                                    currency={currency}
                                    fxRates={fxRates}
                                />
                            </div>
                        </section>

                        {/* BOQ */}
                        <section className="p-8 border-b border-slate-200">
                            <SectionTitle title="Complete Bill of Quantities" />

                            <ReportTable
                                headers={[
                                    "#",
                                    "Activity",
                                    "Category",
                                    "Quantity",
                                    "Unit",
                                    "Rate",
                                    "Amount",
                                ]}
                                rows={boq.map((row, index) => [
                                    index + 1,
                                    row.activity,
                                    row.category,
                                    fmtNumber(row.quantity || 0),
                                    row.unit,
                                    fmtMoney(row.rate || 0, currency, fxRates),
                                    fmtMoney(row.amount || 0, currency, fxRates),
                                ])}
                            />
                        </section>

                        {/* Utilities */}
                        <section className="p-8 border-b border-slate-200">
                            <SectionTitle title="Utilities & Process Details" />

                            <ReportTable
                                headers={[
                                    "System",
                                    "Discipline",
                                    "Amount",
                                    "% of Utilities",
                                ]}
                                rows={utilities.map((u) => {
                                    const utilityTotal = Number(
                                        result.utilities_total || 0
                                    );

                                    const pct = utilityTotal
                                        ? (
                                            (Number(u.amount || 0) /
                                                utilityTotal) *
                                            100
                                        ).toFixed(2)
                                        : "0.00";

                                    return [
                                        u.name,
                                        u.discipline,
                                        fmtMoney(u.amount || 0, currency, fxRates),
                                        `${pct}%`,
                                    ];
                                })}
                            />

                            <div className="text-right mt-4 font-bold">
                                Total Utilities & Process:{" "}
                                {fmtMoney(
                                    result.utilities_total || 0,
                                    currency,
                                    fxRates
                                )}
                            </div>
                        </section>

                        {/* Infrastructure */}
                        <section className="p-8 border-b border-slate-200">
                            <SectionTitle title="Infra & External Details" />

                            <ReportTable
                                headers={[
                                    "Activity",
                                    "Quantity",
                                    "Unit",
                                    "Rate",
                                    "Amount",
                                ]}
                                rows={boq
                                    .filter((row) => row.category === "Infra")
                                    .map((row) => [
                                        row.activity,
                                        fmtNumber(row.quantity || 0),
                                        row.unit,
                                        fmtMoney(row.rate || 0, currency, fxRates),
                                        fmtMoney(row.amount || 0, currency, fxRates),
                                    ])}
                            />
                        </section>

                        {/* Utilities Demand */}
                        {result.utility_demand && (
                            <section className="p-8 border-b border-slate-200">
                                <SectionTitle title="Utility Demand" />

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
                                    {Object.entries(result.utility_demand).map(
                                        ([key, value]) => (
                                            <Info
                                                key={key}
                                                label={formatLabel(key)}
                                                value={formatValue(value)}
                                            />
                                        )
                                    )}
                                </div>
                            </section>
                        )}

                        {/* Design / Cost Factors */}
                        <section className="p-8 border-b border-slate-200">
                            <SectionTitle title="Cost & Design Factors" />

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-4 mt-5">
                                <Info label="Region Multiplier" value={multipliers.region} />
                                <Info label="Location Tier Multiplier" value={multipliers.tier} />
                                <Info label="Building Multiplier" value={multipliers.building} />
                                <Info label="Utility Multiplier" value={multipliers.utility} />
                                <Info label="Project Type Multiplier" value={multipliers.project_type} />
                                <Info label="Combined Multiplier" value={multipliers.combined} />
                                <Info label="Civil City Factor" value={cityFactors.civil_effective} />
                                <Info label="Mechanical City Factor" value={cityFactors.mechanical_effective} />
                                <Info label="Electrical City Factor" value={cityFactors.electrical_effective} />
                                <Info label="Requested City" value={cityFactors.requested} />
                            </div>
                        </section>

                        {/* Assumptions / Risks / Optimizations */}
                        {(insights.assumptions?.length ||
                            insights.risks?.length ||
                            insights.optimizations?.length) ? (
                            <section className="p-8 border-b border-slate-200">
                                <SectionTitle title="Assumptions, Risks & Optimizations" />

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-5">
                                    <InsightBox
                                        title="Key Assumptions"
                                        items={insights.assumptions || []}
                                    />

                                    <InsightBox
                                        title="Risk Drivers"
                                        items={insights.risks || []}
                                    />

                                    <InsightBox
                                        title="Optimizations"
                                        items={insights.optimizations || []}
                                    />
                                </div>
                            </section>
                        ) : null}

                        {/* Final Summary */}
                        <section className="p-8">
                            <div className="bg-slate-900 text-white rounded-lg p-6">
                                <div className="text-xs uppercase tracking-wider text-slate-400">
                                    Total Project Cost
                                </div>

                                <div className="text-3xl font-bold mt-2">
                                    {fmtMoney(
                                        totals.total_project_cost || 0,
                                        currency,
                                        fxRates
                                    )}
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-5 mt-6 text-sm">
                                    <div>
                                        <div className="text-slate-400">Contingency</div>
                                        <div className="font-semibold">
                                            {fmtMoney(
                                                totals.contingency || 0,
                                                currency,
                                                fxRates
                                            )}
                                        </div>
                                    </div>

                                    <div>
                                        <div className="text-slate-400">Contingency %</div>
                                        <div className="font-semibold">
                                            {totals.contingency_pct || 0}%
                                        </div>
                                    </div>

                                    <div>
                                        <div className="text-slate-400">Confidence</div>
                                        <div className="font-semibold">
                                            {totals.confidence_score || 0}%{" "}
                                            ({totals.confidence_label || "—"})
                                        </div>
                                    </div>

                                    <div>
                                        <div className="text-slate-400">Duration</div>
                                        <div className="font-semibold">
                                            {totals.duration_months || 0} months
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="text-center text-xs text-slate-400 mt-6">
                                Generated from the current project estimate.
                            </div>
                        </section>

                    </div>
                </main>
            </div>
        </div>
    );
}

function SectionTitle({ title }) {
    return (
        <h2 className="text-lg font-bold text-slate-900">
            {title}
        </h2>
    );
}

function ReportCard({ label, value }) {
    return (
        <div className="border border-slate-200 rounded-lg p-4">
            <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                {label}
            </div>
            <div className="text-lg font-bold text-slate-900 mt-1">
                {value}
            </div>
        </div>
    );
}

function CategoryCard({ title, data, currency, fxRates }) {
    return (
        <div className="border border-slate-200 rounded-lg p-5">
            <div className="text-xs font-semibold text-slate-500 uppercase">
                {title}
            </div>

            <div className="text-xl font-bold text-slate-900 mt-2">
                {fmtMoney(data?.value || 0, currency, fxRates)}
            </div>

            <div className="text-xs text-slate-500 mt-1">
                {data?.pct || 0}% of total project cost
            </div>
        </div>
    );
}

function Info({ label, value }) {
    return (
        <div>
            <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">
                {label}
            </div>
            <div className="text-sm text-slate-800 font-medium mt-1">
                {value ?? "—"}
            </div>
        </div>
    );
}

function InsightBox({ title, items }) {
    return (
        <div className="border border-slate-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-slate-800">
                {title}
            </h3>

            <ul className="mt-3 space-y-2">
                {items.length ? (
                    items.map((item, index) => (
                        <li
                            key={index}
                            className="text-xs text-slate-600 leading-relaxed"
                        >
                            • {typeof item === "string" ? item : JSON.stringify(item)}
                        </li>
                    ))
                ) : (
                    <li className="text-xs text-slate-400">
                        None available
                    </li>
                )}
            </ul>
        </div>
    );
}

function ReportTable({ headers, rows }) {
    return (
        <div className="overflow-x-auto mt-5">
            <table className="w-full text-sm border-collapse">
                <thead className="bg-slate-50">
                    <tr>
                        {headers.map((header, index) => (
                            <th
                                key={index}
                                className="text-left px-3 py-3 border-b border-slate-200 text-[10px] uppercase tracking-wider text-slate-500 font-semibold"
                            >
                                {header}
                            </th>
                        ))}
                    </tr>
                </thead>

                <tbody>
                    {rows.length ? (
                        rows.map((row, rowIndex) => (
                            <tr
                                key={rowIndex}
                                className="border-b border-slate-100"
                                style={{ breakInside: "avoid", pageBreakInside: "avoid" }}
                            >
                                {row.map((cell, cellIndex) => (
                                    <td
                                        key={cellIndex}
                                        className="px-3 py-3 text-slate-700"
                                    >
                                        {cell}
                                    </td>
                                ))}
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td
                                colSpan={headers.length}
                                className="px-3 py-8 text-center text-slate-400"
                            >
                                No data available.
                            </td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}

function formatLabel(key) {
    return String(key)
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(value) {
    if (value == null) return "—";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
}