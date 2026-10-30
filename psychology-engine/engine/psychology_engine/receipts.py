"""Import an already captured source response without any outbound request."""
import hashlib
from urllib.parse import urlsplit
from .adapters import parse, source_config
from .core import now,stamp,utc


def import_receipt(store,receipt,received_at=None):
    received_at=stamp(received_at or now())
    for key in ('receipt_id','source','source_url','captured_at','payload_utf8','payload_sha256','usage_scope'):
        if not isinstance(receipt.get(key),str) or not receipt[key].strip():raise ValueError('missing receipt field '+key)
    source=receipt['source'];configs=source_config()
    if source not in configs:raise ValueError('unsupported receipt source')
    origin=urlsplit(receipt['source_url']);expected=urlsplit(configs[source]['url'])
    if origin.scheme!='https' or origin.hostname!=expected.hostname or origin.username or origin.password or origin.query:
        raise ValueError('receipt source origin does not match reviewed adapter')
    captured=stamp(receipt['captured_at'])
    if utc(captured)>utc(received_at):raise ValueError('receipt capture is in the future')
    body=receipt['payload_utf8'].encode('utf-8')
    if len(body)>8_000_000:raise ValueError('receipt too large')
    digest=hashlib.sha256(body).hexdigest()
    if digest!=receipt['payload_sha256']:raise ValueError('receipt payload checksum mismatch')
    rows=parse(source,body,captured,configs)
    for r in rows:
        # Later local receipt cannot legitimize an impossible upstream capture.
        for clock in ('event_time','publication_time'):
            if utc(r[clock])>utc(captured):
                raise ValueError(clock+' occurs after upstream capture')
        r['url']=receipt['source_url']
        r['provenance']=dict(r['provenance'],original_url=receipt['source_url'],
            receipt_id=receipt['receipt_id'],upstream_captured_at=captured,
            provider_received_at=captured,provider_received_at_basis='supplied_upstream_capture_attestation',
            locally_received_at=received_at,extracted_at=received_at,
            ingestion_route='existing_evidence_receipt_no_network',
            usage_scope=receipt['usage_scope'],redistribution_status=receipt.get('redistribution_status','unknown'),
            original_envelope_sha256=digest)
        r['revision']=hashlib.sha256((r['revision']+'|'+captured+'|'+digest).encode()).hexdigest()
    # Normal ingestion sets this engine's first-seen to actual receipt import time.
    # Prior research capture does not confer historical availability to this engine.
    result=store.ingest(rows,received_at=received_at,historical=False)
    store.record_acquisition(source,received_at,body)
    store.log_run('receipt_import:'+source,'ok','previously captured response; no HTTP request')
    return dict(result,source=source,receipt_id=receipt['receipt_id'],captured_at=captured,
                locally_received_at=received_at,outbound_requests=0,
                live_collection_validated=False,redistribution_status=receipt.get('redistribution_status','unknown'))
