import React from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { TID } from "@/constants/testIds";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function Wizard({ step, setStep, inputs, setInputs, reference, onFinish }) {
  const patch = (k, v) => setInputs((s) => ({ ...s, [k]: v }));
  const patchComplexity = (k, v) =>
    setInputs((s) => ({ ...s, complexity: { ...s.complexity, [k]: v } }));

  const stepUi = () => {
    switch (step) {
      case 0: return <Step1 inputs={inputs} patch={patch} reference={reference} />;
      case 1: return <Step2 inputs={inputs} patch={patch} reference={reference} />;
      case 2: return <Step3 inputs={inputs} patch={patch} reference={reference} />;
      case 3: return <Step4 inputs={inputs} patch={patch} patchComplexity={patchComplexity} reference={reference} />;
      case 4: return <Step5 inputs={inputs} patch={patch} patchComplexity={patchComplexity} />;
      default: return null;
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900 font-['Manrope']">
          Step {step + 1} — {["Project Details","Building Geometry","Structural & Site","Utilities & Process","Infra & External"][step]}
        </h2>
        <p className="text-xs text-slate-500 mt-1">Fill in the details, then continue.</p>
      </div>
      {stepUi()}
      <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
        <Button data-testid={TID.wizardBack} variant="outline" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}>
          <ChevronLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        {step < 4 ? (
          <Button data-testid={TID.wizardNext} onClick={() => setStep(step + 1)}>
            Next <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        ) : (
          <Button data-testid={TID.wizardNext} onClick={onFinish} className="bg-blue-600 hover:bg-blue-700">
            Calculate Estimate <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        )}
      </div>
    </div>
  );
}

function Field({ label, children, span = 1 }) {
  return (
    <div className={`space-y-1 col-span-${span}`}>
      <Label className="text-xs font-semibold text-slate-600">{label}</Label>
      {children}
    </div>
  );
}

function SelectF({ id, value, onChange, options }) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger data-testid={TID.wizardField(id)} className="h-9 bg-white"><SelectValue /></SelectTrigger>
      <SelectContent className="bg-white z-50">
        {options.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}
      </SelectContent>
    </Select>
  );
}
function InputF({ id, value, onChange, type = "text", ...p }) {
  return <Input data-testid={TID.wizardField(id)} value={value} onChange={(e) => onChange(type === "number" ? +e.target.value : e.target.value)} type={type} className="h-9" {...p} />;
}

function Step1({ inputs, patch, reference }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Field label="Project Name"><InputF id="project_name" value={inputs.project_name} onChange={(v) => patch("project_name", v)} /></Field>
      <Field label="Project Type"><SelectF id="project_type" value={inputs.project_type} onChange={(v) => patch("project_type", v)} options={reference?.project_types || ["Greenfield"]} /></Field>
      <Field label="Industry Type"><SelectF id="industry_type" value={inputs.industry_type} onChange={(v) => patch("industry_type", v)} options={reference?.industries || []} /></Field>
      <Field label="City"><InputF id="location_city" value={inputs.location_city} onChange={(v) => patch("location_city", v)} /></Field>
      <Field label="Country"><InputF id="location_country" value={inputs.location_country} onChange={(v) => patch("location_country", v)} /></Field>
      <Field label="Region"><SelectF id="region" value={inputs.region} onChange={(v) => patch("region", v)} options={reference?.regions || []} /></Field>
      <Field label="Location Tier"><SelectF id="location_tier" value={inputs.location_tier} onChange={(v) => patch("location_tier", v)} options={reference?.tiers || []} /></Field>
    </div>
  );
}
function Step2({ inputs, patch, reference }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Field label="Building Type" span={3}><SelectF id="building_type" value={inputs.building_type} onChange={(v) => patch("building_type", v)} options={reference?.building_types || []} /></Field>
      <Field label="Length (m)"><InputF id="length_m" type="number" value={inputs.length_m} onChange={(v) => patch("length_m", v)} /></Field>
      <Field label="Width (m)"><InputF id="width_m" type="number" value={inputs.width_m} onChange={(v) => patch("width_m", v)} /></Field>
      <Field label="Height (m)"><InputF id="height_m" type="number" value={inputs.height_m} onChange={(v) => patch("height_m", v)} /></Field>
      <Field label="Number of Floors"><InputF id="num_floors" type="number" value={inputs.num_floors} onChange={(v) => patch("num_floors", v)} /></Field>
      <Field label="Bay Spacing (m)"><InputF id="bay_spacing_m" type="number" value={inputs.bay_spacing_m} onChange={(v) => patch("bay_spacing_m", v)} /></Field>
      <Field label="Plot Area (m²)"><InputF id="plot_area_sqm" type="number" value={inputs.plot_area_sqm} onChange={(v) => patch("plot_area_sqm", v)} /></Field>
    </div>
  );
}
function Step3({ inputs, patch, reference }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Field label="Soil Type"><SelectF id="soil_type" value={inputs.soil_type} onChange={(v) => patch("soil_type", v)} options={reference?.soil_types || []} /></Field>
      <Field label="Foundation Type"><SelectF id="foundation_type" value={inputs.foundation_type} onChange={(v) => patch("foundation_type", v)} options={reference?.foundation_types || []} /></Field>
      <Field label="Floor Load (kN/m²)"><InputF id="floor_load_kn" type="number" value={inputs.floor_load_kn} onChange={(v) => patch("floor_load_kn", v)} /></Field>
      <Field label="Column Type"><SelectF id="column_type" value={inputs.column_type} onChange={(v) => patch("column_type", v)} options={reference?.column_types || []} /></Field>
      <Field label="Roof Type"><SelectF id="roof_type" value={inputs.roof_type} onChange={(v) => patch("roof_type", v)} options={reference?.roof_types || []} /></Field>
      <Field label="Wind Speed (m/s)"><InputF id="wind_speed_ms" type="number" value={inputs.wind_speed_ms} onChange={(v) => patch("wind_speed_ms", v)} /></Field>
      <Field label="Seismic Zone" span={3}><InputF id="seismic_zone" value={inputs.seismic_zone} onChange={(v) => patch("seismic_zone", v)} /></Field>
    </div>
  );
}
function Step4({ inputs, patch, patchComplexity, reference }) {
  const toggle = (scope) => {
    const has = inputs.utility_scope.includes(scope);
    patch("utility_scope", has ? inputs.utility_scope.filter((s) => s !== scope) : [...inputs.utility_scope, scope]);
  };
  const complexityList = (reference?.complexity || []).filter((c) => ["gmp_hygienic","high_humidity","cold_region","explosion_risk","utility_redundancy"].includes(c.key));
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Field label="Production Capacity (TPD)"><InputF id="production_capacity_tpd" type="number" value={inputs.production_capacity_tpd} onChange={(v) => patch("production_capacity_tpd", v)} /></Field>
        <Field label="Annual Output (MT)"><InputF id="annual_output_mt" type="number" value={inputs.annual_output_mt} onChange={(v) => patch("annual_output_mt", v)} /></Field>
      </div>
      <div>
        <Label className="text-xs font-semibold text-slate-600">Utility Scope</Label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
          {[...new Set(reference?.utility_scope || [])].map((s) => (
            <label key={s} className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded px-3 py-1.5 bg-white cursor-pointer hover:bg-slate-50">
              <Checkbox data-testid={TID.wizardField(`scope_${s}`)} checked={inputs.utility_scope.includes(s)} onCheckedChange={() => toggle(s)} />
              {s}
            </label>
          ))}
        </div>
      </div>
      <div>
        <Label className="text-xs font-semibold text-slate-600">Process Complexity</Label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
          {complexityList.map((c) => (
            <label key={c.key} className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded px-3 py-1.5 bg-white cursor-pointer hover:bg-slate-50">
              <Checkbox data-testid={TID.wizardField(`complexity_${c.key}`)} checked={!!inputs.complexity[c.key]} onCheckedChange={(v) => patchComplexity(c.key, !!v)} />
              {c.label}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
function Step5({ inputs, patch, patchComplexity }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <ToggleRow label="Include Roads & Pathways" val={inputs.include_roads} onChange={(v) => patch("include_roads", v)} id="include_roads" />
        <ToggleRow label="Include Landscaping" val={inputs.include_landscaping} onChange={(v) => patch("include_landscaping", v)} id="include_landscaping" />
        <ToggleRow label="Include Fencing" val={inputs.include_fence} onChange={(v) => patch("include_fence", v)} id="include_fence" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {["remote_site", "brownfield", "high_floor_load", "seismic_zone_high"].map((k) => (
          <ToggleRow key={k} label={k.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
            val={!!inputs.complexity[k]} onChange={(v) => patchComplexity(k, v)} id={`cx_${k}`} />
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        <Field label={`Contingency (%): ${inputs.contingency_pct}%`}>
          <input type="range" min="4" max="20" step="0.5" value={inputs.contingency_pct}
            onChange={(e) => patch("contingency_pct", +e.target.value)}
            data-testid={TID.wizardField("contingency_pct")}
            className="w-full accent-blue-600" />
        </Field>
      </div>
    </div>
  );
}
function ToggleRow({ label, val, onChange, id }) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded px-3 py-2 bg-white cursor-pointer hover:bg-slate-50">
      <Checkbox data-testid={TID.wizardField(id)} checked={val} onCheckedChange={(v) => onChange(!!v)} />
      {label}
    </label>
  );
}
