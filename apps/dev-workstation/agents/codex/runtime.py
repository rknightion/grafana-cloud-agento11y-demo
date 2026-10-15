#!/usr/bin/env python3
"""Codex 0.162.1 single-turn adapter. No CLI login or inference during setup."""
import base64
import configparser
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import tomllib
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
HOME = Path.home()
CODEX_HOME = HOME / '.codex'
CONFIG = Path(os.environ.get('DEVELOPER_AGENT_CONFIG_FILE', '/run/codex/config.json'))
CREDENTIALS = Path(os.environ.get('AWS_SHARED_CREDENTIALS_FILE', '/run/secrets/developer_aws_credentials'))
TOKEN = Path(os.environ.get('CODEX_OTLP_TOKEN_FILE', '/run/secrets/codex_otlp_token'))
MANAGED = Path(os.environ.get('CODEX_MANAGED_CONFIG_FILE', '/etc/codex/config.toml'))


def private_file(file):
    info = file.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('credential must be a regular file owned by developer with mode 600')
    return file.read_text()


def configuration():
    cfg = json.loads(CONFIG.read_text())
    if cfg.get('provider') != 'amazon-bedrock' or not re.fullmatch(r'[a-z]{2}(?:-[a-z]+)+-\d+', cfg.get('region', '')):
        raise ValueError('Codex requires rendered amazon-bedrock provider and region')
    model = cfg.get('model', {})
    if not isinstance(model.get('id'), str) or not model['id'].startswith('openai.'):
        raise ValueError('Codex requires a rendered Bedrock OpenAI model id')
    for key in ('input', 'output', 'cacheRead', 'cacheWrite'):
        value = model.get('cost', {}).get(key)
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise ValueError('Codex requires explicit finite USD-per-million token prices')
    if min(model['cost']['input'], model['cost']['output']) <= 0:
        raise ValueError('Codex input and output prices must be positive')
    return cfg


def credentials_env(cfg):
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(private_file(CREDENTIALS))
    if not all(parser.get('default', key, fallback='').strip() for key in ('aws_access_key_id', 'aws_secret_access_key')):
        raise ValueError('incomplete scoped AWS credential')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('AWS_', 'OPENAI_', 'CODEX_'))}
    env.update(CODEX_HOME=str(CODEX_HOME), AWS_PROFILE='default', AWS_REGION=cfg['region'],
               AWS_SHARED_CREDENTIALS_FILE=str(CREDENTIALS), AWS_CONFIG_FILE='/dev/null', AWS_EC2_METADATA_DISABLED='true',
               OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE='cumulative',
               OTEL_RESOURCE_ATTRIBUTES=','.join(k+'='+v for k,v in static_tags().items()))
    return env


def static_tags():
    tags = {'agent':'codex', 'developer':os.environ.get('DEVELOPER_NAME','unknown'),
            'team':os.environ.get('DEVELOPER_TEAM','platform'),
            'service.namespace':os.environ.get('SERVICE_NAMESPACE','touchline')}
    if any(not re.fullmatch(r'[a-zA-Z0-9_.-]+', value) for value in tags.values()):
        raise ValueError('developer telemetry tags must be static safe identifiers')
    return tags


def quote(value):
    return json.dumps(value, ensure_ascii=False)


def write_config(text):
    CODEX_HOME.mkdir(mode=0o700, parents=True, exist_ok=True)
    if CODEX_HOME.is_symlink():
        raise ValueError('Codex home may not be a symlink')
    fd = os.open(CODEX_HOME/'config.toml', os.O_CREAT | os.O_TRUNC | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(text)


def reseed(cfg):
    # Managed system hooks are trusted by their deployment location, never by a CLI trust bypass.
    managed = tomllib.loads(MANAGED.read_text())
    if managed.get('hooks') != json.loads((HERE/'hooks.json').read_text())['hooks'] or not managed.get('features', {}).get('hooks'):
        raise ValueError('managed Codex hooks differ from pinned Grafana hooks')
    region = cfg['region']
    lines = [f'model = {quote(cfg["model"]["id"])}', 'model_provider = "amazon-bedrock"',
             'approval_policy = "never"', 'sandbox_mode = "danger-full-access"',
             'model_context_window = 272000', 'model_auto_compact_token_limit = 240000',
             'check_for_update_on_startup = false', 'web_search = "disabled"',
             'developer_instructions = "Work only inside the current seeded repository. Never commit, push, or clone another repository."',
             # Codex 0.162.1 disables even custom OTLP metrics when analytics is false.
             # All three exporters below are explicitly the operator's endpoint or none.
             '[analytics]', f'enabled = {str(bool(cfg.get("otel"))).lower()}', '[feedback]', 'enabled = false',
             '[model_providers.amazon-bedrock]', f'base_url = {quote("https://bedrock-mantle."+region+".api.aws/openai/v1")}',
             '[model_providers.amazon-bedrock.aws]', 'profile = "default"', f'region = {quote(region)}',
             '[shell_environment_policy]', 'inherit = "all"',
             'exclude = ["AWS_*", "OPENAI_*", "CODEX_*", "SIGIL_*", "AGENTO11Y_*", "OTEL_*", "GRAFANA_*"]']
    name = os.environ.get('MCP_SERVER_NAME', 'touchline')
    servers = {
        name: {'command':'node', 'args':['/opt/mcp-tools/src/server.mjs'], 'env':{'MCP_SERVER_NAME':name}},
        'time': {'command':'mcp-server-time', 'args':['--local-timezone','Europe/London']},
        'fetch': {'command':'mcp-server-fetch','args':[]},
        'git': {'command':'mcp-server-git','args':[]},
        'sequential-thinking': {'command':'mcp-server-sequential-thinking','args':[]},
        'memory': {'command':'mcp-server-memory','args':[], 'env':{'MEMORY_FILE_PATH':str(CODEX_HOME/'memory.jsonl')}},
    }
    for name, server in servers.items():
        lines += [f'[mcp_servers.{quote(name)}]', f'command = {quote(server["command"])}', f'args = {json.dumps(server["args"])}']
        if server.get('env'):
            lines += [f'[mcp_servers.{quote(name)}.env]'] + [f'{quote(k)} = {quote(v)}' for k,v in server['env'].items()]
    otel = cfg.get('otel')
    lines += ['[otel]', 'environment = "demo"', 'log_user_prompt = false', 'log_agent_responses = false']
    if otel:
        endpoint = otel['endpoint'].rstrip('/')
        parsed = urlsplit(endpoint)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('native OTLP requires a plain HTTPS endpoint')
        token = private_file(TOKEN).strip()
        if not token or not otel.get('username'):
            raise ValueError('native OTLP requires separate token and username')
        authorization = 'Basic '+base64.b64encode((otel['username']+':'+token).encode()).decode()
        for field, suffix in [('exporter','logs'),('trace_exporter','traces'),('metrics_exporter','metrics')]:
            lines += [f'[otel.{field}.otlp-http]', f'endpoint = {quote(endpoint+"/v1/"+suffix)}',
                      'protocol = "binary"', f'[otel.{field}.otlp-http.headers]', f'Authorization = {quote(authorization)}']
    else:
        lines += ['exporter = "none"', 'trace_exporter = "none"', 'metrics_exporter = "none"']
    lines += ['[otel.span_attributes]']
    for key, value in static_tags().items():
        lines += [f'{quote(key)} = {quote(value)}']
    text = '\n'.join(lines)+'\n'
    tomllib.loads(text)
    write_config(text)


def normalized(events, cfg, resume_id, rc):
    result = {'is_error': True, 'cost_mode':'cumulative', 'total_cost_usd':0, 'session_id':resume_id or None,
              'permission_denials':[], 'num_turns':0, 'subtype':'error', 'result':''}
    complete = False
    failure = False
    for event in events:
        kind = event.get('type')
        if kind == 'thread.started':
            value = event.get('thread_id')
            if not isinstance(value, str) or not re.fullmatch(r'[0-9a-fA-F-]{36}', value):
                raise ValueError('invalid Codex thread id')
            if resume_id and value != resume_id:
                raise ValueError('Codex resumed a different thread')
            result['session_id'] = value
        elif kind == 'turn.completed':
            usage = event['usage']
            values = [usage.get(k, 0) for k in ('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens')]
            if any(type(n) is not int or n < 0 for n in values):
                raise ValueError('invalid Codex token usage')
            inp, cached, written, out = values
            if cached + written > inp:
                raise ValueError('cached token counts exceed input tokens')
            prices = cfg['model']['cost']
            # Pinned exec uses ThreadTokenUsage.total, including prior resumed turns.
            result['total_cost_usd'] = ((inp-cached-written)*prices['input'] + cached*prices['cacheRead'] + written*prices['cacheWrite'] + out*prices['output'])/1e6
            result['num_turns'] += 1
            result['usage'] = usage
            result['cost_estimated'] = True
            complete = True
        elif kind in ('turn.failed','error'):
            failure = True
            result['result'] = str(event.get('error',{}).get('message') or event.get('message') or 'Codex error')
        elif kind == 'item.completed':
            item = event.get('item', {})
            if item.get('type') == 'agent_message' and not failure:
                result['result'] = str(item.get('text',''))
    result['is_error'] = rc != 0 or failure or not complete or not result['session_id']
    result['subtype'] = 'error' if result['is_error'] else 'success'
    if result['is_error'] and not result['result']:
        result['result'] = 'Codex stream ended without successful usage'
    return result


def run(args, cfg):
    prompt, model, resume_id, timeout_s, budget, effort, _mcp, stderr_file = args
    if model != cfg['model']['id'] or effort not in ('low','medium','high'):
        raise ValueError('Codex model or effort is outside rendered configuration')
    if resume_id and not re.fullmatch(r'[0-9a-fA-F-]{36}', resume_id):
        raise ValueError('invalid resume id')
    seconds, dollars = float(timeout_s), float(budget)
    if not all(math.isfinite(v) and v > 0 for v in (seconds, dollars)):
        raise ValueError('Codex needs positive timeout and remaining budget')
    env = credentials_env(cfg)
    reseed(cfg)
    # The hardened Docker container is the execution boundary: its dropped capabilities and
    # no-new-privileges prevent bubblewrap namespaces. Managed hooks retain their own trust.
    command = ['codex', 'exec', '--strict-config', '--json', '--sandbox', 'danger-full-access',
               '-m', model, '-c', 'model_reasoning_effort='+quote(effort)]
    if resume_id:
        command += ['resume', resume_id]
    command += ['-']
    # Child process group ensures timeout or outer orchestration SIGTERM cannot leave paid inference running.
    with tempfile.TemporaryFile(mode='w+t') as output, open(stderr_file, 'w') as errors:
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=output, stderr=errors, text=True, env=env, start_new_session=True)
        def stop(_signum=None, _frame=None):
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        old = signal.signal(signal.SIGTERM, lambda s,f: (stop(), sys.exit(143)))
        try:
            try:
                child.communicate(prompt, timeout=seconds)
                rc = child.returncode
            except subprocess.TimeoutExpired:
                stop()
                child.wait()
                rc = 124
            output.seek(0)
            try:
                result = normalized([json.loads(line) for line in output if line.strip()], cfg, resume_id, rc)
            except (ValueError, TypeError, KeyError, AttributeError) as error:
                result = {'is_error':True,'cost_mode':'cumulative','total_cost_usd':0,'session_id':None,'permission_denials':[], 'result':str(error)}
                rc = rc or 65
        finally:
            stop()
            child.wait()
            signal.signal(signal.SIGTERM, old)
    print(json.dumps(result))
    return rc or (1 if result['is_error'] else 0)


def main():
    operation = sys.argv[1] if len(sys.argv) > 1 else ''
    cfg = configuration()
    if operation in ('setup','reseed','ready'):
        credentials_env(cfg)
        reseed(cfg)
        if operation == 'setup':
            version = subprocess.run(['codex','--version'], check=True, capture_output=True, text=True, timeout=10)
            if version.stdout.strip() != 'codex-cli 0.162.1':
                raise ValueError('Codex binary does not match frozen version 0.162.1')
        return 0
    if operation == 'run' and len(sys.argv) == 10:
        return run(sys.argv[2:], cfg)
    raise ValueError('unknown operation or argument count')


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, configparser.Error, subprocess.SubprocessError) as error:
        print('codex adapter: '+str(error), file=sys.stderr)
        if len(sys.argv) > 1 and sys.argv[1] == 'run':
            print(json.dumps({'is_error':True,'cost_mode':'cumulative','total_cost_usd':0,'session_id':None,'permission_denials':[], 'result':str(error)}))
        sys.exit(2)
