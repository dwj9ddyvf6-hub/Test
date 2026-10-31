// Safe generic CSV parser extracted from convergence-engine.mjs. Internal survivor and vendor crosswalk catalogs are deliberately not included.
export const MAX_EVIDENCE_CSV_BYTES = 10 * 1024 * 1024;
export const MAX_EVIDENCE_CSV_ROWS = 50000;
const REQUIRED = ["ObservedAt", "Entity", "Source", "Metric", "Value"];
const OPTIONAL = ["PublicAt", "ReceivedAt", "Unit", "Method", "Confidence", "EventType", "SourceURL"];
const FIELDS = [...REQUIRED, ...OPTIONAL];
const normalizeHeader = (value) => String(value ?? "").replace(/^\uFEFF/, "").trim().toLowerCase().replace(/[\s_-]+/g, "");
const HEADER_LOOKUP = new Map(FIELDS.map((field) => [normalizeHeader(field), field]));

function parseRows(input) {
  const text = String(input ?? "");
  if (new TextEncoder().encode(text).byteLength > MAX_EVIDENCE_CSV_BYTES) throw new RangeError("CSV exceeds the 10 MiB local import limit.");
  const rows = [];
  let row = [], field = "", quoted = false, afterQuote = false, line = 1, rowLine = 1;
  const pushField = () => { row.push(field); field = ""; afterQuote = false; };
  const pushRow = () => { pushField(); rows.push({ line: rowLine, values: row }); row = []; rowLine = line + 1; if (rows.length > MAX_EVIDENCE_CSV_ROWS + 1) throw new RangeError("CSV exceeds the 50,000-row local import limit."); };
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (ch === '"') { quoted = false; afterQuote = true; }
      else { field += ch; if (ch === "\n") line += 1; else if (ch === "\r" && text[i + 1] !== "\n") line += 1; }
      continue;
    }
    if (afterQuote) {
      if (ch === ",") { pushField(); continue; }
      if (ch === "\r" || ch === "\n") { if (ch === "\r" && text[i + 1] === "\n") i += 1; line += 1; pushRow(); rowLine = line; continue; }
      if (ch === " " || ch === "\t") continue;
      throw new SyntaxError(`Unexpected character after a quoted field on line ${line}.`);
    }
    if (ch === '"') { if (field.length) throw new SyntaxError(`Quote inside an unquoted field on line ${line}.`); quoted = true; continue; }
    if (ch === ",") { pushField(); continue; }
    if (ch === "\r" || ch === "\n") { if (ch === "\r" && text[i + 1] === "\n") i += 1; line += 1; pushRow(); rowLine = line; continue; }
    field += ch;
  }
  if (quoted) throw new SyntaxError("CSV ends inside a quoted field.");
  if (field.length || row.length || afterQuote) pushRow();
  return rows;
}

export function parseEvidenceCsv(input) {
  const parsed = parseRows(input);
  if (!parsed.length) throw new Error("CSV is empty.");
  const headerCells = parsed[0].values.map((x) => String(x).replace(/^\uFEFF/, "").trim());
  const headers = headerCells.map((x) => HEADER_LOOKUP.get(normalizeHeader(x)) || null);
  if (headers.some((x) => x === null)) throw new Error("CSV has an unrecognized column. Use the documented template headers.");
  if (new Set(headers).size !== headers.length) throw new Error("CSV contains duplicate column names.");
  const absent = REQUIRED.filter((field) => !headers.includes(field));
  if (absent.length) throw new Error(`CSV is missing required columns: ${absent.join(", ")}.`);
  const index = new Map(headers.map((field, i) => [field, i]));
  const records = [], rejected = [];
  for (const parsedRow of parsed.slice(1)) {
    const values = parsedRow.values;
    if (values.every((value) => String(value ?? "").trim() === "")) continue;
    const record = { rowNumber: parsedRow.line };
    for (const field of headers) record[field] = String(values[index.get(field)] ?? "");
    let reason = "";
    for (const required of REQUIRED) if (!record[required].trim()) { reason = `${required} is required`; break; }
    if (!reason && !Number.isFinite(Date.parse(record.ObservedAt))) reason = "ObservedAt must be a parseable date or timestamp";
    for (const clock of ["PublicAt", "ReceivedAt"]) if (!reason && record[clock]?.trim() && !Number.isFinite(Date.parse(record[clock]))) reason = `${clock} must be a parseable date or timestamp when supplied`;
    if (!reason && record.SourceURL?.trim()) { try { const url = new URL(record.SourceURL.trim()); if (!["https:", "http:"].includes(url.protocol)) reason = "SourceURL must use HTTP or HTTPS"; } catch { reason = "SourceURL must be a valid HTTP or HTTPS URL"; } }
    const oversized = FIELDS.find((field) => (record[field] ?? "").length > 8192);
    if (!reason && oversized) reason = `${oversized} exceeds the 8,192-character field limit`;
    if (values.length > headers.length && values.slice(headers.length).some((value) => String(value).trim())) reason ||= "Row contains extra values beyond the header columns";
    if (reason) rejected.push({ rowNumber: parsedRow.line, reason }); else records.push(record);
  }
  return { headers, records, rejected, acceptedCount: records.length, rejectedCount: rejected.length, totalRows: records.length + rejected.length };
}

