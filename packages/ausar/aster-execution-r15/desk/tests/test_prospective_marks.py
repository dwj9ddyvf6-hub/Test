"""Read-only valuation fixtures; not historical or prospective profit samples."""
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from backend.prospective_projection import _observed_marks, prospective_snapshot

UTC=timezone.utc
NOW=datetime(2026,10,9,21,0,0,tzinfo=UTC)


def native():
    def quote(bid,ask,age):
        stamp=(NOW-timedelta(seconds=age)).isoformat()
        return {'bid':bid,'ask':ask,'as_of':stamp,'received_at':stamp,'private_unknown':'retained'}
    return {'status':'installed','installed_count':1,'worker':{'running':False},'extra_component':{'x':1},
        'market_data':{'at':(NOW-timedelta(seconds=1)).isoformat(),
                      'quotes':{'BTC-USD':quote('200.10','200.20',5),'ETH-USD':quote('15.05','15.10',7)}},
        'books':[{'sleeve':'BTC_ETH_SMA200','enabled':True,'cash':'1000.12','virtual_principal':'1000',
                  'positions':{'BTC-USD':'0.5','ETH-USD':'2.0'},'mark_scope':'legacy midpoint scope',
                  'last_observed_mid_nav':'old midpoint value','arbitrary_unknown':{'nested':[1,2]}}]}


def recipe():
    stamp=(NOW-timedelta(seconds=2)).isoformat()
    return {'installed':True,'paper_only':True,'event_count':9,'books':[{
        'id':'PUBLIC_IU_BODY_SPOT100','strategy':'iu_body','enabled':False,'symbol':'ETHUSDT','quote_currency':'USDT',
        'cash':'1.50','virtual_principal':500,'position':{'side':'long','qty':'0.125','avg_price':4000},
        'marked_equity':'legacy value untouched','last_receipt':{'capture':{
            'quote':{'bid':'4000.12','ask':'4000.13','asof':stamp},
            'receipts':{'quote':{'received_at':stamp}},'contract':{'symbol':'ETHUSDT','quote_asset':'USDT'}}}}]}


class ProspectiveMarkTests(unittest.TestCase):
    def test_known_native_bid_equity_net_pnl_and_oldest_observed_clock(self):
        source=native();before=copy.deepcopy(source);out=_observed_marks(source,'native',NOW)
        b=out['books'][0]
        # Independently calculated: 1000.12 + .5*200.10 + 2*15.05 = 1130.27.
        self.assertEqual(Decimal(b['observed_marked_equity']),Decimal('1130.27'))
        self.assertEqual(Decimal(b['net_pnl']),Decimal('130.27'));self.assertEqual(b['mark_currency'],'USD')
        self.assertEqual(b['mark_age_seconds'],7);self.assertTrue(b['mark_fresh'])
        self.assertEqual(b['mark_as_of'],(NOW-timedelta(seconds=7)).isoformat())
        self.assertEqual(source,before)
        for key,value in before['books'][0].items():self.assertEqual(b[key],value)
        self.assertIn('gross position',b['observed_mark_scope']);self.assertIn('future liquidation fees',b['observed_mark_scope'])
    def test_known_recipe_bid_equity_in_usdt_with_actual_incurred_cash_cost(self):
        source=recipe();out=_observed_marks(source,'public_recipes',NOW);b=out['books'][0]
        # Cash is already post-fee; no additional historical fee is charged here.
        self.assertEqual(Decimal(b['observed_marked_equity']),Decimal('501.515'))
        self.assertEqual(Decimal(b['net_pnl']),Decimal('1.515'));self.assertEqual(b['mark_currency'],'USDT')
        self.assertEqual(b['mark_max_age_seconds'],10);self.assertEqual(b['mark_age_seconds'],2)
        self.assertEqual(b['id'],source['books'][0]['id']);self.assertEqual(b['marked_equity'],'legacy value untouched')
    def test_dated_mark_keeps_price_value_and_never_becomes_current(self):
        source=native();later=NOW+timedelta(hours=1);out=_observed_marks(source,'native',later)['books'][0]
        self.assertEqual(Decimal(out['observed_marked_equity']),Decimal('1130.27'))
        self.assertEqual(out['mark_age_seconds'],3607);self.assertFalse(out['mark_fresh'])
        self.assertEqual(out['mark_status'],'dated_received_quote_mark')
        self.assertEqual(out['mark_as_of'],(NOW-timedelta(seconds=7)).isoformat())
    def test_held_missing_quote_withholds_complete_book_mark(self):
        source=native();source['market_data']['quotes'].pop('ETH-USD')
        b=_observed_marks(source,'native',NOW)['books'][0]
        self.assertIsNone(b['observed_marked_equity']);self.assertIsNone(b['net_pnl']);self.assertIsNone(b['mark_as_of'])
        self.assertEqual(b['mark_status'],'withheld');self.assertFalse(b['mark_fresh'])
    def test_flat_cash_is_valid_without_any_quote(self):
        a=native();a['books'][0]['positions']={};a.pop('market_data')
        b=_observed_marks(a,'native',NOW)['books'][0]
        self.assertEqual(Decimal(b['observed_marked_equity']),Decimal('1000.12'));self.assertEqual(Decimal(b['net_pnl']),Decimal('.12'))
        self.assertEqual(b['mark_status'],'cash_only');self.assertEqual(b['mark_as_of'],NOW.isoformat())
        a=recipe();a['books'][0]['position']=None;a['books'][0].pop('last_receipt')
        b=_observed_marks(a,'public_recipes',NOW)['books'][0]
        self.assertEqual(Decimal(b['observed_marked_equity']),Decimal('1.50'));self.assertEqual(Decimal(b['net_pnl']),Decimal('-498.50'))
        # Malformed unused market data must not obscure an authoritative flat cash balance.
        a['books'][0]['last_receipt']=True
        self.assertEqual(_observed_marks(a,'public_recipes',NOW)['books'][0]['mark_status'],'cash_only')
        a=native();a['books'][0]['positions']={};a['market_data']=True
        self.assertEqual(_observed_marks(a,'native',NOW)['books'][0]['mark_status'],'cash_only')
    def test_native_malformed_inverted_future_or_unobserved_quotes_withheld(self):
        cases=[]
        for value in [True,None,'NaN','Infinity','-1','0',float('nan')]:
            x=native();x['market_data']['quotes']['BTC-USD']['bid']=value;cases.append(x)
        x=native();x['market_data']['quotes']['BTC-USD']['ask']='199.99';cases.append(x)
        x=native();x['market_data']['quotes']['BTC-USD']['as_of']=None;cases.append(x)
        x=native();x['market_data']['quotes']['BTC-USD']['as_of']='2026-10-09T21:00:00';cases.append(x)
        x=native();x['market_data']['quotes']['BTC-USD']['as_of']=(NOW+timedelta(seconds=1)).isoformat();cases.append(x)
        x=native();x['market_data']['quotes']['BTC-USD']['received_at']=(NOW+timedelta(seconds=1)).isoformat();cases.append(x)
        x=native();x['market_data']['at']=(NOW+timedelta(seconds=1)).isoformat();cases.append(x)
        for index,source in enumerate(cases):
            with self.subTest(case=index):
                out=_observed_marks(source,'native',NOW)['books'][0]
                self.assertIsNone(out['observed_marked_equity']);self.assertIsNone(out['net_pnl']);self.assertIn('mark_error',out)
    def test_recipe_missing_receipt_or_wrong_contract_is_withheld(self):
        for mutation in ['receipt','instrument','currency','contract_missing','contract_null','contract_bool','short','quantity','cash']:
            source=recipe();book=source['books'][0];capture=book['last_receipt']['capture']
            if mutation=='receipt':capture.pop('receipts')
            elif mutation=='instrument':capture['contract']['symbol']='BTCUSDT'
            elif mutation=='currency':capture['contract']['quote_asset']='USD'
            elif mutation=='contract_missing':capture.pop('contract')
            elif mutation=='contract_null':capture['contract']=None
            elif mutation=='contract_bool':capture['contract']=True
            elif mutation=='short':book['position']['side']='short'
            elif mutation=='quantity':book['position']['qty']=True
            elif mutation=='cash':book['cash']='NaN'
            with self.subTest(mutation=mutation):self.assertIsNone(_observed_marks(source,'public_recipes',NOW)['books'][0]['observed_marked_equity'])
    def test_quote_freshness_matches_separate_native_and_recipe_limits(self):
        a=native();b=recipe()
        native_mark=_observed_marks(a,'native',NOW+timedelta(seconds=5))['books'][0]
        recipe_mark=_observed_marks(b,'public_recipes',NOW+timedelta(seconds=9))['books'][0]
        self.assertTrue(native_mark['mark_fresh']);self.assertFalse(recipe_mark['mark_fresh'])
        self.assertEqual(recipe_mark['mark_as_of'],(NOW-timedelta(seconds=2)).isoformat())
    def test_books_are_never_added_converted_or_mutated(self):
        source=native();second=copy.deepcopy(source['books'][0]);second.update(sleeve='ETH_SMA200',cash='7',virtual_principal='20',positions={})
        source['books'].append(second);before=copy.deepcopy(source)
        out=_observed_marks(source,'native',NOW)
        self.assertEqual(len(out['books']),2);self.assertEqual(source,before)
        self.assertEqual(out['books'][1]['observed_marked_equity'],'7');self.assertNotIn('total_equity',out)
        self.assertEqual(out['status'],before['status']);self.assertEqual(out['worker'],before['worker'])
    def test_projection_reads_existing_payloads_without_writes_or_constructors(self):
        with tempfile.TemporaryDirectory()as tmp,patch.dict(os.environ,{},clear=True):
            directory=Path(tmp)
            for name in ['native-prospective.sqlite','public-recipes.sqlite','original-research.sqlite']:(directory/name).write_bytes(b'opaque synthetic reader fixture')
            before={p.name:p.read_bytes()for p in directory.iterdir()}
            payloads={'backend.prospective_native':native(),'backend.public_recipe_runtime':recipe(),'backend.original_research_runtime':{'registered':True,'funding':0,'unknown':'preserved'}}
            original=copy.deepcopy(payloads)
            reader=lambda module:SimpleNamespace(read_status=lambda path:payloads[module])
            class FixedDatetime(datetime):
                @classmethod
                def now(cls,tz=None):return NOW.astimezone(tz)if tz else NOW.replace(tzinfo=None)
            # Set the clock before replacing the shared importlib function used by patch itself.
            with patch('backend.prospective_projection.datetime',FixedDatetime),patch('backend.prospective_projection.importlib.import_module',side_effect=reader):
                output=prospective_snapshot(directory/'aster.sqlite')
            self.assertEqual(payloads,original)
            self.assertEqual(before,{p.name:p.read_bytes()for p in directory.iterdir()})
            self.assertEqual(output['original_research'],original['backend.original_research_runtime'])
            self.assertEqual(output['native']['books'][0]['mark_currency'],'USD')
            self.assertEqual(output['public_recipes']['books'][0]['mark_currency'],'USDT')
            json.dumps(output,allow_nan=False)


if __name__=='__main__':unittest.main()
