"""Contract-shaped descriptive output; unsupported scientific components stay null."""
import hashlib
import json
from datetime import timedelta
from .core import DIMENSIONS,now,utc


def envelope(snapshot,computed_at=None):
    computed_at=computed_at or now()
    if utc(snapshot['as_of'])>utc(computed_at):raise ValueError('information cutoff cannot follow computation')
    evidence=[];observed=[];ages=[];expiries=[]
    for row in snapshot['evidence']:
        p=json.loads(row['provenance'])
        age=(utc(snapshot['as_of'])-utc(row['event_time'])).total_seconds()/3600
        ages.append(age);expiries.append(utc(row['event_time'])+timedelta(hours=row['max_age_hours']))
        evidence.append(dict(evidence_id=row['id'],original_url=row['url'] or None,provider_id=p.get('provider_id',row['source']),publisher=p.get('publisher'),
          raw_content_hash=p.get('raw_content_hash'),source_population=p.get('source_population'),event_at_if_known=row['event_time'],published_at=row['publication_time'],
          updated_at_if_any=p.get('updated_at'),provider_received_at=p['provider_received_at'],locally_received_at=p['locally_received_at'],extracted_at=p['extracted_at'],
          available_at=row['available_at'],revision_parent_id_if_any=p.get('revision_parent_id'),origin_cluster_id=p.get('origin_cluster_id'),exposure_cluster_id=p.get('exposure_cluster_id'),
          lineage_confidence=None,license_and_retention_policy=p.get('license_and_retention_policy'),entity_id=row['entity'],entity_mapping_version=p.get('entity_mapping_version'),
          evidence_span=row['text'] or {'item_id':row['item_id'],'dimension':row['dimension'],'value':row['value'],'units':row['units']},
          missing_reason=p.get('missing_reason'),publication_time_basis=p.get('publication_time_basis')))
        observed.append(dict(name=row['dimension'],value_or_null=row['value'],units=row['units'],window={'event_time':row['event_time'],'horizon':row['horizon']},
                             sample_frame=p.get('source_population'),sample_count=1,effective_count_diagnostic=None,source_age=age,status='observed',evidence_ids=[row['id']]))
    missing=[d for d in DIMENSIONS if snapshot['state'][d]['observations']==0]
    result=dict(contract_version='1.0.0',as_of=snapshot['as_of'],information_cutoff=snapshot['as_of'],computed_at=computed_at,available_at=computed_at,
                expires_at=min(expiries).isoformat() if expiries else None,instrument_id=snapshot['entity'],
                source_population=sorted({e['source_population'] for e in evidence if e['source_population']}),
                observed_states=observed,estimated_states=[],forecast_distributions=[],
                quality=dict(status='partial' if evidence else 'unavailable',coverage_fraction_if_defined=None,coverage_denominator=None,
                raw_item_count=len(evidence)+len(snapshot['excluded']),unique_author_count=None,information_origin_count=None,
                source_lineage_groups=sorted({r['source_family'] for r in snapshot['evidence']}),max_source_age=max(ages) if ages else None,min_source_age=min(ages) if ages else None,
                missing_features=missing,source_outages={s:v for s,v in snapshot.get('source_health',{}).items() if v['status']=='failed'} or None,composition_shift=None,extraction_error_audit=None,out_of_distribution=None,forecast_calibration_age=None,interval_method=None),
                evidence=evidence,model_versions={'engine':'0.4.1','snapshot_schema':snapshot['schema'],'latent_state':None,'calibration':None},
                advisory=dict(pattern_ids=[],observations=[r['id'] for r in snapshot['evidence']],hypotheses=[],rival_explanations=['Fundamental information, sample selection and constraints can explain the same proxy movements.'],
                falsifiers=['No incremental prospective skill against matched baselines.'],timing_risks=['Output is available only after computation, even for historical information cutoffs.'],tensor_authority_unchanged=True,not_an_order=True),
                evidence_stage='HYPOTHESIS',market_validated=False,
                implementation_gaps=['Author concentration and stable panels unavailable','No calibrated claim extraction or latent state','No validated forecast distributions','No automatic policy or execution changes'],
                replay_only=utc(computed_at)>utc(snapshot['as_of']))
    result['output_id']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    return result
