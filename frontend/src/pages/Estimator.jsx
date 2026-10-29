import React from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  RefreshCw,
  GitCompareArrows,
  Download,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import Sidebar from "@/components/estimator/Sidebar";
import RightToolbar from "@/components/estimator/RightToolbar";
import Stepper from "@/components/estimator/Stepper";
import KpiCards from "@/components/estimator/KpiCards";
import { DonutChart, TrendChart } from "@/components/estimator/Charts";
import UtilityCards from "@/components/estimator/UtilityCards";
import Wizard from "@/components/estimator/Wizard";
import EditProjectDialog from "@/components/estimator/EditProjectDialog";
import CityFactorsCard from "@/components/estimator/CityFactorsCard";

import {
  TabsBar,
  BoqTable,
  UtilitiesSummary,
  ProjectOverview,
  AssumptionsBox,
  RisksBox,
  OptimizationsBox,
} from "@/components/estimator/OutputPanels";

import {
  getReference,
  getFxRates,
  calculateFast,
  getInsights,
} from "@/lib/api";

import { fmtMoney, fmtNumber } from "@/lib/format";
import { TID } from "@/constants/testIds";

/* -------------------------------------------------------
   DEFAULT PROJECT INPUTS
------------------------------------------------------- */

const DEFAULT_INPUTS = {
  project_name: "Mondelez",
  user_name: "",
  project_type: "Greenfield",
  industry_type: "Food",
  product_category: "Chocolate",

  location_city: "Hamburg",
  location_country: "Germany",
  region: "MEU",
  continent: "Europe",
  location_tier: "Metro",

  building_type: "Industrial Building (RCC + PEB)",
  length_m: 185,
  width_m: 24,
  height_m: 7,
  num_floors: 1,
  bay_spacing_m: 8,


  rm_warehouse_length_m: "",
  rm_warehouse_width_m: "",
  rm_warehouse_height_m: "",
  rm_warehouse_built_up_area_sqm: "",
  fg_warehouse_length_m: "",
  fg_warehouse_width_m: "",
  fg_warehouse_height_m: "",
  fg_warehouse_built_up_area_sqm: "",

  building_components: [
    "Production Block",
    "Cold Store",
    "Utilities Block",
    "Admin Building",
  ],

  soil_type: "Medium Dense Sand",
  sbc_soil_type: "Hard Stone",
  soil_hardness: "Medium",
  foundation_type: ["Isolated Footing"],

  column_type: "Steel",
  roof_type: "PEB + Insulated Panel",
  seismic_zone: "Zone 0 (Very Low)",
  wind_zone: "Zone 2",
  wind_speed_ms: 45,

  gwt_depth: "Medium (3-8 m)",

  utility_scope: [
    "Boiler House",
    "Chiller Plant",
    "HVAC System",
    "Air Compressors",
    "WTP",
    "Fire Fighting System",
    "Electrical Substation",
  ],

  production_capacity_tpd: 120,
  annual_output_mt: 36000,

  cooling_tunnel_load_tr: 180,
  tempering_utility_demand: "Medium",
  humidity_controlled_pct: 40,
  chocolate_storage_temp_c: 19,
  process_hot_water_lph: 2500,

  oven_capacity_kg_hr: 1200,
  fuel_type: "PNG",
  baking_line_qty: 2,
  compressed_air_demand_cfm: 1500,
  dust_collection_required: true,
  cooling_conveyor_load: "Standard",

  include_roads: true,
  include_landscaping: true,
  include_fence: true,

  land_area_sqm: 8880,
  ground_coverage_pct: 58,
  far_fsi: 1.2,

  water_availability: "Municipal + Borewell",
  grid_reliability: "Good",
  ambient_temp_range: "Temperate (5°C - 30°C)",
  relative_humidity_pct: 70,

  complexity: {
    brownfield: false,
    explosion_risk: false,
    utility_redundancy: true,
    high_floor_load: false,
    remote_site: false,
  },

  currency: "USD",
  base_unit: "mm",
  contingency_pct: 8.0,

  male_employees: 0,
  female_employees: 0,
  num_employees: 0,
  special_work_clothing: "Yes",
  work_shoes_required: "Yes",
  canteen_dining_required: "Yes",
};

/* -------------------------------------------------------
   OUTPUT TABS
------------------------------------------------------- */

const TABS = [
  { key: "summary", label: "Summary" },
  { key: "breakdown", label: "Cost Breakdown" },
  { key: "boq", label: "BOQ" },
  { key: "utilities", label: "Utilities Summary" },
  { key: "process", label: "Process Data" },
  { key: "infra", label: "Infra Summary" },
  { key: "cashflow", label: "Cost Trend" },
  { key: "sensitivity", label: "Sensitivity" },
  { key: "assumptions", label: "Assumptions" },
];

/* -------------------------------------------------------
   ERROR MESSAGE HELPER

   Handles strings, objects, arrays, and API validation
   errors without displaying "[object Object]".
------------------------------------------------------- */

function getReadableError(error) {
  const data = error?.response?.data;

  const detail = data?.detail ?? data?.message ?? data?.error;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;

        const location = Array.isArray(item?.loc)
          ? item.loc.join(" → ")
          : "";

        const message =
          item?.msg ??
          item?.message ??
          item?.detail;

        if (location && message) {
          return `${location}: ${message}`;
        }

        if (message) {
          return String(message);
        }

        try {
          return JSON.stringify(item);
        } catch {
          return "Invalid input";
        }
      })
      .join("; ");
  }

  if (detail && typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return "The server returned an unreadable error.";
    }
  }

  if (typeof data === "string" && data.trim()) {
    return data;
  }

  if (data && typeof data === "object") {
    try {
      return JSON.stringify(data);
    } catch {
      // Fall through to the ordinary error message.
    }
  }

  if (error?.code === "ECONNABORTED") {
    return "The calculation request timed out. Please try again.";
  }

  if (!error?.response && error?.request) {
    return "The server could not be reached. Check that the backend is running and the API URL is correct.";
  }

  if (error?.message) {
    return error.message;
  }

  return "An unexpected error occurred. Check the browser console and backend logs.";
}

function validateInputs(inputs) {

  const floors = Number(inputs.num_floors);

  if (!Number.isFinite(floors) || floors < 1) {
    return "Number of floors must be at least 1.";
  }

  const contingency = Number(inputs.contingency_pct);

  if (
    !Number.isFinite(contingency) ||
    contingency < 4 ||
    contingency > 20
  ) {
    return "Contingency must be between 4% and 20%.";
  }

  return "";
}

/* -------------------------------------------------------
   ESTIMATOR PAGE
------------------------------------------------------- */

export default function Estimator({ initialView = "new-estimate" }) {
  const navigate = useNavigate();

  const [reference, setReference] = React.useState(null);
  const [fxRates, setFxRates] = React.useState({});

  const [inputs, setInputs] = React.useState(() => {
    try {
      const saved = sessionStorage.getItem("estimator_inputs");

      if (!saved) return { ...DEFAULT_INPUTS };

      const parsed = JSON.parse(saved);

      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        return { ...DEFAULT_INPUTS };
      }

      return {
        ...DEFAULT_INPUTS,
        ...parsed,
        complexity: {
          ...DEFAULT_INPUTS.complexity,
          ...(parsed.complexity || {}),
        },
      };
    } catch (error) {
      console.warn("Could not restore estimator inputs:", error);
      return { ...DEFAULT_INPUTS };
    }
  });

  const [result, setResult] = React.useState(() => {
    try {
      const saved = sessionStorage.getItem("estimator_result");

      if (!saved) return null;

      const parsed = JSON.parse(saved);

      return parsed && typeof parsed === "object" ? parsed : null;
    } catch (error) {
      console.warn("Could not restore estimator result:", error);
      return null;
    }
  });

  const [loading, setLoading] = React.useState(false);
  const [step, setStep] = React.useState(initialView === "dashboard" ? 5 : 0);
  const [activeTab, setActiveTab] = React.useState("summary");
  const [editOpen, setEditOpen] = React.useState(false);

  const isFirstInputsChange = React.useRef(true);
  const recalcTimer = React.useRef(null);
  const calculationRequestId = React.useRef(0);

  /* -----------------------------------------------------
     RECALCULATE ESTIMATE

     Keeps the last successful result if a later request
     fails. Ignores stale responses from earlier requests.
  ----------------------------------------------------- */

  const recalc = React.useCallback(async (inp) => {
    const validationError = validateInputs(inp);

    if (validationError) {
      toast.error(validationError);
      return;
    }

    const requestId = ++calculationRequestId.current;

    setLoading(true);

    try {
      const fast = await calculateFast(inp);

      // Ignore an outdated response if a newer calculation
      // has already started.
      if (requestId !== calculationRequestId.current) {
        return;
      }

      if (
        !fast ||
        typeof fast !== "object" ||
        Array.isArray(fast)
      ) {
        throw new Error(
          "The calculation API returned an invalid response. Check the backend server and API response."
        );
      }

      // Some APIs return application errors in a successful
      // HTTP response. Handle those explicitly.
      if (fast.error || fast.detail) {
        const detail = fast.detail ?? fast.error;

        throw new Error(
          typeof detail === "string"
            ? detail
            : JSON.stringify(detail)
        );
      }

      if (
        !fast.totals ||
        typeof fast.totals !== "object" ||
        !Number.isFinite(
          Number(fast.totals.total_project_cost)
        )
      ) {
        throw new Error(
          "The calculation response is missing totals or total_project_cost. Check the backend response format."
        );
      }

      // Store the successful result only after validating it.
      setResult((previous) => ({
        ...fast,
        insights: previous?.insights,
        fx_rates: previous?.fx_rates,
      }));

      toast.success("Estimate recalculated successfully.");

      // Supplementary data is optional. Failure to load
      // exchange rates or insights must not fail the estimate.
      try {
        const [fx, insights] = await Promise.all([
          getFxRates().catch((error) => {
            console.warn("Could not refresh exchange rates:", error);
            return null;
          }),

          getInsights(inp, fast).catch((error) => {
            console.warn("Could not load estimate insights:", error);
            return null;
          }),
        ]);

        // Do not apply supplementary data to a newer result.
        if (requestId !== calculationRequestId.current) {
          return;
        }

        if (fx?.rates && typeof fx.rates === "object") {
          setFxRates(fx.rates);
        }

        setResult((previous) => {
          if (!previous) return previous;

          return {
            ...previous,
            insights: insights ?? previous.insights,
            fx_rates: fx?.rates ?? previous.fx_rates,
          };
        });
      } catch (error) {
        console.warn("Optional estimate data failed to load:", error);
      }
    } catch (error) {
      if (requestId !== calculationRequestId.current) {
        return;
      }

      const message = getReadableError(error);

      console.error("Calculation API error:", {
        message: error?.message,
        status: error?.response?.status,
        response: error?.response?.data,
        error,
      });

      toast.error(`Calculation failed: ${message}`, {
        duration: 8000,
      });
    } finally {
      if (requestId === calculationRequestId.current) {
        setLoading(false);
      }
    }
  }, []);

  /* -----------------------------------------------------
     PERSIST INPUTS
  ----------------------------------------------------- */

  React.useEffect(() => {
    try {
      sessionStorage.setItem(
        "estimator_inputs",
        JSON.stringify(inputs)
      );
    } catch (error) {
      console.warn("Could not save estimator inputs:", error);
    }
  }, [inputs]);

  /* -----------------------------------------------------
     PERSIST SUCCESSFUL RESULT

     Failed calculations do not replace the previous
     successful result.
  ----------------------------------------------------- */

  React.useEffect(() => {
    if (!result) return;

    try {
      sessionStorage.setItem(
        "estimator_result",
        JSON.stringify(result)
      );
    } catch (error) {
      console.warn("Could not save estimator result:", error);
    }
  }, [result]);

  /* -----------------------------------------------------
     LOAD REFERENCE DATA AND EXCHANGE RATES
  ----------------------------------------------------- */

  React.useEffect(() => {
    let cancelled = false;

    async function loadReferenceData() {
      try {
        const [ref, fx] = await Promise.all([
          getReference(),
          getFxRates(),
        ]);

        if (cancelled) return;

        setReference(ref);
        setFxRates(fx?.rates || {});
      } catch (error) {
        if (!cancelled) {
          console.error("Reference data loading error:", error);

          toast.error(
            `Failed to load reference data: ${getReadableError(error)}`
          );
        }
      }
    }

    loadReferenceData();

    return () => {
      cancelled = true;
    };
  }, []);

  /* -----------------------------------------------------
     INITIAL CALCULATION AND DEBOUNCED INPUT UPDATES
  ----------------------------------------------------- */

  React.useEffect(() => {
    if (isFirstInputsChange.current) {
      isFirstInputsChange.current = false;

      let savedResult = null;

      try {
        savedResult = sessionStorage.getItem("estimator_result");
      } catch (error) {
        console.warn("Could not read saved estimate:", error);
      }

      if (!savedResult) {
        recalc(inputs);
      }

      return;
    }

    if (recalcTimer.current) {
      clearTimeout(recalcTimer.current);
    }

    recalcTimer.current = setTimeout(() => {
      recalc(inputs);
    }, 400);

    return () => {
      if (recalcTimer.current) {
        clearTimeout(recalcTimer.current);
      }
    };
  }, [inputs, recalc]);

  React.useEffect(() => {
    return () => {
      if (recalcTimer.current) {
        clearTimeout(recalcTimer.current);
      }

      // Invalidate any in-flight request when unmounting.
      calculationRequestId.current += 1;
    };
  }, []);

  /* -----------------------------------------------------
     SAVE PROJECT
  ----------------------------------------------------- */

  function onSave() {
    if (!result) {
      toast.error("Calculate a successful estimate before saving.");
      return;
    }

    navigate("/reports", {
      state: {
        result,
        inputs,
        currency: inputs.currency,
        fxRates,
        autoPrint: true,
      },
    });
  }

  /* -----------------------------------------------------
     FINISH WIZARD
  ----------------------------------------------------- */

  function onFinish() {
    const validationError = validateInputs(inputs);

    if (validationError) {
      toast.error(validationError);
      return;
    }

    setStep(5);
    recalc(inputs);
  }

  const currency = inputs.currency || "USD";

  const builtUpArea =
    (Number(inputs.length_m) || 0) *
    (Number(inputs.width_m) || 0) *
    (Number(inputs.num_floors) || 0);

  /* -----------------------------------------------------
     DASHBOARD UI
  ----------------------------------------------------- */

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-50">
      <Sidebar
        currency={currency}
        fxRates={fxRates}
        result={result}
        inputs={inputs}
        liveRateIndex={result?.live_rate_index}
        onDashboard={() => {
          setStep(5);
          setActiveTab("summary");
        }}
        onNewEstimate={() => {
          setStep(0);
        }}

        activeProject={{
          name: inputs.project_name,
          location: `${inputs.location_city}, ${inputs.location_country}`,
          builtUp: `${fmtNumber(inputs.length_m * inputs.width_m * inputs.num_floors)} m²`,
          plot: `${fmtNumber(inputs.plot_area_sqm)} m²`,
          lastSaved: new Date().toLocaleString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          }),
        }}

      />

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* HEADER */}

        <header
          data-testid={TID.header}
          className="h-16 flex-shrink-0 flex items-center justify-between px-5 bg-white border-b border-slate-200 gap-4"
        >
          <div className="flex items-center gap-6 min-w-0 flex-1">
            <div className="min-w-0">
              <div className="text-[15px] font-bold text-slate-900 truncate font-['Manrope']">
                {inputs.project_name}
              </div>

              <div className="text-[11px] text-slate-500 flex flex-wrap gap-x-4 mt-0.5">
                <span>
                  Location:{" "}
                  <b className="text-slate-700">
                    {inputs.location_city}, {inputs.location_country}
                  </b>
                </span>

                <span>
                  Project Type:{" "}
                  <b className="text-slate-700">
                    {inputs.project_type}
                  </b>
                </span>

                <span>
                  Industry:{" "}
                  <b className="text-slate-700">
                    {inputs.industry_type}
                  </b>
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <Select
              value={inputs.base_unit || "mm"}
              onValueChange={(value) =>
                setInputs((current) => ({
                  ...current,
                  base_unit: value,
                }))
              }
            >
              <SelectTrigger
                data-testid={TID.unitSelect}
                className="h-9 w-[130px] bg-white text-xs"
              >
                <SelectValue placeholder="Base Unit" />
              </SelectTrigger>

              <SelectContent className="bg-white z-50">
                {["mm", "cm", "m", "ft", "in"].map((unit) => (
                  <SelectItem key={unit} value={unit}>
                    Base Unit: {unit}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={currency}
              onValueChange={(value) =>
                setInputs((current) => ({
                  ...current,
                  currency: value,
                }))
              }
            >
              <SelectTrigger
                data-testid={TID.currencySelect}
                className="h-9 w-[130px] bg-white text-xs"
              >
                <SelectValue placeholder="Currency" />
              </SelectTrigger>

              <SelectContent className="bg-white z-50">
                {(reference?.currencies || ["USD"]).map((item) => (
                  <SelectItem key={item} value={item}>
                    Currency: {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>


            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
              <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-bold">
                {(inputs.user_name || "User")
                  .trim()
                  .split(/\s+/)
                  .map((name) => name[0])
                  .join("")
                  .slice(0, 2)
                  .toUpperCase()}
              </div>

              <div className="hidden md:block leading-tight">
                <div className="text-xs font-semibold text-slate-800">
                  {inputs.user_name || "User"}
                </div>
                <div className="text-[10px] text-slate-500">
                  Estimator
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* ACTION BAR */}

        <div className="flex items-center justify-end gap-2 px-5 py-2 border-b border-slate-200 bg-white">

          <Button
            data-testid={TID.recalcBtn}
            size="sm"
            onClick={() => recalc(inputs)}
            disabled={loading}
          >
            <RefreshCw
              className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""
                }`}
            />
            {loading ? "Calculating..." : "Recalculate"}
          </Button>

          <Button
            data-testid={TID.compareBtn}
            variant="outline"
            size="sm"
            onClick={() => toast.info("Compare is not implemented yet.")}
          >
            <GitCompareArrows className="w-3.5 h-3.5 mr-1.5" />
            Compare
          </Button>

          <Button
            data-testid={TID.exportBtn}
            variant="outline"
            size="sm"
            onClick={() => {
              if (!result) {
                toast.error("Calculate an estimate before exporting.");
                return;
              }

              navigate("/reports", {
                state: {
                  result,
                  inputs,
                  currency,
                  fxRates,
                },
              });
            }}
          >
            <Download className="w-3.5 h-3.5 mr-1.5" />
            Export
          </Button>

        </div>

        {/* MAIN CONTENT */}

        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          <Stepper current={step} onJump={setStep} />

          {step < 5 ? (
            <Wizard
              step={step}
              setStep={setStep}
              inputs={inputs}
              setInputs={setInputs}
              reference={reference}
              onFinish={onFinish}
            />
          ) : (
            <>
              {loading && !result && (
                <div
                  className="bg-white border border-slate-200 rounded-lg p-6 text-sm text-slate-600"
                  role="status"
                >
                  Calculating your estimate...
                </div>
              )}

              {!loading && !result && (
                <div className="bg-white border border-slate-200 rounded-lg p-6">
                  <h2 className="text-base font-semibold text-slate-800">
                    No estimate available
                  </h2>

                  <p className="text-sm text-slate-600 mt-2">
                    Check your project inputs and click Recalculate to
                    generate an estimate.
                  </p>

                  <Button
                    className="mt-4"
                    onClick={() => recalc(inputs)}
                    disabled={loading}
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Calculate Estimate
                  </Button>
                </div>
              )}

              {result && (
                <>
                  <KpiCards
                    totals={result.totals}
                    currency={currency}
                    fxRates={fxRates}
                  />

                  <TabsBar
                    tabs={TABS}
                    active={activeTab}
                    onChange={setActiveTab}
                  />

                  {/* SUMMARY */}



                  {activeTab === "summary" && (
                    <div className="space-y-5">

                      {/* ROW 1: Three dashboard cards */}
                      <div className="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-5 items-start">

                        <div className="min-w-0 w-full">
                          <DonutChart
                            data={result.breakdown || []}
                            currency={currency}
                            fxRates={fxRates}
                            total={result.totals.total_project_cost}
                          />
                        </div>

                        <div className="min-w-0 w-full">
                          <TrendChart
                            data={result.cost_trend || []}
                            currency={currency}
                            fxRates={fxRates}
                          />
                        </div>

                        <div className="min-w-0 w-full">
                          <UtilitiesSummary
                            utilities={result.utilities || []}
                            total={result.utilities_total}
                            currency={currency}
                            fxRates={fxRates}
                          />
                        </div>

                      </div>

                      {/* ROW 2: BOQ and project information */}
                      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">

                        <div className="min-w-0 xl:col-span-8">
                          <BoqTable
                            rows={result.top_cost_items || []}
                            currency={currency}
                            fxRates={fxRates}
                            testid={TID.boqTable}
                          />
                        </div>

                        <div className="min-w-0 xl:col-span-4 space-y-4">

                          <ProjectOverview
                            inputs={inputs}
                            totals={result.totals}
                            onEdit={() => setEditOpen(true)}
                          />

                          <CityFactorsCard
                            cityFactors={result.city_factors}
                            requestedCity={inputs.location_city}
                          />

                          <AssumptionsBox
                            items={result.insights?.assumptions || []}
                          />

                          <RisksBox
                            items={result.insights?.risks || []}
                          />

                          <OptimizationsBox
                            items={result.insights?.optimizations || []}
                          />

                        </div>

                        {/* ROW 3: Utility demand cards */}
                        <div className="min-w-0 xl:col-span-12">
                          <UtilityCards
                            demand={result.utility_demand || []}
                          />
                        </div>

                      </div>

                    </div>
                  )}


                  {/* COST BREAKDOWN */}

                  {activeTab === "breakdown" && (
                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
                      <div className="xl:col-span-5">
                        <DonutChart
                          data={result.breakdown || []}
                          currency={currency}
                          fxRates={fxRates}
                          total={result.totals.total_project_cost}
                        />
                      </div>

                      <div className="xl:col-span-7">
                        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
                          <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
                            Category-wise Breakdown
                          </h3>

                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead className="text-xs text-slate-500 uppercase font-semibold">
                                <tr>
                                  <th className="text-left py-2">Category</th>
                                  <th className="text-right">Amount</th>
                                  <th className="text-right">Cost / m²</th>
                                  <th className="text-right">%</th>
                                </tr>
                              </thead>

                              <tbody>
                                {(result.breakdown || []).map((item, index) => (
                                  <tr
                                    key={item.name || index}
                                    className="border-t border-slate-100"
                                  >
                                    <td className="py-2 text-slate-800">
                                      {item.name}
                                    </td>

                                    <td className="py-2 text-right font-semibold">
                                      {fmtMoney(
                                        item.value,
                                        currency,
                                        fxRates
                                      )}
                                    </td>

                                    <td className="py-2 text-right text-slate-600">
                                      {fmtMoney(
                                        item.cost_per_sqm,
                                        "USD",
                                        fxRates
                                      )}{" "}
                                      / m²
                                      <br />
                                      {fmtMoney(
                                        item.cost_per_sqm,
                                        currency,
                                        fxRates
                                      )}{" "}
                                      / m²
                                    </td>

                                    <td className="py-2 text-right text-slate-600">
                                      {item.pct}%
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* BOQ */}

                  {activeTab === "boq" && (
                    <BoqTable
                      rows={(result.boq || []).map((item, index) => ({
                        ...item,
                        rank: index + 1,
                        pct_of_total:
                          Number(result.totals.total_project_cost) > 0
                            ? +(
                              (item.amount /
                                result.totals.total_project_cost) *
                              100
                            ).toFixed(2)
                            : 0,
                      }))}
                      currency={currency}
                      fxRates={fxRates}
                      testid={TID.boqTable}
                    />
                  )}

                  {/* UTILITIES */}

                  {activeTab === "utilities" && (
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
                      <UtilitiesSummary
                        utilities={result.utilities || []}
                        total={result.utilities_total}
                        currency={currency}
                        fxRates={fxRates}
                      />

                      <UtilityCards
                        demand={result.utility_demand || []}
                      />
                    </div>
                  )}

                  {/* PROCESS DATA */}

                  {activeTab === "process" && (
                    <ProjectOverview
                      inputs={inputs}
                      totals={result.totals}
                      onEdit={() => setEditOpen(true)}
                    />
                  )}


                  {/* INFRA SUMMARY */}
                  {activeTab === "infra" && (() => {
                    const infraRows = (result.boq || []).filter((item) => {
                      const activity = String(item.activity || "").toLowerCase();
                      const category = String(item.category || "").toLowerCase();

                      return (
                        category.includes("infra") ||
                        category.includes("external") ||
                        category.includes("site development") ||
                        activity.includes("roads") ||
                        activity.includes("pathways") ||
                        activity.includes("parking") ||
                        activity.includes("landscaping") ||
                        activity.includes("compound wall") ||
                        activity.includes("fence")
                      );
                    });

                    const breakdownInfraTotal = Number(
                      (result.breakdown || []).find((item) => {
                        const name = String(item.name || "").toLowerCase();
                        return (
                          name.includes("infra") ||
                          name.includes("external") ||
                          name.includes("site development")
                        );
                      })?.value || 0
                    );

                    const boqInfraTotal = infraRows.reduce(
                      (sum, item) => sum + (Number(item.amount) || 0),
                      0
                    );

                    const infraTotal =
                      breakdownInfraTotal > 0 ? breakdownInfraTotal : boqInfraTotal;

                    return (
                      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
                        <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
                          Infra &amp; External
                        </h3>

                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead className="text-xs text-slate-500 uppercase font-semibold">
                              <tr>
                                <th className="text-left py-2">Item</th>
                                <th className="text-right">Amount</th>
                              </tr>
                            </thead>

                            <tbody>
                              {infraRows.map((item, index) => (
                                <tr
                                  key={`${item.activity || "infra"}-${index}`}
                                  className="border-t border-slate-100"
                                >
                                  <td className="py-2">{item.activity}</td>
                                  <td className="py-2 text-right font-semibold">
                                    {fmtMoney(item.amount, currency, fxRates)}
                                  </td>
                                </tr>
                              ))}

                              <tr className="border-t-2 border-slate-200">
                                <td className="py-3 font-semibold">
                                  Total Infra &amp; External
                                </td>
                                <td className="py-3 text-right font-bold">
                                  {fmtMoney(infraTotal, currency, fxRates)}
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    );
                  })()}


                  {/* CASH FLOW */}

                  {activeTab === "cashflow" && (
                    <TrendChart
                      data={result.cost_trend || []}
                      currency={currency}
                      fxRates={fxRates}
                    />
                  )}

                  {/* SENSITIVITY */}

                  {activeTab === "sensitivity" && (
                    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
                      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
                        Sensitivity Analysis
                      </h3>

                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="text-xs text-slate-500 uppercase font-semibold">
                            <tr>
                              <th className="text-left py-2">Scenario</th>
                              <th className="text-right">Δ</th>
                              <th className="text-right">Total</th>
                            </tr>
                          </thead>

                          <tbody>
                            {[
                              ["Steel +5%", 0.02],
                              ["Cement +10%", 0.015],
                              ["Utilities +8%", 0.025],
                              ["Labor +6%", 0.018],
                              ["FX +3%", 0.012],
                            ].map(([label, delta]) => (
                              <tr
                                key={label}
                                className="border-t border-slate-100"
                              >
                                <td className="py-2">{label}</td>

                                <td className="text-right text-amber-600">
                                  +{(delta * 100).toFixed(1)}%
                                </td>

                                <td className="text-right font-semibold">
                                  {fmtMoney(
                                    result.totals.total_project_cost *
                                    (1 + delta),
                                    currency,
                                    fxRates
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* ASSUMPTIONS AND INSIGHTS */}

                  {activeTab === "assumptions" && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                      <AssumptionsBox
                        items={result.insights?.assumptions || []}
                      />

                      <RisksBox
                        items={result.insights?.risks || []}
                      />

                      <OptimizationsBox
                        items={result.insights?.optimizations || []}
                      />

                      {result.insights?.executive_summary && (
                        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
                          <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
                            Executive Summary
                          </h3>

                          <p className="text-sm text-slate-700 leading-relaxed">
                            {result.insights.executive_summary}
                          </p>

                          {result.insights?.source && (
                            <div className="text-[10px] text-slate-400 mt-2 uppercase">
                              Source: {result.insights.source}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* RIGHT TOOLBAR */}

      <RightToolbar
        onAction={(key) => {
          if (key === "quick-inputs") {
            setEditOpen(true);
          } else {
            toast.info(`Opening ${key}...`);
          }
        }}
      />

      {/* EDIT PROJECT DIALOG */}

      <EditProjectDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        inputs={inputs}
        reference={reference}
        onSave={async (updated) => {
          setInputs((current) => ({
            ...current,
            ...updated,
            complexity: {
              ...current.complexity,
              ...(updated.complexity || {}),
            },
          }));

          setEditOpen(false);
        }}
      />
    </div>
  );
}