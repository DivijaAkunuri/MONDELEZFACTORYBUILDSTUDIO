export const CURRENCY_SYMBOLS = {
  USD: "$", EUR: "€", GBP: "£", INR: "₹", JPY: "¥", AUD: "A$", CAD: "C$",
  CHF: "CHF ", CNY: "¥", SGD: "S$", AED: "د.إ ", ZAR: "R", BRL: "R$", MXN: "Mex$",
};

export function fmtMoney(usdAmount, currency = "USD", fxRates = {}, opts = {}) {
  const rate = fxRates?.[currency] ?? 1;
  const val = usdAmount * rate;
  const compact = opts.compact ?? false;
  const digits = opts.digits ?? (compact ? 2 : 0);
  const symbol = CURRENCY_SYMBOLS[currency] || currency + " ";
  const formatter = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
    notation: compact ? "compact" : "standard",
  });
  return `${symbol}${formatter.format(val)}`;
}

export function fmtNumber(v, digits = 0) {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits, maximumFractionDigits: digits,
  }).format(v ?? 0);
}
