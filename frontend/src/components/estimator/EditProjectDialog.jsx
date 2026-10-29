import React from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { TID } from "@/constants/testIds";
import { Save, X } from "lucide-react";

export default function EditProjectDialog({ open, onOpenChange, inputs, reference, onSave }) {
  const [draft, setDraft] = React.useState(inputs);

  React.useEffect(() => {
    if (!open) return;

    const regions = reference?.regions || {};
    const validIndustries = reference?.industries || [];
    const validTiers = reference?.tiers || [];

    const country = inputs.location_country || "";
    const matchedRegion = Object.entries(regions).find(([, countries]) => countries.includes(country))?.[0] || "";

    setDraft({
      ...inputs,
      industry_type: validIndustries.includes(inputs.industry_type) ? inputs.industry_type : "FMCG",
      region: Object.keys(regions).includes(inputs.region) ? inputs.region : matchedRegion,
      location_country: country,
      location_tier: validTiers.includes(inputs.location_tier) ? inputs.location_tier : "Metro",
      sbc_soil_type: inputs.sbc_soil_type === "Hard Stone" ? "Hard" : (inputs.sbc_soil_type === "Soft" ? "Soft" : "Hard"),
      num_employees: inputs.num_employees ?? 0,
      male_employees: inputs.male_employees ?? 0,
      female_employees: inputs.female_employees ?? 0,
      special_work_clothing: inputs.special_work_clothing ?? "Yes",
      work_shoes_required: inputs.work_shoes_required ?? "Yes",
      canteen_dining_required: inputs.canteen_dining_required ?? "Yes",

    });
  }, [open, inputs, reference]);

  const patch = (k, v) => setDraft((s) => ({ ...s, [k]: v }));
  const patchCx = (k, v) => setDraft((s) => ({ ...s, complexity: { ...s.complexity, [k]: v } }));

  const toggleList = (field, item) => {
    const has = (draft[field] || []).includes(item);
    patch(field, has ? draft[field].filter((s) => s !== item) : [...(draft[field] || []), item]);
  };

  const isChocolate = /chocolate|combo/i.test(draft.product_category || "");
  const isBiscuit = /biscuit|wafer|cookie|combo/i.test(draft.product_category || "");

  const employeeTotal = Math.max(0, Number(draft.num_employees) || 0);
  const maleEmployees = Math.max(0, Number(draft.male_employees) || 0);
  const femaleEmployees = Math.max(0, Number(draft.female_employees) || 0);

  const employeeCountValid = maleEmployees + femaleEmployees === employeeTotal;

  const handleSave = () => {
    if (!employeeCountValid) {
      return;
    }

    onSave({
      ...draft,
      num_employees: employeeTotal,
      male_employees: maleEmployees,
      female_employees: femaleEmployees,
      special_work_clothing: draft.special_work_clothing || "Yes",
      work_shoes_required: draft.work_shoes_required || "Yes",
      canteen_dining_required: draft.canteen_dining_required || "Yes",
    });

    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-[720px] bg-white p-0 flex flex-col" data-testid="edit-project-sheet">
        <SheetHeader className="px-6 py-4 border-b border-slate-200 bg-white">
          <SheetTitle className="text-lg font-bold font-['Manrope']">Edit Project Overview</SheetTitle>
          <SheetDescription className="text-xs text-slate-500">
            Update any parameter. Save to recalculate the estimate.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">

          {/* ---- Project Identification ---- */}
          <Section title="Project Identification">
            <Field label="Project Name" span={2}>
              <InputF
                id="project_name"
                value={draft.project_name}
                onChange={(v) => patch("project_name", v)}
              />
            </Field>

            <Field label="User Name" span={2}>
              <InputF
                id="user_name"
                value={draft.user_name ?? ""}
                onChange={(v) => patch("user_name", v)}
                placeholder="Enter your name"
              />
            </Field>

            <Field label="Project Type">
              <SelectF
                id="project_type"
                value={draft.project_type}
                onChange={(v) => patch("project_type", v)}
                options={reference?.project_types}
              />
            </Field>


            <Field label="Industry Type">
              <input
                id="industry_type"
                type="text"
                value="FMCG"
                readOnly
                className="w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-gray-700"
              />
            </Field>


            <Field label="Product Category" span={2}>
              <SelectF
                id="product_category"
                value={draft.product_category}
                onChange={(v) => patch("product_category", v)}
                options={reference?.product_categories}
              />
            </Field>
          </Section>

          {/* ---- Location ---- */}
          <Section title="Location">
            <Field label="City">
              <InputF id="location_city" value={draft.location_city} onChange={(v) => patch("location_city", v)} />
            </Field>
            <Field label="Region">
              <SelectF
                id="region"
                value={draft.region}
                onChange={(v) => {
                  patch("region", v);
                  patch("location_country", "");
                }}
                options={Object.keys(reference?.regions || {})}
              />
            </Field>
            <Field label="Country">
              <SelectF
                id="location_country"
                value={draft.location_country}
                onChange={(v) => patch("location_country", v)}
                options={reference?.regions?.[draft.region] || []}
              />
            </Field>
            <Field label="Currency">
              <SelectF id="currency" value={draft.currency} onChange={(v) => patch("currency", v)} options={reference?.currencies} />
            </Field>
            <Field label="Location Tier">
              <SelectF id="location_tier" value={draft.location_tier} onChange={(v) => patch("location_tier", v)} options={reference?.tiers} />
            </Field>
          </Section>

          {/* ---- Building Geometry ---- */}
          <Section title="Building Geometry">
            <Field label="Building Type" span={2}>
              <SelectF id="building_type" value={draft.building_type} onChange={(v) => patch("building_type", v)} options={reference?.building_types} />
            </Field>
            <Field label="Length (m)">
              <InputF id="length_m" type="number" value={draft.length_m} onChange={(v) => patch("length_m", v)} />
            </Field>
            <Field label="Width (m)">
              <InputF id="width_m" type="number" value={draft.width_m} onChange={(v) => patch("width_m", v)} />
            </Field>
            <Field label="No. of Floors">
              <SelectF
                id="num_floors"
                value={String(draft.num_floors || 1)}
                onChange={(v) => patch("num_floors", Number(v))}
                options={["1", "2", "3", "4"]}
              />
            </Field>
            <Field label="Floor Height(m)">
              <InputF id="height_m" type="number" value={draft.height_m} onChange={(v) => patch("height_m", v)} />
            </Field>
            <Field label="Bay Spacing (Column) (m)">
              <InputF id="bay_spacing_m" type="number" value={draft.bay_spacing_m} onChange={(v) => patch("bay_spacing_m", v)} />
            </Field>


            <Field label="Built-up Area (Length × Width × No. of Floors) (m²)">
              <InputF
                id="built_up_area_display"
                type="text"
                value={
                  Number(draft.length_m) > 0 &&
                    Number(draft.width_m) > 0 &&
                    Number(draft.num_floors) > 0
                    ? (
                      Number(draft.length_m) *
                      Number(draft.width_m) *
                      Number(draft.num_floors)
                    ).toLocaleString()
                    : "Enter dimensions and floors"
                }
                disabled
              />
            </Field>


          </Section>

          <MultiField
            title="Building Components"
            list={reference?.building_components || []}
            selected={draft.building_components || []}
            onToggle={(x) => toggleList("building_components", x)}
            idPrefix="comp"
          />

          {/* ---- Structural & Site ---- */}
          <Section title="Structural & Design">
            <div className="sm:col-span-2">
              <MultiField
                title="Foundation Type"
                list={reference?.foundation_types || []}
                selected={draft.foundation_type || []}
                onToggle={(x) => toggleList("foundation_type", x)}
                idPrefix="foundation"
              />
            </div>

            <Field label="SBC / Soil Type">
              <SelectF id="sbc_soil_type" value={draft.sbc_soil_type} onChange={(v) => patch("sbc_soil_type", v)} options={reference?.sbc_soil_types} />
            </Field>

            <Field label="Column Type">
              <SelectF id="column_type" value={draft.column_type} onChange={(v) => patch("column_type", v)} options={reference?.column_types} />
            </Field>

            <div className="sm:col-span-2">
              <div className="text-xs font-semibold text-slate-600 mb-2">Roof Type by Floor</div>
              <div className="space-y-2">
                {Array.from({ length: Math.min(4, Math.max(1, Number(draft.num_floors) || 1)) }, (_, i) => {
                  const floor = i + 1;
                  const selected = draft.roof_types_by_floor?.[i] || [];

                  return (
                    <div key={floor} className="grid grid-cols-[80px_1fr] items-center gap-2">
                      <div className="h-9 flex items-center px-3 border border-slate-200 rounded bg-slate-50 text-xs font-semibold text-slate-700">
                        Floor {floor}
                      </div>

                      <div className="grid grid-cols-3 gap-2">
                        {(reference?.roof_types || []).slice(0, 3).map((roof) => (
                          <label
                            key={roof}
                            className="flex items-center gap-2 min-w-0 border border-slate-200 rounded px-2 py-2 bg-white cursor-pointer hover:bg-slate-50"
                          >
                            <Checkbox
                              checked={selected.includes(roof)}
                              onCheckedChange={(checked) => {
                                const floors = [...(draft.roof_types_by_floor || [])];
                                const current = floors[i] || [];
                                floors[i] = checked ? [...current, roof] : current.filter((x) => x !== roof);
                                patch("roof_types_by_floor", floors);
                              }}
                            />
                            <span className="text-xs truncate">{roof}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </Section>

          <Section title="Site Conditions">
            <Field label="Seismic Zone">
              <SelectF id="seismic_zone" value={draft.seismic_zone} onChange={(v) => patch("seismic_zone", v)} options={reference?.seismic_zones} />
            </Field>
            <Field label="Wind Zone">
              <SelectF id="wind_zone" value={draft.wind_zone} onChange={(v) => patch("wind_zone", v)} options={reference?.wind_zones} />
            </Field>

            <Field label="Wind Speed (m/s)">
              <InputF
                id="wind_speed_ms"
                type="number"
                value={Math.max(45, Number(draft.wind_speed_ms) || 45)}
                onChange={(v) =>
                  patch("wind_speed_ms", Math.max(45, Number(v) || 45))
                }
              />
            </Field>
            f
            <Field label="GWT Depth">
              <SelectF id="gwt_depth" value={draft.gwt_depth} onChange={(v) => patch("gwt_depth", v)} options={reference?.gwt_depths} />
            </Field>
          </Section>

          {/* ---- Utilities & Process ---- */}
          <Section title="Production Capacity">
            <Field label="Production Capacity (TPD)">
              <InputF id="production_capacity_tpd" type="number" value={draft.production_capacity_tpd} onChange={(v) => patch("production_capacity_tpd", v)} />
            </Field>
            <Field label="Annual Output (MT)">
              <InputF id="annual_output_mt" type="number" value={draft.annual_output_mt} onChange={(v) => patch("annual_output_mt", v)} />
            </Field>
          </Section>

          {/* ---- Employee & Staff Facilities ---- */}
          {(draft.building_components ?? []).includes("Admin Building") && (
            <Section title="Employee & Staff Facilities">
              <Field label="Total Employees">
                <InputF
                  id="num_employees"
                  type="number"
                  value={draft.num_employees ?? 0}
                  onChange={(v) => patch("num_employees", Math.max(0, v))}
                />
              </Field>

              <Field label="Male Employees">
                <InputF
                  id="male_employees"
                  type="number"
                  value={draft.male_employees ?? 0}
                  onChange={(v) => patch("male_employees", Math.max(0, v))}
                />
              </Field>

              <Field label="Female Employees">
                <InputF
                  id="female_employees"
                  type="number"
                  value={draft.female_employees ?? 0}
                  onChange={(v) => patch("female_employees", Math.max(0, v))}
                />
              </Field>

              <Field label="Special / Work Clothing Required?">
                <SelectF
                  id="special_work_clothing"
                  value={draft.special_work_clothing ?? "Yes"}
                  onChange={(v) => patch("special_work_clothing", v)}
                  options={["Yes", "No"]}
                />
              </Field>

              <Field label="Street & Safety Shoes Lockers Required?">
                <SelectF
                  id="work_shoes_required"
                  value={draft.work_shoes_required ?? "Yes"}
                  onChange={(v) => patch("work_shoes_required", v)}
                  options={["Yes", "No"]}
                />
              </Field>
              <Field label="Canteen/Dining Facilities Required?">
                <SelectF
                  id="canteen_dining_required"
                  value={draft.canteen_dining_required ?? "Yes"}
                  onChange={(v) => patch("canteen_dining_required", v)}
                  options={["Yes", "No"]}
                />
              </Field>

              <div className="sm:col-span-2">
                <div
                  className={`rounded border px-3 py-2 text-xs ${employeeCountValid
                    ? "border-slate-200 bg-slate-50 text-slate-600"
                    : "border-red-300 bg-red-50 text-red-600"
                    }`}
                >
                  {employeeCountValid
                    ? `Individual lockers: ${employeeTotal} — one locker per employee. Facilities are located in the Admin Building.`
                    : `Employee count mismatch: Male (${maleEmployees}) + Female (${femaleEmployees}) must equal Total Employees (${employeeTotal}).`}
                </div>
              </div>
            </Section>
          )}


          <MultiField
            title="Utility Scope"
            list={reference?.utility_scope || []}
            selected={draft.utility_scope || []}
            onToggle={(x) => toggleList("utility_scope", x)}
            idPrefix="scope"
          />

          {isChocolate && (
            <Section title="Chocolate Process Utilities">
              <Field label="Cooling Tunnel Load (TR)">
                <InputF id="cooling_tunnel_load_tr" type="number" value={draft.cooling_tunnel_load_tr} onChange={(v) => patch("cooling_tunnel_load_tr", v)} />
              </Field>
              <Field label="Tempering Utility Demand">
                <SelectF id="tempering_utility_demand" value={draft.tempering_utility_demand} onChange={(v) => patch("tempering_utility_demand", v)} options={reference?.tempering_utility_demand} />
              </Field>

              <Field label="Humidity Controlled (%)">
                <InputF
                  id="humidity_controlled_pct"
                  type="number"
                  value={Math.min(
                    100,
                    Math.max(0, Number(draft.humidity_controlled_pct) || 0)
                  )}
                  onChange={(v) =>
                    patch(
                      "humidity_controlled_pct",
                      Math.min(100, Math.max(0, Number(v) || 0))
                    )
                  }
                />
              </Field>

              <Field label="Chocolate Storage Temp (°C)">
                <InputF
                  id="chocolate_storage_temp_c"
                  type="number"
                  min="19"
                  value={draft.chocolate_storage_temp_c}
                  onChange={(v) => {
                    if (v === "") {
                      patch("chocolate_storage_temp_c", "");
                      return;
                    }

                    patch(
                      "chocolate_storage_temp_c",
                      Math.max(19, Number(v))
                    );
                  }}
                />
              </Field>
              <Field label="Process Hot Water (L/hr)">
                <InputF id="process_hot_water_lph" type="number" value={draft.process_hot_water_lph} onChange={(v) => patch("process_hot_water_lph", v)} />
              </Field>
            </Section>
          )}

          {isBiscuit && (
            <Section title="Biscuit Process Utilities">
              <Field label="Oven Capacity (kg/hr)">
                <InputF id="oven_capacity_kg_hr" type="number" value={draft.oven_capacity_kg_hr} onChange={(v) => patch("oven_capacity_kg_hr", v)} />
              </Field>
              <Field label="Fuel Type">
                <SelectF id="fuel_type" value={draft.fuel_type} onChange={(v) => patch("fuel_type", v)} options={reference?.fuel_types} />
              </Field>
              <Field label="Baking Line Qty">
                <InputF id="baking_line_qty" type="number" value={draft.baking_line_qty} onChange={(v) => patch("baking_line_qty", v)} />
              </Field>
              <Field label="Compressed Air (CFM)">
                <InputF id="compressed_air_demand_cfm" type="number" value={draft.compressed_air_demand_cfm} onChange={(v) => patch("compressed_air_demand_cfm", v)} />
              </Field>
              <Field label="Cooling Conveyor Load">
                <SelectF id="cooling_conveyor_load" value={draft.cooling_conveyor_load} onChange={(v) => patch("cooling_conveyor_load", v)} options={reference?.cooling_conveyor_load} />
              </Field>
              <Field label="Dust Collection Required">
                <BoolBox id="dust_collection_required" checked={draft.dust_collection_required} onChange={(v) => patch("dust_collection_required", v)} />
              </Field>
            </Section>
          )}

          {/* ---- Infra & Site ---- */}
          <Section title="External Works Scope">
            <Field label="Roads,Pathways & Parking Bays">
              <BoolBox id="include_roads" checked={draft.include_roads} onChange={(v) => patch("include_roads", v)} />
            </Field>
            <Field label="Landscaping">
              <BoolBox id="include_landscaping" checked={draft.include_landscaping} onChange={(v) => patch("include_landscaping", v)} />
            </Field>
            <Field label="Compound Wall / Fence">
              <BoolBox id="include_fence" checked={draft.include_fence} onChange={(v) => patch("include_fence", v)} />
            </Field>
          </Section>

          <Section title="Site Inputs">
            <Field label="Land Area (m²)">
              <InputF id="land_area_sqm" type="number" value={draft.land_area_sqm} onChange={(v) => patch("land_area_sqm", v)} />
            </Field>
            <Field label="Ground Coverage (%)">
              <InputF id="ground_coverage_pct" type="number" value={draft.ground_coverage_pct} onChange={(v) => patch("ground_coverage_pct", v)} />
            </Field>
            <Field label="FAR / FSI">
              <InputF id="far_fsi" type="number" value={draft.far_fsi} onChange={(v) => patch("far_fsi", v)} />
            </Field>
            <Field label="Water Availability">
              <SelectF id="water_availability" value={draft.water_availability} onChange={(v) => patch("water_availability", v)} options={reference?.water_availability} />
            </Field>
            <Field label="Electrical Grid Reliability">
              <SelectF id="grid_reliability" value={draft.grid_reliability} onChange={(v) => patch("grid_reliability", v)} options={reference?.grid_reliability} />
            </Field>
            <Field label="Ambient Temperature">
              <SelectF id="ambient_temp_range" value={draft.ambient_temp_range} onChange={(v) => patch("ambient_temp_range", v)} options={reference?.ambient_temp_ranges} />
            </Field>

            <Field label="Relative Humidity (%)">
              <InputF
                id="relative_humidity_pct"
                type="number"
                value={Math.min(
                  100,
                  Math.max(0, Number(draft.relative_humidity_pct) || 0)
                )}
                onChange={(v) =>
                  patch(
                    "relative_humidity_pct",
                    Math.min(100, Math.max(0, Number(v) || 0))
                  )
                }
              />
            </Field></Section>


          {/* ---- Complexity ---- */}
          <MultiField
            title="Complexity Factors"
            list={reference?.complexity || []}
            selected={Object.keys(draft.complexity || {}).filter((k) => draft.complexity[k])}
            onToggle={(k) => patchCx(k, !draft.complexity[k])}
            idPrefix="complexity"
          />

          {/* ---- Contingency ---- */}
          <Section title="Contingency">
            <Field label={`Contingency: ${draft.contingency_pct}%`} span={2}>
              <input
                type="range"
                min="4"
                max="20"
                step="0.5"
                value={draft.contingency_pct}
                onChange={(e) => patch("contingency_pct", +e.target.value)}
                data-testid={TID.wizardField("contingency_pct")}
                className="w-full accent-blue-600"
              />
            </Field>
          </Section>
        </div>

        <SheetFooter className="flex-row items-center justify-end gap-2 border-t border-slate-200 px-6 py-3 bg-slate-50">
          <Button
            variant="outline"
            data-testid="edit-cancel-btn"
            onClick={() => {
              setDraft(inputs);
              onOpenChange(false);
            }}
          >
            <X className="w-4 h-4 mr-1" /> Cancel
          </Button>

          <Button
            data-testid="edit-save-btn"
            onClick={handleSave}
            disabled={!employeeCountValid}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="w-4 h-4 mr-1" /> Save & Recalculate
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet >
  );
}

/* ---------- Local primitives ---------- */

function Section({ title, children }) {
  return (
    <div>
      <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-l-2 border-blue-500 pl-2">
        {title}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {children}
      </div>
    </div>
  );
}

function Field({ label, children, span = 1 }) {
  const spanCls = span === 2 ? "sm:col-span-2" : "";

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
      <SelectTrigger
        data-testid={TID.wizardField(`edit_${id}`)}
        className="h-9 bg-white text-sm"
      >
        <SelectValue />
      </SelectTrigger>

      <SelectContent className="bg-white z-[70] max-h-[280px]">
        {(options || []).map((o) => (
          <SelectItem key={o} value={o}>
            {o}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}


function InputF({
  id,
  value,
  onChange,
  type = "text",
  disabled = false,
}) {
  return (
    <Input
      data-testid={TID.wizardField(`edit_${id}`)}
      value={value ?? ""}
      onChange={(e) => {
        if (typeof onChange === "function") {
          onChange(
            type === "number"
              ? e.target.value === ""
                ? ""
                : Number(e.target.value)
              : e.target.value
          );
        }
      }}
      type={type}
      min={type === "number" ? 0 : undefined}
      disabled={disabled}
      readOnly={!onChange}
      className="h-9 text-sm"
    />
  );
}


function BoolBox({ id, checked, onChange }) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded h-9 px-3 bg-white cursor-pointer hover:bg-slate-50">
      <Checkbox
        data-testid={TID.wizardField(`edit_${id}`)}
        checked={checked}
        onCheckedChange={(v) => onChange(!!v)}
      />
      <span>{checked ? "Yes" : "No"}</span>
    </label>
  );
}

function MultiField({ title, list, selected, onToggle, idPrefix }) {
  return (
    <div>
      <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-l-2 border-blue-500 pl-2">
        {title}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
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
                data-testid={TID.wizardField(`edit_${idPrefix}_${key}`)}
                checked={checked}
                onCheckedChange={() => onToggle(key)}
              />
              <span className="truncate">{label}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}