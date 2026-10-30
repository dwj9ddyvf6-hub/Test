import argparse
import csv
import json
import time
from pathlib import Path
from .core import Store, now
from .adapters import collect, SOURCES, source_config
from .evaluation import evaluate
from .patterns import detect, forecast
from .contract import envelope
from .operations import health, backup
from .receipts import import_receipt


def report(snapshot):
    lines=['# Psychology Engine evidence report','',f"As of: {snapshot['as_of']}",f"Entity: {snapshot['entity']}; horizon: {snapshot['horizon']}",'',
           'Research advisory only. Tensor retains entry timing authority. Predictive validation is not established.','',
           '| Dimension | Measures | Declared source families |','|---|---|---|']
    for dim,state in snapshot['state'].items():
        lines.append(f"| {dim} | {json.dumps(state['measures']) if state['measures'] is not None else 'UNKNOWN'} | {state['source_family_count']} |")
    lines += ['',f"Included observations: {len(snapshot['evidence'])}; excluded: {len(snapshot['excluded'])}.",
              f"Decision: {snapshot['decision']['action']}. No order interface is implemented.",'',
              'VIX measures option-implied risk, not surveyed beliefs. Fed text measures institutional language, not investor consensus. Family counts are provenance counts, not statistical independence guarantees.','',
              '## Evidence', '']
    for r in snapshot['evidence']:
        lines.append(f"- {r['source']} / {r['item_id']} / revision {r['revision']}: {r['dimension']}={r['value']} {r['units']}; published {r['publication_time']}; first seen {r['first_seen']}.")
    for r in snapshot['excluded']:
        lines.append(f"- Excluded {r['source']} ({r['id']}): {r['reason']}.")
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description='Psychology Engine: research advisory, no orders')
    p.add_argument('--db',default='psychology.sqlite')
    sub=p.add_subparsers(dest='command',required=True)
    imp=sub.add_parser('import'); imp.add_argument('file'); imp.add_argument('--trusted-historical',action='store_true')
    snap=sub.add_parser('snapshot'); snap.add_argument('--as-of',default=None); snap.add_argument('--entity',default='US_MARKET'); snap.add_argument('--horizon',default='1d'); snap.add_argument('--markdown',action='store_true'); snap.add_argument('--contract',action='store_true')
    mon=sub.add_parser('monitor'); mon.add_argument('--scheduled',action='store_true'); mon.add_argument('--source-config'); mon.add_argument('--source',choices=SOURCES,required=True); mon.add_argument('--cycles',type=int,default=1); mon.add_argument('--interval',type=float,default=60)
    ev=sub.add_parser('evaluate'); ev.add_argument('file'); ev.add_argument('--min-train',type=int,default=20); ev.add_argument('--cost-bps',type=float,default=5)
    pat=sub.add_parser('patterns'); pat.add_argument('--as-of',required=True); pat.add_argument('--entity',default='US_MARKET'); pat.add_argument('--horizon',default='1d')
    fc=sub.add_parser('forecast'); fc.add_argument('--as-of',required=True); fc.add_argument('--entity',default='US_MARKET'); fc.add_argument('--horizon',default='1d'); fc.add_argument('--source',required=True); fc.add_argument('--dimension',required=True); fc.add_argument('--units',required=True)
    sub.add_parser('capabilities')
    hc=sub.add_parser('health');hc.add_argument('--source',action='append',choices=SOURCES);hc.add_argument('--as-of');hc.add_argument('--max-check-age-hours',type=float,default=48)
    bk=sub.add_parser('backup');bk.add_argument('destination')
    rc=sub.add_parser('import-receipt');rc.add_argument('file')
    args=p.parse_args()
    if args.command=='health':
        result,code=health(args.db,args.source or list(SOURCES),args.as_of,args.max_check_age_hours)
        print(json.dumps(result,indent=2));return code
    if args.command=='backup':
        print(json.dumps(backup(args.db,args.destination),indent=2));return 0
    if args.command=='capabilities':
        print(Path(__file__).with_name('capabilities.json').read_text());return
    if args.command=='evaluate':
        print(json.dumps(evaluate(json.loads(Path(args.file).read_text()),args.min_train,args.cost_bps),indent=2)); return
    store=Store(args.db)
    try:
        if args.command=='import-receipt':
            print(json.dumps(import_receipt(store,json.loads(Path(args.file).read_text())),indent=2))
        elif args.command=='import':
            with open(args.file) as f:
                rows=json.load(f) if args.file.endswith('.json') else list(csv.DictReader(f))
            print(json.dumps(store.ingest(rows,historical=args.trusted_historical)))
        elif args.command=='snapshot':
            s=store.snapshot(args.as_of or now(),args.entity,args.horizon)
            print(json.dumps(envelope(s),indent=2) if args.contract else report(s) if args.markdown else json.dumps(s,indent=2))
        elif args.command=='patterns':
            print(json.dumps(detect(store,args.as_of,args.entity,args.horizon),indent=2))
        elif args.command=='forecast':
            print(json.dumps(forecast(store,args.as_of,args.entity,args.horizon,args.source,args.dimension,args.units),indent=2))
        elif args.command=='monitor':
            if not 1<=args.cycles<=100 or not 60<=args.interval<=3600:
                p.error('cycles must be 1..100 and interval 60..3600 seconds')
            configs=source_config(args.source_config)
            if (args.cycles>1 or args.scheduled) and configs[args.source].get('persistent_use_authorized') is not True:
                p.error('Repeated collection requires an explicitly versioned source-policy review in --source-config')
            outcomes=[]
            for i in range(args.cycles):
                result=collect(store,args.source,configs=configs)
                outcomes.append(result)
                print(json.dumps(dict(result,cycle=i+1)),flush=True)
                if i+1<args.cycles: time.sleep(args.interval)
            succeeded=sum(r['status']=='ok' for r in outcomes)
            status='ok' if succeeded==len(outcomes) else 'partial' if succeeded else 'failed'
            exit_code=0 if status=='ok' else 3 if status=='partial' else 1
            print(json.dumps({'type':'monitor_summary','source':args.source,'status':status,'succeeded':succeeded,'failed':len(outcomes)-succeeded,'exit_code':exit_code,'outcomes':outcomes}),flush=True)
            return exit_code
    finally:
        store.close()

if __name__=='__main__': raise SystemExit(main() or 0)
