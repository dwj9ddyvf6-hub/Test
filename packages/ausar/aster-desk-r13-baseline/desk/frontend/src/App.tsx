import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';
import {
  Activity, Archive, ArrowDownLeft, ArrowRight, ArrowUpRight, BookOpen, Check, CheckCircle2,
  ChevronDown, Circle, ClipboardList, Clock3, Database, Download, FileText, Layers3,
  LayoutDashboard, LoaderCircle, Menu, MoreHorizontal, Pause, Play, Plus, RefreshCw,
  Search, Settings2, ShieldCheck, Sparkles, Trash2, Users, Wallet, X, type LucideIcon,
} from 'lucide-react';
import { api } from './api';
import Autonomy from './Autonomy';
import type { Agent, DeskSnapshot, Order, Task, TaskKind } from './types';

type Section = 'overview' | 'legacy_overview' | 'books' | 'market' | 'inbox' | 'research' | 'operations' | 'agents' | 'tasks' | 'watchlist' | 'book' | 'journal' | 'controls';
type ModalKind = 'funding' | 'watchlist' | 'quote' | 'order' | 'task' | 'approve';
type ModalState = {kind: ModalKind; clientId: string; symbol?: string; taskKind?: TaskKind; order?: Order};
const navigation: {id: Section; label: string; icon: LucideIcon}[] = [
  {id:'overview',label:'Overview',icon:LayoutDashboard},
  {id:'books',label:'Books & orders',icon:Wallet},
  {id:'market',label:'Market workspace',icon:Layers3},
  {id:'agents',label:'Agent team',icon:Users},
  {id:'tasks',label:'Work queue',icon:ClipboardList},
  {id:'inbox',label:'Inbox & alerts',icon:BookOpen},
  {id:'research',label:'Research lab',icon:FileText},
  {id:'journal',label:'Journal',icon:Archive},
  {id:'operations',label:'Operations',icon:Activity},
  {id:'book',label:'Manual ledger',icon:ClipboardList},
  {id:'controls',label:'Brief controls',icon:Settings2},
];
const copy: Record<Section, {title: string; subtitle: string}> = {
  overview: {title: 'Your desk, always in focus.', subtitle: 'Independent books, supplied order intents and operations that continue without the browser.'},
  legacy_overview: {title:'Manual ledger overview',subtitle:'Separate operator-approved account and local tasks.'},
  books: {title:'Separate books. Clear ownership.',subtitle:'Authorize an intent; the background desk manages timing, execution, protection and reconciliation.'},
  market: {title:'Market data with provenance.',subtitle:'Configured feeds, historical bars, exchange sessions and actual quote timestamps.'},
  inbox: {title:'A shared channel for evidence.',subtitle:'Local agent handoffs, observed alerts and incident records.'},
  research: {title:'Evidence before conclusions.',subtitle:'Immutable study plans, source artifacts and explicit operational decisions.'},
  operations: {title:'The desk keeps working.',subtitle:'Unattended refresh, reconciliation, durable schedules and visible retry receipts.'},
  agents: {title: 'A team with clear responsibilities.', subtitle: 'Six operational agents. Every handoff leaves a record.'},
  tasks: {title: 'Good work has a paper trail.', subtitle: 'Follow queued work, agent steps and the results they produce.'},
  watchlist: {title: 'Data with a source.', subtitle: 'Your symbols and manually supplied quotes, with age and provenance.'},
  book: {title: 'The separate manual ledger.', subtitle: 'Fund the workspace, create an intent, then explicitly approve its fill.'},
  journal: {title: 'The desk remembers.', subtitle: 'A chronological record of actions, actors and outcomes.'},
  controls: {title: 'You set the pace.', subtitle: 'Runtime, data freshness and provider connections at a glance.'},
};
const agentIcons: Record<string, LucideIcon> = {
  coordinator: Sparkles, data_steward: Database, accountant: Wallet, risk_officer: ShieldCheck,
  execution_clerk: ClipboardList, archivist: Archive,
};
const workflow = ['data_steward', 'accountant', 'risk_officer', 'execution_clerk', 'coordinator', 'archivist'];
const taskLabels: Record<string, string> = {desk_brief: 'Desk brief', data_audit: 'Data audit', reconcile: 'Book reconciliation', research_note: 'Evidence note', operational_cycle: 'Operational cycle', desk_cycle: 'Operational cycle', cycle: 'Operational cycle'};
const currency = new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2});
const number = new Intl.NumberFormat('en-US', {maximumFractionDigits: 6});
const money = (value: number | null | undefined) => value == null ? '—' : currency.format(value);
const quantity = (value: number) => number.format(value);
const humanize = (value: string) => value.replaceAll('_', ' ');
function dateTime(value: string | null | undefined) {
  if (!value) return 'Not yet';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unknown date' : date.toLocaleString(undefined, {month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'});
}
function relative(value: string | null | undefined) {
  if (!value) return 'Not yet run';
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}
function localDateTime() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 19);
}

function Badge({status, children}: {status: string; children?: ReactNode}) {
  return <span className={`badge badge-${status}`}><span className="badge-dot" />{children || humanize(status)}</span>;
}
function Panel({title, subtitle, action, children, className = ''}: {title?: string; subtitle?: string; action?: ReactNode; children: ReactNode; className?: string}) {
  return <section className={`panel ${className}`}>
    {(title || action) && <div className="panel-heading"><div>{title && <h2>{title}</h2>}{subtitle && <p>{subtitle}</p>}</div>{action}</div>}
    {children}
  </section>;
}
function Empty({icon: Icon = Layers3, title, description, action}: {icon?: LucideIcon; title: string; description: string; action?: ReactNode}) {
  return <div className="empty"><span className="empty-icon"><Icon size={23} strokeWidth={1.6} /></span><h3>{title}</h3><p>{description}</p>{action}</div>;
}
function Metric({label, value, note, icon: Icon, highlight = false}: {label: string; value: string; note: string; icon: LucideIcon; highlight?: boolean}) {
  return <div className={`metric ${highlight ? 'metric-highlight' : ''}`}><div className="metric-label">{label}<Icon size={16} /></div><strong>{value}</strong><span>{note}</span></div>;
}
function IconButton({label, icon: Icon, onClick, disabled}: {label: string; icon: LucideIcon; onClick: () => void; disabled?: boolean}) {
  return <button className="icon-button" aria-label={label} title={label} onClick={onClick} disabled={disabled}><Icon size={16} /></button>;
}

export default function App() {
  const [section, setSection] = useState<Section>('overview');
  const [autonomousStatus,setAutonomousStatus]=useState<{running:boolean;worker_alive:boolean;healthy:boolean}|null>(null);
  const [desk, setDesk] = useState<DeskSnapshot | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [toast, setToast] = useState<{message: string; error?: boolean} | null>(null);
  const [modal, setModal] = useState<ModalState | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [taskFilter, setTaskFilter] = useState('all');
  const [journalSearch, setJournalSearch] = useState('');
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const refreshInFlight = useRef<Promise<void> | null>(null);
  const refreshGeneration = useRef(0);

  const refresh = useCallback(async (force = false) => {
    if (refreshInFlight.current) {
      if (!force) return refreshInFlight.current;
      await refreshInFlight.current;
    }
    const generation = ++refreshGeneration.current;
    const request = (async () => {
      try {
        const [deskResult, healthResult] = await Promise.allSettled([api<DeskSnapshot>('/desk'), api<Record<string, unknown>>('/health')]);
        if (generation !== refreshGeneration.current) return;
        if (healthResult.status === 'fulfilled') {
          const value = healthResult.value;
          const runtime = value.autonomy as {running:boolean;worker_alive:boolean;healthy:boolean};
          setHealth(value); setHealthError(null); setAutonomousStatus(runtime);
        } else {
          setHealthError(healthResult.reason instanceof Error ? healthResult.reason.message : 'Service health unavailable');
          setAutonomousStatus(null);
        }
        if (deskResult.status === 'rejected') throw deskResult.reason;
        setDesk(deskResult.value); setConnectionError(null); setLastRefresh(new Date());
      } catch (error) { if (generation === refreshGeneration.current) setConnectionError(error instanceof Error ? error.message : 'Unable to reach the desk'); }
    })();
    refreshInFlight.current = request;
    try {await request;} finally {if (refreshInFlight.current === request) refreshInFlight.current = null;}
  }, []);
  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => {if (!document.hidden) void refresh();}, 3000);
    const onVisible = () => {if (!document.hidden) void refresh();};
    document.addEventListener('visibilitychange', onVisible);
    return () => {window.clearInterval(timer); document.removeEventListener('visibilitychange', onVisible); ++refreshGeneration.current; refreshInFlight.current = null;};
  }, [refresh]);
  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 6000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  async function mutate(path: string, body: unknown, message: string, method = 'POST') {
    setBusy(path);
    try { await api(path, method, body); await refresh(true); setToast({message}); return true; }
    catch (error) { setToast({message: error instanceof Error ? error.message : 'Action failed', error: true}); return false; }
    finally { setBusy(null); }
  }
  function openModal(kind: ModalKind, extra: Partial<ModalState> = {}) {
    setModalError(null); setModal({kind, clientId: crypto.randomUUID(), ...extra});
  }
  async function runCycle() {await mutate('/runtime/cycle', {}, 'Operational cycle added to the work queue.');}
  async function runAgent(agent: Agent) {
    const kind: TaskKind | undefined = {coordinator: 'desk_brief', data_steward: 'data_audit', accountant: 'reconcile', archivist: 'research_note'}[agent.id] as TaskKind | undefined;
    if (kind === 'research_note') {openModal('task', {taskKind: kind}); return;}
    if (kind) await mutate('/tasks', {kind}, `${taskLabels[kind]} added to the work queue.`);
    else await runCycle();
  }
  async function submitModal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!modal) return;
    const values = new FormData(event.currentTarget);
    const get = (key: string) => String(values.get(key) || '').trim();
    let path = ''; let payload: unknown;
    if (modal.kind === 'funding') {path = '/account/funding'; payload = {amount: Number(get('amount')), client_id: modal.clientId};}
    else if (modal.kind === 'watchlist') {path = '/watchlist'; payload = {symbol: get('symbol').toUpperCase()};}
    else if (modal.kind === 'quote') {path = '/quotes'; payload = {symbol: get('symbol').toUpperCase(), price: Number(get('price')), as_of: new Date(get('as_of')).toISOString(), source: get('source')};}
    else if (modal.kind === 'order') {path = '/orders'; payload = {symbol: get('symbol').toUpperCase(), side: get('side'), quantity: Number(get('quantity')), type: 'market', client_id: modal.clientId};}
    else if (modal.kind === 'approve') {path = `/orders/${modal.order!.id}/approve`; payload = {};}
    else {path = '/tasks'; payload = {kind: get('kind'), title: get('title') || undefined, instructions: get('instructions') || undefined, symbol: get('symbol').toUpperCase() || undefined};}
    setBusy(path); setModalError(null);
    try {await api(path, 'POST', payload); await refresh(true); setModal(null); setToast({message: modal.kind === 'approve' ? 'Paper order approved. The book has been refreshed.' : modal.kind === 'order' ? 'Order intent created. Explicit approval is required to fill.' : modal.kind === 'task' ? 'Task queued. Follow its progress in the work queue.' : 'Saved to your desk.'});}
    catch (error) {setModalError(error instanceof Error ? error.message : 'Unable to save');}
    finally {setBusy(null);}
  }
  function navigate(id: Section) {setSection(id); setMobileOpen(false);}
  const activeTasks = desk?.tasks.filter(task => ['queued', 'running'].includes(task.status)) || [];
  const pendingOrders = desk?.orders.filter(order => order.status === 'pending_review') || [];
  const workingAgents = desk?.agents.filter(agent => agent.status === 'working').length || 0;
  const taskDetail = desk?.tasks.find(task => task.id === selectedTask);
  const operationLabel = !autonomousStatus ? (healthError ? 'Operations status unavailable' : 'Connecting operations')
    : !autonomousStatus.running ? 'Operations paused' : !autonomousStatus.worker_alive ? 'Operations unavailable'
    : autonomousStatus.healthy ? 'Operations on' : 'Operations degraded';

  return <div className="app-shell">
    {mobileOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
      <a className="brand" href="#" onClick={event => {event.preventDefault(); navigate('overview');}}><span className="brand-symbol"><Sparkles size={23} strokeWidth={1.8} /></span><span>Aster<span className="brand-desk">Desk</span></span></a>
      <div className="workspace-switch"><span className="workspace-avatar">A</span><div><strong>Personal workspace</strong><small>Paper environment</small></div><ChevronDown size={14} /></div>
      <span className="nav-label">WORKSPACE</span>
      <nav aria-label="Main navigation">{navigation.map(item => <button key={item.id} className={`nav-item ${section === item.id ? 'active' : ''}`} onClick={() => navigate(item.id)} aria-current={section === item.id ? 'page' : undefined}><item.icon size={18} strokeWidth={1.7} /><span>{item.label}</span>{item.id === 'tasks' && activeTasks.length > 0 && <span className="nav-count">{activeTasks.length}</span>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-note"><span className="small-orbit"><ShieldCheck size={19} /></span><strong>Built for oversight.</strong><p>You authorize order intents. The desk maintains execution and the evidence trail.</p><button onClick={() => navigate('controls')}>Workspace controls <ArrowRight size={14} /></button></div><div className="sidebar-user"><div className="user-avatar">OP</div><div><strong>Desk operator</strong><small>Local workspace</small></div><MoreHorizontal size={17} /></div></div>
    </aside>
    <div className="workspace-main">
      <header className="topbar"><div className="topbar-left"><IconButton label="Open navigation" icon={Menu} onClick={() => setMobileOpen(true)} /><span>Workspace</span><span className="crumb-slash">/</span><strong>{navigation.find(item => item.id === section)?.label}</strong></div><div className="topbar-status"><span className="paper-chip"><Circle size={8} fill="currentColor" /> Paper mode</span><span className={`worker-chip ${connectionError || (autonomousStatus?.running && !autonomousStatus.worker_alive) ? 'offline' : autonomousStatus?.running ? 'running' : ''}`}><span />{connectionError ? 'Desk unreachable' : operationLabel}</span><span className="local-operations-chip">Local operations</span><span className="strategy-chip">{desk ? desk.desk.strategy_count : '—'} strategies</span><IconButton label="Refresh desk" icon={RefreshCw} onClick={() => void refresh()} /></div></header>
      <main>
        <div className="page-heading"><div><div className="eyebrow">{section === 'overview' ? 'YOUR WORKSPACE' : navigation.find(item => item.id === section)?.label.toUpperCase()}</div><h1>{copy[section].title}</h1><p>{copy[section].subtitle}</p></div><div className="heading-actions"><button className="button button-primary" onClick={() => openModal('task')} disabled={!desk}><Plus size={16} /> New task</button></div></div>
        {connectionError && <div className="notice notice-error" role="alert"><Activity size={18} /><div><strong>Desk connection interrupted</strong><p>{connectionError}{desk ? ' · Showing the last received snapshot.' : ' · Start the local backend, then refresh.'}</p></div><button className="button button-small button-ghost" onClick={() => void refresh()}>Retry</button></div>}
        {!desk ? <Panel><Empty icon={connectionError ? Activity : LoaderCircle} title={connectionError ? 'Waiting for your desk' : 'Opening your workspace'} description={connectionError ? 'The workspace will appear when the local service is available.' : 'Loading the actual account, agents and activity.'} /></Panel> : <>
          {['overview','books','market','inbox','research','operations'].includes(section) && <Autonomy view={section as 'overview'|'books'|'market'|'inbox'|'research'|'operations'} legacy={desk} onQuote={()=>openModal('quote')} onWatchlist={()=>openModal('watchlist')} onManual={()=>navigate('book')} />}
          {section === 'legacy_overview' && <>
            <div className="metrics-grid"><Metric label="Account equity" value={money(desk.account.equity)} note={desk.account.missing_marks ? `${desk.account.missing_marks} position marks missing` : 'Cash + marked paper holdings'} icon={Wallet} highlight /><Metric label="Available cash" value={money(desk.account.available_cash)} note={`${money(desk.account.reserved_cash)} reserved for intents`} icon={ArrowDownLeft} /><Metric label="Paper positions" value={String(desk.positions.length)} note={`${money(desk.account.market_value)} marked value`} icon={Layers3} /><Metric label="Work in progress" value={String(activeTasks.length).padStart(2, '0')} note={`${workingAgents} agents working · ${desk.tasks.filter(task => task.status === 'completed').length} tasks completed`} icon={ClipboardList} /></div>
            <div className="overview-grid">
              <div className="overview-left"><Panel title="The operational loop" subtitle="Six clear handoffs. One durable record." action={<span className="quiet-label"><span className="live-dot" /> Local automation</span>} className="workflow-panel"><div className="workflow-track">{workflow.map((id, index) => {const agent = desk.agents.find(item => item.id === id); const Icon = agentIcons[id]; return <div className="workflow-node" key={id}><div className={`workflow-icon ${agent?.status === 'working' ? 'working' : ''}`}><Icon size={21} strokeWidth={1.7} /><span>{index + 1}</span></div><strong>{agent?.name || humanize(id)}</strong><small>{agent?.status || 'Unavailable'}</small>{index < 5 && <ArrowRight className="workflow-arrow" size={15} />}</div>;})}</div><div className="workflow-footer"><div><strong>A useful next step, whenever you’re ready.</strong><p>Audit quotes, reconcile the book and record an operational brief.</p></div><button className="button button-primary" onClick={() => void runCycle()} disabled={!!busy}><Play size={14} /> Run one cycle</button></div></Panel>
                <Panel title="Recent work" subtitle="Actual tasks and their latest state" action={<button className="text-button" onClick={() => navigate('tasks')}>View queue <ArrowUpRight size={14} /></button>}>{desk.tasks.length ? <div className="task-list">{desk.tasks.slice(0, 4).map(task => <TaskRow key={task.id} task={task} onClick={() => setSelectedTask(task.id)} />)}</div> : <Empty icon={ClipboardList} title="A clean slate for your next task" description="Run a desk cycle or ask an agent to audit, reconcile or preserve a note." action={<button className="button button-secondary" onClick={() => openModal('task')}><Plus size={15} /> Create a task</button>} />}</Panel>
              </div>
              <div className="overview-right"><Panel title="Workspace readiness" className="readiness-panel"><div className="readiness-list"><Readiness icon={Wallet} title="Paper account" detail={desk.account.cash ? `${money(desk.account.cash)} in cash` : 'Ready for your first deposit'} status={desk.account.cash ? 'ready' : 'empty'} /><Readiness icon={Database} title="Market data" detail={desk.watchlist.filter(item => item.quote?.fresh).length ? `${desk.watchlist.filter(item => item.quote?.fresh).length} fresh manual quotes` : 'Manual quotes · none fresh'} status={desk.watchlist.some(item => item.quote?.fresh) ? 'ready' : 'empty'} /><Readiness icon={Users} title="Operational agents" detail={`${desk.agents.length} agents · ${workingAgents ? `${workingAgents} working` : 'ready when needed'}`} status="ready" /><Readiness icon={Sparkles} title="Model reasoning" detail={desk.desk.reasoning.configured ? desk.desk.reasoning.model || 'Configured provider' : 'Optional · not configured'} status={desk.desk.reasoning.configured ? 'ready' : 'empty'} /></div><button className="button button-secondary full-width" onClick={() => navigate('controls')}>Open controls <ArrowRight size={14} /></button></Panel>
                <div className="operator-card"><span className="operator-icon"><ShieldCheck size={22} /></span><div className="eyebrow">OPERATOR IN CONTROL</div><h3>Intent first.<br />Approval second.</h3><p>Paper orders are created by you and filled only after your explicit approval.</p><button className="text-button" onClick={() => navigate('book')}>Open paper book <ArrowRight size={15} /></button></div>
              </div>
            </div>
            <Panel title="On your watchlist" subtitle="Only quotes you have actually supplied" action={<button className="text-button" onClick={() => navigate('watchlist')}>All symbols <ArrowUpRight size={14} /></button>}>{desk.watchlist.length ? <WatchTable desk={desk} onQuote={symbol => openModal('quote', {symbol})} compact /> : <div className="inline-empty"><div className="inline-empty-icon"><Layers3 size={21} /></div><div><strong>Your watchlist starts with you.</strong><p>Add a symbol, then enter a price and its source.</p></div><button className="button button-secondary" onClick={() => openModal('watchlist')}><Plus size={15} /> Add symbol</button></div>}</Panel>
          </>}
          {section === 'agents' && <>
            <div className="section-strip"><div><span className="violet-dot" /><strong>{desk.agents.length} operational agents</strong><span>Local workers run without a model provider.</span></div><button className="button button-secondary" onClick={() => void runCycle()} disabled={!!busy}><Play size={14} /> Run one cycle</button></div>
            <div className="agent-grid">{desk.agents.map(agent => {const Icon = agentIcons[agent.id] || Users; const action = {coordinator: 'Write desk brief', data_steward: 'Audit data', accountant: 'Reconcile book', risk_officer: 'Review operations', execution_clerk: 'Review pending intents', archivist: 'Preserve a note'}[agent.id] || 'Run operational cycle'; return <Panel key={agent.id} className="agent-card"><div className="agent-card-head"><span className="agent-avatar"><Icon size={24} strokeWidth={1.6} /></span><Badge status={agent.status} /></div><h2>{agent.name}</h2><p className="agent-role">{agent.role}</p><div className="capabilities">{agent.capabilities.map(capability => <span key={capability}><Check size={12} />{humanize(capability)}</span>)}</div><div className="agent-last"><Clock3 size={13} /><span>{relative(agent.last_run_at)}</span></div>{agent.last_result && <details className="agent-result"><summary>Last result <ChevronDown size={13} /></summary><pre>{agent.last_result}</pre></details>}<button className="button button-secondary full-width" onClick={() => void runAgent(agent)} disabled={!!busy}>{action}<ArrowRight size={14} /></button>{['risk_officer', 'execution_clerk'].includes(agent.id) && <small className="action-note">Runs the six-agent operational cycle.</small>}</Panel>;})}</div>
            <div className="subtle-note"><ShieldCheck size={16} /><span>Agents audit data, reconcile balances and document work. Only supplied operator/API intents enter autonomous execution.</span></div>
          </>}
          {section === 'tasks' && <>
            <div className="section-strip"><div className="filter-tabs" aria-label="Task filter">{[['all', 'All work'], ['active', 'In progress'], ['completed', 'Completed']].map(([id, label]) => <button key={id} className={taskFilter === id ? 'selected' : ''} onClick={() => setTaskFilter(id)}>{label}{id === 'active' && <span>{activeTasks.length}</span>}</button>)}</div><button className="button button-secondary" onClick={() => void runCycle()} disabled={!!busy}><Play size={14} /> One cycle</button></div>
            <Panel>{desk.tasks.filter(task => taskFilter === 'all' || (taskFilter === 'active' ? ['queued', 'running'].includes(task.status) : task.status === 'completed')).length ? <div className="task-list task-list-large">{desk.tasks.filter(task => taskFilter === 'all' || (taskFilter === 'active' ? ['queued', 'running'].includes(task.status) : task.status === 'completed')).map(task => <TaskRow key={task.id} task={task} onClick={() => setSelectedTask(task.id)} />)}</div> : <Empty icon={ClipboardList} title={taskFilter === 'all' ? 'Your work queue is clear' : 'No tasks in this view'} description="Create an operational brief, data audit, reconciliation or evidence note." action={<button className="button button-primary" onClick={() => openModal('task')}><Plus size={15} /> New task</button>} />}</Panel>
          </>}
          {section === 'watchlist' && <>
            <div className="section-strip"><div><span className="violet-dot" /><strong>{desk.watchlist.length} symbols</strong><span>Freshness window: {desk.settings.quote_max_age_seconds}s</span></div><div className="button-row"><button className="button button-secondary" onClick={() => openModal('quote')}><Database size={15} /> Enter quote</button><button className="button button-primary" onClick={() => openModal('watchlist')}><Plus size={15} /> Add symbol</button></div></div>
            <Panel>{desk.watchlist.length ? <WatchTable desk={desk} onQuote={symbol => openModal('quote', {symbol})} onRemove={symbol => void mutate(`/watchlist/${encodeURIComponent(symbol)}`, undefined, `${symbol} removed from watchlist.`, 'DELETE')} busy={!!busy} /> : <Empty icon={Layers3} title="Start with a symbol you follow" description="Quotes stay empty until you enter a real price, timestamp and source." action={<button className="button button-primary" onClick={() => openModal('watchlist')}><Plus size={15} /> Add your first symbol</button>} />}</Panel><div className="subtle-note"><Database size={16} /><span>Manual data is used as supplied. Quotes are timestamped and become stale; paper orders require a fresh quote.</span></div>
          </>}
          {section === 'book' && <>
            <div className="metrics-grid"><Metric label="Cash balance" value={money(desk.account.cash)} note={`${money(desk.account.available_cash)} available`} icon={Wallet} highlight /><Metric label="Reserved cash" value={money(desk.account.reserved_cash)} note={`${pendingOrders.length} intents awaiting review`} icon={Clock3} /><Metric label="Realized P/L" value={money(desk.account.realized_pnl)} note="From actual paper fills" icon={CheckCircle2} /><Metric label="Unrealized P/L" value={money(desk.account.unrealized_pnl)} note={desk.account.missing_marks ? `${desk.account.missing_marks} marks missing` : 'From supplied position marks'} icon={Layers3} /></div>
            <div className="section-strip"><div><ShieldCheck size={18} /><strong>Human-created, explicitly approved.</strong></div><div className="button-row"><button className="button button-secondary" onClick={() => openModal('funding')}><Plus size={15} /> Add paper funds</button><button className="button button-primary" onClick={() => openModal('order')}><Plus size={15} /> Create order intent</button></div></div>
            <Panel title="Positions" subtitle="Current quantities and supplied marks">{desk.positions.length ? <div className="table-scroll"><table><thead><tr><th>Symbol</th><th className="numeric">Quantity</th><th className="numeric">Average cost</th><th className="numeric">Mark</th><th>Quote</th><th className="numeric">Market value</th><th className="numeric">Unrealized P/L</th></tr></thead><tbody>{desk.positions.map(position => <tr key={position.symbol}><td className="symbol">{position.symbol}</td><td className="numeric mono">{quantity(position.quantity)}</td><td className="numeric mono">{money(position.average_cost)}</td><td className="numeric mono">{money(position.mark_price)}</td><td><Badge status={position.mark_price == null ? 'missing' : position.quote_fresh ? 'fresh' : 'stale'} /></td><td className="numeric mono">{money(position.market_value)}</td><td className={`numeric mono ${position.unrealized_pnl !== null && position.unrealized_pnl < 0 ? 'negative' : ''}`}>{money(position.unrealized_pnl)}</td></tr>)}</tbody></table></div> : <Empty icon={Wallet} title="Your paper book is empty" description="Add paper funds and a manual quote to create your first order intent." action={<button className="button button-secondary" onClick={() => openModal('funding')}><Plus size={15} /> Add paper funds</button>} />}</Panel>
            <Panel title="Order intents" subtitle="Reservations are held until approval or cancellation" action={<span className="count-chip">{pendingOrders.length} awaiting review</span>}>{desk.orders.length ? <div className="order-list">{desk.orders.map(order => <div className="order-row" key={order.id}><span className={`order-side ${order.side}`}><ArrowUpRight size={19} /></span><div className="order-primary"><strong>{order.side === 'buy' ? 'Buy' : 'Sell'} {quantity(order.quantity)} <span>{order.symbol}</span></strong><small>{dateTime(order.created_at)}{order.fill_price != null ? ` · Filled at ${money(order.fill_price)}` : ''}</small>{order.reason && <p>{order.reason}</p>}</div><Badge status={order.status} /><div className="order-actions">{order.status === 'pending_review' && <><button className="button button-small button-ghost" onClick={() => void mutate(`/orders/${order.id}/cancel`, {}, 'Order intent cancelled. Reservation released.')} disabled={!!busy}>Cancel</button><button className="button button-small button-primary" onClick={() => openModal('approve', {order})} disabled={!!busy}>Review & approve</button></>}</div></div>)}</div> : <div className="inline-empty"><div className="inline-empty-icon"><ClipboardList size={22} /></div><div><strong>No order intents yet</strong><p>This separate ledger uses explicit approval; autonomous intents live in Books & orders.</p></div></div>}</Panel>
            <Panel title="Fill receipts" subtitle="Executed paper fills and manual quote provenance">{desk.fills.length ? <div className="table-scroll"><table><thead><tr><th>Time</th><th>Symbol</th><th>Side</th><th className="numeric">Quantity</th><th className="numeric">Fill price</th><th className="numeric">Notional</th><th>Source</th></tr></thead><tbody>{desk.fills.map(fill => <tr key={fill.id}><td className="muted">{dateTime(fill.timestamp)}</td><td className="symbol">{fill.symbol}</td><td className="capitalize">{fill.side}</td><td className="numeric mono">{quantity(fill.quantity)}</td><td className="numeric mono">{money(fill.price)}</td><td className="numeric mono">{money(fill.notional)}</td><td className="muted">{fill.source}</td></tr>)}</tbody></table></div> : <p className="panel-quiet">No fills recorded. Approving an eligible intent creates a paper fill at the available manual quote.</p>}</Panel>
          </>}
          {section === 'journal' && <>
            <div className="section-strip"><div><strong>{desk.events.length} recorded events</strong><span>Actors and timestamps preserved</span></div><label className="search-field"><Search size={15} /><input aria-label="Search journal" placeholder="Search journal…" value={journalSearch} onChange={event => setJournalSearch(event.target.value)} /></label></div>
            <Panel>{desk.events.length ? <div className="journal-list">{desk.events.filter(event => `${event.event_type} ${event.actor} ${event.message}`.toLowerCase().includes(journalSearch.toLowerCase())).map(event => <details className="journal-event" key={event.id}><summary><span className="journal-event-icon"><FileText size={17} /></span><div><strong>{event.message}</strong><span><span className="event-type">{humanize(event.event_type)}</span> · {event.actor}</span></div><time>{dateTime(event.timestamp)}</time><ChevronDown size={15} /></summary><div className="journal-payload"><span className="eyebrow">EVENT #{event.id}</span><pre>{JSON.stringify(event.payload, null, 2)}</pre></div></details>)}{!desk.events.some(event => `${event.event_type} ${event.actor} ${event.message}`.toLowerCase().includes(journalSearch.toLowerCase())) && <p className="panel-quiet">No journal events match this search.</p>}</div> : <Empty icon={BookOpen} title="The first action starts your journal" description="Funding, manual quotes, paper orders and task outcomes are recorded here." />}</Panel>
          </>}
          {section === 'controls' && <>
            <div className="controls-grid"><Panel title="Operational runtime" subtitle="Recurring cycles are separate from manually queued work"><div className="runtime-body"><div className="runtime-status"><span className={`runtime-orbit ${desk.desk.runtime.running ? 'running' : ''}`}><Activity size={27} strokeWidth={1.5} /></span><div><h3>{desk.desk.runtime.running ? 'Recurring cycles are active' : 'Recurring cycles are paused'}</h3><p>Manually submitted tasks still run while paused.</p></div></div><div className="key-values"><div><span>Last heartbeat</span><strong>{dateTime(desk.desk.runtime.heartbeat_at)}</strong></div><div><span>Last cycle</span><strong>{dateTime(desk.desk.runtime.last_cycle_at)}</strong></div></div><div className="button-row"><button className={`button ${desk.desk.runtime.running ? 'button-secondary' : 'button-primary'}`} onClick={() => void mutate('/runtime', {running: !desk.desk.runtime.running}, desk.desk.runtime.running ? 'Recurring cycles paused.' : 'Recurring cycles started.')} disabled={!!busy}>{desk.desk.runtime.running ? <Pause size={15} /> : <Play size={15} />}{desk.desk.runtime.running ? 'Pause cycles' : 'Start cycles'}</button><button className="button button-secondary" onClick={() => void runCycle()} disabled={!!busy}><RefreshCw size={15} /> Run one cycle</button></div></div></Panel>
              <Panel title="Connections" subtitle="Truthful workspace capabilities"><div className="connection-list"><Connection icon={Database} title="Market data" label="Manual input" description={desk.connections.market_data.status} /><Connection icon={Wallet} title="Execution" label="Paper workspace" description={desk.connections.broker.status} /><Connection icon={Sparkles} title="Model reasoning" label={desk.connections.reasoning.configured ? 'Configured' : 'Not configured'} description={desk.connections.reasoning.configured ? `${desk.connections.reasoning.provider} · ${desk.connections.reasoning.model || 'Model unspecified'}` : 'Local operational workers are available.'} /></div><div className="connection-note">Model reasoning is optional and used only for explicitly submitted briefs or notes.</div></Panel></div>
            <div className="controls-grid"><Panel title="Workspace settings" subtitle="Intervals in seconds"><SettingsForm desk={desk} busy={!!busy} onSave={values => mutate('/settings', values, 'Workspace settings saved.', 'PATCH')} /></Panel><Panel title="Your data, preserved" subtitle="Export the desk’s recorded state"><div className="export-body"><span className="export-icon"><Archive size={25} strokeWidth={1.6} /></span><h3>Take the paper trail with you.</h3><p>Download account records, tasks, quotes, orders and the event journal as JSON.</p><a className="button button-secondary" href="/api/export" download="aster-desk-export.json"><Download size={15} /> Export workspace</a></div></Panel></div>
            <Panel title="Service health" subtitle="Reported by the local worker and database"><div className="health-body">{healthError ? <p className="negative">{healthError}</p> : health ? <details><summary><span><span className="live-dot" /> Health response received</span><ChevronDown size={14} /></summary><pre>{JSON.stringify(health, null, 2)}</pre></details> : <p className="muted">Loading service health…</p>}</div></Panel>
          </>}
          <footer className="workspace-footer"><span><span className="footer-dot" /> {connectionError ? 'Last received snapshot' : 'Connected to your local desk'}</span><span>{lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString(undefined, {hour: '2-digit', minute: '2-digit', second: '2-digit'})}` : ''} · USD</span></footer>
        </>}
      </main>
    </div>
    {toast && <div className={`toast ${toast.error ? 'toast-error' : ''}`} role={toast.error ? 'alert' : 'status'}>{toast.error ? <Activity size={18} /> : <CheckCircle2 size={18} />}<span>{toast.message}</span><IconButton label="Dismiss notification" icon={X} onClick={() => setToast(null)} /></div>}
    {modal && desk && <Dialog title={{funding: 'Add paper funds', watchlist: 'Add a watchlist symbol', quote: 'Enter a manual quote', order: 'Create an order intent', task: 'Create a task', approve: 'Approve this paper fill'}[modal.kind]} onClose={() => {if (!busy) setModal(null);}}><form key={modal.clientId} onSubmit={event => void submitModal(event)}>
      {modal.kind === 'funding' && <><p className="form-intro">Deposit paper cash into this workspace. Funding is recorded separately from trading P/L.</p><Field label="Amount (USD)" name="amount" type="number" min="0.01" step="0.01" placeholder="0.00" required autoFocus /><div className="form-context">Current cash <strong className="mono">{money(desk.account.cash)}</strong></div></>}
      {modal.kind === 'watchlist' && <><p className="form-intro">Add an equities symbol. A price appears only when you supply a quote.</p><Field label="Symbol" name="symbol" placeholder="e.g. AAPL" maxLength={15} required autoFocus /></>}
      {modal.kind === 'quote' && <><p className="form-intro">Enter an observed price with its actual timestamp and source. This quote can be used for paper fills while fresh.</p><div className="form-grid"><Field label="Symbol" name="symbol" defaultValue={modal.symbol} placeholder="e.g. AAPL" maxLength={15} required autoFocus /><Field label="Price (USD)" name="price" type="number" min="0.000001" step="any" placeholder="0.00" required /></div><Field label="Observation time (your local timezone)" name="as_of" type="datetime-local" step="1" defaultValue={localDateTime()} required /><Field label="Source / provenance" name="source" placeholder="Where did you observe this quote?" maxLength={160} required /><div className="form-note">The timestamp is saved in UTC. Freshness window: {desk.settings.quote_max_age_seconds} seconds.</div></>}
      {modal.kind === 'order' && <><p className="form-intro">Create a paper market-order intent. Cash or shares will be reserved; nothing fills until you approve it.</p><Field label="Symbol" name="symbol" defaultValue={modal.symbol} placeholder="e.g. AAPL" maxLength={15} list="quoted-symbols" required autoFocus /><datalist id="quoted-symbols">{desk.watchlist.map(item => <option key={item.symbol} value={item.symbol} />)}</datalist><div className="form-grid"><label className="field"><span>Side</span><select name="side"><option value="buy">Buy</option><option value="sell">Sell</option></select></label><Field label="Quantity" name="quantity" type="number" min="0.000001" step="any" placeholder="0" required /></div><div className="form-context">Available cash <strong className="mono">{money(desk.account.available_cash)}</strong></div><div className="form-note">Fresh manual quote required. Approval rechecks price, funds and shares.</div></>}
      {modal.kind === 'task' && <><p className="form-intro">Give your operational team a clear piece of work. The task, steps and results are recorded.</p><label className="field"><span>Task type</span><select name="kind" defaultValue={modal.taskKind || 'desk_brief'}><option value="desk_brief">Desk brief</option><option value="data_audit">Data audit</option><option value="reconcile">Book reconciliation</option><option value="research_note">Evidence note</option></select></label><Field label="Title (optional)" name="title" placeholder="Give this task a name" maxLength={160} autoFocus /><Field label="Symbol (optional)" name="symbol" placeholder="e.g. AAPL" maxLength={15} /><label className="field"><span>Instructions / source text (optional)</span><textarea name="instructions" rows={5} placeholder="Add context or evidence you want preserved…" maxLength={12000} /></label><div className="form-note">{desk.desk.reasoning.configured ? `Configured model: ${desk.desk.reasoning.model || desk.desk.reasoning.provider}. Explicit brief and note tasks may use model reasoning.` : 'Local automation is available. Model reasoning is not configured.'}</div></>}
      {modal.kind === 'approve' && modal.order && <><p className="form-intro">You are authorizing a paper fill. The service will recheck the latest manual quote and available balances.</p><div className="approval-summary"><span className="eyebrow">PAPER MARKET ORDER</span><h3>{modal.order.side === 'buy' ? 'Buy' : 'Sell'} {quantity(modal.order.quantity)} {modal.order.symbol}</h3>{(() => {const quote = desk.watchlist.find(item => item.symbol === modal.order!.symbol)?.quote; return <><div className="key-values"><div><span>Latest supplied price</span><strong className="mono">{money(quote?.price)}</strong></div><div><span>Quote state</span><Badge status={quote ? quote.fresh ? 'fresh' : 'stale' : 'missing'} /></div>{quote && <><div><span>Source</span><strong>{quote.source}</strong></div><div><span>Observed</span><strong>{dateTime(quote.as_of)}</strong></div></>}</div><p className="form-note">Actual paper fill uses the fresh manual quote available when approval is processed.</p></>;})()}</div></>}
      {modalError && <p className="form-error" role="alert">{modalError}</p>}<div className="dialog-actions"><button type="button" className="button button-secondary" onClick={() => setModal(null)} disabled={!!busy}>Cancel</button><button type="submit" className="button button-primary" disabled={!!busy}>{busy ? <LoaderCircle className="spin" size={15} /> : modal.kind === 'approve' ? <Check size={15} /> : <Plus size={15} />}{busy ? 'Saving…' : {funding: 'Add paper funds', watchlist: 'Add symbol', quote: 'Save manual quote', order: 'Create intent', task: 'Queue task', approve: 'Approve paper fill'}[modal.kind]}</button></div>
    </form></Dialog>}
    {taskDetail && <Dialog title="Task details" onClose={() => setSelectedTask(null)} wide><div className="task-detail-heading"><Badge status={taskDetail.status} /><span className="quiet-label">{taskLabels[taskDetail.kind] || humanize(taskDetail.kind)}</span><h3>{taskDetail.title}</h3><p>Created {dateTime(taskDetail.created_at)}{taskDetail.completed_at && ` · Completed ${dateTime(taskDetail.completed_at)}`}</p></div><div className="task-steps">{taskDetail.steps.length ? taskDetail.steps.map((step, index) => <div className={`task-step ${step.status}`} key={step.id}><span className="step-number">{step.status === 'completed' ? <Check size={15} /> : step.status === 'running' ? <LoaderCircle className="spin" size={15} /> : index + 1}</span><div><div className="step-heading"><strong>{step.title}</strong><Badge status={step.status} /></div><span className="step-agent">{desk?.agents.find(agent => agent.id === step.agent_id)?.name || humanize(step.agent_id)}</span>{step.result && <pre>{step.result}</pre>}</div></div>) : <p className="panel-quiet">Waiting for the worker to create the first step.</p>}</div>{taskDetail.result && <div className="task-result"><span className="eyebrow">RECORDED RESULT</span><pre>{taskDetail.result}</pre></div>}{taskDetail.error && <p className="form-error" role="alert">{taskDetail.error}</p>}<div className="dialog-actions">{['queued', 'running'].includes(taskDetail.status) && <button className="button button-secondary" disabled={!!busy} onClick={() => void mutate(`/tasks/${taskDetail.id}/cancel`, {}, 'Task cancellation recorded.')}>Cancel task</button>}<button className="button button-primary" onClick={() => setSelectedTask(null)}>Done</button></div></Dialog>}
  </div>;
}

function TaskRow({task, onClick}: {task: Task; onClick: () => void}) {
  const completed = task.steps.filter(step => step.status === 'completed').length;
  return <button className="task-row" onClick={onClick}><span className={`task-icon ${task.status}`}><ClipboardList size={19} strokeWidth={1.6} /></span><div className="task-row-info"><strong>{task.title}</strong><small>{taskLabels[task.kind] || humanize(task.kind)} · {task.steps.length ? `${completed}/${task.steps.length} steps` : 'Awaiting worker'}</small></div><Badge status={task.status} /><time>{relative(task.created_at)}</time><ArrowRight size={16} /></button>;
}
function Readiness({icon: Icon, title, detail, status}: {icon: LucideIcon; title: string; detail: string; status: string}) {
  return <div className="readiness-item"><span className="readiness-icon"><Icon size={17} /></span><div><strong>{title}</strong><small>{detail}</small></div>{status === 'ready' ? <CheckCircle2 className="ready-check" size={17} /> : <span className="empty-state-dot" />}</div>;
}
function WatchTable({desk, onQuote, onRemove, compact, busy}: {desk: DeskSnapshot; onQuote: (symbol: string) => void; onRemove?: (symbol: string) => void; compact?: boolean; busy?: boolean}) {
  return <div className="table-scroll"><table><thead><tr><th>Symbol</th><th className="numeric">Manual quote</th><th>Status</th><th>Observed</th>{!compact && <th>Source</th>}<th className="numeric">Actions</th></tr></thead><tbody>{(compact ? desk.watchlist.slice(0, 5) : desk.watchlist).map(item => <tr key={item.symbol}><td><span className="symbol-cell"><span className="symbol-avatar">{item.symbol.slice(0, 1)}</span><strong className="symbol">{item.symbol}</strong></span></td><td className="numeric mono">{money(item.quote?.price)}</td><td><Badge status={item.quote ? item.quote.fresh ? 'fresh' : 'stale' : 'missing'}>{item.quote ? item.quote.fresh ? 'Fresh' : 'Stale' : 'No quote'}</Badge></td><td className="muted">{item.quote ? dateTime(item.quote.as_of) : '—'}</td>{!compact && <td className="muted source-cell">{item.quote?.source || '—'}</td>}<td><div className="table-actions"><button className="button button-small button-ghost" onClick={() => onQuote(item.symbol)} disabled={busy}>Enter quote</button>{onRemove && <IconButton label={`Remove ${item.symbol}`} icon={Trash2} onClick={() => onRemove(item.symbol)} disabled={busy} />}</div></td></tr>)}</tbody></table></div>;
}
function Connection({icon: Icon, title, label, description}: {icon: LucideIcon; title: string; label: string; description: string}) {
  return <div className="connection-item"><span className="readiness-icon"><Icon size={19} /></span><div><div><strong>{title}</strong><span>{label}</span></div><p>{humanize(description)}</p></div></div>;
}
function SettingsForm({desk, busy, onSave}: {desk: DeskSnapshot; busy: boolean; onSave: (values: DeskSnapshot['settings']) => Promise<boolean>}) {
  const [saved, setSaved] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    const okay = await onSave({quote_max_age_seconds: Number(values.get('quote_max_age_seconds')), heartbeat_seconds: Number(values.get('heartbeat_seconds')), cycle_interval_seconds: Number(values.get('cycle_interval_seconds'))});
    if (okay) setSaved(true);
  }
  return <form className="settings-form" key={JSON.stringify(desk.settings)} onSubmit={event => void submit(event)} onChange={() => setSaved(false)}><Field label="Quote freshness window" name="quote_max_age_seconds" type="number" defaultValue={desk.settings.quote_max_age_seconds} min="1" max="86400" step="1" required /><div className="form-grid"><Field label="Heartbeat interval" name="heartbeat_seconds" type="number" defaultValue={desk.settings.heartbeat_seconds} min="1" max="60" step="1" required /><Field label="Cycle interval" name="cycle_interval_seconds" type="number" defaultValue={desk.settings.cycle_interval_seconds} min="5" max="86400" step="1" required /></div><button className="button button-secondary" type="submit" disabled={busy}><Check size={15} />{saved ? 'Settings saved' : 'Save settings'}</button></form>;
}
function Field({label, ...props}: {label: string} & React.InputHTMLAttributes<HTMLInputElement>) {
  return <label className="field"><span>{label}</span><input {...props} /></label>;
}
function Dialog({title, children, onClose, wide = false}: {title: string; children: ReactNode; onClose: () => void; wide?: boolean}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  useEffect(() => {const dialog = dialogRef.current; dialog?.showModal(); return () => dialog?.close();}, []);
  return <dialog ref={dialogRef} className={`dialog ${wide ? 'dialog-wide' : ''}`} onCancel={event => {event.preventDefault(); onClose();}} onClick={event => {if (event.target === dialogRef.current) {const bounds = dialogRef.current.getBoundingClientRect(); if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) onClose();}}} aria-labelledby="dialog-title"><div className="dialog-heading"><h2 id="dialog-title">{title}</h2><IconButton label="Close dialog" icon={X} onClick={onClose} /></div><div className="dialog-body">{children}</div></dialog>;
}
