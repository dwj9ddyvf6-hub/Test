import ast
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest

from backend.tensor_daily_models import (
    ALL_COLUMNS, ASSET_ROOT, PRICE_VOLUME_COLUMNS, MANIFEST_SHA256,
    DailyModelInputError, DailyModelIntegrityError, anchor_for, evaluate_daily20,
    feature_frame, load_frozen_models, phase, rank_daily20, verify_model_assets,
)


class FrozenDaily20ModelsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = load_frozen_models()
        cls.known = json.loads((ASSET_ROOT / 'AMD_C01_LEDGER_ORACLE.json').read_text())

    def synthetic(self, count=None):
        anchor = anchor_for('AMD')
        if count is None:
            count = 234 + ((anchor.phase - 233) % 20)
        rows = []
        for i in range(count):
            timestamp = anchor.first_timestamp + i * 86400
            row = {key: 1.0 for key in (
                'open', 'close', 'volume', 'atr14', 'return20', 'return60', 'rvol', 'dollar_volume20',
                'ema21', 'bullish_votes', 'bearish_votes', 'ribbon_inversion_count', 'ribbon_width',
                'ribbon_slope', 'obv_slope5', 'squeeze_on', 'squeeze_momentum', 'squeeze_length',
                'mcdx_position', 'mcdx_position_delta3', 'macd_histogram', 'efficiency10',
                'normalized_sign_entropy20', 'prior_sell_avwap', 'overhead60_atr',
                'vote_stoch', 'vote_aroon', 'vote_di', 'vote_obv', 'vote_squeeze', 'vote_pivot', 'vote_wave',
            )}
            row.update(symbol='AMD', interval='1d', bar_index=i, timestamp=timestamp,
                       completed_at=timestamp + 23400, usable_at=timestamp + 23400,
                       source_origin_timestamp=anchor.first_timestamp, native_status='ready',
                       close=20.0, open=20.0, ema21=19.0, volume=1e6, dollar_volume20=2e6,
                       ut_regime='bullish', prior_sell_completed_at=None)
            rows.append(row)
        return rows

    def evaluate(self, rows, **kwargs):
        return evaluate_daily20('AMD', rows, as_of_ms=kwargs.get('as_of_ms', rows[-1]['usable_at'] * 1000))

    def test_frozen_assets_and_exact_original_thresholds(self):
        receipt = verify_model_assets()
        self.assertEqual(receipt['status'], 'PASS')
        self.assertEqual(receipt['new_fits'], 0)
        self.assertEqual(receipt['canonical_symbols'], 1817)
        self.assertEqual(hashlib.sha256((ASSET_ROOT / 'MANIFEST.json').read_bytes()).hexdigest(), MANIFEST_SHA256)
        pv = self.models['price_volume']
        tensor = self.models['price_volume_plus_tensor']
        self.assertEqual(pv.columns, PRICE_VOLUME_COLUMNS)
        self.assertEqual(tensor.columns, ALL_COLUMNS)
        self.assertEqual(len(tensor.columns), 35)
        self.assertEqual(pv.threshold, 0.006985566706545021)
        self.assertEqual(tensor.threshold, 0.006122960477423353)
        for model in self.models.values():
            self.assertEqual(len(model.trees), 100)
            self.assertEqual(model.impute({c: None for c in model.columns}), model.medians)

    def test_original_sklearn_numerical_oracles(self):
        for name, model in self.models.items():
            oracle = json.loads((ASSET_ROOT / (name + '-oracle.json')).read_text())
            for vector, expected in zip(oracle['vectors'], oracle['expected_predictions']):
                prediction = model.predict(dict(zip(model.columns, vector)))
                self.assertEqual(prediction, expected)

    def test_known_c01_financial_prediction_parity_without_fitting(self):
        self.assertEqual(self.known['transform_max_absolute_difference'], 0.0)
        self.assertTrue(self.known['transform_null_masks_equal'])
        self.assertEqual(len(self.known['records']), 32)
        for record in self.known['records']:
            for name, model in self.models.items():
                prediction = model.predict(record['features'])
                self.assertEqual(prediction, record['portable_predictions'][name])
                # Original CSV predictions carry twelve significant digits.
                self.assertAlmostEqual(prediction, record['original_ledger_predictions'][name], delta=1e-12)

    @unittest.skipUnless(shutil.which('node'), 'Native engine requires Node')
    def test_native_daily_transform_reproduces_archived_predictions(self):
        from backend.tensor_engine import extract_native_feature_rows
        path = ASSET_ROOT.parents[1] / 'tensor_state_repair/engine/fixtures/AMD-1d-completed.json'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), self.known['fixture_sha256'])
        fixture = json.loads(path.read_text())
        history = extract_native_feature_rows('AMD', '1d', fixture['bars'],
                                              as_of_ms=fixture['bars'][-1]['usable_at_ms'])
        transformed = feature_frame(history.rows)
        for record in self.known['records']:
            vector = transformed[record['bar_index']]
            self.assertEqual(vector, record['features'])
            decisions = self.evaluate(history.rows[:record['bar_index'] + 1])
            for d in decisions:
                name = 'price_volume' if d.sleeve_id == 'D20_PV' else 'price_volume_plus_tensor'
                self.assertTrue(d.eligible)
                self.assertEqual(d.score, record['portable_predictions'][name])
                self.assertEqual(d.selected, d.score >= d.threshold)
                self.assertEqual(d.entry_bar_index, d.bar_index + 1)
                self.assertEqual(d.target_exit_bar_index, d.bar_index + 21)

    def test_threshold_boundary_is_inclusive_and_unmodified(self):
        for model in self.models.values():
            self.assertTrue(model.selects(model.threshold))
            self.assertFalse(model.selects(math.nextafter(model.threshold, -math.inf)))
            with self.assertRaises(DailyModelInputError):
                model.selects(math.nan)

    def test_original_modulo_phase_and_missing_future_horizon(self):
        rows = self.synthetic()
        d = self.evaluate(rows)
        self.assertEqual(len(d), 2)
        self.assertTrue(all(x.eligible for x in d))
        self.assertTrue(all(x.bar_index % 20 == phase('AMD') for x in d))
        self.assertTrue(all(x.entry_bar_index == len(rows) for x in d))
        self.assertTrue(all(x.hold_bars == 20 for x in d))
        # No next bar, next opening, future exit or label exists in this input.
        rows.append(dict(rows[-1], bar_index=len(rows), timestamp=rows[-1]['timestamp'] + 86400,
                         completed_at=rows[-1]['completed_at'] + 86400, usable_at=rows[-1]['usable_at'] + 86400))
        self.assertTrue(all(x.reason == 'phase_not_selected' and x.score is None for x in self.evaluate(rows)))

    def test_explicit_readiness_liquidity_and_exclusion_reasons(self):
        for field, value, reason in (
            ('native_status', 'warmup', 'native_not_ready'),
            ('close', 4.99, 'price_below_5'), ('dollar_volume20', 999999, 'liquidity_below_1m'),
            ('atr14', 0, 'invalid_atr'),
        ):
            rows = self.synthetic()
            rows[-1][field] = value
            self.assertTrue(all(x.reason == reason and not x.eligible for x in self.evaluate(rows)))
        self.assertTrue(all(x.reason == 'warmup' for x in self.evaluate(self.synthetic(100))))

    def test_no_silent_ordinal_origin_or_symbol_rebase(self):
        rows = self.synthetic()
        with self.assertRaisesRegex(DailyModelInputError, 'ordinal'):
            self.evaluate(rows[1:])
        rows = self.synthetic()
        rows[0]['timestamp'] += 1
        with self.assertRaisesRegex(DailyModelInputError, 'origin'):
            self.evaluate(rows)
        rows = self.synthetic()
        rows[15]['bar_index'] += 1
        with self.assertRaisesRegex(DailyModelInputError, 'ordinal'):
            self.evaluate(rows)
        with self.assertRaisesRegex(DailyModelInputError, 'enrollment'):
            anchor_for('UNKNOWN_NEW_STOCK')

    def test_forward_append_conserves_original_terminal_ordinal(self):
        anchor = anchor_for('AMD')
        rows = self.synthetic(anchor.original_rows)
        # Synthetic increasing clocks reach the original endpoint on the last row.
        step = (anchor.last_timestamp - anchor.first_timestamp) // (len(rows) - 1)
        for i, row in enumerate(rows):
            row['timestamp'] = anchor.first_timestamp + i * step
            row['completed_at'] = row['timestamp'] + 100
            row['usable_at'] = row['completed_at']
        rows[-1]['timestamp'] = anchor.last_timestamp
        rows[-1]['completed_at'] = anchor.last_timestamp + 100
        rows[-1]['usable_at'] = anchor.last_timestamp + 100
        self.evaluate(rows)
        # Dropping and reindexing an interior row preserves the origin/last date,
        # but destroys the archive's sampling ordinal and must fail.
        del rows[100]
        for i, row in enumerate(rows):
            row['bar_index'] = i
        with self.assertRaisesRegex(DailyModelInputError, 'endpoint ordinal'):
            self.evaluate(rows)

    def test_shared_actual_receipt_clock_for_historical_seed(self):
        rows = self.synthetic()
        # An entire seed can first become known in one provider response.
        # Original C1 requires completion <= usable, never a strict receipt order.
        receipt = rows[-1]['completed_at'] + 300
        for row in rows:
            row['usable_at'] = receipt
        self.assertTrue(all(d.eligible for d in self.evaluate(rows)))
        self.assertTrue(all(d.decision_at == receipt for d in self.evaluate(rows)))

    def test_invalid_or_future_clock_never_produces_decision(self):
        rows = self.synthetic()
        with self.assertRaisesRegex(DailyModelInputError, 'unavailable'):
            self.evaluate(rows, as_of_ms=rows[-1]['usable_at'] * 1000 - 1)
        rows[-1]['usable_at'] = rows[-1]['completed_at'] - 1
        with self.assertRaises(DailyModelInputError):
            self.evaluate(rows)
        rows = self.synthetic()
        rows[-1]['completed_at'] = rows[-2]['completed_at']
        with self.assertRaises(DailyModelInputError):
            self.evaluate(rows)
        rows = self.synthetic()
        del rows[-1]['return60']
        with self.assertRaisesRegex(DailyModelInputError, 'columns'):
            self.evaluate(rows)

    def test_future_sell_anchor_and_label_columns(self):
        rows = self.synthetic()
        base = self.evaluate(rows)
        for row in rows:
            row['c_future_return'] = 1000000
            row['forward_20_return'] = -9999
        self.assertEqual(self.evaluate(rows), base)
        rows[-1]['prior_sell_completed_at'] = rows[-1]['completed_at']
        with self.assertRaisesRegex(DailyModelInputError, 'earlier'):
            self.evaluate(rows)

    def test_causal_state_ages_and_neutral_vote_encoding(self):
        rows = self.synthetic(8)
        for row in rows:
            row['vote_stoch'] = None
        rows[0]['native_status'] = 'warmup'
        rows[1]['squeeze_on'] = 0
        rows[2]['squeeze_on'] = None
        rows[3]['squeeze_on'] = 0
        rows[4]['ut_regime'] = None
        transformed = feature_frame(rows)
        self.assertIsNone(transformed[0]['vote_stoch'])
        self.assertEqual(transformed[1]['vote_stoch'], 0)
        self.assertEqual(transformed[1]['squeeze_release_age'], 1)
        self.assertIsNone(transformed[3]['squeeze_release_age'])
        self.assertIsNone(transformed[4]['ut_state_age'])
        self.assertEqual(transformed[5]['ut_state_age'], 0)
        self.assertEqual(transformed[7]['ut_state_age'], 2)

    def test_rank_keeps_independent_sleeves_and_symbol_tie_break(self):
        d = self.evaluate(self.synthetic())[0]
        a = replace(d, selected=True, predicted_net_qqq_excess=0.02, symbol='Z')
        b = replace(d, selected=True, predicted_net_qqq_excess=0.02, symbol='A')
        c = replace(d, selected=True, predicted_net_qqq_excess=0.03, symbol='B')
        self.assertEqual([x.symbol for x in rank_daily20([a, b, c])], ['B', 'A', 'Z'])
        with self.assertRaisesRegex(DailyModelInputError, 'separately'):
            rank_daily20([a, replace(b, sleeve_id='D20_TENSOR')])

    def test_corrupt_numerical_body_rejected_before_prediction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'models'
            shutil.copytree(ASSET_ROOT, root)
            file = root / 'price_volume.json'
            file.write_bytes(file.read_bytes() + b' ')
            with self.assertRaises(DailyModelIntegrityError):
                load_frozen_models(root)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'models'
            shutil.copytree(ASSET_ROOT, root)
            file = root / 'MANIFEST.json'
            file.write_bytes(file.read_bytes() + b' ')
            with self.assertRaises(DailyModelIntegrityError):
                load_frozen_models(root)

    def test_runtime_has_no_fit_or_unpickle_operation(self):
        from backend import tensor_daily_models
        tree = ast.parse(Path(tensor_daily_models.__file__).read_text())
        called = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute)]
        self.assertNotIn('fit', called)
        self.assertNotIn('fit_predict', called)
        imports = [alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
                   for alias in node.names]
        self.assertNotIn('joblib', imports)
        self.assertNotIn('pickle', imports)


if __name__ == '__main__':
    unittest.main()
