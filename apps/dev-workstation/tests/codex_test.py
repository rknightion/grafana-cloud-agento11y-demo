"""Exercise the installed adapter boundary with a fake Codex process, never inference."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import tomllib
import unittest

ADAPTER = Path(__file__).resolve().parents[1] / 'agents/codex/adapter'


class CodexAdapterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'bin').mkdir()
        (self.root / 'work').mkdir()
        self.cfg = self.root / 'config.json'
        self.cfg.write_text(json.dumps({'provider': 'amazon-bedrock', 'region': 'us-east-1',
            'model': {'id': 'openai.gpt-5.6-luna', 'cost': {'input': .22, 'output': 1.32, 'cacheRead': .022, 'cacheWrite': .275}},
            'otel': {'endpoint': 'https://otlp.example.test/otlp', 'username': 'fixture'}}))
        self.key = self.root / 'aws'
        self.key.write_text('[default]\naws_access_key_id=fixture\naws_secret_access_key=fixture\n')
        self.key.chmod(0o600)
        self.token = self.root / 'token'
        self.token.write_text('separate-otlp-fixture')
        self.token.chmod(0o600)
        self.capture = self.root / 'capture.json'
        self.env = {**os.environ, 'HOME': str(self.root), 'PATH': str(self.root / 'bin') + ':' + os.environ['PATH'],
            'DEVELOPER_AGENT_CONFIG_FILE': str(self.cfg), 'AWS_SHARED_CREDENTIALS_FILE': str(self.key),
            'CODEX_OTLP_TOKEN_FILE': str(self.token), 'CODEX_MANAGED_CONFIG_FILE': str(ADAPTER.parent / 'managed-config.toml'),
            'AWS_ACCESS_KEY_ID': 'must-drop', 'AWS_BEARER_TOKEN_BEDROCK': 'must-drop',
            'AGENT_STATE_DIR': str(self.root / 'state'), 'CAPTURE': str(self.capture),
            'DEVELOPER_NAME': 'fixture-developer', 'DEVELOPER_TEAM': 'platform'}
        self.fake('''
import json, os, sys
from pathlib import Path
Path(os.environ['CAPTURE']).write_text(json.dumps({'args':sys.argv[1:], 'env':dict(os.environ), 'prompt':sys.stdin.read()}))
print(json.dumps({'type':'thread.started','thread_id':'00000000-0000-4000-8000-000000000001'}))
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'done'}}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':1000,'cached_input_tokens':200,'cache_write_input_tokens':100,'output_tokens':100,'reasoning_output_tokens':20}}))
''')

    def fake(self, source):
        target = self.root / 'bin/codex'
        target.write_text('#!/usr/bin/env python3\n' + textwrap.dedent(source))
        target.chmod(0o755)

    def invoke(self, op, *args):
        return subprocess.run([str(ADAPTER), op, *args], env=self.env, cwd=self.root/'work', text=True, capture_output=True, timeout=10)

    def run_turn(self, resume='', seconds='3'):
        return self.invoke('run', 'use tools safely', 'openai.gpt-5.6-luna', resume, seconds, '.3', 'low', 'touchline', str(self.root/'stderr'))

    def test_initial_resume_and_cumulative_cost(self):
        first = self.run_turn()
        self.assertEqual(first.returncode, 0, first.stderr)
        result = json.loads(first.stdout)
        self.assertEqual(result['cost_mode'], 'cumulative')
        self.assertAlmostEqual(result['total_cost_usd'], (.22*700 + .022*200 + .275*100 + 1.32*100)/1e6)
        self.assertFalse(result['is_error'])
        captured = json.loads(self.capture.read_text())
        self.assertNotIn('--ephemeral', captured['args'])
        self.assertNotIn('--bypass-hook-trust', captured['args'])
        sandbox = captured['args'].index('--sandbox')
        self.assertEqual(captured['args'][sandbox + 1], 'danger-full-access')
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', captured['args'])
        self.assertNotIn('AWS_ACCESS_KEY_ID', captured['env'])
        self.assertNotIn('AWS_BEARER_TOKEN_BEDROCK', captured['env'])
        self.assertIn('developer=fixture-developer', captured['env']['OTEL_RESOURCE_ATTRIBUTES'])
        self.assertEqual(captured['prompt'], 'use tools safely')
        resumed = self.run_turn(result['session_id'])
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        args = json.loads(self.capture.read_text())['args']
        self.assertIn('resume', args)
        self.assertIn(result['session_id'], args)
        self.assertAlmostEqual(json.loads(resumed.stdout)['total_cost_usd'], result['total_cost_usd'])

    def test_truncated_or_failed_stream_is_never_success(self):
        for source in ("print('{broken')", "print('{\"type\":\"turn.failed\",\"error\":{\"message\":\"policy blocked\"}}')"):
            self.fake(source)
            result = self.run_turn()
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(json.loads(result.stdout)['is_error'])

    def test_timeout_returns_error(self):
        self.fake('import time\ntime.sleep(30)')
        result = self.run_turn(seconds='.1')
        self.assertEqual(result.returncode, 124, result.stderr)
        self.assertTrue(json.loads(result.stdout)['is_error'])

    def test_reseed_native_otel_mcp_and_managed_hooks(self):
        self.env['SERVICE_NAMESPACE'] = 'renamed-demo'
        result = self.invoke('reseed')
        self.assertEqual(result.returncode, 0, result.stderr)
        cfg = tomllib.loads((self.root/'.codex/config.toml').read_text())
        self.assertEqual(cfg['model_provider'], 'amazon-bedrock')
        self.assertEqual(cfg['sandbox_mode'], 'danger-full-access')
        self.assertEqual(cfg['approval_policy'], 'never')
        self.assertFalse(cfg['analytics']['enabled'])
        self.assertLessEqual(cfg['model_context_window'], 272000)
        for field, signal in [('exporter','logs'),('trace_exporter','traces'),('metrics_exporter','metrics')]:
            self.assertEqual(cfg['otel'][field]['otlp-http']['endpoint'], 'https://otlp.example.test/otlp/v1/'+signal)
            self.assertTrue(cfg['otel'][field]['otlp-http']['headers']['Authorization'].startswith('Basic '))
        self.assertEqual(cfg['otel']['span_attributes']['developer'], 'fixture-developer')
        self.assertEqual(cfg['otel']['span_attributes']['service.namespace'], 'renamed-demo')
        self.assertEqual(cfg['mcp_servers']['touchline']['command'], 'node')
        self.assertEqual((self.root/'.codex/config.toml').stat().st_mode & 0o777, 0o600)
        managed = tomllib.loads((ADAPTER.parent/'managed-config.toml').read_text())
        self.assertEqual(managed['hooks'], json.loads((ADAPTER.parent/'hooks.json').read_text())['hooks'])
        self.assertTrue(managed['features']['hooks'])

    def test_unknown_model_and_insecure_credential_fail_before_spawn(self):
        self.key.chmod(0o644)
        result = self.run_turn()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.capture.exists())
        self.key.chmod(0o600)
        result = self.invoke('run', 'hi', 'unconfigured-model', '', '3', '.3', 'low', 'touchline', str(self.root/'stderr'))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.capture.exists())


if __name__ == '__main__':
    unittest.main()
