import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from betaforge.codex_runner import AppServer, child_environment, integration_smoke_prompt, resolve_codex, run, safe_event, verify_implementation, verify_prompt


class RunnerTests(unittest.TestCase):
    def test_explicit_executable_precedes_path_and_mac_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ('explicit', 'codex', 'mac-codex'):
                executable=root/name;executable.write_text('#!/bin/sh\n');executable.chmod(0o700)
            with patch.dict(os.environ, {'PATH':str(root)}), \
                 patch('betaforge.codex_runner.DEFAULT_CODEX',str(root/'mac-codex')):
                self.assertEqual(resolve_codex(str(root/'explicit')),str(root/'explicit'))
                self.assertEqual(resolve_codex('explicit'),str(root/'explicit'))
                with self.assertRaisesRegex(FileNotFoundError,'not found or not executable'):
                    resolve_codex(str(root/'missing'))

    def test_default_executable_uses_path_before_mac_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ('codex', 'mac-codex'):
                executable=root/name;executable.write_text('#!/bin/sh\n');executable.chmod(0o700)
            with patch.dict(os.environ, {'PATH':str(root)}), \
                 patch('betaforge.codex_runner.DEFAULT_CODEX',str(root/'mac-codex')):
                self.assertEqual(resolve_codex(),str(root/'codex'))
            with patch.dict(os.environ, {'PATH':''}), \
                 patch('betaforge.codex_runner.DEFAULT_CODEX',str(root/'mac-codex')):
                self.assertEqual(resolve_codex(),str(root/'mac-codex'))

    def test_unavailable_executable_creates_no_output_or_evidence_store(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);output=root/'run'
            nonexecutable=root/'codex';nonexecutable.write_text('#!/bin/sh\n');nonexecutable.chmod(0o600)
            with patch.dict(os.environ, {'PATH':str(root)}), \
                 patch('betaforge.codex_runner.DEFAULT_CODEX',str(nonexecutable)), \
                 patch('betaforge.codex_runner.EvidenceTools') as tools:
                for executable in (None,str(nonexecutable),str(root/'missing')):
                    with self.subTest(executable=executable), self.assertRaisesRegex(FileNotFoundError,'Codex executable'):
                        run(root/'packet.json',None,output,executable=executable)
                    self.assertFalse(output.exists())
                tools.assert_not_called()

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
                self.assertEqual(executable,sys.executable)
                return AppServer('',cwd,event_path,command=[sys.executable,'-u','-c',code])
            with patch('betaforge.codex_runner.EvidenceTools',return_value=tools), \
                 patch('betaforge.codex_runner.shutil.which',return_value=sys.executable) as which, \
                 patch('betaforge.codex_runner.AppServer',side_effect=fake_server), \
                 patch('betaforge.codex_runner.subprocess.run',return_value=subprocess.CompletedProcess([],0,'fake codex')) as version:
                state=run(root/'packet.json',prompt,root/'run',timeout_seconds=5)
            which.assert_called_once_with('codex')
            self.assertEqual(version.call_args.args[0],[sys.executable,'--version'])
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
            self.assertIn('management_history.py', saved['implementation_sha256'])

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


class StructuredRunnerTests(unittest.TestCase):
    server_code = '''import sys,json
for line in sys.stdin:
 m=json.loads(line);method=m.get('method')
 if 'id' not in m:continue
 result={}
 if method in ('thread/start','thread/resume'):result={'model':'gpt-6.1-sol','thread':{'id':'thread'}}
 if method=='turn/start':result={'turn':{'id':'turn'}}
 print(json.dumps({'id':m['id'],'result':result}),flush=True)
 if method=='turn/start':
  print(json.dumps({'method':'item/completed','params':{'item':{'type':'agentMessage','phase':'final_answer','text':'Unsubmitted prose.'}}}),flush=True)
  print(json.dumps({'method':'turn/completed','params':{'turn':{'id':'turn','status':'completed'}}}),flush=True)
'''

    def invoke(self, root, tools, **options):
        def fake_server(executable,cwd,event_path):
            return AppServer('',cwd,event_path,command=[sys.executable,'-u','-c',self.server_code])
        with patch('betaforge.codex_runner.EvidenceTools',return_value=tools), \
             patch('betaforge.codex_runner.AppServer',side_effect=fake_server), \
             patch('betaforge.codex_runner.subprocess.run',return_value=subprocess.CompletedProcess([],0,'fake codex')):
            return run(root/'packet.json',root/'prompt.md',root/'run',timeout_seconds=5,executable=sys.executable,structured=True,**options)

    def tools(self):
        tools=Mock(analysis_contract={},packet={},identity={'packet_sha256':'packet'})
        tools.state={'calculations':{},'inputs':{},'rounds':[]}
        tools.coverage.return_value={'complete':True,'delivered_pages':0}
        tools.catalogue.return_value={};tools.get_calculation_definitions.return_value={}
        tools.reopen_revision_research.side_effect=lambda: tools.state.pop('analysis_sha256',None)
        return tools

    def test_structured_completion_requires_submission_and_does_not_replace_saved_answer(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'prompt.md').write_text('Original instructions.')
            state=self.invoke(root,self.tools())
            self.assertEqual(state['status'],'incomplete_submission')
            self.assertEqual(state['analysis_validation_status'],'not_submitted')
            self.assertFalse((root/'run/answer.md').exists())
            events=[json.loads(line) for line in (root/'run/events.jsonl').read_text().splitlines()]
            thread=next(e['message']['params'] for e in events if e['message'].get('method')=='thread/start')
            self.assertIn('submit_analysis',[t['name'] for t in thread['dynamicTools']])
            self.assertIn('schema_version:2', thread['baseInstructions'])
            self.assertIn('Omit all weights and weighted results unless evidence', thread['baseInstructions'])
            self.assertIn('analysis_report.py',state['implementation_sha256'])

    def test_feedback_revision_freezes_original_and_rejects_second_revision_or_changed_feedback(self):
        from betaforge.tools import digest, write_json
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'prompt.md').write_text('Original instructions.')
            tools=self.tools();first=self.invoke(root,tools)
            output=root/'run'
            (output/'analysis.json').write_text('{"draft": true}')
            (output/'answer.md').write_text('Original draft')
            first['analysis_sha256']=digest(output/'analysis.json')
            write_json(output/'run.json',first)
            tools.state['analysis_sha256']=first['analysis_sha256']
            feedback=dict(schema_version=1,packet_sha256='packet',analysis_sha256=first['analysis_sha256'],reviewer='Independent',verdict='revise',summary='Challenge forecast.',findings=[],disagreements=[])
            review=root/'feedback.json';write_json(review,feedback)
            changed=dict(feedback,analysis_sha256='fabricated');write_json(review,changed)
            with self.assertRaisesRegex(ValueError,'hash'):self.invoke(root,tools,resume=True,review_feedback=review)
            self.assertFalse((output/'prior-invocations').exists())
            write_json(review,feedback)
            revised=self.invoke(root,tools,resume=True,review_feedback=review)
            self.assertEqual(revised['revision_count'],1)
            self.assertEqual(revised['content_review_status'],'revision_pending_review')
            self.assertEqual((output/'prior-invocations/000-answer.md').read_text(),'Original draft')
            self.assertEqual(json.loads((output/'prior-invocations/000-analysis.json').read_text()),{'draft':True})
            self.assertEqual(revised['prompt_sha256'],first['prompt_sha256'])
            self.assertTrue((output/'resume-prompt.txt').read_text().startswith('Original instructions.'))
            self.assertIn('Challenge forecast.',(output/'resume-prompt.txt').read_text())
            self.assertEqual(revised['review_feedback_sha256'],digest(output/'review-feedback.json'))
            with self.assertRaisesRegex(ValueError,'one review revision'):self.invoke(root,tools,resume=True,review_feedback=review)
            (output/'review-feedback.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'feedback changed'):self.invoke(root,tools,resume=True)

    def test_feedback_requires_explicit_structured_resume(self):
        with self.assertRaisesRegex(ValueError,'requires --resume --structured'):
            run('packet','prompt','unused',review_feedback='feedback')


    def test_preflight_failure_closes_initialized_store(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'prompt.md').write_text('')
            tools=self.tools()
            with self.assertRaisesRegex(ValueError,'Prompt required'):
                self.invoke(root,tools)
            tools.store.close.assert_called_once()

    def test_revision_startup_failure_preserves_recoverable_pending_state(self):
        import test_tools
        from betaforge.tools import digest, write_json
        for failure in ('prompt', 'workspace', 'server'):
            with self.subTest(failure=failure):
                fixture=test_tools.ToolsTests('test_search_does_not_satisfy_reading_and_full_pages_do')
                fixture.setUp()
                try:
                    root=fixture.root;output=(root/'newrun').resolve();prompt=root/'prompt.md'
                    prompt.write_text('Original instructions.')
                    def fake_server(executable,cwd,event_path):
                        return AppServer('',cwd,event_path,command=[sys.executable,'-u','-c',self.server_code])
                    def invoke(**options):
                        with patch('betaforge.codex_runner.AppServer',side_effect=fake_server), \
                             patch('betaforge.codex_runner.subprocess.run',return_value=subprocess.CompletedProcess([],0,'fake codex')):
                            return run(fixture.packet,prompt,output,timeout_seconds=5,executable=sys.executable,structured=True,**options)
                    first=invoke()
                    (output/'analysis.json').write_text('{"draft":true}')
                    (output/'answer.md').write_text('Original draft')
                    first.update(status='completed',analysis_sha256=digest(output/'analysis.json'))
                    write_json(output/'run.json',first)
                    tool_state=json.loads((output/'tool-state.json').read_text())
                    tool_state['analysis_sha256']=first['analysis_sha256']
                    write_json(output/'tool-state.json',tool_state)
                    feedback=dict(schema_version=1,packet_sha256=first['identity']['packet_sha256'],analysis_sha256=first['analysis_sha256'],reviewer='Independent',verdict='revise',summary='Challenge forecast.',findings=[],disagreements=[])
                    feedback_path=root/'feedback.json';write_json(feedback_path,feedback)
                    original_write=Path.write_text;original_mkdir=Path.mkdir
                    def write(path,*args,**kwargs):
                        if path==output/'resume-prompt.txt':raise OSError('Injected prompt failure')
                        return original_write(path,*args,**kwargs)
                    def mkdir(path,*args,**kwargs):
                        if path==output/'workspace':raise OSError('Injected workspace failure')
                        return original_mkdir(path,*args,**kwargs)
                    with patch('betaforge.codex_runner.subprocess.run',return_value=subprocess.CompletedProcess([],0,'fake codex')), \
                         patch('betaforge.codex_runner.AppServer',side_effect=OSError('Injected startup failure') if failure=='server' else fake_server), \
                         patch.object(Path,'write_text',write if failure=='prompt' else original_write), \
                         patch.object(Path,'mkdir',mkdir if failure=='workspace' else original_mkdir):
                        failed=run(fixture.packet,prompt,output,timeout_seconds=5,executable=sys.executable,structured=True,resume=True,review_feedback=feedback_path)
                    self.assertEqual(failed['status'],'failed')
                    self.assertEqual(failed['revision_count'],1)
                    self.assertIsNone(failed['analysis_sha256'])
                    self.assertEqual(failed['review_feedback_sha256'],digest(output/'review-feedback.json'))
                    pending=json.loads((output/'tool-state.json').read_text())
                    self.assertEqual(pending['revision_count'],1)
                    self.assertNotIn('analysis_sha256',pending)
                    self.assertEqual((output/'prior-invocations/000-answer.md').read_text(),'Original draft')
                    recovered=invoke(resume=True)
                    self.assertIn(recovered['status'],('incomplete_reading','incomplete_submission'))
                    self.assertEqual(recovered['revision_count'],1)
                    self.assertIn('Challenge forecast.',(output/'resume-prompt.txt').read_text())
                finally:
                    fixture.tearDown()
