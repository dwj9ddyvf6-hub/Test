type Row = Record<string, unknown>;
const row = (v: unknown): Row => v && typeof v === 'object' && !Array.isArray(v) ? v as Row : {};
const rows = (v: unknown): Row[] => Array.isArray(v) ? v.map(row) : [];
const text = (v: unknown) => v == null ? '—' : String(v);
const amount = (v: unknown) => (typeof v !== 'number' && typeof v !== 'string') || (typeof v === 'string' && !v.trim()) || !Number.isFinite(Number(v)) ? '—' : Number(v).toLocaleString(undefined, {maximumFractionDigits: 2});

export default function ProspectiveSleeves({data}: {data: unknown}) {
  const source = row(data);
  const groups = [
    ['native', 'Native cryptocurrency paper books', 'USD'],
    ['public_recipes', 'Public recipe paper books', 'USDT'],
  ];
  const originals = row(source.original_research);
  return <section className="panel"><div className="panel-heading"><div><h2>Prospective research and paper execution</h2><p>Each book has independent virtual capital. Forward results accumulate from actual observations.</p></div></div>
    {groups.map(([key, title, currency]) => {
      const component = row(source[key]);
      const books = rows(component.books);
      const worker = row(component.worker);
      const active = worker.running ?? worker.active;
      const workerStatus = active === true ? 'Running' : active === false ? 'Stopped' : 'Health unobserved';
      return <div key={key} className="study-card"><h3>{title}</h3><p>{workerStatus} · {text(component.status || (component.installed ? 'Installed' : component.installed === false ? 'Not installed' : 'Unobserved'))}</p>
        {books.length > 0 && <div className="table-scroll"><table><thead><tr><th>Strategy</th><th>Entries</th><th>Cash</th><th>Observed equity</th><th>Net P&amp;L</th><th>Position</th><th>Latest decision</th></tr></thead><tbody>{books.map(book => {
          const cycle = row(book.latest_cycle);
          const position = book.positions ?? book.position;
          const markCurrency = text(book.mark_currency ?? currency);
          const markDate = book.mark_as_of ? `${text(book.mark_as_of)} · ${book.mark_fresh ? 'Fresh' : 'Dated'}` : text(book.mark_status);
          return <tr key={text(book.sleeve ?? book.id)}><td>{text(book.sleeve ?? book.strategy)}</td><td>{book.enabled === true ? 'Enabled' : book.enabled === false ? 'Paused' : 'Unobserved'}</td><td>{amount(book.cash)} {currency}</td><td title={text(book.observed_mark_scope)}>{amount(book.observed_marked_equity)} {markCurrency}<small style={{display: 'block'}}>{markDate}</small></td><td>{amount(book.net_pnl)} {markCurrency}</td><td>{position == null ? 'Flat' : JSON.stringify(position)}</td><td>{text(cycle.status ?? book.last_received_at)}</td></tr>;
        })}</tbody></table></div>}
      </div>;
    })}
    <div className="study-card"><h3>Original strategy research pilots</h3><p>{text(originals.status || (originals.installed ? 'Collecting evidence' : 'Not installed'))}. New source receipts and future outcomes qualify the original hypotheses.</p></div>
  </section>;
}
