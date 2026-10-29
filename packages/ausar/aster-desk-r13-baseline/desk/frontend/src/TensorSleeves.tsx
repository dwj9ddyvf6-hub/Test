import {ChevronDown, Layers3, Pause, Play, RefreshCw} from 'lucide-react';

type Row = Record<string, unknown>;
type Props = {
  data?: Row;
  trading: Row;
  busy: boolean;
  action: (path: string, payload?: unknown, method?: string) => Promise<boolean>;
  bookId?: string;
};

const object = (value: unknown): Row => value !== null && typeof value === 'object' && !Array.isArray(value) ? value as Row : {};
const records = (value: unknown): Row[] => Array.isArray(value) ? value.map(object) : [];
const text = (value: unknown) => value == null ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value);
const number = (value: unknown): number | null => value == null || value === '' || !Number.isFinite(Number(value)) ? null : Number(value);
const cash = (value: unknown) => number(value) == null ? '—' : new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'}).format(number(value)!);
const date = (value: unknown, milliseconds = false) => {
  if (value == null || value === '') return 'Not yet';
  const stamp = milliseconds ? new Date(Number(value)) : new Date(String(value));
  return Number.isNaN(stamp.getTime()) ? 'Unavailable' : stamp.toLocaleString(undefined, {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'});
};

const RULES: Record<string, {title: string; frame: string; selection: string; ranking: string}> = {
  H1STATE: {
    title: 'Hourly Tensor state repair', frame: 'Hourly · 20 native bars',
    selection: 'At least 234 native bars, price ≥ $5, positive ATR14 and mean 20-bar dollar volume ≥ $1m. Seven endpoint votes; net bullish balance improves by at least 2 over three bars, with at least two improving channels.',
    ranking: 'Rank by balance repair + 0.01 × current balance + 0.001 × clipped OBV slope / volume; break ties by symbol. A candidate consumes its 20-bar cooldown even when entry is denied.',
  },
  WSTATE: {
    title: 'Weekly Tensor state repair', frame: 'Weekly · 20 native bars',
    selection: 'The same frozen state-repair test on completed weekly bars: seven endpoint votes, three-bar balance repair ≥ 2 and at least two improving channels. Weekly liquidity is measured on weekly bars.',
    ranking: 'Rank by balance repair + 0.01 × current balance + 0.001 × clipped OBV slope / volume; break ties by symbol. A candidate consumes its 20-bar cooldown even when entry is denied.',
  },
  D20PV: {
    title: 'Daily20 price / volume', frame: 'Daily · 20 native bars',
    selection: 'Use the frozen six-feature price/volume model, medians and training threshold. Select predicted net QQQ excess ≥ 0.006985566706545021 on the original symbol-specific 20-bar phase.',
    ranking: 'Rank by predicted net QQQ excess, then symbol. Preserve the original history anchor and native bar numbering; no refitting or phase reset.',
  },
  D20TENSOR: {
    title: 'Daily20 Tensor augmented', frame: 'Daily · 20 native bars',
    selection: 'Use the frozen six price/volume plus 29 Tensor features, medians and training threshold. Select predicted net QQQ excess ≥ 0.006122960477423353 on the original symbol-specific 20-bar phase.',
    ranking: 'Rank by predicted net QQQ excess, then symbol. Preserve the original history anchor and native bar numbering; no refitting or phase reset.',
  },
};

function Status({value, tone = ''}: {value: string; tone?: string}) {
  return <span className={`badge ${tone ? `badge-${tone}` : ''}`}><span className="badge-dot" />{value}</span>;
}

export default function TensorSleeves({data, trading, busy, action, bookId}: Props) {
  const installations = records(data?.installations).filter(item => !bookId || item.book_id === bookId);
  const books = records(trading.books), positions = records(trading.positions), decisions = records(data?.decisions);
  if (bookId && !installations.length) return null;
  return <section className="panel tensor-sleeves" aria-label="Executable paper strategy sleeves">
    <div className="panel-heading"><div><h2>{bookId ? 'Strategy for this paper book' : 'Executable paper sleeves'}</h2><p>Independent cash books · deterministic rules · local paper execution</p></div>
      {installations.length > 0 && <button className="button button-secondary button-small" disabled={busy} onClick={() => void action('/strategies/run')}><RefreshCw size={14} /> Run strategy pass</button>}
    </div>
    {!installations.length ? <div className="empty"><span className="empty-icon"><Layers3 size={25} /></span><h3>No strategy sleeves installed</h3><p>Strategy definitions remain available without funding or creating orders. An explicit installation assigns each sleeve its own local paper book.</p></div> : <>
      <p className="tensor-sleeves-note">Target: outperform QQQ and SPY after costs. Forward results require actual fills and comparable benchmark coverage. Entries require each sleeve’s full data policy, fresh eligible quotes and settled cash.</p>
      <div className="tensor-sleeve-grid">{installations.map(installation => {
        const config = object(installation.config), readiness = object(installation.readiness), assessment = object(readiness.entry_eligibility), census = object(assessment.census);
        const sleeve = text(installation.sleeve), isTensor = installation.family === 'tensor' || (installation.family == null && sleeve in RULES);
        const metadata = object(installation.rule_metadata || config.rule_metadata), ruleConfig = object(config.rule_config);
        const cycle = readiness.cycle ? object(readiness.cycle) : {
          origin_ms: assessment.origin_ms, next_open_ms: assessment.next_open_ms, expires_ms: assessment.expires_ms,
          cursor: census.attempted, status: census.complete === true ? 'last_assessment_complete' : 'awaiting_assessment', updated_at: assessment.assessed_at,
        };
        const rule = isTensor ? RULES[sleeve] : {
          title: text(metadata.title || metadata.name || config.name || config.rule_id || sleeve),
          frame: metadata.frame === '1d' ? `Daily · up to ${text(config.max_hold_bars || metadata.max_hold_bars)} bars` : text(metadata.frame || `${text(config.frame)} · public rule reconstruction`),
          selection: text(ruleConfig.entry || metadata.selection || 'Evaluate the pinned public rule on completed, observed source bars. Read the exact rule configuration and provenance below.'),
          ranking: text(metadata.ranking || 'Use the pinned deterministic ranking and symbol tie break.'),
        };
        const book = books.find(item => item.id === installation.book_id), account = object(book?.account), policy = object(book?.policy);
        const held = positions.filter(position => position.book_id === installation.book_id && (number(position.quantity) ?? 0) !== 0);
        const latest = decisions.find(decision => decision.installation_id === installation.id);
        const count = number(readiness.enrollment_count), covered = number(readiness.native_coverage), cursor = number(cycle.cursor);
        const enabled = installation.enabled === true, ready = readiness.status === 'ready';
        const expires = number(cycle.expires_ms), expired = expires != null && Date.now() >= expires;
        const missing = number(account.missing_marks) ?? 0, stale = number(account.stale_marks) ?? 0;
        const failedReads = records(readiness.failed_reads), coverageErrors = records(readiness.coverage).filter(row => row.status === 'failed');
        const errors = failedReads.length ? failedReads : records(readiness.errors).length ? records(readiness.errors) : coverageErrors;
        const failedCount = Array.isArray(readiness.failed_reads) ? readiness.failed_reads.length : number(readiness.failed_reads);
        const latestError = readiness.error || readiness.last_error;
        const pinned = {installation_id: installation.id, sleeve, book_id: installation.book_id,
          config_sha256: installation.config_sha256, universe_file: config.universe_file,
          universe_sha256: config.universe_sha256, source_manifest_sha256: config.source_manifest_sha256,
          seed_directory: config.seed_directory, opening_window_seconds: config.opening_window_seconds,
          hold_native_bars: config.hold_native_bars, maximum_slots: config.maximum_slots,
          family: installation.family, rule_id: config.rule_id, rules_sha256: config.rules_sha256,
          rule_source_sha256: config.rule_source_sha256, rule_definition_sha256: config.rule_definition_sha256,
          rule_config: config.rule_config, rule_metadata: metadata, source_provenance: config.source_provenance,
          book_policy_sha256: book?.policy_hash, local_execution_policy: {
            fees_per_order: policy.fees_per_order, slippage_bps: policy.slippage_bps,
            allow_short: policy.allow_short, halted: policy.halted}};
        return <article className="tensor-sleeve-card" key={text(installation.id)}>
          <div className="tensor-sleeve-heading"><div><span className="eyebrow">{rule?.frame || text(config.frame)}</span><h3>{rule?.title || sleeve}</h3><small>{text(book?.name || installation.book_id)}</small></div><Status value={enabled ? 'Entries enabled' : 'Entries paused'} tone={enabled ? 'enabled' : 'warning'} /></div>
          <div className="tensor-sleeve-account"><div><span>Paper equity</span><strong className="mono">{cash(account.equity)}</strong></div><div><span>Available settled cash</span><strong className="mono">{cash(account.available_cash)}</strong></div><div><span>Unsettled proceeds</span><strong className="mono">{cash(account.unsettled_cash)}</strong></div><div><span>Positions / pending intents</span><strong className="mono">{held.length} / {text(installation.pending_intents)}</strong></div></div>
          {(missing > 0 || stale > 0) && <p className="tensor-sleeve-warning">Valuation coverage: {missing} missing marks · {stale} stale marks.</p>}
          {policy.halted === true && <p className="tensor-sleeve-warning">Book entry policy is halted{policy.halt_reason ? `: ${text(policy.halt_reason)}` : '.'}</p>}
          {held.length > 0 && <p className="tensor-sleeve-warning">Held basket: {held.map(position => text(position.symbol)).join(', ')}</p>}
          <div className="tensor-sleeve-readiness"><Status value={ready ? isTensor ? 'Native cycle complete' : 'Source histories ready' : 'Awaiting complete native cycle'} tone={ready ? 'enabled' : 'warning'} /><p>{covered ?? '—'} / {count ?? '—'} native histories ready · {cursor ?? 0} / {count ?? '—'} symbols scanned in {isTensor ? 'this cycle' : 'last assessment'}</p><progress aria-label={`${rule?.title || sleeve} native history coverage`} value={covered ?? 0} max={count && count > 0 ? count : 1} /><small>Signal origin {date(cycle.origin_ms, true)}{expires != null && <> · {expired ? 'Entry window closed' : 'Entry deadline'} {date(expires, true)}</>}</small><small>Cycle state: {text(cycle.status || 'not started').replaceAll('_', ' ')} · Updated {date(cycle.updated_at)}</small></div>
          {((failedCount ?? 0) > 0 || errors.length > 0 || Boolean(latestError)) && <div className="tensor-sleeve-warning" role="note"><p>{failedCount ?? errors.length} failed data reads{latestError ? ` · ${text(latestError)}` : ''}</p>{errors.slice(0, 5).map((error, index) => <p key={`${text(error.symbol)}-${index}`}>{error.symbol ? `${text(error.symbol)}: ` : ''}{text(error.error || error.reason || error.message || 'Data evidence unavailable')}</p>)}</div>}
          <div className="tensor-sleeve-decision"><span>Latest recorded decision</span>{latest ? <><strong>{text(latest.symbol)} · {text(latest.role)} · {text(latest.status).replaceAll('_', ' ')}</strong><p>{text(latest.reason).replaceAll('_', ' ')}</p><small>{date(latest.created_at)}</small></> : <p>No decisions recorded for this sleeve.</p>}</div>
          <div className="tensor-sleeve-actions"><button className="button button-secondary button-small" disabled={busy} onClick={() => void action(`/strategies/${encodeURIComponent(text(installation.id))}`, {enabled: !enabled}, 'PATCH')}>{enabled ? <Pause size={14} /> : <Play size={14} />}{enabled ? 'Pause new entries' : 'Enable new entries'}</button><small>Owned exits continue when entries are paused.</small></div>
          <details className="receipt tensor-sleeve-rules"><summary>Selection, sizing and execution rules <ChevronDown size={14} /></summary><div><p>{rule?.selection || 'Read the pinned installation policy below.'}</p><p>{rule?.ranking}</p>{isTensor ? <><p>Tensor sleeves require a ready native engine, at least 234 bars, price ≥ $5, positive ATR14 and mean 20-bar native dollar volume ≥ $1m. Selection uses the pinned enrollment; SPY, QQQ, B and GOLD are excluded.</p><p>At most 10 positions including pending buys. Each whole-share entry, including costs, is capped at 10% of book equity, 1% of mean 20-bar native dollar volume, and available settled cash.</p><p>Enter only at the next eligible native opening within the configured window; expired opportunities are skipped. Exit after 20 observed native bars from the actual filled entry.</p></> : <><p>{text(metadata.sizing || installation.sizing || 'Whole shares only, capped by the pinned equity/liquidity budgets and available settled cash. Pending entries reserve slots and cash; sale proceeds follow the desk’s T+1 paper convention.')}</p><p>{text(metadata.entry || 'Enter only inside the pinned next-opening window using a fresh observed quote; expired opportunities are skipped.')}</p><p>{text(metadata.exit || 'Exit according to the pinned public rule. Entry pause preserves owned exit obligations and existing positions.')}</p><p>A public reconstruction is distinct from verified access to a private strategy implementation.</p></>}<p>Quote paper fills can differ from an ideal opening-price backtest.</p></div></details>
          <details className="receipt"><summary>Installation and decision receipts <ChevronDown size={14} /></summary><pre>{JSON.stringify({installation: pinned, readiness, latest_decision: latest || null, execution: installation.execution}, null, 2)}</pre></details>
        </article>;
      })}</div>
    </>}
  </section>;
}
