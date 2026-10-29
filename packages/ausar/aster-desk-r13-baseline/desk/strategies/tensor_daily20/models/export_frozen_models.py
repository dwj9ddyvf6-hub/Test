#!/usr/bin/env python3
"""Export two hash-pinned, trusted R11 artifacts. No fit or calibration occurs.

This one-time development utility requires the original scientific environment.
Runtime reads only the resulting JSON numerical trees, never joblib/pickle.
"""
from pathlib import Path
import argparse, hashlib, json, shutil

SOURCE_SHA = {
    'price_volume': '36216e1b8f0000066cf51356b70a7a54a885e154ee417a42d360ab921d634965',
    'price_volume_plus_tensor': 'e7776b115b908380dc3df85210302736d306d38538568e91e26cf3f6e0c4b300',
}

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, d):
    p.write_text(json.dumps(d, indent=2, allow_nan=False) + '\n')

def main():
    import joblib
    import numpy as np
    import sklearn
    parser = argparse.ArgumentParser()
    parser.add_argument('--research-root', type=Path, required=True)
    a = parser.parse_args()
    output = Path(__file__).resolve().parent
    c01 = a.research_root / 'experiments/predictive_information'
    files = []
    parity = []
    for name, expected in SOURCE_SHA.items():
        source = c01 / ('1d-H20-' + name + '.joblib.gz')
        if sha(source) != expected:
            raise ValueError('Original frozen model identity differs: ' + name)
        # Only these two exact, known research bodies are trusted for one-time load.
        saved = joblib.load(source)
        m = saved['model']
        if m.n_iter_ != 100 or m.is_categorical_ is not None or m.loss != 'squared_error':
            raise ValueError('Unsupported frozen estimator')
        trees = []
        for stage in m._predictors:
            if len(stage) != 1:
                raise ValueError('Unexpected multi-output stage')
            trees.append([
                {'value': float(n['value']), 'feature': int(n['feature_idx']),
                 'threshold': float(n['num_threshold']),
                 'left': int(n['left']), 'right': int(n['right']),
                 'leaf': bool(n['is_leaf']), 'missing_left': bool(n['missing_go_to_left'])}
                for n in stage[0].nodes
            ])
            if any(n['is_categorical'] for n in stage[0].nodes):
                raise ValueError('Categorical tree unsupported')
        payload = {
            'schema': 'tensor-daily20-frozen-numerical-model/1',
            'source_filename': source.name, 'source_sha256': expected,
            'source_plan_sha256': saved['plan_sha256'],
            'source_producer_sha256': saved['code_sha256'],
            'frame': '1d', 'hold_bars': 20, 'model': name,
            'columns': saved['columns'], 'medians': [float(x) for x in saved['medians']],
            'threshold': float(saved['threshold']),
            'baseline': float(m._baseline_prediction[0][0]),
            'trees': trees, 'original_fit_count': 1, 'new_fits': 0,
            'target': 'fractional stock return net 10bps per side minus gross QQQ return',
        }
        write(output / (name + '.json'), payload)
        shutil.copyfile(source, output / source.name)
        # Seeded arbitrary feature probes, medians and missing-value replacement.
        rng = np.random.default_rng(1109)
        z = rng.normal(size=(1000, len(saved['columns'])))
        z = np.vstack([saved['medians'], np.zeros(len(saved['columns'])), z])
        expected_predictions = m.predict(z)
        actual = []
        for vector in z:
            v = payload['baseline']
            for tree in trees:
                j = 0
                while not tree[j]['leaf']:
                    node = tree[j]
                    j = node['left'] if vector[node['feature']] <= node['threshold'] else node['right']
                v += tree[j]['value']
            actual.append(v)
        maximum = float(np.max(np.abs(np.asarray(actual) - expected_predictions)))
        if maximum > 1e-15:
            raise ValueError('Numerical tree export differs')
        parity.append({'model': name, 'probes': len(z), 'maximum_absolute_prediction_difference': maximum,
                       'new_fits': 0, 'source_sha256': expected})
        # A small exact sklearn oracle fixture, not financial-label calibration.
        write(output / (name + '-oracle.json'), {
            'schema': 'tensor-daily20-original-estimator-oracle/1',
            'model': name, 'source_sha256': expected, 'financial_outcomes_read': 0,
            'vectors': z[:16].tolist(), 'expected_predictions': expected_predictions[:16].tolist(),
        })
    preparation_path = a.research_root / 'experiments/INPUT_PREPARATION.json'
    preparation = json.loads(preparation_path.read_text())
    native_receipt_path = c01 / 'NATIVE_SOURCE_1d_RECEIPT.json'
    allowed = {g['symbol']: g for g in json.loads(native_receipt_path.read_text())['groups']}
    anchors = {}
    for source in preparation['sources']:
        for group in source['groups']:
            symbol = group['symbol']
            if group['interval'] == '1d' and symbol in allowed:
                anchors[symbol] = {
                    'symbol': symbol, 'frame': '1d',
                    'first_timestamp': group['first_timestamp'],
                    'last_timestamp': group['last_timestamp'],
                    'original_rows': group['accepted_bars'],
                    'input_sha256': group['sha256'],
                    'native_feature_sha256': allowed[symbol]['outputSha256'],
                    'phase': int(hashlib.sha256(symbol.encode()).hexdigest(), 16) % 20,
                }
    if len(anchors) != 1817:
        raise ValueError('Original daily source-anchor count differs')
    write(output / 'DAILY_SOURCE_ANCHORS.json', {
        'schema': 'tensor-daily20-canonical-source-anchors/1',
        'source_preparation_sha256': sha(preparation_path),
        'source_native_receipt_sha256': sha(native_receipt_path),
        'ordinal_contract': 'Supply every retained observed source bar from its exact original first timestamp; '
                            'no rolling-window truncation or origin rebase. New bars append to that ordinal sequence. '
                            'Matching origin alone does not certify an unchanged corporate-action adjustment history.',
        'symbols': dict(sorted(anchors.items())),
    })
    write(output / 'EXPORT_PROVENANCE.json', {
        'schema': 'tensor-daily20-portable-export-provenance/1',
        'status': 'PASS', 'new_fits': 0, 'new_calibrations': 0,
        'sklearn_version': sklearn.__version__, 'numpy_version': np.__version__,
        'source_producer_sha256': sha(a.research_root / 'scripts/test_predictive_information.py'),
        'exporter_sha256': sha(__file__), 'parity': parity,
        'runtime_unpickling': False,
    })
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != 'MANIFEST.json':
            files.append({'path': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path)})
    write(output / 'MANIFEST.json', {
        'schema': 'tensor-daily20-model-asset-manifest/1', 'status': 'FROZEN_ORIGINAL_R11_MODELS',
        'new_fits': 0, 'new_calibrations': 0, 'files': files,
    })
    print(json.dumps({'status': 'PASS', 'assets': len(files), 'manifest_sha256': sha(output / 'MANIFEST.json'), 'parity': parity}))

if __name__ == '__main__':
    main()
