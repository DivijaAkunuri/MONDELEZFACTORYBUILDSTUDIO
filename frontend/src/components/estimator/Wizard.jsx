import React, { useState } from "react";
import { lookupLocation } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { TID } from "@/constants/testIds";
import { ChevronLeft, ChevronRight } from "lucide-react";

const STEP_TITLES = [
  "Project Details", "Building Geometry", "Structural & Site",
  "Utilities & Process", "Infra & External",
];

export default function Wizard({ step, setStep, inputs, setInputs, reference, onFinish }) {
  const patch = (k, v) => setInputs((s) => ({ ...s, [k]: v }));
  const validateAreas = () => {
    const length = Number(inputs.length_m);
    const width = Number(inputs.width_m);
    const plotArea = Number(inputs.plot_area_sqm);
    const landArea = Number(inputs.land_area_sqm);

    if (!Number.isFinite(length) || length <= 0) {
      return "Length must be greater than 0.";
    }

    if (!Number.isFinite(width) || width <= 0) {
      return "Width must be greater than 0.";
    }

    const minimumArea = length * width;

    if (!Number.isFinite(minimumArea) || minimumArea <= 0) {
      return "Length × Width must be greater than 0.";
    }

    if (!Number.isFinite(plotArea) || plotArea <= 0) {
      return "Plot Area must be greater than 0.";
    }

    if (plotArea < minimumArea) {
      return `Plot Area must be at least ${minimumArea} m² (Length × Width).`;
    }

    if (!Number.isFinite(landArea) || landArea <= 0) {
      return "Land Area must be greater than 0.";
    }

    if (landArea < minimumArea) {
      return `Land Area must be at least ${minimumArea} m² (Length × Width).`;
    }

    return "";
  };
  const patchComplexity = (k, v) =>
    setInputs((s) => ({ ...s, complexity: { ...s.complexity, [k]: v } }));

  const stepUi = () => {
    switch (step) {
      case 0: return <Step1 inputs={inputs} patch={patch} reference={reference} />;
      case 1: return <Step2 inputs={inputs} patch={patch} setInputs={setInputs} reference={reference} />;
      case 2: return <Step3 inputs={inputs} patch={patch} reference={reference} />;
      case 3: return <Step4 inputs={inputs} patch={patch} patchComplexity={patchComplexity} reference={reference} />;
      case 4: return <Step5 inputs={inputs} patch={patch} patchComplexity={patchComplexity} reference={reference} />;
      default: return null;
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900 font-['Manrope']">
          Step {step + 1} — {STEP_TITLES[step]}
        </h2>
        <p className="text-xs text-slate-500 mt-1">Fill in the details, then continue.</p>
      </div>
      {stepUi()}
      <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
        <Button data-testid={TID.wizardBack} variant="outline" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}>
          <ChevronLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        {step < 4 ? (
          <Button
            data-testid={TID.wizardNext}
            onClick={() => {
              if (step === 1) {
                const error = validateAreas();

                if (error) {
                  window.alert(error);
                  return;
                }
              }

              setStep(step + 1);
            }}
          >
            Next <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        ) : (
          <Button data-testid={TID.wizardNext} onClick={() => {
            const error = validateAreas();

            if (error) {
              window.alert(error);
              return;
            }

            onFinish();
          }} className="bg-blue-600 hover:bg-blue-700">
            Calculate Estimate <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        )}
      </div>
    </div>
  );
}

/* ---------- Reusable form primitives ---------- */
function Section({ title, children }) {
  return (
    <div className="mb-5">
      <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-3 border-l-2 border-blue-500 pl-2">{title}</div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{children}</div>
    </div>
  );
}
function Field({ label, children, span = 1 }) {
  const spanCls = span === 3 ? "md:col-span-3" : span === 2 ? "md:col-span-2" : "";
  return (
    <div className={`space-y-1 ${spanCls}`}>
      <Label className="text-xs font-semibold text-slate-600">{label}</Label>
      {children}
    </div>
  );
}
function SelectF({ id, value, onChange, options }) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger data-testid={TID.wizardField(id)} className="h-9 bg-white">
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="bg-white z-50 max-h-[280px]">
        {(options || []).map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}
      </SelectContent>
    </Select>
  );
}
function InputF({ id, value, onChange, type = "text", ...p }) {
  return (
    <Input
      data-testid={TID.wizardField(id)}
      value={value ?? ""}
      onChange={(e) => onChange(type === "number" ? +e.target.value : e.target.value)}
      type={type}
      className="h-9"
      {...p}
    />
  );
}
function CheckboxGrid({ list, selected, onToggle, idPrefix }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-1">
      {(list || []).map((s) => {
        const key = typeof s === "string" ? s : s.key;
        const label = typeof s === "string" ? s : s.label;
        const checked = selected.includes(key);
        return (
          <label
            key={key}
            className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded px-3 py-1.5 bg-white cursor-pointer hover:bg-slate-50"
          >
            <Checkbox
              data-testid={TID.wizardField(`${idPrefix}_${key}`)}
              checked={checked}
              onCheckedChange={() => onToggle(key)}
            />
            <span>{label}</span>
          </label>
        );
      })}
    </div>
  );
}

/* ---------- Step 1 : Project Identification ---------- */

function Step1({ inputs, patch, reference }) {
  const [locations, setLocations] = useState([]);
  const [loadingLocation, setLoadingLocation] = useState(false);
  const [locationError, setLocationError] = useState("");

  const findLocation = async () => {
    if (!inputs.location_city?.trim()) {
      setLocationError("Please enter a city name.");
      return;
    }

    setLoadingLocation(true);
    setLocationError("");
    setLocations([]);

    try {
      const data = await lookupLocation(inputs.location_city.trim());
      setLocations(data.locations || []);

      if (!data.locations?.length) {
        setLocationError("No matching locations found.");
      }
    } catch (error) {
      setLocationError(
        error.response?.data?.detail ||
        "Could not find the location. Please try again."
      );
    } finally {
      setLoadingLocation(false);
    }
  };

  const selectLocation = (location) => {
    const availableRegions = Object.keys(reference?.regions || {});

    const matchedRegion = availableRegions.includes(location.region)
      ? location.region
      : availableRegions.find((region) =>
        (reference?.regions?.[region] || []).includes(location.country)
      );

    patch("location_city", location.city);

    if (matchedRegion) {
      patch("region", matchedRegion);
      patch("location_country", location.country);
    } else {
      setLocationError(
        `Found ${location.country}, but it is not in your estimator's region mapping.`
      );
      return;
    }

    setLocations([]);
    setLocationError("");
  };

  return (
    <>
      <Section title="Project Identification">
        <Field label="Project Name" span={3}>
          <InputF
            id="project_name"
            value={inputs.project_name}
            onChange={(v) => patch("project_name", v)}
          />
        </Field>

        <Field label="Project Type">
          <InputF
            id="project_type"
            value={inputs.project_type}
            onChange={(v) => patch("project_type", v)}
          />
        </Field>

        <Field label="Industry Type">
          <InputF id="industry_type" value="FMCG" readOnly />
        </Field>

        <Field label="Product Category">
          <SelectF
            id="product_category"
            value={inputs.product_category}
            onChange={(v) => patch("product_category", v)}
            options={reference?.product_categories}
          />
        </Field>
      </Section>

      <Section title="Location">
        <Field label="City">
          <InputF
            id="location_city"
            value={inputs.location_city}
            onChange={(v) => {
              patch("location_city", v);
              setLocations([]);
              setLocationError("");
            }}
            placeholder="Enter a city"
          />

          <Button
            type="button"
            className="mt-2 w-full"
            onClick={findLocation}
            disabled={loadingLocation}
          >
            {loadingLocation ? "Searching..." : "Find Location"}
          </Button>
        </Field>

        <Field label="Country">
          <SelectF
            id="location_country"
            value={inputs.location_country}
            onChange={(v) => patch("location_country", v)}
            options={reference?.regions?.[inputs.region] || []}
          />
        </Field>

        <Field label="Currency">
          <SelectF
            id="currency"
            value={inputs.currency}
            onChange={(v) => patch("currency", v)}
            options={reference?.currencies}
          />
        </Field>

        <Field label="Region">
          <SelectF
            id="region"
            value={inputs.region}
            onChange={(v) => {
              patch("region", v);
              patch("location_country", "");
            }}
            options={Object.keys(reference?.regions || {})}
          />
        </Field>

        <Field label="Location Tier (Stage 1)">
          <SelectF
            id="location_tier"
            value={inputs.location_tier}
            onChange={(v) => patch("location_tier", v)}
            options={reference?.tiers}
          />
        </Field>
      </Section>

      {locationError && (
        <p className="mb-3 text-sm text-red-600" role="alert">
          {locationError}
        </p>
      )}

      {locations.length > 0 && (
        <div className="mb-5 rounded-lg border border-slate-200 p-3">
          <p className="mb-2 text-sm font-semibold text-slate-700">
            Select the correct location:
          </p>

          <div className="space-y-2">
            {locations.map((location, index) => (
              <button
                key={`${location.country_code}-${location.city}-${index}`}
                type="button"
                onClick={() => selectLocation(location)}
                className="block w-full rounded-md border border-slate-200 p-3 text-left text-sm hover:bg-slate-50"
              >
                <span className="font-medium">
                  {location.city}, {location.country}
                </span>

                {location.state && (
                  <span className="block text-xs text-slate-500">
                    {location.state}
                  </span>
                )}

                <span className="block text-xs text-slate-500">
                  {location.formatted}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
}


/* ---------- Step 2 : Building Geometry ---------- */

function Step2({ inputs, patch, setInputs, reference }) {
  const toggle = (item) => {
    const has = inputs.building_components?.includes(item);

    patch(
      "building_components",
      has
        ? inputs.building_components.filter((s) => s !== item)
        : [...(inputs.building_components || []), item]
    );
  };

  const length = Number(inputs.length_m);
  const width = Number(inputs.width_m);
  const plotArea = Number(inputs.plot_area_sqm);
  const minimumArea = length * width;

  const areaError =
    !Number.isFinite(length) || length <= 0
      ? "Length must be greater than 0."
      : !Number.isFinite(width) || width <= 0
        ? "Width must be greater than 0."
        : !Number.isFinite(plotArea) || plotArea <= 0
          ? "Plot Area must be greater than 0."
          : plotArea < minimumArea
            ? `Plot Area must be at least ${minimumArea} m² (Length × Width).`
            : "";

  const updateDimension = (field, value) => {
    const nextValue = Number(value) || 0;

    setInputs((current) => {
      const nextLength =
        field === "length_m"
          ? nextValue
          : Number(current.length_m) || 0;

      const nextWidth =
        field === "width_m"
          ? nextValue
          : Number(current.width_m) || 0;

      const nextArea =
        nextLength > 0 && nextWidth > 0
          ? nextLength * nextWidth
          : 0;

      return {
        ...current,
        [field]: nextValue,
        plot_area_sqm: nextArea,
        land_area_sqm: nextArea,
      };
    });
  };
  return (
    <>
      <Section title="Building Envelope">
        <Field label="Building Type" span={3}>
          <SelectF
            id="building_type"
            value={inputs.building_type}
            onChange={(v) => patch("building_type", v)}
            options={reference?.building_types}
          />
        </Field>

        <Field label="Length (m)">
          <InputF
            id="length_m"
            type="number"
            min="0"
            value={inputs.length_m}
            onChange={(v) => patch("length_m", v)}
          />
        </Field>

        <Field label="Width (m)">
          <InputF
            id="width_m"
            type="number"
            min="0"
            value={inputs.width_m}
            onChange={(v) => patch("width_m", v)}
          />
        </Field>

        <Field label="Clear Height (m)">
          <InputF
            id="height_m"
            type="number"
            value={inputs.height_m}
            onChange={(v) => patch("height_m", v)}
          />
        </Field>

        <Field label="Number of Floors">
          <InputF
            id="num_floors"
            type="number"
            value={inputs.num_floors}
            onChange={(v) => patch("num_floors", v)}
          />
        </Field>

        <Field label="Bay Spacing (m)">
          <InputF
            id="bay_spacing_m"
            type="number"
            value={inputs.bay_spacing_m}
            onChange={(v) => patch("bay_spacing_m", v)}
          />
        </Field>

        <Field label="Plot Area (m²)">
          <InputF
            id="plot_area_sqm"
            type="number"
            min="0"
            value={inputs.plot_area_sqm ?? ""}
            onChange={(v) => patch("plot_area_sqm", v)}
          />
        </Field>
      </Section>

      {areaError && (
        <p className="mt-2 text-sm text-red-600" role="alert">
          {areaError}
        </p>
      )}

      <div>
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-l-2 border-blue-500 pl-2">
          Building Components
        </div>

        <CheckboxGrid
          list={reference?.building_components || []}
          selected={inputs.building_components || []}
          onToggle={toggle}
          idPrefix="comp"
        />
      </div>
    </>
  );
}


/* ---------- Step 3 : Structural & Site ---------- */
function Step3({ inputs, patch, reference }) {
  return (
    <>
      <Section title="Structural & Design">
        <div className="md:col-span-3"><div className="text-xs font-semibold text-slate-600 mb-1">Foundation Type</div><CheckboxGrid list={reference?.foundation_types || []} selected={inputs.foundation_type || []} onToggle={(item) => { const has = (inputs.foundation_type || []).includes(item); patch("foundation_type", has ? inputs.foundation_type.filter((s) => s !== item) : [...(inputs.foundation_type || []), item]); }} idPrefix="foundation" /></div>
        <Field label="SBC / Soil Type"><SelectF id="sbc_soil_type" value={inputs.sbc_soil_type} onChange={(v) => patch("sbc_soil_type", v)} options={reference?.sbc_soil_types} /></Field>
        <Field label="Column Type"><SelectF id="column_type" value={inputs.column_type} onChange={(v) => patch("column_type", v)} options={reference?.column_types} /></Field>
        <Field label="Roof Type"><SelectF id="roof_type" value={inputs.roof_type} onChange={(v) => patch("roof_type", v)} options={reference?.roof_types} /></Field>
        <Field label="Floor Load (kN/m²)"><InputF id="floor_load_kn" type="number" value={inputs.floor_load_kn} onChange={(v) => patch("floor_load_kn", v)} /></Field>
      </Section>
      <Section title="Site Conditions">
        <Field label="Seismic Zone"><SelectF id="seismic_zone" value={inputs.seismic_zone} onChange={(v) => patch("seismic_zone", v)} options={reference?.seismic_zones} /></Field>
        <Field label="Wind Zone"><SelectF id="wind_zone" value={inputs.wind_zone} onChange={(v) => patch("wind_zone", v)} options={reference?.wind_zones} /></Field>
        <Field label="Wind Speed (m/s)"><InputF id="wind_speed_ms" type="number" value={inputs.wind_speed_ms} onChange={(v) => patch("wind_speed_ms", v)} /></Field>
        <Field label="Ground Water Table Depth"><SelectF id="gwt_depth" value={inputs.gwt_depth} onChange={(v) => patch("gwt_depth", v)} options={reference?.gwt_depths} /></Field>
      </Section>
    </>
  );
}

/* ---------- Step 4 : Utilities & Process ---------- */
function Step4({ inputs, patch, patchComplexity, reference }) {
  const toggleScope = (scope) => {
    const has = inputs.utility_scope.includes(scope);
    patch("utility_scope", has
      ? inputs.utility_scope.filter((s) => s !== scope)
      : [...inputs.utility_scope, scope]);
  };
  const isChocolate = /chocolate|combo/i.test(inputs.product_category || "");
  const isBiscuit = /biscuit|wafer|cookie|combo/i.test(inputs.product_category || "");
  const processComplexity = (reference?.complexity || []).filter((c) =>
    ["gmp_hygienic", "high_humidity", "cold_region", "explosion_risk", "utility_redundancy"].includes(c.key));

  return (
    <>
      <Section title="Production Capacity">
        <Field label="Production Capacity (TPD)"><InputF id="production_capacity_tpd" type="number" value={inputs.production_capacity_tpd} onChange={(v) => patch("production_capacity_tpd", v)} /></Field>
        <Field label="Annual Output (MT)"><InputF id="annual_output_mt" type="number" value={inputs.annual_output_mt} onChange={(v) => patch("annual_output_mt", v)} /></Field>
      </Section>
      <div className="mb-5">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-l-2 border-blue-500 pl-2">Utility Scope</div>
        <CheckboxGrid list={reference?.utility_scope || []} selected={inputs.utility_scope} onToggle={toggleScope} idPrefix="scope" />
      </div>

      {isChocolate && (
        <Section title="Chocolate Process Utilities">
          <Field label="Cooling Tunnel Load (TR)"><InputF id="cooling_tunnel_load_tr" type="number" value={inputs.cooling_tunnel_load_tr} onChange={(v) => patch("cooling_tunnel_load_tr", v)} /></Field>
          <Field label="Tempering Utility Demand"><SelectF id="tempering_utility_demand" value={inputs.tempering_utility_demand} onChange={(v) => patch("tempering_utility_demand", v)} options={reference?.tempering_utility_demand} /></Field>
          <Field label="Humidity Controlled Areas (%)"><InputF id="humidity_controlled_pct" type="number" value={inputs.humidity_controlled_pct} onChange={(v) => patch("humidity_controlled_pct", v)} /></Field>
          <Field label="Chocolate Storage Temp (°C)"><InputF id="chocolate_storage_temp_c" type="number" value={inputs.chocolate_storage_temp_c} onChange={(v) => patch("chocolate_storage_temp_c", v)} /></Field>
          <Field label="Process Hot Water (L/hr)"><InputF id="process_hot_water_lph" type="number" value={inputs.process_hot_water_lph} onChange={(v) => patch("process_hot_water_lph", v)} /></Field>
        </Section>
      )}
      {isBiscuit && (
        <Section title="Biscuit Process Utilities">
          <Field label="Oven Capacity (kg/hr)"><InputF id="oven_capacity_kg_hr" type="number" value={inputs.oven_capacity_kg_hr} onChange={(v) => patch("oven_capacity_kg_hr", v)} /></Field>
          <Field label="Fuel Type"><SelectF id="fuel_type" value={inputs.fuel_type} onChange={(v) => patch("fuel_type", v)} options={reference?.fuel_types} /></Field>
          <Field label="Baking Line Quantity"><InputF id="baking_line_qty" type="number" value={inputs.baking_line_qty} onChange={(v) => patch("baking_line_qty", v)} /></Field>
          <Field label="Compressed Air Demand (CFM)"><InputF id="compressed_air_demand_cfm" type="number" value={inputs.compressed_air_demand_cfm} onChange={(v) => patch("compressed_air_demand_cfm", v)} /></Field>
          <Field label="Cooling Conveyor Load"><SelectF id="cooling_conveyor_load" value={inputs.cooling_conveyor_load} onChange={(v) => patch("cooling_conveyor_load", v)} options={reference?.cooling_conveyor_load} /></Field>
          <Field label="Dust Collection Required">
            <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded h-9 px-3 bg-white">
              <Checkbox
                data-testid={TID.wizardField("dust_collection_required")}
                checked={inputs.dust_collection_required}
                onCheckedChange={(v) => patch("dust_collection_required", !!v)}
              />
              <span>Yes</span>
            </label>
          </Field>
        </Section>
      )}

      <div className="mb-2">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-l-2 border-blue-500 pl-2">Process Complexity</div>
        <CheckboxGrid
          list={processComplexity}
          selected={Object.keys(inputs.complexity).filter((k) => inputs.complexity[k])}
          onToggle={(k) => patchComplexity(k, !inputs.complexity[k])}
          idPrefix="complexity"
        />
      </div>
    </>
  );
}

/* ---------- Step 5 : Infra & Site Inputs ---------- */
function Step5({ inputs, patch, patchComplexity, reference }) {
  const siteComplexity = (reference?.complexity || []).filter((c) =>
    ["remote_site", "brownfield", "high_floor_load", "seismic_zone_high"].includes(c.key));

  return (
    <>

      {(inputs.building_components ?? []).includes("Admin Building") && (
        <Section title="Employee & Staff Facilities">
          <Field label="Total Employees">
            <InputF id="num_employees" type="number" value={inputs.num_employees ?? 0} onChange={(v) => patch("num_employees", v)} />
          </Field>
          <Field label="Male Employees">
            <InputF id="male_employees" type="number" value={inputs.male_employees ?? 0} onChange={(v) => patch("male_employees", v)} />
          </Field>
          <Field label="Female Employees">
            <InputF id="female_employees" type="number" value={inputs.female_employees ?? 0} onChange={(v) => patch("female_employees", v)} />
          </Field>
          <Field label="Special / Work Clothing Required?">
            <SelectF id="special_work_clothing" value={inputs.special_work_clothing ?? "Yes"} onChange={(v) => patch("special_work_clothing", v)} options={["Yes", "No"]} />
          </Field>
          <Field label="Work Shoes / Boots Required?">
            <SelectF id="work_shoes_required" value={inputs.work_shoes_required ?? "Yes"} onChange={(v) => patch("work_shoes_required", v)} options={["Yes", "No"]} />
          </Field>
        </Section>
      )}

      <Section title="External Works Scope">
        <Field label="Roads & Pathways">
          <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded h-9 px-3 bg-white">
            <Checkbox data-testid={TID.wizardField("include_roads")} checked={inputs.include_roads} onCheckedChange={(v) => patch("include_roads", !!v)} />
            <span>Include</span>
          </label>
        </Field>
        <Field label="Landscaping">
          <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded h-9 px-3 bg-white">
            <Checkbox data-testid={TID.wizardField("include_landscaping")} checked={inputs.include_landscaping} onCheckedChange={(v) => patch("include_landscaping", !!v)} />
            <span>Include</span>
          </label>
        </Field>
        <Field label="Compound Wall / Fence">
          <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded h-9 px-3 bg-white">
            <Checkbox data-testid={TID.wizardField("include_fence")} checked={inputs.include_fence} onCheckedChange={(v) => patch("include_fence", !!v)} />
            <span>Include</span>
          </label>
        </Field>
      </Section>

      <Section title="Site Inputs">
        <Field label="Land Area (m²)">
          <InputF
            id="land_area_sqm"
            type="number"
            min="0"
            value={inputs.land_area_sqm ?? ""}
            onChange={(v) => patch("land_area_sqm", v)}
          />
        </Field>
        <Field label="Ground Coverage (%)"><InputF id="ground_coverage_pct" type="number" value={inputs.ground_coverage_pct} onChange={(v) => patch("ground_coverage_pct", v)} /></Field>
        <Field label="FAR / FSI"><InputF id="far_fsi" type="number" value={inputs.far_fsi} onChange={(v) => patch("far_fsi", v)} /></Field>
        <Field label="Water Availability"><SelectF id="water_availability" value={inputs.water_availability} onChange={(v) => patch("water_availability", v)} options={reference?.water_availability} /></Field>
        <Field label="Electrical Grid Reliability"><SelectF id="grid_reliability" value={inputs.grid_reliability} onChange={(v) => patch("grid_reliability", v)} options={reference?.grid_reliability} /></Field>
        <Field label="Ambient Temperature Range"><SelectF id="ambient_temp_range" value={inputs.ambient_temp_range} onChange={(v) => patch("ambient_temp_range", v)} options={reference?.ambient_temp_ranges} /></Field>
        <Field label="Relative Humidity (%)"><InputF id="relative_humidity_pct" type="number" value={inputs.relative_humidity_pct} onChange={(v) => patch("relative_humidity_pct", v)} /></Field>
      </Section>

      <div className="mb-5">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-l-2 border-blue-500 pl-2">Site Complexity</div>
        <CheckboxGrid
          list={siteComplexity}
          selected={Object.keys(inputs.complexity).filter((k) => inputs.complexity[k])}
          onToggle={(k) => patchComplexity(k, !inputs.complexity[k])}
          idPrefix="complexity"
        />
      </div>

      <Section title="Contingency">
        <Field label={`Contingency (%): ${inputs.contingency_pct}%`} span={3}>
          <input
            type="range" min="4" max="20" step="0.5"
            value={inputs.contingency_pct}
            onChange={(e) => patch("contingency_pct", +e.target.value)}
            data-testid={TID.wizardField("contingency_pct")}
            className="w-full accent-blue-600"
          />
        </Field>
      </Section>
    </>
  );
}
