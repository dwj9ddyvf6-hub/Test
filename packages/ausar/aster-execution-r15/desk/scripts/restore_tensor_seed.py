#!/usr/bin/env python3
"""Restore the exact research input seed; bounded retried, cached metadata reads."""
import argparse,hashlib,importlib.util,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(__file__).with_name('restore_native_cache_git.py')
EXPECTED='9fba9ffe95502f985f70a250a1e40142502691055f09c4b18a7576367f1a65a2'
COMMIT='4f292e229f7526f2d11a95a1549d90bf2fe47cb9'
PREFIX='research/native-cache-r11/tensor-r11-native-cache-v2-20261009T031700Z-dc3a9ebc'

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'data/research-seed-r11');p.add_argument('--receipt',type=Path,required=True);a=p.parse_args()
 if hashlib.sha256(SOURCE.read_bytes()).hexdigest()!=EXPECTED:raise RuntimeError('Frozen reconstruction helper differs from its pinned identity')
 spec=importlib.util.spec_from_file_location('research_seed_restore',SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 original_api=m.api;cache={};retries=[]
 def cached_api(endpoint):
  if endpoint not in cache:
   for attempt in range(4):
    try:
     d=original_api(endpoint)
     if '/git/trees/' in endpoint and d.get('truncated') is not False:raise RuntimeError('Incomplete tree response')
     cache[endpoint]=d;break
    except RuntimeError:
     if attempt==3:raise
     retries.append({'endpoint':endpoint,'attempt':attempt+1});time.sleep(min(2**attempt,4))
  return cache[endpoint]
 m.api=cached_api
 result=m.verify_or_restore(COMMIT,PREFIX,'native-inputs',str(a.output))
 result.update({'schema':'tensor-r12-immutable-seed-restore/1','repository':m.REPOSITORY,'prefix':PREFIX,'output':str(a.output.resolve()),'original_restore_source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'metadata_retries':retries,'unique_metadata_reads':len(cache),'fits_or_financial_trials':0})
 a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['metadata_retries']}))
if __name__=='__main__':main()
