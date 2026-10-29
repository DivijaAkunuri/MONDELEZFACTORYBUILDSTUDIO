
import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { getReference, calculateFast } from "@/lib/api";
import Sidebar from "@/components/estimator/Sidebar";

const EMPTY_LOCATION = {
    city: "",
    region: "",
    country: "",
};

function getApiData(value) {
    return value?.data ?? value;
}

function getTotal(result) {
    const value = result?.totals?.total_project_cost;
    return Number.isFinite(Number(value)) ? Number(value) : null;
}

function LocationCard({
    title,
    location,
    setLocation,
    regions,
    countriesByRegion,
    loadingRegions,
}) {
    const countries = countriesByRegion[location.region] || [];

    const update = (field, value) => {
        setLocation((previous) => ({
            ...previous,
            [field]: value,
            ...(field === "region" ? { country: "" } : {}),
        }));
    };

    return (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-5">
                <h2 className="text-lg font-semibold text-slate-900">
                    {title}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                    Choose a region and country, then enter the city.
                </p>
            </div>

            <div className="space-y-4">
                <div>
                    <label className="mb-1.5 block text-sm font-medium text-slate-700">
                        Region
                    </label>

                    <select
                        value={location.region}
                        onChange={(event) => update("region", event.target.value)}
                        required
                        disabled={loadingRegions}
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    >
                        <option value="">
                            {loadingRegions ? "Loading regions..." : "Select region"}
                        </option>

                        {regions.map((region) => (
                            <option key={region} value={region}>
                                {region}
                            </option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="mb-1.5 block text-sm font-medium text-slate-700">
                        Country
                    </label>

                    <select
                        value={location.country}
                        onChange={(event) => update("country", event.target.value)}
                        required
                        disabled={!location.region || countries.length === 0}
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none disabled:bg-slate-100"
                    >
                        <option value="">Select country</option>

                        {countries.map((country) => (
                            <option key={country} value={country}>
                                {country}
                            </option>
                        ))}
                    </select>

                    {location.region && countries.length === 0 && (
                        <p className="mt-1 text-xs text-amber-700">
                            No countries are available for this region in the reference data.
                        </p>
                    )}
                </div>

                <div>
                    <label className="mb-1.5 block text-sm font-medium text-slate-700">
                        City
                    </label>

                    <input
                        type="text"
                        value={location.city}
                        onChange={(event) => update("city", event.target.value)}
                        placeholder="Enter city name"
                        required
                        className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />

                    <p className="mt-1 text-xs text-slate-500">
                        Enter the city manually.
                    </p>
                </div>
            </div>
        </section>
    );
}

function ResultCard({ title, location, result, currency }) {
    const total = getTotal(result);

    return (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="font-semibold text-slate-900">{title}</h3>

            <p className="mt-1 text-sm text-slate-500">
                {[location.city, location.region, location.country]
                    .filter(Boolean)
                    .join(", ")}
            </p>

            {total === null ? (
                <p className="mt-5 text-sm text-amber-700">
                    The API did not return a valid total project cost.
                </p>
            ) : (
                <>
                    <p className="mt-5 text-sm text-slate-500">
                        Estimated project cost
                    </p>

                    <p className="mt-1 break-words text-2xl font-bold text-slate-900">
                        {currency}{" "}
                        {total.toLocaleString(undefined, {
                            maximumFractionDigits: 2,
                        })}
                    </p>

                    {result?.totals?.cost_per_sqm != null && (
                        <p className="mt-3 text-sm text-slate-600">
                            Cost per m²: {currency}{" "}
                            {Number(result.totals.cost_per_sqm).toLocaleString()}
                        </p>
                    )}
                </>
            )}
        </section>
    );
}

export default function CompareOptions() {
    const navigate = useNavigate();
    const routeLocation = useLocation();

    const [reference, setReference] = React.useState(null);
    const [loadingRegions, setLoadingRegions] = React.useState(true);
    const [referenceError, setReferenceError] = React.useState("");

    const [locationA, setLocationA] = React.useState({ ...EMPTY_LOCATION });
    const [locationB, setLocationB] = React.useState({ ...EMPTY_LOCATION });

    const [projectInputs, setProjectInputs] = React.useState(() => {
        const passedInputs = routeLocation.state?.inputs;

        if (passedInputs) return passedInputs;

        try {
            const saved = sessionStorage.getItem("estimator_inputs");
            return saved ? JSON.parse(saved) : null;
        } catch {
            return null;
        }
    });

    const [results, setResults] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState("");

    React.useEffect(() => {
        let cancelled = false;

        async function loadReference() {
            setLoadingRegions(true);
            setReferenceError("");

            try {
                const response = await getReference();
                const data = getApiData(response);

                if (!data || typeof data.regions !== "object") {
                    throw new Error(
                        "The reference API did not return the expected region-to-country data."
                    );
                }

                if (!cancelled) {
                    setReference(data);

                    // Preselect the estimator's existing region and country
                    // when they are available in the reference data.
                    const regionNames = Object.keys(data.regions || {});
                    const existingRegion = projectInputs?.region;
                    const defaultRegion = regionNames.includes(existingRegion)
                        ? existingRegion
                        : "";

                    const defaultCountries = data.regions?.[defaultRegion] || [];
                    const existingCountry = projectInputs?.location_country;
                    const defaultCountry = defaultCountries.includes(existingCountry)
                        ? existingCountry
                        : "";

                    setLocationA((previous) => ({
                        ...previous,
                        region: previous.region || defaultRegion,
                        country: previous.country || defaultCountry,
                        city: previous.city || projectInputs?.location_city || "",
                    }));
                }
            } catch (err) {
                if (!cancelled) {
                    setReferenceError(
                        err.message || "Unable to load regions and countries."
                    );
                }
            } finally {
                if (!cancelled) setLoadingRegions(false);
            }
        }

        loadReference();

        return () => {
            cancelled = true;
        };
    }, [projectInputs]);

    const countriesByRegion = reference?.regions || {};
    const regions = Object.keys(countriesByRegion);

    const updateProjectField = (field, value) => {
        setProjectInputs((previous) => ({
            ...previous,
            [field]: value,
        }));
    };

    const handleCompare = async (event) => {
        event.preventDefault();
        setError("");
        setResults(null);

        if (referenceError) {
            setError("Region data could not be loaded. Please try again.");
            return;
        }

        if (!projectInputs) {
            setError(
                "Project inputs were not found. Open Compare from your estimator after entering your project details."
            );
            return;
        }

        for (const [name, selected] of [
            ["Location A", locationA],
            ["Location B", locationB],
        ]) {
            if (
                !selected.region ||
                !selected.country ||
                !selected.city.trim()
            ) {
                setError(
                    `${name}: select a region and country, and enter a city.`
                );
                return;
            }

            if (!(countriesByRegion[selected.region] || []).includes(selected.country)) {
                setError(
                    `${name}: the selected country does not belong to the selected region in the reference data.`
                );
                return;
            }
        }

        const length = Number(projectInputs.length_m);
        const width = Number(projectInputs.width_m);

        if (
            !Number.isFinite(length) ||
            !Number.isFinite(width) ||
            length <= 0 ||
            width <= 0
        ) {
            setError(
                "The shared project must have valid length and width values greater than zero."
            );
            return;
        }

        setLoading(true);

        try {
            const buildPayload = (selected) => ({
                ...projectInputs,
                location_city: selected.city.trim(),
                location_country: selected.country,
                region: selected.region,
            });

            const [resultA, resultB] = await Promise.all([
                calculateFast(buildPayload(locationA)),
                calculateFast(buildPayload(locationB)),
            ]);

            if (
                !resultA?.totals ||
                !Number.isFinite(Number(resultA.totals.total_project_cost)) ||
                !resultB?.totals ||
                !Number.isFinite(Number(resultB.totals.total_project_cost))
            ) {
                throw new Error(
                    "The calculation API did not return valid totals for both locations."
                );
            }

            setResults({ resultA, resultB });
        } catch (err) {
            setError(
                err.message ||
                "Unable to calculate both estimates. Check the backend response and try again."
            );
        } finally {
            setLoading(false);
        }
    };

    const totalA = getTotal(results?.resultA);
    const totalB = getTotal(results?.resultB);

    const currency =
        projectInputs?.currency ||
        routeLocation.state?.currency ||
        "USD";

    const difference =
        totalA !== null && totalB !== null ? totalA - totalB : null;

    const percentageDifference =
        totalA !== null && totalB !== null && totalB !== 0
            ? (Math.abs(difference) / totalB) * 100
            : null;

    return (
        <div className="flex h-screen w-full overflow-hidden bg-slate-50">
            <Sidebar />

            <div className="flex min-w-0 flex-1 flex-col overflow-y-auto"></div>
            <header className="border-b border-slate-200 bg-white">
                <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-5">
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900">
                            Compare Options
                        </h1>
                        <p className="mt-1 text-sm text-slate-500">
                            Compare the same construction project across two locations.
                        </p>
                    </div>

                    <button
                        type="button"
                        onClick={() => navigate(-1)}
                        className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                    >
                        Back
                    </button>
                </div>
            </header>

            <main className="mx-auto max-w-7xl space-y-6 px-5 py-7">
                {referenceError && (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                        {referenceError}
                    </div>
                )}

                <form onSubmit={handleCompare} className="space-y-6">
                    <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                        <LocationCard
                            title="Location A"
                            location={locationA}
                            setLocation={setLocationA}
                            regions={regions}
                            countriesByRegion={countriesByRegion}
                            loadingRegions={loadingRegions}
                        />

                        <LocationCard
                            title="Location B"
                            location={locationB}
                            setLocation={setLocationB}
                            regions={regions}
                            countriesByRegion={countriesByRegion}
                            loadingRegions={loadingRegions}
                        />
                    </div>

                    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                        <h2 className="text-lg font-semibold text-slate-900">
                            Shared Project Inputs
                        </h2>

                        <p className="mt-1 text-sm text-slate-500">
                            These values are reused for both locations.
                        </p>

                        {!projectInputs ? (
                            <p className="mt-4 text-sm text-amber-700">
                                No saved estimator inputs were found. Return to the estimator,
                                enter your project details, and open Compare again.
                            </p>
                        ) : (
                            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-slate-700">
                                        Project Name
                                    </label>
                                    <input
                                        value={projectInputs.project_name || ""}
                                        onChange={(event) =>
                                            updateProjectField("project_name", event.target.value)
                                        }
                                        className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                                    />
                                </div>

                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-slate-700">
                                        Length (m)
                                    </label>
                                    <input
                                        type="number"
                                        min="0.01"
                                        step="any"
                                        value={projectInputs.length_m ?? ""}
                                        onChange={(event) =>
                                            updateProjectField("length_m", event.target.value)
                                        }
                                        required
                                        className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                                    />
                                </div>

                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-slate-700">
                                        Width (m)
                                    </label>
                                    <input
                                        type="number"
                                        min="0.01"
                                        step="any"
                                        value={projectInputs.width_m ?? ""}
                                        onChange={(event) =>
                                            updateProjectField("width_m", event.target.value)
                                        }
                                        required
                                        className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                                    />
                                </div>

                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-slate-700">
                                        Building Type
                                    </label>
                                    <input
                                        value={projectInputs.building_type || ""}
                                        onChange={(event) =>
                                            updateProjectField("building_type", event.target.value)
                                        }
                                        className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                                    />
                                </div>

                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-slate-700">
                                        Built-up Area (m²)
                                    </label>
                                    <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-medium text-slate-800">
                                        {(
                                            Number(projectInputs.length_m || 0) *
                                            Number(projectInputs.width_m || 0)
                                        ).toLocaleString()}
                                    </div>
                                </div>

                                <div>
                                    <label className="mb-1.5 block text-sm font-medium text-slate-700">
                                        Project Type
                                    </label>
                                    <input
                                        value={projectInputs.project_type || ""}
                                        readOnly
                                        className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm"
                                    />
                                </div>
                            </div>
                        )}
                    </section>

                    {error && (
                        <div
                            role="alert"
                            className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
                        >
                            {error}
                        </div>
                    )}

                    <div className="flex justify-end">
                        <button
                            type="submit"
                            disabled={loading || loadingRegions || !projectInputs}
                            className="rounded-lg bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {loading ? "Calculating..." : "Compare Estimated Costs"}
                        </button>
                    </div>
                </form>

                {results && (
                    <section className="space-y-5">
                        <div>
                            <h2 className="text-xl font-bold text-slate-900">
                                Comparison Results
                            </h2>
                            <p className="mt-1 text-sm text-slate-500">
                                Both calculations use the same project inputs.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                            <ResultCard
                                title="Location A"
                                location={locationA}
                                result={results.resultA}
                                currency={currency}
                            />

                            <ResultCard
                                title="Location B"
                                location={locationB}
                                result={results.resultB}
                                currency={currency}
                            />
                        </div>

                        {difference !== null && (
                            <section className="rounded-xl border border-slate-200 bg-white p-5">
                                <h3 className="font-semibold text-slate-900">
                                    Cost Difference
                                </h3>

                                <p className="mt-2 text-2xl font-bold text-slate-900">
                                    {currency}{" "}
                                    {Math.abs(difference).toLocaleString(undefined, {
                                        maximumFractionDigits: 2,
                                    })}
                                </p>

                                <p className="mt-2 text-sm text-slate-600">
                                    {difference === 0
                                        ? "Both locations returned the same estimated cost."
                                        : difference < 0
                                            ? "Location A returned the lower estimated cost."
                                            : "Location B returned the lower estimated cost."}
                                </p>

                                {percentageDifference !== null && (
                                    <p className="mt-1 text-sm text-slate-500">
                                        Difference relative to Location B:{" "}
                                        {percentageDifference.toFixed(2)}%
                                    </p>
                                )}

                                <p className="mt-3 text-xs text-slate-500">
                                    Confirm that your backend applies the appropriate
                                    location-specific cost factors before relying on this result.
                                    Both totals are displayed in the estimator's configured
                                    currency; cross-currency conversion is not performed here.
                                </p>
                            </section>
                        )}
                    </section>
                )}
            </main>
        </div>
    );
}
