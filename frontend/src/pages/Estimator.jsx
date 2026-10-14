import React from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Bell, HelpCircle, Save, RefreshCw, GitCompareArrows, Download, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import Sidebar from "@/components/estimator/Sidebar";
import RightToolbar from "@/components/estimator/RightToolbar";
import Stepper from "@/components/estimator/Stepper";
import KpiCards from "@/components/estimator/KpiCards";
import { DonutChart, TrendChart } from "@/components/estimator/Charts";
import UtilityCards from "@/components/estimator/UtilityCards";
import Wizard from "@/components/estimator/Wizard";
import EditProjectDialog from "@/components/estimator/EditProjectDialog";
import CityFactorsCard from "@/components/estimator/CityFactorsCard";
import { TabsBar, BoqTable, UtilitiesSummary, ProjectOverview, AssumptionsBox, RisksBox, OptimizationsBox } from "@/components/estimator/OutputPanels";
import { getReference, getFxRates, calculateFast, getInsights, saveEstimate } from "@/lib/api";
import { fmtMoney, fmtNumber } from "@/lib/format";
import { TID } from "@/constants/testIds";



const DEFAULT_INPUTS = {

  project_name: "Chocolate & Bakery Manufacturing Plant", user_name: "", project_type: "Greenfield", industry_type: "Food", product_category: "Chocolate Plant",

  location_city: "Hamburg", location_country: "Germany", region: "MEU", continent: "Europe", location_tier: "Metro",

  building_type: "Industrial Building (RCC + PEB)", length_m: 185, width_m: 100, height_m: 10.5, num_floors: 1, bay_spacing_m: 8,

  plot_area_sqm: 32000, building_components: ["Production Block", "Warehouse", "Cold Store", "Utilities Block", "Admin Building"],

  soil_type: "Medium Dense Sand", sbc_soil_type: "Hard Stone", soil_hardness: "Medium", foundation_type: ["Raft Foundation"],

  column_type: "Steel", roof_type: "PEB + Insulated Panel", seismic_zone: "Zone 0 (Very Low)", wind_zone: "Zone 2", wind_speed_ms: 24,

  gwt_depth: "Medium (3-8 m)", utility_scope: ["Boiler House", "Chiller Plant", "HVAC System", "Air Compressors", "Water Treatment Plant", "Fire Fighting System", "Electrical Substation"],

  production_capacity_tpd: 120, annual_output_mt: 36000, cooling_tunnel_load_tr: 180, tempering_utility_demand: "Medium",

  humidity_controlled_pct: 40, chocolate_storage_temp_c: 16, process_hot_water_lph: 2500, oven_capacity_kg_hr: 1200, fuel_type: "PNG", baking_line_qty: 2,

  compressed_air_demand_cfm: 1500, dust_collection_required: true, cooling_conveyor_load: "Standard", include_roads: true, include_landscaping: true, include_fence: true,

  land_area_sqm: 32000, ground_coverage_pct: 58, far_fsi: 1.2, water_availability: "Municipal + Borewell", grid_reliability: "Good",

  ambient_temp_range: "Temperate (5°C - 30°C)", relative_humidity_pct: 70,

  complexity: { seismic_zone_high: false, high_humidity: false, cold_region: false, brownfield: false, gmp_hygienic: true, explosion_risk: false, utility_redundancy: true, high_floor_load: false, remote_site: false },

  currency: "USD", base_unit: "mm", contingency_pct: 8.0, num_employees: 0, male_employees: 0, female_employees: 0, special_work_clothing: "Yes", work_shoes_required: "Yes",

};



const TABS = [

  { key: "summary", label: "Summary" }, { key: "breakdown", label: "Cost Breakdown" }, { key: "boq", label: "BOQ" },

  { key: "utilities", label: "Utilities Summary" }, { key: "process", label: "Process Data" }, { key: "infra", label: "Infra Summary" },

  { key: "cashflow", label: "Cash Flow" }, { key: "sensitivity", label: "Sensitivity" }, { key: "assumptions", label: "Assumptions" },

];



export default function Estimator() {
  const navigate = useNavigate();

  const [reference, setReference] = React.useState(null);

  const [fxRates, setFxRates] = React.useState({});



  const [inputs, setInputs] = React.useState(() => {

    try {

      const saved = sessionStorage.getItem("estimator_inputs");

      return saved ? JSON.parse(saved) : DEFAULT_INPUTS;

    } catch (e) {

      console.warn("Could not restore estimator inputs:", e);

      return DEFAULT_INPUTS;

    }

  });



  const [result, setResult] = React.useState(() => {

    try {

      const saved = sessionStorage.getItem("estimator_result");

      return saved ? JSON.parse(saved) : null;

    } catch (e) {

      console.warn("Could not restore estimator result:", e);

      return null;

    }

  });



  const [loading, setLoading] = React.useState(false);

  const [step, setStep] = React.useState(5);

  const [activeTab, setActiveTab] = React.useState("summary");

  const [editOpen, setEditOpen] = React.useState(false);

  const isFirstInputsChange = React.useRef(true);

  const recalcTimer = React.useRef(null);



  React.useEffect(() => {

    try { sessionStorage.setItem("estimator_inputs", JSON.stringify(inputs)); }

    catch (e) { console.warn("Could not save estimator inputs:", e); }

  }, [inputs]);



  React.useEffect(() => {

    if (result) {

      try { sessionStorage.setItem("estimator_result", JSON.stringify(result)); }

      catch (e) { console.warn("Could not save estimator result:", e); }

    }

  }, [result]);



  React.useEffect(() => {
    (async () => {
      try {
        const [ref, fx] = await Promise.all([getReference(), getFxRates()]);
        setReference(ref);
        setFxRates(fx.rates || {});
      } catch (e) {
        toast.error("Failed to load reference data");
      }

    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);



  React.useEffect(() => {
    if (isFirstInputsChange.current) {
      isFirstInputsChange.current = false;

      const savedResult = sessionStorage.getItem("estimator_result");

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



  const recalc = React.useCallback(async (inp = inputs) => {

    setLoading(true);

    try {

      const fast = await calculateFast(inp);

      setResult((prev) => ({ ...fast, insights: prev?.insights, fx_rates: prev?.fx_rates }));

      setLoading(false);

      toast.success("Estimate recalculated");



      (async () => {

        try {

          const [fx, ins] = await Promise.all([getFxRates().catch(() => null), getInsights(inp, fast).catch(() => null)]);

          setResult((prev) => {

            if (!prev) return prev;

            return { ...prev, insights: ins ?? prev.insights, fx_rates: fx?.rates ?? prev.fx_rates };

          });

          if (fx?.rates) setFxRates(fx.rates);

        } catch (_) { }

      })();

    } catch (e) {

      setLoading(false);

      toast.error("Calculation failed: " + (e.response?.data?.detail || e.message));

    }

  }, [inputs]);



  function onSave() {

    if (!result) return;

    navigate("/reports", { state: { result, inputs, currency, fxRates, autoPrint: true } });

  }



  async function onFinish() { setStep(5); }



  const currency = inputs.currency;



  return (

    <div className="flex h-screen w-full overflow-hidden bg-slate-50">

      <Sidebar currency={currency} fxRates={fxRates} result={result} inputs={inputs} liveRateIndex={result?.live_rate_index}

        activeProject={{

          name: inputs.project_name, location: `${inputs.location_city}, ${inputs.location_country}`,

          builtUp: `${fmtNumber(inputs.length_m * inputs.width_m * inputs.num_floors)} m²`, plot: `${fmtNumber(inputs.plot_area_sqm)} m²`,

          lastSaved: new Date().toLocaleString("en-GB", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }),

        }}

      />



      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        <header data-testid={TID.header} className="h-16 flex-shrink-0 flex items-center justify-between px-5 bg-white border-b border-slate-200 gap-4">

          <div className="flex items-center gap-6 min-w-0 flex-1">

            <div className="min-w-0">

              <div className="text-[15px] font-bold text-slate-900 truncate font-['Manrope']">{inputs.project_name}</div>

              <div className="text-[11px] text-slate-500 flex flex-wrap gap-x-4 mt-0.5">

                <span>Location : <b className="text-slate-700">{inputs.location_city}, {inputs.location_country}</b></span>

                <span>Project Type : <b className="text-slate-700">{inputs.project_type}</b></span>

                <span>Industry : <b className="text-slate-700">{inputs.industry_type}</b></span>

              </div>

            </div>

          </div>



          <div className="flex items-center gap-2 flex-shrink-0">

            <Select value={inputs.base_unit} onValueChange={(v) => setInputs((s) => ({ ...s, base_unit: v }))}>

              <SelectTrigger data-testid={TID.unitSelect} className="h-9 w-[130px] bg-white text-xs"><SelectValue placeholder="Base Unit" /></SelectTrigger>

              <SelectContent className="bg-white z-50">{["mm", "cm", "m", "ft", "in"].map((u) => <SelectItem key={u} value={u}>Base Unit : {u}</SelectItem>)}</SelectContent>

            </Select>



            <Select value={inputs.currency} onValueChange={(v) => setInputs((s) => ({ ...s, currency: v }))}>

              <SelectTrigger data-testid={TID.currencySelect} className="h-9 w-[130px] bg-white text-xs"><SelectValue /></SelectTrigger>

              <SelectContent className="bg-white z-50">{(reference?.currencies || ["USD"]).map((c) => <SelectItem key={c} value={c}>Currency : {c}</SelectItem>)}</SelectContent>

            </Select>



            <Button variant="ghost" size="icon" className="relative">

              <Bell className="w-4 h-4 text-slate-600" />

              <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[9px] rounded-full w-4 h-4 flex items-center justify-center">6</span>

            </Button>



            <Button variant="ghost" size="icon"><HelpCircle className="w-4 h-4 text-slate-600" /></Button>



            <div className="flex items-center gap-2 pl-2 border-l border-slate-200">

              <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-xs font-bold">

                {(inputs.user_name || "User")

                  .trim()

                  .split(/\s+/)

                  .map((n) => n[0])

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



        <div className="flex items-center justify-end gap-2 px-5 py-2 border-b border-slate-200 bg-white">

          <Button data-testid={TID.saveBtn} variant="outline" size="sm" onClick={onSave}><Save className="w-3.5 h-3.5 mr-1.5" />Save</Button>

          <Button data-testid={TID.recalcBtn} size="sm" onClick={() => recalc(inputs)} disabled={loading}>

            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />{loading ? "Calculating..." : "Recalculate"}

          </Button>

          <Button data-testid={TID.compareBtn} variant="outline" size="sm"><GitCompareArrows className="w-3.5 h-3.5 mr-1.5" />Compare</Button>

          <Button data-testid={TID.exportBtn} variant="outline" size="sm"><Download className="w-3.5 h-3.5 mr-1.5" />Export</Button>

          <Button variant="ghost" size="icon" className="h-8 w-8"><MoreVertical className="w-4 h-4" /></Button>

        </div>



        <div className="flex-1 overflow-y-auto p-5 space-y-5">

          <Stepper current={step} onJump={setStep} />



          {step < 5 ? (

            <Wizard step={step} setStep={setStep} inputs={inputs} setInputs={setInputs} reference={reference} onFinish={onFinish} />

          ) : (

            <>

              <KpiCards totals={result?.totals} currency={currency} fxRates={fxRates} />

              <TabsBar tabs={TABS} active={activeTab} onChange={setActiveTab} />



              {result && activeTab === "summary" && (

                <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">

                  <div className="xl:col-span-4"><DonutChart data={result.breakdown} currency={currency} fxRates={fxRates} total={result.totals.total_project_cost} /></div>

                  <div className="xl:col-span-5"><TrendChart data={result.cost_trend} currency={currency} fxRates={fxRates} /></div>

                  <div className="xl:col-span-3"><UtilitiesSummary utilities={result.utilities} total={result.utilities_total} currency={currency} fxRates={fxRates} /></div>

                  <div className="xl:col-span-8"><BoqTable rows={result.top_cost_items} currency={currency} fxRates={fxRates} testid={TID.boqTable} /></div>



                  <div className="xl:col-span-4 space-y-4">

                    <ProjectOverview inputs={inputs} totals={result.totals} onEdit={() => setEditOpen(true)} />

                    <CityFactorsCard cityFactors={result.city_factors} requestedCity={inputs.location_city} />

                    <AssumptionsBox items={result.insights?.assumptions || []} />

                    <RisksBox items={result.insights?.risks || []} />

                    <OptimizationsBox items={result.insights?.optimizations || []} />

                  </div>



                  <div className="xl:col-span-12"><UtilityCards demand={result.utility_demand} /></div>

                </div>

              )}



              {result && activeTab === "breakdown" && (

                <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">

                  <div className="xl:col-span-5"><DonutChart data={result.breakdown} currency={currency} fxRates={fxRates} total={result.totals.total_project_cost} /></div>

                  <div className="xl:col-span-7">

                    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">

                      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">Category-wise Breakdown</h3>

                      <table className="w-full text-sm">

                        <thead className="text-xs text-slate-500 uppercase font-semibold">

                          <tr><th className="text-left py-2">Category</th><th className="text-right">Amount</th><th className="text-right">Cost / m²</th><th className="text-right">%</th></tr>

                        </thead>

                        <tbody>

                          {result.breakdown.map((b) => (

                            <tr key={b.name} className="border-t border-slate-100">

                              <td className="py-2 text-slate-800">{b.name}</td>

                              <td className="py-2 text-right font-semibold">{fmtMoney(b.value, currency, fxRates)}</td>

                              <td className="py-2 text-right text-slate-600">{fmtMoney(b.cost_per_sqm, "USD", fxRates)} / m²<br />{fmtMoney(b.cost_per_sqm, currency, fxRates)} / m²</td>

                              <td className="py-2 text-right text-slate-600">{b.pct}%</td>

                            </tr>

                          ))}

                        </tbody>

                      </table>

                    </div>

                  </div>

                </div>

              )}



              {result && activeTab === "boq" && (

                <BoqTable rows={result.boq.map((r, i) => ({ ...r, rank: i + 1, pct_of_total: +(r.amount / result.totals.total_project_cost * 100).toFixed(2) }))} currency={currency} fxRates={fxRates} testid={TID.boqTable} />

              )}



              {result && activeTab === "utilities" && (

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">

                  <UtilitiesSummary utilities={result.utilities} total={result.utilities_total} currency={currency} fxRates={fxRates} />

                  <UtilityCards demand={result.utility_demand} />

                </div>

              )}



              {result && activeTab === "process" && <ProjectOverview inputs={inputs} totals={result.totals} onEdit={() => setEditOpen(true)} />}



              {result && activeTab === "infra" && (

                <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">

                  <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">Infra & External</h3>

                  <table className="w-full text-sm">

                    <thead className="text-xs text-slate-500 uppercase font-semibold">

                      <tr><th className="text-left py-2">Item</th><th className="text-right">Amount</th></tr>

                    </thead>

                    <tbody>

                      {(result.boq || []).filter((r) => r.category === "Infra").map((r) => (

                        <tr key={r.activity} className="border-t border-slate-100">

                          <td className="py-2">{r.activity}</td>

                          <td className="py-2 text-right font-semibold">{fmtMoney(r.amount, currency, fxRates)}</td>

                        </tr>

                      ))}

                      <tr className="border-t-2 border-slate-200">

                        <td className="py-3 font-semibold">Total Infra & External</td>

                        <td className="py-3 text-right font-bold">{fmtMoney(result.breakdown.find((b) => b.name === "Infra & External")?.value || 0, currency, fxRates)}</td>

                      </tr>

                    </tbody>

                  </table>

                </div>

              )}



              {result && activeTab === "cashflow" && <TrendChart data={result.cost_trend} currency={currency} fxRates={fxRates} />}



              {result && activeTab === "sensitivity" && (

                <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">

                  <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">Sensitivity Analysis</h3>

                  <table className="w-full text-sm">

                    <thead className="text-xs text-slate-500 uppercase font-semibold">

                      <tr><th className="text-left py-2">Scenario</th><th className="text-right">Δ</th><th className="text-right">Total</th></tr>

                    </thead>

                    <tbody>

                      {[["Steel +5%", 0.02], ["Cement +10%", 0.015], ["Utilities +8%", 0.025], ["Labor +6%", 0.018], ["FX +3%", 0.012]].map(([k, d]) => (

                        <tr key={k} className="border-t border-slate-100">

                          <td className="py-2">{k}</td>

                          <td className="text-right text-amber-600">+{(d * 100).toFixed(1)}%</td>

                          <td className="text-right font-semibold">{fmtMoney(result.totals.total_project_cost * (1 + d), currency, fxRates)}</td>

                        </tr>

                      ))}

                    </tbody>

                  </table>

                </div>

              )}



              {result && activeTab === "assumptions" && (

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

                  <AssumptionsBox items={result.insights?.assumptions || []} />

                  <RisksBox items={result.insights?.risks || []} />

                  <OptimizationsBox items={result.insights?.optimizations || []} />



                  {result.insights?.executive_summary && (

                    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">

                      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">Executive Summary</h3>

                      <p className="text-sm text-slate-700 leading-relaxed">{result.insights.executive_summary}</p>

                      <div className="text-[10px] text-slate-400 mt-2 uppercase">Source: {result.insights?.source}</div>

                    </div>

                  )}

                </div>

              )}

            </>

          )}

        </div>

      </div>



      <RightToolbar onAction={(k) => {

        if (k === "quick-inputs") setEditOpen(true);

        else toast.info(`Opening ${k}...`);

      }} />



      <EditProjectDialog

        open={editOpen}

        onOpenChange={setEditOpen}

        inputs={inputs}

        reference={reference}

        onSave={async (updated) => { setInputs(updated); }}

      />

    </div>

  );

}