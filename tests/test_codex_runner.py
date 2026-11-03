import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from betaforge.codex_runner import AppServer, child_environment, integration_smoke_prompt, run, safe_event, verify_implementation, verify_prompt


class RunnerTests(unittest.TestCase):
    def test_run_requests_and_records_sol_xhigh(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            prompt=root/'prompt.md';prompt.write_text('Inspect the supplied evidence.')
            tools=Mock(analysis_contract={},packet={},identity={})
            tools.state={'calculations':{},'inputs':{},'rounds':[]}
            tools.coverage.return_value={'complete':True,'delivered_pages':0}
            tools.catalogue.return_value={}
            tools.get_calculation_definitions.return_value={}
            code='''import sys,json
for line in sys.stdin:
 m=json.loads(line)
 method=m.get('method')
 if 'id' not in m:continue
 result={}
 if method=='thread/start':result={'model':'gpt-6.1-sol','thread':{'id':'thread'}}
 if method=='turn/start':result={'turn':{'id':'turn'}}
 print(json.dumps({'id':m['id'],'result':result}),flush=True)
 if method=='turn/start':
  print(json.dumps({'method':'item/completed','params':{'item':{'type':'agentMessage','phase':'final_answer','text':'Complete.'}}}),flush=True)
  print(json.dumps({'method':'turn/completed','params':{'turn':{'id':'turn','status':'completed'}}}),flush=True)
'''
            def fake_server(executable,cwd,event_path):
                return AppServer('',cwd,event_path,command=[sys.executable,'-u','-c',code])
            with patch('betaforge.codex_runner.EvidenceTools',return_value=tools), \
                 patch('betaforge.codex_runner.AppServer',side_effect=fake_server), \
                 patch('betaforge.codex_runner.subprocess.run',return_value=subprocess.CompletedProcess([],0,'fake codex')):
                state=run(root/'packet.json',prompt,root/'run',timeout_seconds=5)
            self.assertEqual(state['status'],'completed')
            events=[json.loads(line) for line in (root/'run/events.jsonl').read_text().splitlines()]
            requests={event['message'].get('method'):event['message'].get('params',{})
                      for event in events if event['direction']=='out'}
            thread=requests['thread/start'];turn=requests['turn/start']
            self.assertEqual(thread['model'],'gpt-6.1-sol')
            self.assertEqual(thread['config']['model_reasoning_effort'],'xhigh')
            self.assertFalse(thread['allowProviderModelFallback'])
            self.assertEqual((turn['model'],turn['effort']),('gpt-6.1-sol','xhigh'))
            saved=json.loads((root/'run/run.json').read_text())
            self.assertEqual((saved['model'],saved['reasoning_effort']),('gpt-6.1-sol','xhigh'))

    def test_smoke_uses_supplied_report_without_company_or_period_assumptions(self):
        prompt=integration_smoke_prompt(['other-issuer-annual-2030'])
        self.assertIn('"other-issuer-annual-2030"',prompt)
        self.assertIn('original page 1 image',prompt)
        self.assertIn('revenue_ebit',prompt)
        self.assertNotIn('granges',prompt.lower())
        self.assertNotIn('Q3',prompt)
        with self.assertRaisesRegex(ValueError,'supplied report'):
            integration_smoke_prompt([])

    def test_child_environment_excludes_provider_credentials(self):
        with patch.dict(os.environ, {'BORSDATA_API_KEY':'test','OPENAI_API_KEY':'test','SOME_SECRET':'test','PATH':'ordinary'}):
            environment=child_environment()
            self.assertNotIn('BORSDATA_API_KEY',environment)
            self.assertNotIn('OPENAI_API_KEY',environment)
            self.assertNotIn('SOME_SECRET',environment)
            self.assertEqual(environment['PATH'],'ordinary')

    def test_prompt_identity_for_packet_and_resume(self):
        signature=verify_prompt({},'original')
        self.assertEqual(verify_prompt({'prompt_sha256':signature},'original'),signature)
        with self.assertRaises(ValueError):verify_prompt({'prompt_sha256':signature},'changed')
        with self.assertRaises(ValueError):verify_prompt({},'changed',{'prompt_sha256':signature})

    def test_resume_requires_same_formula_and_tool_implementation(self):
        current={'tools.py':'a','financials.py':'b','storage.py':'c','codex_runner.py':'d'}
        verify_implementation(current,{'implementation_sha256':dict(current)})
        changed=dict(current,**{'financials.py':'changed'})
        with self.assertRaisesRegex(ValueError,'separately identified'):
            verify_implementation(changed,{'implementation_sha256':current})
        with self.assertRaisesRegex(ValueError,'complete formula identity'):
            verify_implementation(current,{'implementation_sha256':{'tools.py':'a'}})

    def test_event_log_does_not_duplicate_image_data(self):
        result=safe_event({'content':[{'imageUrl':'data:image/png;base64,TEST'}]})
        self.assertNotIn('base64,TEST',json.dumps(result))
        self.assertIn('image_data_sha256',json.dumps(result))

    def test_jsonrpc_round_trip_and_interruption_message(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            code='''import sys,json
for line in sys.stdin:
 m=json.loads(line)
 if 'id' in m:print(json.dumps({'id':m['id'],'result':{'method':m['method']}}),flush=True)
'''
            server=AppServer('',root,root/'events.jsonl',command=[sys.executable,'-u','-c',code])
            request=server.request('initialize',{})
            self.assertEqual(server.wait_response(request,time.monotonic()+3,lambda _:None)['method'],'initialize')
            server.shutdown('thread','turn')
            events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
            self.assertTrue(any(e['message'].get('method')=='turn/interrupt' for e in events))
            self.assertIsNotNone(server.process.poll())

    def test_silent_server_deadline_is_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            server=AppServer('',root,root/'events.jsonl',command=[sys.executable,'-u','-c','import sys\nfor line in sys.stdin: pass'])
            started=time.monotonic()
            try:
                request=server.request('initialize',{})
                with self.assertRaises(TimeoutError):server.wait_response(request,time.monotonic()+0.1,lambda _:None)
                self.assertLess(time.monotonic()-started,1)
            finally:server.shutdown()


if __name__=='__main__':unittest.main()
