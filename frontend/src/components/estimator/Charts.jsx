import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from "recharts";
import { TID } from "@/constants/testIds";
import { fmtMoney, fmtNumber } from "@/lib/format";

const DONUT_COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#64748B"];
const LINE_COLORS = { base: "#2563EB", current: "#10B981", benchmark: "#F59E0B" };


export function DonutChart({ data, currency, fxRates, total }) {
  return (
    <div
      data-testid={TID.donut}
      className="min-w-0 w-full bg-white border border-slate-200 rounded-lg p-4 sm:p-5 shadow-sm"
    >
      <h3 className="text-sm font-semibold text-slate-800 font-['Manrope'] mb-4">
        Cost Breakdown (% of Total Cost)
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] items-center gap-4">
        {/* Donut chart */}
        <div className="relative w-full min-w-0 h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                innerRadius={55}
                outerRadius={85}
                paddingAngle={2}
                stroke="#fff"
                strokeWidth={2}
              >
                {data.map((_, i) => (
                  <Cell
                    key={i}
                    fill={DONUT_COLORS[i % DONUT_COLORS.length]}
                  />
                ))}
              </Pie>

              <Tooltip
                contentStyle={{
                  background: "#fff",
                  border: "1px solid #e2e8f0",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(v) => fmtMoney(v, currency, fxRates)}
              />
            </PieChart>
          </ResponsiveContainer>

          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <div className="text-[10px] text-slate-500 uppercase tracking-wider">
              {currency}
            </div>
            <div className="text-base sm:text-lg font-extrabold text-slate-900 font-['Manrope']">
              {fmtMoney(total, currency, fxRates, { compact: true })}
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="min-w-0 w-full space-y-3">
          {data.map((row, i) => (
            <div
              key={row.name}
              className="grid grid-cols-[10px_minmax(0,1fr)_auto] items-start gap-2 text-xs sm:text-[13px]"
            >
              <span
                className="mt-1 w-2.5 h-2.5 rounded-sm"
                style={{
                  background: DONUT_COLORS[i % DONUT_COLORS.length],
                }}
              />

              <span className="min-w-0 whitespace-normal break-words leading-5 text-slate-700">
                {row.name}
              </span>

              <span className="whitespace-nowrap text-right text-slate-900 font-semibold tabular-nums">
                {row.pct}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function TrendChart({ data, currency, fxRates }) {
  const tooltipFmt = (v) => fmtMoney(v, currency, fxRates, { compact: true });
  return (
    <div data-testid={TID.line} className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-800 font-['Manrope']">Cost Trend ({currency})</h3>
        <div className="text-xs text-slate-500 border border-slate-200 rounded px-2 py-1">Monthly</div>
      </div>
      <div className="h-[240px]">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#f1f5f9" vertical={false} />
            <XAxis dataKey="period" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false}
              tickFormatter={(v) => fmtMoney(v, currency, fxRates, { compact: true })} />
            <Tooltip formatter={tooltipFmt}
              contentStyle={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 12 }} />
            <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
            <Line type="monotone" dataKey="base" name="Base Cost" stroke={LINE_COLORS.base} strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="current" name="Current Estimate" stroke={LINE_COLORS.current} strokeWidth={2} dot={{ r: 3 }} />
            <Line type="monotone" dataKey="benchmark" name="Benchmark" stroke={LINE_COLORS.benchmark} strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
