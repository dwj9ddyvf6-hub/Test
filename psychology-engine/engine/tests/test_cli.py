import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from psychology_engine.__main__ import main

class CLITests(unittest.TestCase):
    def test_monitor_failure_and_partial_exit_codes(self):
        for outcomes,code,status in (([{'source':'fed_press','status':'failed','error_type':'TimeoutError'}],1,'failed'),([{'source':'fed_press','status':'ok','inserted':1},{'source':'fed_press','status':'failed','error_type':'TimeoutError'}],3,'partial'),([{'source':'fed_press','status':'ok','inserted':1}],0,'ok')):
            with tempfile.TemporaryDirectory() as folder:
                config=Path(folder)/'config.json';config.write_text(json.dumps({'fed_press':{'config_version':'fixture-authorized','persistent_use_authorized':True}}))
                args=['psychology_engine','--db',str(Path(folder)/'db.sqlite'),'monitor','--source','fed_press','--cycles',str(len(outcomes)),'--source-config',str(config)]
                buffer=io.StringIO()
                with patch('sys.argv',args),patch('sys.stdout',buffer),patch('psychology_engine.__main__.collect',side_effect=outcomes),patch('psychology_engine.__main__.time.sleep'):
                    self.assertEqual(main(),code)
                summary=json.loads(buffer.getvalue().splitlines()[-1]);self.assertEqual(summary['status'],status);self.assertEqual(summary['outcomes'],outcomes)
    def test_complete_registry_and_four_detector_counts(self):
        p=Path('docs/research_companion')
        self.assertEqual(len(json.loads((p/'pattern_registry.json').read_text())['patterns']),16)
        self.assertEqual(len(json.loads((p/'data_source_registry.json').read_text())['sources']),50)
        capability=json.loads(Path('psychology_engine/capabilities.json').read_text())
        self.assertEqual(len(capability['implemented_detectors']),4)
        self.assertEqual(len(capability['research_cards']),16)
