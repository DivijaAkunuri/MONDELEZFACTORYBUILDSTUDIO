
import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
    ArrowLeft,
    GitCompareArrows,
    MapPin,
    Loader2,
} from "lucide-react";
import { toast } from "sonner";

import Sidebar from "@/components/estimator/Sidebar";
import { getReference, calculateFast } from "@/lib/api";
import { fmtMoney, fmtNumber } from "@/lib/format";

const inputClass =
    "mt-1.5 w-full min-w-0 rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-100";

const labelClass = "block text-sm font-medium text-slate-700";

const cardClass =
    "rounded-xl border border-slate-200 bg-white p-5 shadow-sm";

function readSavedInputs() {
    try {
        const saved = sessionStorage.getItem("estimator_inputs");
        return saved ? JSON.parse(saved) : {};
    } catch {
        return {};
    }
}

function getErrorMessage(error) {
    const detail =
        error?.response?.data?.detail ??
        error?.response?.data?.message ??
        error?.message;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
        return detail.map((item) => item.msg || "Invalid input").join(", ");
    }

    return "Unable to calculate costs. Check your backend connection.";
}

function LocationCard({
    title,
    location,
    onChange,
    regions,
    loading,
}) {
    const countries = Array.isArray(regions?.[location.region])
        ? regions[location.region]
        : [];

    return (
        <section className={cardClass}>
            <div className="mb-5 flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                    <MapPin size={20} />
                </div>

                <div>
                    <h2 className="text-lg font-semibold text-slate-900">
                        {title}
                    </h2>
                    <p className="mt-1 text-sm text-slate-500">
                        Select the location for your estimate.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div>
                    <label className={labelClass}>Region</label>
                    <select
                        className={inputClass}
                        value={location.region}
                        disabled={loading}
                        onChange={(event) =>
                            onChange({
                                region: event.target.value,
                                country: "",
                                city: location.city,
                            })
                        }
                    >
                        <option value="">Select region</option>
                        {Object.keys(regions || {}).sort().map((region) => (
                            <option key={region} value={region}>
                                {region}
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className={labelClass}>Country</label>
                    <select
                        className={inputClass}
                        value={location.country}
                        disabled={!location.region || loading}
                        onChange={(event) =>
                            onChange({
                                ...location,
                                country: event.target.value,
                            })
                        }
                    >
                        <option value="">Select country</option>
                        {countries.map((country) => (
                            <option key={country} value={country}>
                                {country}
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className={labelClass}>City</label>
                    <input
                        className={inputClass}
                        value={location.city}
                        placeholder="Enter city name"
                        onChange={(event) =>
                            onChange({
                                ...location,
                                city: event.target.value,
                            })
                        }
                    />
                    <p className="mt-1.5 text-xs text-slate-500">
                        Enter the city manually.
                    </p>
                </div>
            </div>
        </section>
    );
}

function ResultCard({ title, location, result }) {
    const total = Number(result?.totals?.total_project_cost);

    return (
        <section className={cardClass}>
            <p className="text-sm font-medium text-slate-500">{title}</p>

            <h3 className="mt-1 text-lg font-semibold text-slate-900">
                {location.city}, {location.country}
            </h3>

            <p className="mt-5 text-sm text-slate-500">
                Estimated project cost
            </p>

            <p className="mt-1 break-words text-2xl font-bold text-blue-700">
                {Number.isFinite(total)
                    ? fmtMoney(total, "USD")
                    : "Not available"}
            </p>

            {result?.totals?.built_up_area_sqm != null && (
                <p className="mt-3 text-sm text-slate-500">
                    Built-up area:{" "}
                    {fmtNumber(Number(result.totals.built_up_area_sqm))} m²
                </p>
            )}
        </section>
    );
}

export default function CompareOptions() {
    const navigate = useNavigate();
    const routeLocation = useLocation();

    const [reference, setReference] = React.useState(null);
    const [referenceLoading, setReferenceLoading] = React.useState(true);
    const [loading, setLoading] = React.useState(false);
    const [comparison, setComparison] = React.useState(null);

    const [projectInputs, setProjectInputs] = React.useState(() => ({
        ...readSavedInputs(),
        ...(routeLocation.state?.inputs || {}),
    }));

    const [locationA, setLocationA] = React.useState(() => {
        const inputs = {
            ...readSavedInputs(),
            ...(routeLocation.state?.inputs || {}),
        };

        return {
            region: inputs.region || "",
            country: inputs.location_country || "",
            city: inputs.location_city || "",
        };
    });

    const [locationB, setLocationB] = React.useState({
        region: "",
        country: "",
        city: "",
    });

    React.useEffect(() => {
        let cancelled = false;

        async function loadReference() {
            try {
                const data = await getReference();

                if (!cancelled) {
                    setReference(data || {});
                }
            } catch (error) {
                console.error("Reference data loading failed:", error);

                if (!cancelled) {
                    toast.error("Could not load region and country options.");
                }
            } finally {
                if (!cancelled) {
                    setReferenceLoading(false);
                }
            }
        }

        loadReference();

        return () => {
            cancelled = true;
        };
    }, []);

    React.useEffect(() => {
        const passedInputs = routeLocation.state?.inputs;

        if (passedInputs) {
            setProjectInputs((previous) => ({
                ...previous,
                ...passedInputs,
            }));

            setLocationA({
                region: passedInputs.region || "",
                country: passedInputs.location_country || "",
                city: passedInputs.location_city || "",
            });
        }
    }, [routeLocation.state]);

    const regions = reference?.regions || {};

    const patchProjectInput = (key, value) => {
        setProjectInputs((previous) => ({
            ...previous,
            [key]: value,
        }));
        setComparison(null);
    };

    const builtUpArea =
        (Number(projectInputs.length_m) || 0) *
        (Number(projectInputs.width_m) || 0) *
        (Number(projectInputs.num_floors) || 1);

    async function compareCosts() {
        if (
            !locationA.region ||
            !locationA.country ||
            !locationA.city.trim()
        ) {
            toast.error("Complete all fields for Location A.");
            return;
        }

        if (
            !locationB.region ||
            !locationB.country ||
            !locationB.city.trim()
        ) {
            toast.error("Complete all fields for Location B.");
            return;
        }

        if (
            locationA.city.trim().toLowerCase() ===
            locationB.city.trim().toLowerCase() &&
            locationA.country === locationB.country
        ) {
            toast.error("Choose two different locations.");
            return;
        }

        if (
            !Number.isFinite(Number(projectInputs.length_m)) ||
            Number(projectInputs.length_m) <= 0 ||
            !Number.isFinite(Number(projectInputs.width_m)) ||
            Number(projectInputs.width_m) <= 0
        ) {
            toast.error("Length and width must be greater than zero.");
            return;
        }

        setLoading(true);
        setComparison(null);

        const makePayload = (location) => ({
            ...projectInputs,

            region: location.region,
            location_country: location.country,
            location_city: location.city.trim(),

            // Plot area follows the building footprint.
            plot_area_sqm:
                Number(projectInputs.length_m) *
                Number(projectInputs.width_m),

            // Preserve the saved land area if it satisfies backend validation.
            land_area_sqm: Math.max(
                Number(projectInputs.land_area_sqm) || 0,
                Number(projectInputs.length_m) *
                Number(projectInputs.width_m) *
                2
            ),
        });

        try {
            const [resultA, resultB] = await Promise.all([
                calculateFast(makePayload(locationA)),
                calculateFast(makePayload(locationB)),
            ]);

            const totalA = Number(resultA?.totals?.total_project_cost);
            const totalB = Number(resultB?.totals?.total_project_cost);

            if (!Number.isFinite(totalA) || !Number.isFinite(totalB)) {
                throw new Error(
                    "The backend response did not contain valid project totals."
                );
            }

            setComparison({
                resultA,
                resultB,
                totalA,
                totalB,
                difference: totalB - totalA,
                percentage:
                    totalA !== 0 ? ((totalB - totalA) / totalA) * 100 : null,
            });

            toast.success("Comparison completed.");
        } catch (error) {
            console.error("Comparison failed:", error);
            toast.error(getErrorMessage(error));
        } finally {
            setLoading(false);
        }
    }

    const activeProject = {
        name: projectInputs.project_name || "—",
        location: `${projectInputs.location_city || "—"}${
            projectInputs.location_country
                ? `, ${projectInputs.location_country}`
                : ""
        }`,
        builtUp: `${fmtNumber(builtUpArea)} m²`,
        lastSaved: "—",
    };

    return (
        <div className="flex h-screen w-full overflow-hidden bg-slate-50">
            <Sidebar
                result={routeLocation.state?.result || null}
                inputs={projectInputs}
                liveRateIndex={routeLocation.state?.result?.live_rate_index}
                onDashboard={() => navigate("/dashboard")}
                onNewEstimate={() => navigate("/")}
                activeProject={activeProject}
            />

            <div className="flex min-w-0 flex-1 flex-col overflow-y-auto">
                <main className="w-full flex-1 p-4 sm:p-6 lg:p-8">
                    <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                                Compare Options
                            </h1>
                            <p className="mt-1 text-sm text-slate-500 sm:text-base">
                                Compare the same construction project across two locations.
                            </p>
                        </div>

                        <button
                            type="button"
                            onClick={() => navigate(-1)}
                            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
                        >
                            <ArrowLeft size={16} />
                            Back
                        </button>
                    </header>

                    <div className="grid grid-cols-1 items-stretch gap-5 xl:grid-cols-2">
                        <LocationCard
                            title="Location A"
                            location={locationA}
                            onChange={(next) => {
                                setLocationA(next);
                                setComparison(null);
                            }}
                            regions={regions}
                            loading={referenceLoading}
                        />

                        <LocationCard
                            title="Location B"
                            location={locationB}
                            onChange={(next) => {
                                setLocationB(next);
                                setComparison(null);
                            }}
                            regions={regions}
                            loading={referenceLoading}
                        />
                    </div>

                    <section className={`${cardClass} mt-5`}>
                        <h2 className="text-lg font-semibold text-slate-900">
                            Shared Project Inputs
                        </h2>
                        <p className="mt-1 mb-5 text-sm text-slate-500">
                            These values are reused for both locations.
                        </p>

                        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                            <div>
                                <label className={labelClass}>Project Name</label>
                                <input
                                    className={inputClass}
                                    value={projectInputs.project_name || ""}
                                    onChange={(event) =>
                                        patchProjectInput("project_name", event.target.value)
                                    }
                                />
                            </div>

                            <div>
                                <label className={labelClass}>Length (m)</label>
                                <input
                                    className={inputClass}
                                    type="number"
                                    min="0.01"
                                    value={projectInputs.length_m ?? ""}
                                    onChange={(event) =>
                                        patchProjectInput("length_m", event.target.value)
                                    }
                                />
                            </div>

                            <div>
                                <label className={labelClass}>Width (m)</label>
                                <input
                                    className={inputClass}
                                    type="number"
                                    min="0.01"
                                    value={projectInputs.width_m ?? ""}
                                    onChange={(event) =>
                                        patchProjectInput("width_m", event.target.value)
                                    }
                                />
                            </div>

                            <div>
                                <label className={labelClass}>Building Type</label>
                                <input
                                    className={inputClass}
                                    value={projectInputs.building_type || ""}
                                    onChange={(event) =>
                                        patchProjectInput("building_type", event.target.value)
                                    }
                                />
                            </div>

                            <div>
                                <label className={labelClass}>Built-up Area (m²)</label>
                                <input
                                    className={`${inputClass} bg-slate-50`}
                                    value={fmtNumber(builtUpArea)}
                                    readOnly
                                />
                                <p className="mt-1 text-xs text-slate-500">
                                    Length × width × floors.
                                </p>
                            </div>

                            <div>
                                <label className={labelClass}>Project Type</label>
                                <input
                                    className={inputClass}
                                    value={projectInputs.project_type || ""}
                                    onChange={(event) =>
                                        patchProjectInput("project_type", event.target.value)
                                    }
                                />
                            </div>
                        </div>
                    </section>

                    <div className="mt-6 flex justify-center">
                        <button
                            type="button"
                            onClick={compareCosts}
                            disabled={loading || referenceLoading}
                            className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-7 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto sm:min-w-72"
                        >
                            {loading ? (
                                <>
                                    <Loader2 size={18} className="animate-spin" />
                                    Calculating...
                                </>
                            ) : (
                                <>
                                    <GitCompareArrows size={18} />
                                    Compare Estimated Costs
                                </>
                            )}
                        </button>
                    </div>

                    {comparison && (
                        <section className="mt-8 space-y-5">
                            <div>
                                <h2 className="text-xl font-bold text-slate-900">
                                    Comparison Results
                                </h2>
                                <p className="mt-1 text-sm text-slate-500">
                                    Estimated costs for the same project in both locations.
                                </p>
                            </div>

                            <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
                                <ResultCard
                                    title="Location A"
                                    location={locationA}
                                    result={comparison.resultA}
                                />

                                <ResultCard
                                    title="Location B"
                                    location={locationB}
                                    result={comparison.resultB}
                                />
                            </div>

                            <section className={cardClass}>
                                <h3 className="text-lg font-semibold text-slate-900">
                                    Cost Difference
                                </h3>

                                <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2">
                                    <div>
                                        <p className="text-sm text-slate-500">
                                            Absolute difference (B − A)
                                        </p>
                                        <p className="mt-1 break-words text-2xl font-bold text-slate-900">
                                            {fmtMoney(
                                                Math.abs(comparison.difference),
                                                "USD"
                                            )}
                                        </p>
                                        <p className="mt-1 text-sm text-slate-500">
                                            {comparison.difference > 0
                                                ? "Location B is more expensive."
                                                : comparison.difference < 0
                                                    ? "Location B is less expensive."
                                                    : "Both locations have the same estimated cost."}
                                        </p>
                                    </div>

                                    <div>
                                        <p className="text-sm text-slate-500">
                                            Percentage difference relative to Location A
                                        </p>
                                        <p className="mt-1 text-2xl font-bold text-slate-900">
                                            {comparison.percentage == null
                                                ? "N/A"
                                                : `${Math.abs(comparison.percentage).toFixed(2)}%`}
                                        </p>
                                        {comparison.percentage != null && (
                                            <p className="mt-1 text-sm text-slate-500">
                                                {comparison.percentage > 0
                                                    ? "Location B costs more."
                                                    : comparison.percentage < 0
                                                        ? "Location B costs less."
                                                        : "There is no cost difference."}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </section>
                        </section>
                    )}

                    <footer className="py-6 text-center text-xs text-slate-400">
                        Estimates are based on the selected locations and shared project inputs.
                    </footer>
                </main>
            </div>
        </div>
    );
}
