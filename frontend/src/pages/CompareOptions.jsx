
import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const initialLocation = {
  city: "",
  region: "",
  country: "",
};

const initialProject = {
  projectName: "",
  buildingType: "FMCG Plant",
  length: "100",
  width: "50",
  complexity: "Medium",
};

function LocationCard({ title, location, setLocation, color }) {
  const updateField = (field, value) => {
    setLocation((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const fields = [
    { key: "city", label: "City", placeholder: "e.g. Bengaluru" },
    { key: "region", label: "Region / State", placeholder: "e.g. Karnataka" },
    { key: "country", label: "Country", placeholder: "e.g. India" },
  ];

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-5 flex items-center gap-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg text-lg font-bold ${color}`}
        >
          {title.endsWith("A") ? "A" : "B"}
        </div>

        <div>
          <h2 className="text-lg font-semibold text-slate-800">
            {title}
          </h2>
          <p className="text-sm text-slate-500">
            Enter the location details
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {fields.map((field) => (
          <div key={field.key}>
            <label className="mb-1.5 block text-sm font-medium text-slate-700">
              {field.label}
            </label>

            <input
              type="text"
              value={location[field.key]}
              onChange={(event) =>
                updateField(field.key, event.target.value)
              }
              placeholder={field.placeholder}
              required
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>
        ))}
      </div>
    </section>
  );
}

function ResultCard({ title, location, result, currency }) {
  const total =
    result?.totals?.total_project_cost ??
    result?.total_project_cost ??
    result?.total_cost;

  const costPerSqm =
    result?.totals?.cost_per_sqm ??
    result?.cost_per_sqm;

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>

      <p className="mt-1 text-sm text-slate-500">
        {[location.city, location.region, location.country]
          .filter(Boolean)
          .join(", ")}
      </p>

      {total !== undefined ? (
        <div className="mt-5">
          <p className="text-sm text-slate-500">
            Estimated project cost
          </p>
          <p className="mt-1 break-words text-2xl font-bold text-slate-900">
            {currency}{" "}
            {Number(total).toLocaleString(undefined, {
              maximumFractionDigits: 2,
            })}
          </p>

          {costPerSqm !== undefined && (
            <p className="mt-3 text-sm text-slate-600">
              Cost per m²: {currency}{" "}
              {Number(costPerSqm).toLocaleString(undefined, {
                maximumFractionDigits: 2,
              })}
            </p>
          )}
        </div>
      ) : (
        <p className="mt-5 text-sm text-slate-500">
          The calculation API did not return a recognized total-cost
          field. Check the response structure before displaying results.
        </p>
      )}
    </section>
  );
}

export default function CompareOptions() {
  const navigate = useNavigate();
  const routeLocation = useLocation();

  const existingInputs = routeLocation.state?.inputs;

  const [locationA, setLocationA] = useState({
    ...initialLocation,
  });

  const [locationB, setLocationB] = useState({
    ...initialLocation,
  });

  const [project, setProject] = useState(() => ({
    ...initialProject,
    projectName: existingInputs?.project_name ?? "",
    buildingType:
      existingInputs?.industry_type ??
      existingInputs?.building_type ??
      initialProject.buildingType,
    length:
      existingInputs?.length_m != null
        ? String(existingInputs.length_m)
        : initialProject.length,
    width:
      existingInputs?.width_m != null
        ? String(existingInputs.width_m)
        : initialProject.width,
    complexity:
      existingInputs?.complexity_level ??
      initialProject.complexity,
  }));

  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const updateProject = (field, value) => {
    setProject((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const validateForm = () => {
    if (
      !locationA.city.trim() ||
      !locationA.region.trim() ||
      !locationA.country.trim()
    ) {
      return "Please complete all three fields for Location A.";
    }

    if (
      !locationB.city.trim() ||
      !locationB.region.trim() ||
      !locationB.country.trim()
    ) {
      return "Please complete all three fields for Location B.";
    }

    if (!project.projectName.trim()) {
      return "Please enter a project name.";
    }

    if (
      !Number.isFinite(Number(project.length)) ||
      !Number.isFinite(Number(project.width)) ||
      Number(project.length) <= 0 ||
      Number(project.width) <= 0
    ) {
      return "Length and width must both be greater than zero.";
    }

    return "";
  };

  const handleCompare = async (event) => {
    event.preventDefault();
    setError("");
    setResults(null);

    const validationError = validateForm();

    if (validationError) {
      setError(validationError);
      return;
    }

    if (!existingInputs) {
      setError(
        "Your existing estimator inputs were not provided. Open Compare from the estimator after creating your project estimate so the full project inputs can be reused."
      );
      return;
    }

    setLoading(true);

    try {
      /*
       * IMPORTANT:
       * Set REACT_APP_BACKEND_URL to your deployed backend URL.
       * This code reuses your existing estimator inputs and changes
       * the city for each calculation.
       *
       * The backend must support these location-specific fields for
       * regional pricing to work correctly.
       */
      const backendUrl = (
        process.env.REACT_APP_BACKEND_URL || ""
      ).replace(/\/$/, "");

      const calculateForLocation = async (selectedLocation) => {
        const payload = {
          ...existingInputs,
          project_name: project.projectName,
          length_m: Number(project.length),
          width_m: Number(project.width),
          city: selectedLocation.city,
          region: selectedLocation.region,
          country: selectedLocation.country,
        };

        const response = await fetch(
          `${backendUrl}/api/estimator/calculate-fast`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
          }
        );

        if (!response.ok) {
          const message = await response.text();
          throw new Error(
            `Calculation failed (${response.status}): ${message}`
          );
        }

        return response.json();
      };

      const [resultA, resultB] = await Promise.all([
        calculateForLocation(locationA),
        calculateForLocation(locationB),
      ]);

      setResults({
        resultA,
        resultB,
      });
    } catch (err) {
      setError(
        err.message ||
          "Unable to calculate the comparison. Please check your backend configuration."
      );
    } finally {
      setLoading(false);
    }
  };

  const currency =
    existingInputs?.currency ||
    "USD";

  const totalA =
    results?.resultA?.totals?.total_project_cost ??
    results?.resultA?.total_project_cost ??
    results?.resultA?.total_cost;

  const totalB =
    results?.resultB?.totals?.total_project_cost ??
    results?.resultB?.total_project_cost ??
    results?.resultB?.total_cost;

  const comparableTotals =
    Number.isFinite(Number(totalA)) &&
    Number.isFinite(Number(totalB));

  const difference = comparableTotals
    ? Number(totalA) - Number(totalB)
    : null;

  const percentageDifference =
    comparableTotals && Number(totalB) !== 0
      ? (Math.abs(difference) / Number(totalB)) * 100
      : null;

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4">
          <div>
            <h1 className="text-xl font-bold text-slate-900">
              Compare Construction Costs
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Compare the same project across two locations.
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
        <form onSubmit={handleCompare} className="space-y-6">
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            <LocationCard
              title="Location A"
              location={locationA}
              setLocation={setLocationA}
              color="bg-blue-100 text-blue-700"
            />

            <LocationCard
              title="Location B"
              location={locationB}
              setLocation={setLocationB}
              color="bg-violet-100 text-violet-700"
            />
          </div>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-5">
              <h2 className="text-lg font-semibold text-slate-800">
                Shared Project Inputs
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                These project details are reused for both locations.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Project Name
                </label>
                <input
                  value={project.projectName}
                  onChange={(event) =>
                    updateProject("projectName", event.target.value)
                  }
                  placeholder="Enter project name"
                  required
                  className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Building / Industry Type
                </label>
                <input
                  value={project.buildingType}
                  onChange={(event) =>
                    updateProject("buildingType", event.target.value)
                  }
                  required
                  className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Project Complexity
                </label>
                <select
                  value={project.complexity}
                  onChange={(event) =>
                    updateProject("complexity", event.target.value)
                  }
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Length (m)
                </label>
                <input
                  type="number"
                  min="0.01"
                  step="any"
                  value={project.length}
                  onChange={(event) =>
                    updateProject("length", event.target.value)
                  }
                  required
                  className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
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
                  value={project.width}
                  onChange={(event) =>
                    updateProject("width", event.target.value)
                  }
                  required
                  className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-slate-700">
                  Calculated Area (m²)
                </label>
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-semibold text-slate-800">
                  {Number(project.length) > 0 &&
                  Number(project.width) > 0
                    ? (
                        Number(project.length) *
                        Number(project.width)
                      ).toLocaleString()
                    : "—"}
                </div>
              </div>
            </div>

            <p className="mt-4 text-xs text-slate-500">
              The building type and complexity fields are displayed here
              for comparison planning. Your backend's existing input model
              determines which values are actually used in the calculation.
            </p>
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
              disabled={loading}
              className="rounded-lg bg-slate-900 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading
                ? "Calculating both locations..."
                : "Compare Estimated Costs"}
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
                Results returned by your estimator backend.
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

            {comparableTotals && (
              <section className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="font-semibold text-slate-800">
                  Cost Difference
                </h3>

                <p className="mt-3 text-2xl font-bold text-slate-900">
                  {currency}{" "}
                  {Math.abs(difference).toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </p>

                <p className="mt-2 text-sm text-slate-600">
                  {difference === 0
                    ? "Both estimates have the same total."
                    : difference < 0
                    ? "Location A has the lower returned total."
                    : "Location B has the lower returned total."}
                </p>

                {percentageDifference !== null && (
                  <p className="mt-1 text-sm text-slate-500">
                    Difference relative to Location B:{" "}
                    {percentageDifference.toFixed(2)}%
                  </p>
                )}

                <p className="mt-3 text-xs text-slate-500">
                  This comparison is valid only if both totals use the same
                  currency and the backend applies verified location-specific
                  construction rates.
                </p>
              </section>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
