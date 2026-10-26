import { create } from "zustand";
import { persist } from "zustand/middleware";
import { mergeSignals } from "@/lib/tensor/live-signals";
import type { Interval, LiveSignal, WatchItem } from "@/lib/tensor/types";
import { canonicalWatchlistSymbol } from "@/lib/tensor/watchlist-symbol";

const DEFAULT_WATCH: WatchItem[] = [
  "SATL",
  "SKYQ",
  "RDW",
  "INDI",
  "SPY",
  "QQQ",
  "NVDA",
  "MU",
  "AAPL",
  "AMD",
  "TSLA",
  "WULF",
  "POET",
].map((symbol) => ({
  symbol,
  enteredAt: null,
  addedAt: "2026-08-01T00:00:00.000Z",
}));

export type DeskView =
  | "desk"
  | "scanners"
  | "tensor"
  | "scan"
  | "live"
  | "watch"
  | "vector"
  | "publish"
  | "alerts"
  | "members"
  | "guide"
  | "buys"
  | "observe"
  | "paper"
  | "review"
  | "source";
export type ScanFilter = "all" | "buys" | "sells" | "reversal" | "setup" | "wait" | "conflict" | "risk";
export type LiveFilter = "all" | "signal" | "tape" | "marker";

type DeskState = {
  items: WatchItem[];
  selected: string;
  interval: Interval;
  view: DeskView;
  scanFilter: ScanFilter;
  liveFilter: LiveFilter;
  signals: LiveSignal[];
  legendOpen: boolean;
  add: (raw: string) => string | null;
  remove: (symbol: string) => void;
  adoptWatch: (symbols: string[]) => void;
  select: (symbol: string) => void;
  setInterval: (interval: Interval) => void;
  setView: (view: DeskView) => void;
  setScanFilter: (filter: ScanFilter) => void;
  setLiveFilter: (filter: LiveFilter) => void;
  markEntered: (symbol: string, entered: boolean) => void;
  selectRelative: (delta: number, symbols: string[]) => void;
  pushSignals: (incoming: LiveSignal[]) => LiveSignal[];
  clearSignals: () => void;
  setLegendOpen: (open: boolean) => void;
};

export const useDeskStore = create<DeskState>()(
  persist(
    (set, get) => ({
      items: DEFAULT_WATCH,
      selected: "AFRM",
      interval: "5m",
      view: "desk",
      scanFilter: "all",
      liveFilter: "all",
      signals: [],
      legendOpen: false,
      add: (raw) => {
        const symbol = canonicalWatchlistSymbol(raw);
        if (!symbol) return "Use a canonical ticker such as MU or BRK.B.";
        if (get().items.some((i) => i.symbol === symbol)) return "Already on the desk.";
        set({
          items: [...get().items, { symbol, enteredAt: null, addedAt: new Date().toISOString() }],
          selected: symbol,
          view: "tensor",
        });
        return null;
      },
      remove: (symbol) => {
        const next = get().items.filter((i) => i.symbol !== symbol);
        set({
          items: next,
          selected: get().selected === symbol ? (next[0]?.symbol ?? "SPY") : get().selected,
        });
      },
      adoptWatch: (symbols) => {
        const now = new Date().toISOString();
        const items = get().items.slice();
        const seen = new Set(items.map((i) => i.symbol));
        let added = false;
        for (const raw of symbols) {
          const symbol = canonicalWatchlistSymbol(raw);
          if (!symbol || seen.has(symbol)) continue;
          seen.add(symbol);
          items.push({ symbol, enteredAt: null, addedAt: now });
          added = true;
        }
        if (!added) return;
        const selected = items.some((i) => i.symbol === get().selected) ? get().selected : items[0].symbol;
        set({ items, selected });
      },
      select: (symbol) => set({ selected: symbol, view: "tensor" }),
      setInterval: (interval) => set({ interval }),
      setView: (view) => set({ view }),
      setScanFilter: (scanFilter) => set({ scanFilter }),
      setLiveFilter: (liveFilter) => set({ liveFilter }),
      markEntered: (symbol, entered) => {
        set({
          items: get().items.map((i) =>
            i.symbol === symbol ? { ...i, enteredAt: entered ? new Date().toISOString() : null } : i,
          ),
        });
        void import("@/lib/desk-api").then(({ pinHeldName }) => {
          void pinHeldName({ data: { symbol, held: entered } });
        });
      },
      selectRelative: (delta, symbols) => {
        if (!symbols.length) return;
        const cur = symbols.indexOf(get().selected);
        const i = cur < 0 ? 0 : (cur + delta + symbols.length) % symbols.length;
        set({ selected: symbols[i] });
      },
      pushSignals: (incoming) => {
        const { next, fresh } = mergeSignals(get().signals, incoming);
        set({ signals: next });
        return fresh;
      },
      clearSignals: () => set({ signals: [] }),
      setLegendOpen: (legendOpen) => set({ legendOpen }),
    }),
    {
      name: "galath-desk-v8",
      partialize: (s) => ({
        items: s.items,
        selected: s.selected,
        interval: s.interval,
        view: s.view,
        signals: s.signals.slice(0, 80),
      }),
    },
  ),
);
