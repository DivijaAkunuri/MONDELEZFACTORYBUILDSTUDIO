
export const CURRENCY_SYMBOLS = {
  USD: "$",
};

export function fmtMoney(usdAmount, currency = "USD", fxRates = {}, opts = {}) {
  const compact = opts?.compact ?? false;
  const digits = opts?.digits ?? (compact ? 2 : 0);

  const formatter = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    notation: compact ? "compact" : "standard",
  });

  return `$${formatter.format(usdAmount ?? 0)}`;
}

export function fmtNumber(v, digits = 0) {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(v ?? 0);
}
