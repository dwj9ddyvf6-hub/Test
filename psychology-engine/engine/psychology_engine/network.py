"""Conservative interpretation of the documented managed-runtime v1 policy.
The sidecar remains the enforcement authority. Unknown rule semantics never grant
access. No fallback route, redirect, proxy override or policy mutation exists.
"""
import json
from pathlib import Path
from urllib.parse import urlsplit


def decision(url,policy,method='GET'):
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.username or parsed.password or parsed.port not in (None,443):
        return {'allowed':False,'reason':'collector_requires_public_https_default_port'}
    if method!='GET':return {'allowed':False,'reason':'collector_supports_GET_only'}
    if not isinstance(policy,dict) or policy.get('version')!=1:
        return {'allowed':False,'reason':'unsupported_or_missing_policy_version'}
    http=policy.get('http_network_policy')
    if not isinstance(http,dict):return {'allowed':False,'reason':'missing_http_policy'}
    mode=http.get('type')
    if mode=='unrestricted':return {'allowed':True,'reason':'documented_unrestricted_policy_sidecar_still_applies'}
    if mode!='restricted':return {'allowed':False,'reason':'unsupported_http_policy_mode'}
    rules=http.get('egress_rules')
    if not isinstance(rules,list):return {'allowed':False,'reason':'unsupported_egress_rules'}
    host=(parsed.hostname or '').lower()
    for rule in rules:
        # Only the host-only schema is documented and present in this executor.
        # Do not guess wildcard, method, path, scheme, port or deny precedence.
        if not isinstance(rule,dict) or set(rule)!={'host'}:continue
        granted=rule['host']
        if not isinstance(granted,str) or any(c in granted for c in '*:/?#@[]'):continue
        if granted.lower()==host:return {'allowed':True,'reason':'exact_host_rule'}
    return {'allowed':False,'reason':'no_supported_exact_host_grant','host':host,'method':method,'scheme':'https'}


def check(url,path='/etc/codex/network-policy.json'):
    p=Path(path)
    if not p.is_file():raise PermissionError('network policy not present; supply an independently reviewed deployment policy')
    result=decision(url,json.loads(p.read_text()))
    if not result['allowed']:raise PermissionError(result['reason'])
    return result
