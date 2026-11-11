
import React from "react";
import { CheckCircle2, AlertTriangle, Lightbulb } from "lucide-react";
import { TID } from "@/constants/testIds";
import { fmtMoney, fmtNumber } from "@/lib/format";

export function TabsBar({ tabs, active, onChange }) {
  return (
    <div className="flex space-x-6 border-b border-slate-200 px-2 mb-4 overflow-x-auto">
      {tabs.map((t) => (
        <button
          key={t.key}
          data-testid={TID.tab(t.key)}
          onClick={() => onChange(t.key)}
          className={`py-3 text-sm font-semibold whitespace-nowrap ${active === t.key
            ? "text-blue-600 border-b-2 border-blue-600"
            : "text-slate-500 hover:text-slate-800"
            }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function BoqTable({ rows, testid }) {
  if (!rows?.length) return <Empty text="No cost items" />;

  return (
    <div
      data-testid={testid}
      className="bg-white border border-slate-200 rounded-lg overflow-hidden shadow-sm"
    >
      <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800 font-['Manrope']">
          Top {rows.length} Cost Items
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-[11px] uppercase text-slate-500 font-semibold tracking-wider">
            <tr>
              <th className="text-left px-4 py-2 w-10">#</th>
              <th className="text-left px-4 py-2">Activity</th>
              <th className="text-right px-4 py-2">Rate (USD)</th>
              <th className="text-right px-4 py-2">Amount (USD)</th>
              <th className="text-right px-4 py-2 w-24">% of Total</th>
            </tr>
          </thead>

          <tbody>
            {rows.map((r, i) => (
              <tr
                key={i}
                data-testid={TID.boqRow(i + 1)}
                className="border-t border-slate-100 hover:bg-slate-50"
              >
                <td className="px-4 py-2 text-slate-500">
                  {r.rank ?? i + 1}
                </td>

                <td className="px-4 py-2 text-slate-800 font-medium">
                  {r.activity}
                </td>

                <td className="px-4 py-2 text-right text-slate-700">
                  {fmtMoney(r.rate, "USD")}
                </td>

                <td className="px-4 py-2 text-right text-slate-900 font-semibold">
                  {fmtMoney(r.amount, "USD")}
                </td>

                <td className="px-4 py-2 text-right text-slate-600">
                  {r.pct_of_total ?? "—"}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function UtilitiesSummary({ utilities, total }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm h-full">
      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
        Utilities Cost Summary (USD $)
      </h3>

      <div className="space-y-2">
        {utilities.map((u) => (
          <div
            key={u.name}
            className="flex items-center justify-between text-sm border-b border-slate-100 pb-2"
          >
            <span className="text-slate-700">{u.name}</span>

            <span className="text-slate-900 font-semibold">
              {fmtMoney(u.amount, "USD")}
            </span>
          </div>
        ))}

        <div className="flex items-center justify-between pt-2 text-sm">
          <span className="text-blue-700 font-semibold">
            Total Utilities Cost
          </span>

          <span className="text-blue-700 font-bold">
            {fmtMoney(total, "USD")}
          </span>
        </div>
      </div>
    </div>
  );
}



export function ProjectOverview({ inputs }) {
  const isWarehouse = inputs.product_category === "Warehouse";
  const components = inputs.building_components || [];
  const complexity = inputs.complexity || {};
  const fgType = inputs.fg_warehouse_type || "";

  const hasComponent = (name) => components.includes(name);

  const display = (value) => {
    if (value === undefined || value === null || value === "") return "—";
    if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
    return value;
  };

  const number = (value, suffix = "") => {
    if (value === undefined || value === null || value === "") return "—";
    const n = Number(value);
    return Number.isFinite(n)
      ? `${n.toLocaleString("en-IN", { maximumFractionDigits: 2 })}${suffix}`
      : "—";
  };

  const yesNo = (value) => (value ? "Yes" : "No");

  const area = (length, width, floors = 1) => {
    const l = Number(length);
    const w = Number(width);
    const f = Number(floors);
    if (!l || !w || !f) return "—";
    return number(l * w * f, " m²");
  };

  const rows = [
    ["Project Type", display(inputs.project_type)],
    ["Industry Type", display(inputs.industry_type)],
    ["Product Category", display(inputs.product_category)],
    ["Building Type", display(inputs.building_type)],
    [
      "Location",
      [inputs.location_city, inputs.location_country].filter(Boolean).join(", ") || "—",
    ],
    ["Region", display(inputs.region)],
    ["Location Tier", display(inputs.location_tier)],
    ["Land Area", number(inputs.land_area_sqm, " m²")],
    ["Building Components", display(components)],
  ];

  // Main building details - not applicable to Warehouse
  if (!isWarehouse) {
    rows.push(
      ["Building Length", number(inputs.length_m, " m")],
      ["Building Width", number(inputs.width_m, " m")],
      ["Number of Floors", display(inputs.num_floors)],
      ["Floor Height", number(inputs.height_m, " m")],
      ["Bay Spacing", number(inputs.bay_spacing_m, " m")],
      ["Main Building Built-up Area", area(inputs.length_m, inputs.width_m, inputs.num_floors)]
    );
  }

  // Employee details
  if (hasComponent("Admin Building")) {
    rows.push(
      ["Male Employees", display(inputs.male_employees)],
      ["Female Employees", display(inputs.female_employees)],
      ["Total Employees", display(inputs.num_employees)],
      ["Special Work Clothing", yesNo(inputs.special_work_clothing)],
      ["Work Shoes Required", yesNo(inputs.work_shoes_required)]
    );
  }

  // Raw material warehouse
  if (!isWarehouse && hasComponent("RM Warehouse")) {
    rows.push(
      ["RM Warehouse Length", number(inputs.rm_wh_length_m, " m")],
      ["RM Warehouse Width", number(inputs.rm_wh_width_m, " m")],
      ["RM Warehouse Height", number(inputs.rm_wh_height_m, " m")],
      ["RM Warehouse Built-up Area", area(inputs.rm_wh_length_m, inputs.rm_wh_width_m)],
      ["Optimize RM Warehouse Columns", yesNo(inputs.rm_wh_optimize_columns)],
      ["RM Warehouse Bay Spacing", number(inputs.rm_wh_bay_spacing_m, " m")]
    );
  }

  // Finished goods warehouse
  if (fgType) {
    rows.push(["FG Warehouse Type", fgType]);

    if (fgType === "Chocolate" || fgType === "Combo") {
      rows.push(
        ["Chocolate Warehouse Length", number(inputs.fg_wh_chocolate_length_m, " m")],
        ["Chocolate Warehouse Width", number(inputs.fg_wh_chocolate_width_m, " m")],
        ["Chocolate Warehouse Height", number(inputs.fg_wh_chocolate_height_m, " m")],
        ["Chocolate Warehouse Built-up Area", area(inputs.fg_wh_chocolate_length_m, inputs.fg_wh_chocolate_width_m)],
        ["Optimize Chocolate Warehouse Columns", yesNo(inputs.fg_wh_chocolate_optimize_columns)],
        ["Chocolate Warehouse Bay Spacing", number(inputs.fg_wh_chocolate_bay_spacing_m, " m")]
      );
    }

    if (fgType === "Bakery" || fgType === "Combo") {
      rows.push(
        ["Bakery Warehouse Length", number(inputs.fg_wh_bakery_length_m, " m")],
        ["Bakery Warehouse Width", number(inputs.fg_wh_bakery_width_m, " m")],
        ["Bakery Warehouse Height", number(inputs.fg_wh_bakery_height_m, " m")],
        ["Bakery Warehouse Built-up Area", area(inputs.fg_wh_bakery_length_m, inputs.fg_wh_bakery_width_m)],
        ["Optimize Bakery Warehouse Columns", yesNo(inputs.fg_wh_bakery_optimize_columns)],
        ["Bakery Warehouse Bay Spacing", number(inputs.fg_wh_bakery_bay_spacing_m, " m")]
      );
    }
  }

  // Structural and site conditions
  rows.push(
    ["Foundation Type", display(inputs.foundation_type)],
    ["Soil Type", display(inputs.sbc_soil_type)],
    ["Column Type", display(inputs.column_type)],
    ["Roof Type", display(inputs.roof_type)],
    ["Seismic Zone", display(inputs.seismic_zone)],
    ["Wind Zone", display(inputs.wind_zone)],
    ["Wind Speed", number(inputs.wind_speed_ms, " m/s")],
    ["Groundwater Table Depth", number(inputs.gwt_depth, " m")]
  );

  // Production details
  rows.push(
    ["Production Capacity", number(inputs.production_capacity_tpd, " tons/day")],
    ["Annual Output", number(inputs.annual_output_mt, " metric tons")]
  );

  // Utility scope
  if (hasComponent("Utilities Block")) {
    rows.push(["Selected Utilities", display(inputs.utility_scope)]);
  }

  // Chocolate process utilities
  if (/chocolate|combo/i.test(inputs.product_category || "")) {
    rows.push(
      ["Cooling Tunnel Load", number(inputs.cooling_tunnel_load_tr, " TR")],
      ["Humidity Control Minimum", number(inputs.humidity_controlled_min_pct, "%")],
      ["Humidity Control Maximum", number(inputs.humidity_controlled_max_pct, "%")],
      ["Chocolate Storage Temperature", number(inputs.chocolate_storage_temp_c, " °C")],
      ["Process Hot Water Demand", number(inputs.process_hot_water_lph, " LPH")]
    );
  }

  // Bakery process utilities
  if (/bakery|biscuit|wafer|cookie|combo/i.test(inputs.product_category || "")) {
    rows.push(
      ["Oven Capacity", number(inputs.oven_capacity_kg_hr, " kg/hr")],
      ["Fuel Type", display(inputs.fuel_type)],
      ["Baking Line Quantity", display(inputs.baking_line_qty)],
      ["Compressed Air Demand", number(inputs.compressed_air_demand_cfm, " CFM")],
      ["Cooling Conveyor Load", number(inputs.cooling_conveyor_load)],
      ["Dust Collection Required", yesNo(inputs.dust_collection_required)]
    );
  }

  // Process complexity
  rows.push(
    ["Explosion Risk", yesNo(complexity.explosion_risk)],
    ["Utility Redundancy", yesNo(complexity.utility_redundancy)]
  );

  // External works
  rows.push(
    ["Roads Included", yesNo(inputs.include_roads)],
    ["Landscaping Included", yesNo(inputs.include_landscaping)],
    ["Fence Included", yesNo(inputs.include_fence)]
  );

  // Site inputs
  rows.push(
    ["Water Availability", display(inputs.water_availability)],
    ["Electrical Grid Reliability", display(inputs.grid_reliability)],
    ["Ambient Temperature Range", display(inputs.ambient_temp_range)],
    ["Relative Humidity", number(inputs.relative_humidity_pct, "%")]
  );

  // Site complexity - not shown for Warehouse
  if (!isWarehouse) {
    rows.push(
      ["Remote Site", yesNo(complexity.remote_site)],
      ["Brownfield Site", yesNo(complexity.brownfield)],
      ["High Floor Load", yesNo(complexity.high_floor_load)]
    );
  }

  // Contingency
  rows.push(["Contingency Percentage", number(inputs.contingency_pct, "%")]);

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm w-full">
      <h3 className="text-sm font-semibold text-slate-800 mb-3">
        Project Summary
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1.5">
        {rows.map(([label, value]) => (
          <div
            key={label}
            className="flex items-start text-xs py-1 border-b border-slate-100"
          >
            <div className="text-slate-500 w-[46%] flex-shrink-0 pr-2">
              {label}
            </div>

            <div className="text-slate-500 mr-2">:</div>

            <div className="text-slate-800 font-medium flex-1 break-words">
              {value ?? "—"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}


export function AssumptionsBox({ items }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
        Key Assumptions
      </h3>

      <ul className="space-y-2">
        {items.map((t, i) => (
          <li
            key={i}
            className="flex items-start gap-2 text-[13px] text-slate-700"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RisksBox({ items }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
        Risk & Cost Drivers
      </h3>

      <ul className="space-y-2">
        {items.map((t, i) => (
          <li
            key={i}
            className="flex items-start gap-2 text-[13px] text-slate-700"
          >
            <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function OptimizationsBox({ items }) {
  if (!items?.length) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-800 mb-3 font-['Manrope']">
        Optimization Suggestions
      </h3>

      <ul className="space-y-2">
        {items.map((t, i) => (
          <li
            key={i}
            className="flex items-start gap-2 text-[13px] text-slate-700"
          >
            <Lightbulb className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Empty({ text }) {
  return (
    <div className="text-sm text-slate-500 p-6 bg-white rounded-lg border border-slate-200">
      {text}
    </div>
  );
}
