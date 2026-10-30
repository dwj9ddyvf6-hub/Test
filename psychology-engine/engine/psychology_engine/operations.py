"""Read-only health inspection and SQLite online backups. No scheduler activation."""
import sqlite3
import os
from pathlib import Path
from urllib.parse import quote
from .core import stamp,utc,now


def open_readonly(path):
    p=Path(path).resolve()
    if not p.is_file():raise FileNotFoundError('database not initialized')
    db=sqlite3.connect('file:'+quote(str(p),safe='/')+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    return db


def health(path,sources,as_of=None,max_check_age_hours=48):
    as_of=stamp(as_of or now())
    if not 0<max_check_age_hours<=24*365:raise ValueError('invalid health check age')
    try:db=open_readonly(path)
    except FileNotFoundError:return {'status':'unavailable','reason':'database_not_initialized','sources':{},'as_of':as_of},1
    try:
        if db.execute('PRAGMA user_version').fetchone()[0]!=3:return {'status':'unavailable','reason':'unsupported_schema','as_of':as_of},1
        integrity=db.execute('PRAGMA quick_check').fetchone()[0]
        if integrity!='ok':return {'status':'unavailable','reason':'database_integrity_failure','as_of':as_of},1
        states={}
        for source in sources:
            run=db.execute('SELECT * FROM runs WHERE source=? AND time<=? ORDER BY time DESC LIMIT 1',(source,as_of)).fetchone()
            # Match snapshot vintage ordering before checking value/access/freshness.
            # A null or withdrawn latest revision must invalidate its older value.
            eligible=db.execute("""WITH ranked AS (
                SELECT *,ROW_NUMBER() OVER (
                    PARTITION BY source,item_id,dimension,entity,horizon,units
                    ORDER BY publication_time DESC,first_seen DESC,ingest_time DESC,id DESC
                ) AS vintage_rank FROM observations
                WHERE source=? AND first_seen<=? AND publication_time<=?
                  AND event_time<=? AND available_at<=?
            ) SELECT * FROM ranked WHERE vintage_rank=1""",
                (source,as_of,as_of,as_of,as_of)).fetchall()
            count=len(eligible)
            fresh_ok=any(r['value'] is not None and r['access_status'] in
                         ('public','licensed','user_import','fixture') and
                         (utc(as_of)-utc(r['event_time'])).total_seconds()/3600<=r['max_age_hours']
                         for r in eligible)
            run_age=(utc(as_of)-utc(run['time'])).total_seconds()/3600 if run else None
            state='healthy' if run and run['status']=='ok' and run_age<=max_check_age_hours and fresh_ok else 'degraded' if count else 'unavailable'
            states[source]={'status':state,'last_check':run['time'] if run else None,'last_result':run['status'] if run else None,'check_age_hours':run_age,'observations_available':count,'fresh_observation_present':fresh_ok}
        healthy=sum(s['status']=='healthy' for s in states.values())
        status='healthy' if states and healthy==len(states) else 'degraded' if any(s['observations_available'] for s in states.values()) else 'unavailable'
        return {'status':status,'as_of':as_of,'database_integrity':'ok','sources':states,'network_not_checked':True,'interpretation':'Operational availability is not predictive validity or license approval'},0 if status=='healthy' else 3 if status=='degraded' else 1
    except sqlite3.DatabaseError:return {'status':'unavailable','reason':'database_error','as_of':as_of},1
    finally:db.close()


def backup(source,destination):
    target=Path(destination)
    if target.exists():raise FileExistsError('backup destination already exists')
    # Exclusive creation prevents accidental replacement of an existing artifact.
    target.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    os.close(fd)
    src=None;dst=None
    try:
        src=open_readonly(source);dst=sqlite3.connect(str(target));src.backup(dst)
        if dst.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('backup integrity failed')
    except Exception:
        if dst:dst.close();dst=None
        target.unlink(missing_ok=True)
        raise
    finally:
        if dst:dst.close()
        if src:src.close()
    return {'status':'ok','consistent_sqlite_backup':True,'bytes':target.stat().st_size}
