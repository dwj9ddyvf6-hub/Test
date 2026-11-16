// Intl formatters own native ICU allocations, outside the JavaScript heap.
// Reuse them across bars and symbols; bound retention across venue options.
const formatters = new Map();
const MAX_FORMATTERS = 64;

export function tensorDateFormatter(locale, options) {
  const key = JSON.stringify([locale, Object.entries(options).sort(([a], [b]) => a.localeCompare(b))]);
  let formatter = formatters.get(key);
  if (formatter) return formatter;
  // Preserve Intl's validation/fallback behavior: failed constructors are not cached.
  formatter = new Intl.DateTimeFormat(locale, options);
  if (formatters.size >= MAX_FORMATTERS) {
    formatters.delete(formatters.keys().next().value);
  }
  formatters.set(key, formatter);
  return formatter;
}
