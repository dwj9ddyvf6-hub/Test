export function parseCsv(source) {
  const input = String(source).replace(/^\uFEFF/, '');
  const records = [];
  let record = [];
  let field = '';
  let quoted = false;

  for (let i = 0; i < input.length; i++) {
    const char = input[i];
    if (quoted) {
      if (char === '"' && input[i + 1] === '"') {
        field += '"';
        i++;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
      continue;
    }
    if (char === '"' && field.length === 0) {
      quoted = true;
    } else if (char === ',') {
      record.push(field);
      field = '';
    } else if (char === '\r' || char === '\n') {
      if (char === '\r' && input[i + 1] === '\n') i++;
      record.push(field);
      if (record.some(value => value !== '')) records.push(record);
      record = [];
      field = '';
    } else {
      field += char;
    }
  }
  if (quoted) throw new Error('CSV contains an unterminated quoted field.');
  if (field.length || record.length) {
    record.push(field);
    if (record.some(value => value !== '')) records.push(record);
  }

  if (!records.length) return [];
  const headers = records.shift();
  return records.map((values, index) => {
    if (values.length !== headers.length) throw new Error(`CSV row ${index + 2} has ${values.length} fields; expected ${headers.length}.`);
    return Object.fromEntries(headers.map((header, column) => [header, values[column]]));
  });
}

export function serializeCsv(rows, headers = Object.keys(rows[0] || {}), { quoteAll = false, quoteNonEmpty = false, quoteHeaders = false, quoteEmptyFields = [], lineEnding = '\r\n' } = {}) {
  const encode = (value, quoteEmpty = false) => {
    const text = value == null ? '' : String(value);
    return quoteAll || (quoteNonEmpty && text.length > 0) || (quoteEmpty && text.length === 0) || /[",\r\n]/.test(text)
      ? `"${text.replaceAll('"', '""')}"`
      : text;
  };
  const headerRow = headers.map(header => quoteHeaders ? encode(header) : header).join(',');
  const emptyFields = new Set(quoteEmptyFields);
  return [headerRow, ...rows.map(row => headers.map(header => encode(row[header], emptyFields.has(header))).join(','))].join(lineEnding) + lineEnding;
}
