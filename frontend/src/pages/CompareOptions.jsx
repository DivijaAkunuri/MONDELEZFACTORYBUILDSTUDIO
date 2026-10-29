
import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, GitCompareArrows, MapPin, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { getReference, calculateFast } from "@/lib/api";
import { fmtMoney, fmtNumber } from "@/lib/format";

const inputClass =
  "mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-100";

const labelClass = "block text-sm font-medium text-slate-700";

const cardClass =
  "rounded-xl border border-slate-200 bg-white p-5 shadow-sm";

function readSavedInputs() {
  try {
    const saved = sessionStorage.getItem("estimator_inputs");
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return parsed;
      }
    }
  } catch (error) {
    console.warn("Could not read saved estimator inputs:", error);
  }

  return {};
}

function getErrorMessage(error) {
  const detail =
    error?.response?.data?.detail ??
    error?.response?.data?.message ??
    error?.message;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join(", ");
  }

  return "Unable to calculate the estimate. Please check your backend connection.";
}

function LocationCard({
  title,
  location,
  onChange,
  regions,
  referenceLoading,
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
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Choose a region, country and city.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
        <div>
          <label className={labelClass}>Region</label>
          <select
            className={inputClass}
            value={location.region}
            disabled={referenceLoading}
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
            disabled={!location.region || referenceLoading}
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
            type="text"
            placeholder="Enter city name"
            value={location.city}
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

function ResultCard({ title, location, result, currency, fxRates }) {
  const total = Number(result?.totals?.total_project_cost);

  return (
    <section className={cardClass}>
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <h3 className="mt-1 text-lg font-semibold text-slate-900">
        {location.city}, {location.country}
      </h3>

      <p className="mt-5 text-sm text-slate-500">Estimated project cost</p>
      <p className="mt-1 break-words text-2xl font-bold text-blue-700">
        {Number.isFinite(total)
          ? fmtMoney(total, currency, fxRates)
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
  const [projectInputs, setProjectInputs] = React.useState(() => {
    const saved = readSavedInputs();
    const passed = routeLocation.state?.inputs || {};

    return { ...saved, ...passed };
  });

  const [locationA, setLocationA] = React.useState(() => {
    const saved = readSavedInputs();
    const passed = routeLocation.state?.inputs || {};
    const inputs = { ...saved, ...passed };

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
        console.error("Failed to load reference data:", error);
        if (!cancelled) {
          toast.error("Could not load regions and countries.");
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
    const saved = routeLocation.state?.inputs;
    if (saved && typeof saved === "object") {
      setProjectInputs((previous) => ({ ...previous, ...saved }));
      setLocationA({
        region: saved.region || "",
        country: saved.location_country || "",
        city: saved.location_city || "",
      });
    }
  }, [routeLocation.state]);

  const regions = reference?.regions || {};
  const currency = projectInputs.currency || "USD";
  const fxRates = routeLocation.state?.fxRates || {};

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
    if (!locationA.region || !locationA.country || !locationA.city.trim()) {
      toast.error("Complete the region, country and city for Location A.");
      return;
    }

    if (!locationB.region || !locationB.country || !locationB.city.trim()) {
      toast.error("Complete the region, country and city for Location B.");
      return;
    }

    if (
      locationA.city.trim().toLowerCase() ===
        locationB.city.trim().toLowerCase() &&
      locationA.country === locationB.country
    ) {
      toast.error("Choose two different locations to compare.");
      return;
    }

    if (
      !Number.isFinite(Number(projectInputs.length_m)) ||
      Number(projectInputs.length_m) <= 0 ||
      !Number.isFinite(Number(projectInputs.width_m)) ||
      Number(projectInputs.width_m) <= 0
    ) {
      toast.error("Length and width must both be greater than zero.");
      return;
    }

    setLoading(true);
    setComparison(null);

    const createPayload = (location) => ({
      ...projectInputs,
      region: location.region,
      location_country: location.country,
      location_city: location.city.trim(),
      plot_area_sqm:
        Number(projectInputs.length_m) * Number(projectInputs.width_m),
      land_area_sqm:
        Number(projectInputs.length_m) * Number(projectInputs.width_m),
    });

    try {
      const [resultA, resultB] = await Promise.all([
        calculateFast(createPayload(locationA)),
        calculateFast(createPayload(locationB)),
      ]);

      const totalA = Number(resultA?.totals?.total_project_cost);
      const totalB = Number(resultB?.totals?.total_project_cost);

      if (
        !Number.isFinite(totalA) ||
        !Number.isFinite(totalB)
      ) {
        throw new Error(
          "The backend response did not contain a valid total project cost."
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

      toast.success("Location comparison completed.");
    } catch (error) {
      console.error("Comparison calculation failed:", error);
      toast.error(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen w-full bg-slate-50">
      <main className="mx-auto w-full max-w-none px-4 py-6 sm:px-6 lg:px-8">
        {/* Page heading */}
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-100 text-blue-700">
                <GitCompareArrows size={23} />
              </div>

              <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                  Compare Options
                </h1>
                <p className="mt-1 text-sm text-slate-500 sm:text-base">
                  Compare the same construction project across two locations.
                </p>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
          >
            <ArrowLeft size={16} />
            Back
          </button>
        </header>

        {/* Location A and B */}
        <div className="grid grid-cols-1 items-stretch gap-5 lg:grid-cols-2">
          <LocationCard
            title="Location A"
            location={locationA}
            onChange={(next) => {
              setLocationA(next);
              setComparison(null);
            }}
            regions={regions}
            referenceLoading={referenceLoading}
          />

          <LocationCard
            title="Location B"
            location={locationB}
            onChange={(next) => {
              setLocationB(next);
              setComparison(null);
            }}
            regions={regions}
            referenceLoading={referenceLoading}
          />
        </div>

        {/* Shared project inputs */}
        <section className={`${cardClass} mt-5`}>
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-900">
              Shared Project Inputs
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              These project details are reused for both locations.
            </p>
          </div>

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
                Calculated from length × width × floors.
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

        {/* Compare button */}
        <div className="mt-6 flex justify-center">
          <button
            type="button"
            onClick={compareCosts}
            disabled={loading || referenceLoading}
            className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto sm:min-w-72"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={18} />
                Calculating comparison...
              </>
            ) : (
              <>
                <GitCompareArrows size={18} />
                Compare Estimated Costs
              </>
            )}
          </button>
        </div>

        {/* Results appear after calculation */}
        {comparison && (
          <section className="mt-8 space-y-5">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Comparison Results
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Estimated costs for the same project in each location.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <ResultCard
                title="Location A"
                location={locationA}
                result={comparison.resultA}
                currency={currency}
                fxRates={fxRates}
              />

              <ResultCard
                title="Location B"
                location={locationB}
                result={comparison.resultB}
                currency={currency}
                fxRates={fxRates}
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
                      currency,
                      fxRates
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
                        ? "Location B costs more than Location A."
                        : comparison.percentage < 0
                          ? "Location B costs less than Location A."
                          : "There is no cost difference."}
                    </p>
                  )}
                </div>
              </div>
            </section>
          </section>
        )}

        <footer className="py-6 text-center text-xs text-slate-400">
          Estimates are based on the shared project inputs and the selected
          locations.
        </footer>
      </main>
    </div>
  );
}
