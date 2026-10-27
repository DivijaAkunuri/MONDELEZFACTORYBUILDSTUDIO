import React, { useState } from "react";
import { lookupLocation } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { TID } from "@/constants/testIds";
import { ChevronLeft, ChevronRight } from "lucide-react";

const STEP_TITLES = [
  "Project Details",
  "Building Geometry",
  "Structural & Site",
  "Utilities & Process",
  "Infra & External",
];

export default function Wizard({
  step,
  setStep,
  inputs,
  setInputs,
  reference,
  onFinish,
}) {
  const [attemptedNext, setAttemptedNext] = useState(false);
  const [attemptedFinish, setAttemptedFinish] = useState(false);

  const patch = (key, value) => {
    setInputs((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const patchComplexity = (key, value) => {
    setInputs((current) => ({
      ...current,
      complexity: {
        ...(current.complexity || {}),
        [key]: value,
      },
    }));
  };

  // Validate dimensions and both manually entered areas.
  const validateAreas = () => {
    const length = Number(inputs.length_m);
    const width = Number(inputs.width_m);
    const plotArea = Number(inputs.plot_area_sqm);
    const landArea = Number(inputs.land_area_sqm);

    if (
      inputs.length_m === "" ||
      inputs.length_m == null ||
      !Number.isFinite(length) ||
      length <= 0
    ) {
      return {
        field: "length_m",
        message: "Length must be greater than 0.",
      };
    }

    if (
      inputs.width_m === "" ||
      inputs.width_m == null ||
      !Number.isFinite(width) ||
      width <= 0
    ) {
      return {
        field: "width_m",
        message: "Width must be greater than 0.",
      };
    }

    const minimumArea = length * width;

    if (!Number.isFinite(minimumArea) || minimumArea <= 0) {
      return {
        field: "length_m",
        message: "Length × Width must be greater than 0.",
      };
    }

    if (
      inputs.plot_area_sqm === "" ||
      inputs.plot_area_sqm == null ||
      !Number.isFinite(plotArea) ||
      plotArea <= 0
    ) {
      return {
        field: "plot_area_sqm",
        message: "Plot Area must be greater than 0.",
      };
    }

    if (plotArea < minimumArea) {
      return {
        field: "plot_area_sqm",
        message: `Plot Area must be at least ${minimumArea} m² (Length × Width).`,
      };
    }

    if (
      inputs.land_area_sqm === "" ||
      inputs.land_area_sqm == null ||
      !Number.isFinite(landArea) ||
      landArea <= 0
    ) {
      return {
        field: "land_area_sqm",
        message: "Land Area must be greater than 0.",
      };
    }

    if (landArea < minimumArea) {
      return {
        field: "land_area_sqm",
        message: `Land Area must be at least ${minimumArea} m² (Length × Width).`,
      };
    }

    return null;
  };

  const stepUi = () => {
    switch (step) {
      case 0:
        return (
          <Step1
            inputs={inputs}
            patch={patch}
            reference={reference}
          />
        );

      case 1:
        return (
          <Step2
            inputs={inputs}
            patch={patch}
            reference={reference}
            showErrors={attemptedNext}
          />
        );

      case 2:
        return (
          <Step3
            inputs={inputs}
            patch={patch}
            reference={reference}
          />
        );

      case 3:
        return (
          <Step4
            inputs={inputs}
            patch={patch}
            patchComplexity={patchComplexity}
            reference={reference}
          />
        );

      case 4:
        return (
          <Step5
            inputs={inputs}
            patch={patch}
            patchComplexity={patchComplexity}
            reference={reference}
            showErrors={attemptedFinish}
          />
        );

      default:
        return null;
    }
  };

  const handleNext = () => {
    if (step === 1) {
      setAttemptedNext(true);

      const error = validateAreas();

      if (error) {
        return;
      }
    }

    setStep(step + 1);
  };

  const handleFinish = () => {
    setAttemptedFinish(true);

    const error = validateAreas();

    if (error) {
      if (error.field === "length_m" || error.field === "width_m" ||
        error.field === "plot_area_sqm") {
        setStep(1);
        setAttemptedNext(true);
      } else {
        setStep(4);
      }

      return;
    }

    onFinish();
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm">
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900 font-['Manrope']">
          Step {step + 1} — {STEP_TITLES[step]}
        </h2>

        <p className="text-xs text-slate-500 mt-1">
          Fill in the details, then continue.
        </p>
      </div>

      {stepUi()}

      <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
        <Button
          data-testid={TID.wizardBack}
          variant="outline"
          onClick={() => setStep(Math.max(0, step - 1))}
          disabled={step === 0}
        >
          <ChevronLeft className="w-4 h-4 mr-1" />
          Back
        </Button>

        {step < 4 ? (
          <Button
            data-testid={TID.wizardNext}
            onClick={handleNext}
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        ) : (
          <Button
            data-testid={TID.wizardNext}
            onClick={handleFinish}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Calculate Estimate
            <ChevronRight className="w-4 h-4 ml-1" />
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
      <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-3 border-l-2 border-blue-500 pl-2">
        {title}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {children}
      </div>
    </div>
  );
}

function Field({ label, children, span = 1 }) {
  const spanClass =
    span === 3
      ? "md:col-span-3"
      : span === 2
        ? "md:col-span-2"
        : "";

  return (
    <div className={`space-y-1 ${spanClass}`}>
      <Label className="text-xs font-semibold text-slate-600">
        {label}
      </Label>

      {children}
    </div>
  );
}

function SelectF({ id, value, onChange, options }) {
  return (
    <Select
      value={value == null || value === "" ? undefined : String(value)}
      onValueChange={onChange}
    >
      <SelectTrigger
        data-testid={TID.wizardField(id)}
        className="h-9 bg-white"
      >
        <SelectValue placeholder="Select an option" />
      </SelectTrigger>

      <SelectContent className="bg-white z-50 max-h-[280px]">
        {(options || []).map((option) => {
          const optionValue =
            typeof option === "string" ? option : option.key;

          const optionLabel =
            typeof option === "string" ? option : option.label;

          return (
            <SelectItem
              key={optionValue}
              value={String(optionValue)}
            >
              {optionLabel}
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}


function InputF({ id, value, onChange, type = "text", ...props }) {
  const limits = {
    relative_humidity_pct: { min: 0, max: 100 },
    humidity_controlled_pct: { min: 0, max: 100 },
    wind_speed_ms: { min: 45, max: Infinity },
  };

  const limit = limits[id];

  return (
    <Input
      data-testid={TID.wizardField(id)}
      value={value ?? ""}
      onChange={(event) => {
        const rawValue = event.target.value;

        if (type === "number" && limit) {
          if (rawValue === "") {
            onChange(limit.min);
            return;
          }

          const number = Number(rawValue);

          if (!Number.isFinite(number)) return;

          onChange(
            Math.min(limit.max, Math.max(limit.min, number))
          );
          return;
        }

        onChange(
          type === "number"
            ? rawValue === "" ? "" : Number(rawValue)
            : type === "range" ? Number(rawValue) : rawValue
        );
      }}
      type={type}
      min={limit?.min ?? props.min}
      max={Number.isFinite(limit?.max) ? limit.max : props.max}
      onBlur={(event) => {
        if (!limit) {
          props.onBlur?.(event);
          return;
        }

        const number = Number(event.target.value);

        onChange(
          event.target.value === "" || !Number.isFinite(number)
            ? limit.min
            : Math.min(limit.max, Math.max(limit.min, number))
        );

        props.onBlur?.(event);
      }}
      className="h-9"
      {...props}
    />
  );
}


function CheckboxGrid({ list, selected = [], onToggle, idPrefix }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-1">
      {(list || []).map((item) => {
        const key = typeof item === "string" ? item : item.key;
        const label = typeof item === "string" ? item : item.label;
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

function ErrorMessage({ children }) {
  if (!children) return null;

  return (
    <p className="mt-1 text-xs text-red-600" role="alert">
      {children}
    </p>
  );
}

/* ---------- Step 1 : Project Identification ---------- */

function Step1({ inputs, patch, reference }) {
  const [locations, setLocations] = useState([]);
  const [loadingLocation, setLoadingLocation] = useState(false);
  const [locationError, setLocationError] = useState("");


  const findLocation = async () => {
    const city = inputs.location_city?.trim();

    if (!city) {
      setLocationError("Please enter a city name.");
      return;
    }

    setLoadingLocation(true);
    setLocationError("");
    setLocations([]);

    try {
      const data = await lookupLocation(city);
      const results = Array.isArray(data?.locations) ? data.locations : [];

      setLocations(results);

      if (results.length === 0) {
        setLocationError(
          "No matching locations found. Try entering the city with its country name."
        );
      }
    } catch (error) {
      console.error("Location lookup failed:", error);
      console.error("Response data:", error.response?.data);
      console.error("Response status:", error.response?.status);

      setLocationError(
        error.response?.data?.detail ||
        error.message ||
        "Could not find the location. Please try again."
      );
    } finally {
      setLoadingLocation(false);
    }
  };



  const selectLocation = (location) => {
    const regions = reference?.regions || {};
    const availableRegions = Object.keys(regions);

    const normalize = (value) =>
      String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toLowerCase();

    const country = String(location.country || "").trim();

    if (!country) {
      setLocationError(
        "The location lookup did not return a country. Please select another result."
      );
      return;
    }

    // Match the returned country against your existing country-to-region mapping.
    const matchedRegion = availableRegions.find((region) =>
      (regions[region] || []).some(
        (mappedCountry) => normalize(mappedCountry) === normalize(country)
      )
    );

    if (!matchedRegion) {
      setLocationError(
        `Found ${country}, but this country is not in your estimator's region mapping.`
      );
      return;
    }

    patch("location_city", location.city || inputs.location_city);
    patch("location_country", country);
    patch("region", matchedRegion);

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
            onChange={(value) => patch("project_name", value)}
          />
        </Field>

        <Field label="Project Type">
          <InputF
            id="project_type"
            value={inputs.project_type}
            onChange={(value) => patch("project_type", value)}
          />
        </Field>

        <Field label="Industry Type">
          <InputF id="industry_type" value="FMCG" readOnly />
        </Field>

        <Field label="Product Category">
          <SelectF
            id="product_category"
            value={inputs.product_category}
            onChange={(value) => patch("product_category", value)}
            options={reference?.product_categories}
          />
        </Field>
      </Section>

      <Section title="Location">
        <Field label="City">
          <InputF
            id="location_city"
            value={inputs.location_city}
            onChange={(value) => {
              patch("location_city", value);
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
            onChange={(value) => patch("location_country", value)}
            options={reference?.regions?.[inputs.region] || []}
          />
        </Field>

        <Field label="Currency">
          <SelectF
            id="currency"
            value={inputs.currency}
            onChange={(value) => patch("currency", value)}
            options={reference?.currencies}
          />
        </Field>

        <Field label="Region">
          <SelectF
            id="region"
            value={inputs.region}
            onChange={(value) => {
              patch("region", value);
              patch("location_country", "");
            }}
            options={Object.keys(reference?.regions || {})}
          />
        </Field>

        <Field label="Location Tier (Stage 1)">
          <SelectF
            id="location_tier"
            value={inputs.location_tier}
            onChange={(value) => patch("location_tier", value)}
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

function Step2({ inputs, patch, reference, showErrors }) {
  const toggle = (item) => {
    const current = inputs.building_components || [];
    const has = current.includes(item);

    patch(
      "building_components",
      has
        ? current.filter((component) => component !== item)
        : [...current, item]
    );
  };

  const length = Number(inputs.length_m);
  const width = Number(inputs.width_m);
  const plotArea = Number(inputs.plot_area_sqm);
  const minimumArea = length * width;

  const lengthError =
    inputs.length_m === "" ||
      inputs.length_m == null ||
      !Number.isFinite(length) ||
      length <= 0
      ? "Length must be greater than 0."
      : "";

  const widthError =
    inputs.width_m === "" ||
      inputs.width_m == null ||
      !Number.isFinite(width) ||
      width <= 0
      ? "Width must be greater than 0."
      : "";

  const plotAreaError =
    lengthError || widthError
      ? ""
      : inputs.plot_area_sqm === "" ||
        inputs.plot_area_sqm == null ||
        !Number.isFinite(plotArea) ||
        plotArea <= 0
        ? "Plot Area must be greater than 0."
        : plotArea < minimumArea
          ? `Plot Area must be at least ${minimumArea} m² (Length × Width).`
          : "";

  return (
    <>
      <Section title="Building Envelope">
        <Field label="Building Type" span={3}>
          <SelectF
            id="building_type"
            value={inputs.building_type}
            onChange={(value) => patch("building_type", value)}
            options={reference?.building_types}
          />
        </Field>

        <Field label="Length (m)">
          <InputF
            id="length_m"
            type="number"
            min="0"
            value={inputs.length_m}
            onChange={(value) => patch("length_m", value)}
            aria-invalid={!!lengthError && showErrors}
          />

          {showErrors && <ErrorMessage>{lengthError}</ErrorMessage>}
        </Field>

        <Field label="Width (m)">
          <InputF
            id="width_m"
            type="number"
            min="0"
            value={inputs.width_m}
            onChange={(value) => patch("width_m", value)}
            aria-invalid={!!widthError && showErrors}
          />

          {showErrors && <ErrorMessage>{widthError}</ErrorMessage>}
        </Field>
        <Field label="Number of Floors">
          <InputF
            id="num_floors"
            type="number"
            value={inputs.num_floors}
            onChange={(value) => patch("num_floors", value)}
          />
        </Field>

        <Field label="Floor Height(m)">
          <InputF
            id="height_m"
            type="number"
            value={inputs.height_m}
            onChange={(value) => patch("height_m", value)}
          />
        </Field>

        <Field label="Bay Spacing (Column) (m)">
          <InputF
            id="bay_spacing_m"
            type="number"
            value={inputs.bay_spacing_m}
            onChange={(value) => patch("bay_spacing_m", value)}
          />
        </Field>


        <Field label="Built-up Area (Length × Width × No. of Floors) (m²)">
          <InputF
            id="built_up_area_display"
            type="text"
            value={
              Number(inputs.length_m) > 0 &&
                Number(inputs.width_m) > 0 &&
                Number(inputs.num_floors) > 0
                ? (
                  Number(inputs.length_m) *
                  Number(inputs.width_m) *
                  Number(inputs.num_floors)
                ).toLocaleString()
                : "Enter dimensions and floors"
            }
            disabled
            onChange={() => { }}
          />
        </Field>


      </Section>

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

        <Section title="Warehouses Geometry">
          <div className="col-span-full">
            <h3 className="text-sm font-semibold text-slate-700 border-b border-slate-200 pb-2 mb-3">
              RM Warehouse (Raw Material)
            </h3>
          </div>

          <Field label="RM Warehouse Length (m)">
            <InputF
              id="rm_warehouse_length_m"
              type="number"
              min="0"
              value={inputs.rm_warehouse_length_m ?? ""}
              onChange={(value) => patch("rm_warehouse_length_m", value)}
            />
          </Field>

          <Field label="RM Warehouse Width (m)">
            <InputF
              id="rm_warehouse_width_m"
              type="number"
              min="0"
              value={inputs.rm_warehouse_width_m ?? ""}
              onChange={(value) => patch("rm_warehouse_width_m", value)}
            />
          </Field>

          <Field label="RM Warehouse Height (m)">
            <InputF
              id="rm_warehouse_height_m"
              type="number"
              min="0"
              value={inputs.rm_warehouse_height_m ?? ""}
              onChange={(value) => patch("rm_warehouse_height_m", value)}
            />
          </Field>

          <Field label="RM Warehouse Built-up Area (m²)">
            <InputF
              id="rm_warehouse_built_up_area_sqm"
              type="number"
              min="0"
              value={inputs.rm_warehouse_built_up_area_sqm ?? ""}
              onChange={(value) =>
                patch("rm_warehouse_built_up_area_sqm", value)
              }
            />
          </Field>

          <div className="col-span-full mt-4">
            <h3 className="text-sm font-semibold text-slate-700 border-b border-slate-200 pb-2 mb-3">
              FG Warehouse (Finished Goods)
            </h3>
          </div>

          <Field label="FG Warehouse Length (m)">
            <InputF
              id="fg_warehouse_length_m"
              type="number"
              min="0"
              value={inputs.fg_warehouse_length_m ?? ""}
              onChange={(value) => patch("fg_warehouse_length_m", value)}
            />
          </Field>

          <Field label="FG Warehouse Width (m)">
            <InputF
              id="fg_warehouse_width_m"
              type="number"
              min="0"
              value={inputs.fg_warehouse_width_m ?? ""}
              onChange={(value) => patch("fg_warehouse_width_m", value)}
            />
          </Field>

          <Field label="FG Warehouse Height (m)">
            <InputF
              id="fg_warehouse_height_m"
              type="number"
              min="0"
              value={inputs.fg_warehouse_height_m ?? ""}
              onChange={(value) => patch("fg_warehouse_height_m", value)}
            />
          </Field>

          <Field label="FG Warehouse Built-up Area (m²)">
            <InputF
              id="fg_warehouse_built_up_area_sqm"
              type="number"
              min="0"
              value={inputs.fg_warehouse_built_up_area_sqm ?? ""}
              onChange={(value) =>
                patch("fg_warehouse_built_up_area_sqm", value)
              }
            />
          </Field>
        </Section>

      </div>
    </>
  );
}

/* ---------- Step 3 : Structural & Site ---------- */

function Step3({ inputs, patch, reference }) {
  const toggleFoundation = (item) => {
    const current = inputs.foundation_type || [];
    const has = current.includes(item);

    patch(
      "foundation_type",
      has
        ? current.filter((value) => value !== item)
        : [...current, item]
    );
  };

  return (
    <>
      <Section title="Structural & Design">
        <div className="md:col-span-3">
          <div className="text-xs font-semibold text-slate-600 mb-1">
            Foundation Type
          </div>

          <CheckboxGrid
            list={reference?.foundation_types || []}
            selected={inputs.foundation_type || []}
            onToggle={toggleFoundation}
            idPrefix="foundation"
          />
        </div>

        <Field label="SBC / Soil Type">
          <SelectF
            id="sbc_soil_type"
            value={inputs.sbc_soil_type}
            onChange={(value) => patch("sbc_soil_type", value)}
            options={reference?.sbc_soil_types}
          />
        </Field>

        <Field label="Column Type">
          <SelectF
            id="column_type"
            value={inputs.column_type}
            onChange={(value) => patch("column_type", value)}
            options={reference?.column_types}
          />
        </Field>

        <Field label="Roof Type">
          <SelectF
            id="roof_type"
            value={inputs.roof_type}
            onChange={(value) => patch("roof_type", value)}
            options={reference?.roof_types}
          />
        </Field>

        <Field label="Floor Load (kN/m²)">
          <InputF
            id="floor_load_kn"
            type="number"
            value={inputs.floor_load_kn}
            onChange={(value) => patch("floor_load_kn", value)}
          />
        </Field>
      </Section>

      <Section title="Site Conditions">
        <Field label="Seismic Zone">
          <SelectF
            id="seismic_zone"
            value={inputs.seismic_zone}
            onChange={(value) => patch("seismic_zone", value)}
            options={reference?.seismic_zones}
          />
        </Field>

        <Field label="Wind Zone">
          <SelectF
            id="wind_zone"
            value={inputs.wind_zone}
            onChange={(value) => patch("wind_zone", value)}
            options={reference?.wind_zones}
          />
        </Field>



        <Field label="Wind Speed (m/s)">
          <InputF
            id="wind_speed_ms"
            type="number"
            min="45"
            step="1"
            value={Math.max(45, Number(inputs.wind_speed_ms) || 45)}
            onChange={(value) => {
              if (value === "") {
                patch("wind_speed_ms", 45);
                return;
              }

              const number = Number(value);

              if (Number.isFinite(number)) {
                patch("wind_speed_ms", Math.max(45, number));
              }
            }}
          />
        </Field>


        <Field label="Ground Water Table Depth">
          <SelectF
            id="gwt_depth"
            value={inputs.gwt_depth}
            onChange={(value) => patch("gwt_depth", value)}
            options={reference?.gwt_depths}
          />
        </Field>
      </Section>
    </>
  );
}

/* ---------- Step 4 : Utilities & Process ---------- */

function Step4({ inputs, patch, patchComplexity, reference }) {
  const toggleScope = (scope) => {
    const current = inputs.utility_scope || [];
    const has = current.includes(scope);

    patch(
      "utility_scope",
      has
        ? current.filter((item) => item !== scope)
        : [...current, scope]
    );
  };

  const isChocolate = /chocolate|combo/i.test(
    inputs.product_category || ""
  );

  const isBiscuit = /biscuit|wafer|cookie|combo/i.test(
    inputs.product_category || ""
  );

  const processComplexity = (reference?.complexity || []).filter((item) =>
    [
      "explosion_risk",
      "utility_redundancy",
    ].includes(item.key)
  );

  return (
    <>
      <Section title="Production Capacity">
        <Field label="Production Capacity (TPD)">
          <InputF
            id="production_capacity_tpd"
            type="number"
            value={inputs.production_capacity_tpd}
            onChange={(value) => patch("production_capacity_tpd", value)}
          />
        </Field>

        <Field label="Annual Output (MT)">
          <InputF
            id="annual_output_mt"
            type="number"
            value={inputs.annual_output_mt}
            onChange={(value) => patch("annual_output_mt", value)}
          />
        </Field>
      </Section>

      <div className="mb-5">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-l-2 border-blue-500 pl-2">
          Utility Scope
        </div>

        <CheckboxGrid
          list={reference?.utility_scope || []}
          selected={inputs.utility_scope || []}
          onToggle={toggleScope}
          idPrefix="scope"
        />
      </div>

      {isChocolate && (
        <Section title="Chocolate Process Utilities">
          <Field label="Cooling Tunnel Load (TR)">
            <InputF
              id="cooling_tunnel_load_tr"
              type="number"
              value={inputs.cooling_tunnel_load_tr}
              onChange={(value) => patch("cooling_tunnel_load_tr", value)}
            />
          </Field>

          <Field label="Tempering Utility Demand">
            <SelectF
              id="tempering_utility_demand"
              value={inputs.tempering_utility_demand}
              onChange={(value) =>
                patch("tempering_utility_demand", value)
              }
              options={reference?.tempering_utility_demand}
            />
          </Field>


          <Field label="Humidity Controlled Areas (%)">
            <InputF
              id="humidity_controlled_pct"
              type="number"
              min="0"
              max="100"
              step="1"
              value={Math.min(
                100,
                Math.max(0, Number(inputs.humidity_controlled_pct) || 0)
              )}
              onChange={(value) => {
                if (value === "") {
                  patch("humidity_controlled_pct", "");
                  return;
                }

                const number = Number(value);

                if (Number.isFinite(number)) {
                  patch(
                    "humidity_controlled_pct",
                    Math.min(100, Math.max(0, number))
                  );
                }
              }}
            />
          </Field>


          <Field label="Chocolate Storage Temp (°C)">
            <InputF
              id="chocolate_storage_temp_c"
              type="number"
              value={inputs.chocolate_storage_temp_c}
              onChange={(value) =>
                patch("chocolate_storage_temp_c", value)
              }
            />
          </Field>

          <Field label="Process Hot Water (L/hr)">
            <InputF
              id="process_hot_water_lph"
              type="number"
              value={inputs.process_hot_water_lph}
              onChange={(value) =>
                patch("process_hot_water_lph", value)
              }
            />
          </Field>
        </Section>
      )}

      {isBiscuit && (
        <Section title="Biscuit Process Utilities">
          <Field label="Oven Capacity (kg/hr)">
            <InputF
              id="oven_capacity_kg_hr"
              type="number"
              value={inputs.oven_capacity_kg_hr}
              onChange={(value) =>
                patch("oven_capacity_kg_hr", value)
              }
            />
          </Field>

          <Field label="Fuel Type">
            <SelectF
              id="fuel_type"
              value={inputs.fuel_type}
              onChange={(value) => patch("fuel_type", value)}
              options={reference?.fuel_types}
            />
          </Field>

          <Field label="Baking Line Quantity">
            <InputF
              id="baking_line_qty"
              type="number"
              value={inputs.baking_line_qty}
              onChange={(value) => patch("baking_line_qty", value)}
            />
          </Field>

          <Field label="Compressed Air Demand (CFM)">
            <InputF
              id="compressed_air_demand_cfm"
              type="number"
              value={inputs.compressed_air_demand_cfm}
              onChange={(value) =>
                patch("compressed_air_demand_cfm", value)
              }
            />
          </Field>

          <Field label="Cooling Conveyor Load">
            <SelectF
              id="cooling_conveyor_load"
              value={inputs.cooling_conveyor_load}
              onChange={(value) =>
                patch("cooling_conveyor_load", value)
              }
              options={reference?.cooling_conveyor_load}
            />
          </Field>

          <Field label="Dust Collection Required">
            <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded h-9 px-3 bg-white">
              <Checkbox
                data-testid={TID.wizardField("dust_collection_required")}
                checked={!!inputs.dust_collection_required}
                onCheckedChange={(value) =>
                  patch("dust_collection_required", !!value)
                }
              />

              <span>Yes</span>
            </label>
          </Field>
        </Section>
      )}

      <div className="mb-2">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-l-2 border-blue-500 pl-2">
          Process Complexity
        </div>

        <CheckboxGrid
          list={processComplexity}
          selected={Object.keys(inputs.complexity || {}).filter(
            (key) => inputs.complexity[key]
          )}
          onToggle={(key) =>
            patchComplexity(key, !inputs.complexity?.[key])
          }
          idPrefix="complexity"
        />
      </div>
    </>
  );
}

/* ---------- Step 5 : Infra & Site Inputs ---------- */

function Step5({
  inputs,
  patch,
  patchComplexity,
  reference,
  showErrors,
}) {
  const siteComplexity = (reference?.complexity || []).filter((item) =>
    [
      "remote_site",
      "brownfield",
      "high_floor_load",
    ].includes(item.key)
  );

  const length = Number(inputs.length_m);
  const width = Number(inputs.width_m);
  const landArea = Number(inputs.land_area_sqm);
  const minimumArea = length * width;

  const dimensionsValid =
    inputs.length_m !== "" &&
    inputs.length_m != null &&
    Number.isFinite(length) &&
    length > 0 &&
    inputs.width_m !== "" &&
    inputs.width_m != null &&
    Number.isFinite(width) &&
    width > 0;

  const landAreaError = !dimensionsValid
    ? ""
    : inputs.land_area_sqm === "" ||
      inputs.land_area_sqm == null ||
      !Number.isFinite(landArea) ||
      landArea <= 0
      ? "Land Area must be greater than 0."
      : landArea < minimumArea
        ? `Land Area must be at least ${minimumArea} m² (Length × Width).`
        : "";

  const toggleBoolean = (key, value) => {
    patch(key, !!value);
  };

  return (
    <>
      {(inputs.building_components || []).includes("Admin Building") && (
        <Section title="Employee & Staff Facilities">
          <Field label="Total Employees">
            <InputF
              id="num_employees"
              type="number"
              min="0"
              value={inputs.num_employees ?? 0}
              onChange={(value) =>
                patch("num_employees", Math.max(0, Number(value) || 0))
              }
            />
          </Field>

          <Field label="Male Employees">
            <InputF
              id="male_employees"
              type="number"
              min="0"
              value={inputs.male_employees ?? 0}
              onChange={(value) =>
                patch("male_employees", Math.max(0, Number(value) || 0))
              }
            />
          </Field>

          <Field label="Female Employees">
            <InputF
              id="female_employees"
              type="number"
              min="0"
              value={inputs.female_employees ?? 0}
              onChange={(value) =>
                patch("female_employees", Math.max(0, Number(value) || 0))
              }
            />
          </Field>

          <Field label="Special / Work Clothing Required?">
            <SelectF
              id="special_work_clothing"
              value={inputs.special_work_clothing ?? "Yes"}
              onChange={(value) =>
                patch("special_work_clothing", value)
              }
              options={["Yes", "No"]}
            />
          </Field>

          <Field label="Street & Safety Shoes Lockers Required?">
            <SelectF
              id="work_shoes_required"
              value={inputs.work_shoes_required ?? "Yes"}
              onChange={(value) =>
                patch("work_shoes_required", value)
              }
              options={["Yes", "No"]}
            />
          </Field>
          <Field label="Canteen/Dining Facilities Required?">
            <SelectF
              id="canteen_dining_required"
              value={inputs.canteen_dining_required ?? "Yes"}
              onChange={(value) =>
                patch("canteen_dining_required", value)
              }
              options={["Yes", "No"]}
            />
          </Field>
        </Section>
      )}

      <Section title="External Works Scope">
        <Field label="Roads,Pathways & Parking Bays">
          <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded h-9 px-3 bg-white">
            <Checkbox
              data-testid={TID.wizardField("include_roads")}
              checked={!!inputs.include_roads}
              onCheckedChange={(value) =>
                toggleBoolean("include_roads", value)
              }
            />

            <span>Include</span>
          </label>
        </Field>

        <Field label="Landscaping">
          <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded h-9 px-3 bg-white">
            <Checkbox
              data-testid={TID.wizardField("include_landscaping")}
              checked={!!inputs.include_landscaping}
              onCheckedChange={(value) =>
                toggleBoolean("include_landscaping", value)
              }
            />

            <span>Include</span>
          </label>
        </Field>

        <Field label="Compound Wall / Fence">
          <label className="flex items-center gap-2 text-sm text-slate-700 border border-slate-200 rounded h-9 px-3 bg-white">
            <Checkbox
              data-testid={TID.wizardField("include_fence")}
              checked={!!inputs.include_fence}
              onCheckedChange={(value) =>
                toggleBoolean("include_fence", value)
              }
            />

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
            value={inputs.land_area_sqm}
            onChange={(value) => patch("land_area_sqm", value)}
            aria-invalid={!!landAreaError && showErrors}
          />

          {showErrors && <ErrorMessage>{landAreaError}</ErrorMessage>}
        </Field>

        <Field label="Ground Coverage (%)">
          <InputF
            id="ground_coverage_pct"
            type="number"
            value={inputs.ground_coverage_pct}
            onChange={(value) => patch("ground_coverage_pct", value)}
          />
        </Field>

        <Field label="FAR / FSI">
          <InputF
            id="far_fsi"
            type="number"
            value={inputs.far_fsi}
            onChange={(value) => patch("far_fsi", value)}
          />
        </Field>

        <Field label="Water Availability">
          <SelectF
            id="water_availability"
            value={inputs.water_availability}
            onChange={(value) => patch("water_availability", value)}
            options={reference?.water_availability}
          />
        </Field>

        <Field label="Electrical Grid Reliability">
          <SelectF
            id="grid_reliability"
            value={inputs.grid_reliability}
            onChange={(value) => patch("grid_reliability", value)}
            options={reference?.grid_reliability}
          />
        </Field>

        <Field label="Ambient Temperature Range">
          <SelectF
            id="ambient_temp_range"
            value={inputs.ambient_temp_range}
            onChange={(value) => patch("ambient_temp_range", value)}
            options={reference?.ambient_temp_ranges}
          />
        </Field>





        <Field label="Relative Humidity (%)">
          <InputF
            id="relative_humidity_pct"
            type="range"
            min="0"
            max="100"
            step="1"
            value={Math.min(
              100,
              Math.max(0, Number(inputs.relative_humidity_pct) || 0)
            )}
            onChange={(value) =>
              patch(
                "relative_humidity_pct",
                Math.min(100, Math.max(0, Number(value) || 0))
              )
            }
          />
          <span className="text-sm text-slate-600">
            {Math.min(
              100,
              Math.max(0, Number(inputs.relative_humidity_pct) || 0)
            )}%
          </span>
        </Field>




      </Section>

      <div className="mb-5">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 border-l-2 border-blue-500 pl-2">
          Site Complexity
        </div>

        <CheckboxGrid
          list={siteComplexity}
          selected={Object.keys(inputs.complexity || {}).filter(
            (key) => inputs.complexity[key]
          )}
          onToggle={(key) =>
            patchComplexity(key, !inputs.complexity?.[key])
          }
          idPrefix="complexity"
        />
      </div>

      <Section title="Contingency">
        <Field
          label={`Contingency (%): ${inputs.contingency_pct}%`}
          span={3}
        >
          <input
            type="range"
            min="4"
            max="20"
            step="0.5"
            value={inputs.contingency_pct ?? 4}
            onChange={(event) =>
              patch("contingency_pct", Number(event.target.value))
            }
            data-testid={TID.wizardField("contingency_pct")}
            className="w-full accent-blue-600"
          />
        </Field>
      </Section>
    </>
  );
}