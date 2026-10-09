#!/usr/bin/env python3
"""LLM4SZZ Figshare v1 with a Sonnet transport, separate from frozen runs.

Default is read-only preflight. A fresh single-run directory, explicit limits,
API credentials and acknowledgements are required for live execution.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import importlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from types import SimpleNamespace, ModuleType
import zipfile

from api_baseline_final_v2_common import select_subject, safe_environment, workspace_headers
from llm_baseline_common import BaselineError, load_json, repository_snapshot, sha256_file, write_json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / 'baselines'
SOURCE = BASE / 'llm4szz-figshare-v1/llmszz-replication-package1'
ARCHIVE = BASE / 'llm4szz-replication-package.zip'
ARCHIVE_SHA = 'd00c8d5c356acdd8a58c09ceeef9c78d4c8357963287286b546b0d4e15226c72'
GRAMMAR = BASE / 'szz-agent-llm4szz-adapter/llm4szz/build/my-languages.so'
GRAMMAR_SHA = '7e293128f1e14c647f0360ff1c58a1b6d8226f1b104a814ef05ddfd90793780f'
PYTHON = BASE / 'venv/bin/python'
MODEL = 'claude-sonnet-5'
CONDITION = 'LLM4SZZ-ORIGINAL-V1-SONNET-20260930'
RESOURCE_ACK = 'I_ACKNOWLEDGE_LLM4SZZ_ORIGINAL_RESOURCE_USE'
BILLING_ACK = 'I_ACKNOWLEDGE_ANTHROPIC_API_BILLING'
FILES = ('constants.py', 'llm.py', 'llm4szz.py', 'util.py', 'parse_patch.py',
         'prompts.py', 'cal_statistics_util.py')


def verify_source():
    if sha256_file(ARCHIVE) != ARCHIVE_SHA or sha256_file(GRAMMAR) != GRAMMAR_SHA:
        raise BaselineError('original archive or platform grammar changed')
    with zipfile.ZipFile(ARCHIVE) as archive:
        for name in FILES:
            if (SOURCE / name).read_bytes() != archive.read('llmszz-replication-package1/' + name):
                raise BaselineError(f'original source differs from archive: {name}')
    return {'archive': str(ARCHIVE), 'archive_sha256': ARCHIVE_SHA,
            'doi': '10.6084/m9.figshare.27418236.v1',
            'source_files': {name: sha256_file(SOURCE / name) for name in FILES},
            'grammar': str(GRAMMAR), 'grammar_sha256': GRAMMAR_SHA,
            'grammar_boundary': 'Existing macOS arm64 build; original archive binary is Linux x86-64.',
            'script_sha256': sha256_file(Path(__file__)),
            'helper_sha256': {n: sha256_file(ROOT / 'scripts' / n) for n in
                             ('api_baseline_final_v2_common.py', 'llm_baseline_common.py')},
            'python_executable': str(PYTHON)}


def original_prediction(logs, repo: Path, source: Path = SOURCE):
    """Execute the original selection block, not a rewritten approximation.

    Keep list(set(...)) and get_r_commits' first-in-order latest-date tie rule.
    No Oracle is passed to this function.
    """
    import git
    util = ast.parse((source / 'util.py').read_text())
    recent = next(n for n in util.body if isinstance(n, ast.FunctionDef) and n.name == 'get_r_commits')
    stats = ast.parse((source / 'cal_statistics_util.py').read_text())
    metrics = next(n for n in stats.body if isinstance(n, ast.FunctionDef) and n.name == 'get_metrics')
    container = next(n for n in ast.walk(metrics) if isinstance(n, ast.If)
                     and ast.unparse(n.test) == 'os.path.exists(save_path)')
    def assigned(node, name):
        return isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
    start = next(i for i, n in enumerate(container.body) if assigned(n, 'final_find_cids'))
    end = next(i for i, n in enumerate(container.body) if assigned(n, 'find_cnt'))
    ns = {'git': git, 'os': os, 'REPOS_DIR': str(repo), 'repo_name': '', 'logs': logs, 's1_cnt': 0}
    exec(compile(ast.Module([recent] + container.body[start:end], type_ignores=[]),
                 str(source / 'cal_statistics_util.py'), 'exec'), ns)
    return ns['final_find_cids']


def single_iteration_code(text):
    # The outer repetition is managed by the caller; the search body is verbatim.
    marker = 'for cnt in range(0, 3):'
    if text.count(marker) != 1:
        raise BaselineError('original outer repetition anchor changed')
    return text.replace(marker, 'for cnt in range(0, 1):')


class SonnetTransport:
    """Replace OpenAI network I/O beneath the UNCHANGED original Client."""
    def __init__(self, run_dir, cap, max_output_tokens, stub=False, provider=None):
        self.run_dir = Path(run_dir)
        self.cap = Decimal(cap)
        self.max_output_tokens = max_output_tokens
        self.stub = stub
        self.provider = provider
        self.calls = []
        self.spent = Decimal('0')
        self.chat = SimpleNamespace(completions=self)

    def save(self):
        write_json(self.run_dir / 'model-calls.json', {'calls': self.calls,
                   'known_cost_usd': str(self.spent), 'pricing': 'input USD2/output USD10 per million; Sep-7 snapshot',
                   'usage_complete': all(c['state'] == 'completed' for c in self.calls)})

    def create(self, *, model, messages, temperature):
        # These inputs come from the original llm.py after its 30,000-character trim.
        if model != 'gpt-4o-mini' or temperature != 0.0:
            raise BaselineError('unexpected original model-call contract')
        # Isolate the caller's conversation from transport/SDK changes.
        messages = deepcopy(messages)
        system = '\n'.join(m['content'] for m in messages if m['role'] == 'system')
        body = {'model': MODEL, 'max_tokens': self.max_output_tokens,
                'messages': [m for m in messages if m['role'] != 'system']}
        if system:
            body['system'] = system
        worst = (Decimal(len(json.dumps(body).encode()) + 1024) * 2 + self.max_output_tokens * 10) / 1000000
        if self.spent + worst > self.cap:
            raise BaselineError('conservative per-run cost gate reached before request')
        # Log independent request-time snapshots: both the caller and SDK may
        # mutate their lists or nested dictionaries after this call starts.
        call = {'state': 'started', 'original_request': {'model': model, 'temperature': temperature, 'messages': deepcopy(messages)},
                'request': deepcopy(body), 'temperature_sent': False, 'test_stub': self.stub}
        self.calls.append(call)
        self.save()
        started = time.monotonic()
        try:
            if self.stub:
                from run_llm_baseline_subject import llm4szz_stub_reply
                reply = llm4szz_stub_reply(messages)
                call.update(input_tokens=0, output_tokens=0, stop_reason='fixture', response_id=None)
            else:
                if self.provider is None:
                    import anthropic
                    self.provider = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'],
                        base_url='https://api.anthropic.com', max_retries=0, default_headers=workspace_headers())
                response = self.provider.messages.create(**body)
                reply = ''.join(b.text for b in response.content if getattr(b, 'type', None) == 'text')
                usage = response.usage
                call.update(input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                            stop_reason=response.stop_reason, response_id=response.id,
                            response=response.model_dump(), thinking_tokens=None)
                self.spent += (Decimal(usage.input_tokens) * 2 + Decimal(usage.output_tokens) * 10) / 1000000
            call.update(state='completed', seconds=time.monotonic() - started, reply=reply)
            self.save()
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])
        except BaseException as exc:
            call.update(state='failed', error_type=type(exc).__name__, seconds=time.monotonic() - started)
            self.save()
            raise


def worker(run_dir):
    run_dir = Path(run_dir).resolve()
    config = load_json(run_dir / 'run.json')
    if os.environ.get('LLM4SZZ_ORIGINAL_WORKER') != CONDITION or config['condition'] != CONDITION:
        raise BaselineError('worker must be started by the gated launcher')
    if sha256_file(GRAMMAR) != config['source']['grammar_sha256']:
        raise BaselineError('platform grammar changed after preflight')
    from importlib.metadata import version
    write_json(run_dir / 'runtime.json', {'python': sys.version, 'packages': {
        name: version(name) for name in ('tree-sitter', 'GitPython', 'PyDriller', 'tiktoken', 'openai', 'anthropic')}})
    source = run_dir / 'source'
    for name, expected in config['source']['source_files'].items():
        if sha256_file(source / name) != expected:
            raise BaselineError('source snapshot changed')
    sys.path.insert(0, str(source))
    # Optional local-transformer imports are unused by original pipeline=None.
    sys.modules.setdefault('torch', ModuleType('torch'))
    sys.modules.setdefault('transformers', ModuleType('transformers'))
    constants = importlib.import_module('constants')
    for key, value in {'CWD': run_dir, 'REPOS_DIR': run_dir / 'repos',
                       'DATASET_DIR': run_dir / 'dataset', 'SAVE_LOG_DIR': run_dir / 'save_logs',
                       'TMP_DIR': run_dir / 'tmp_dir', 'TREE_SITTER_DIR': GRAMMAR.parent}.items():
        setattr(constants, key, str(value))
    llm = importlib.import_module('llm')
    transport = SonnetTransport(run_dir, config['cap_usd'], config['max_output_tokens'], config['test_stub'])
    llm.OpenAI = lambda **_kwargs: transport
    transport.save()
    code = single_iteration_code((source / 'llm4szz.py').read_text())
    (run_dir / 'single-iteration.py.txt').write_text(code)
    exec(compile(code, str(source / 'llm4szz.py'), 'exec'), {'__name__': '__main__', '__file__': str(source / 'llm4szz.py')})
    # Original code catches exceptions; retain them, do not call the run successful.
    if (run_dir / 'err_infos.json').exists() and load_json(run_dir / 'err_infos.json'):
        raise BaselineError('upstream recorded errors; see err_infos.json')
    raw = run_dir / 'save_logs/subject' / config['synthetic_fix'] / 'llm4szz0.json'
    write_json(run_dir / 'prediction.json', {'predicted_bics': original_prediction(load_json(raw), run_dir / 'repos/subject', source),
               'raw_result': str(raw), 'raw_result_sha256': sha256_file(raw),
               'extraction': 'original get_metrics selection block and original get_r_commits',
               'python_hash_seed': os.environ.get('PYTHONHASHSEED', 'random')})
    return 0


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sample-id', required=True)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--test-stub', action='store_true')
    p.add_argument('--run-dir', type=Path)
    p.add_argument('--per-run-cap-usd')
    p.add_argument('--timeout-seconds', type=int, default=600)
    p.add_argument('--max-output-tokens', type=int, default=4096)
    p.add_argument('--hash-seed', type=int, default=0)
    p.add_argument('--acknowledge-resource-use')
    p.add_argument('--acknowledge-api-billing')
    return p


def gates(args):
    if args.timeout_seconds <= 0 or args.max_output_tokens <= 0 or not 0 <= args.hash_seed <= 4294967295:
        raise BaselineError('invalid time/output/hash-seed setting')
    if not args.execute:
        if args.run_dir or args.test_stub or args.per_run_cap_usd:
            raise BaselineError('execution options require --execute')
        return
    if args.run_dir is None or args.run_dir.exists():
        raise BaselineError('a fresh --run-dir is required')
    try:
        cap = Decimal(args.per_run_cap_usd or 'NaN')
    except InvalidOperation as exc:
        raise BaselineError('cost cap must be numeric') from exc
    if not cap.is_finite() or cap <= 0:
        raise BaselineError('an explicit positive cost cap is required')
    if args.acknowledge_resource_use != RESOURCE_ACK:
        raise BaselineError('missing resource acknowledgement')
    if not args.test_stub and (args.acknowledge_api_billing != BILLING_ACK or not os.environ.get('ANTHROPIC_API_KEY')):
        raise BaselineError('live execution requires API key and billing acknowledgement')


def main(argv=None):
    args = parser().parse_args(argv)
    gates(args)
    source = verify_source()
    subject = select_subject(args.sample_id)
    config = {'condition': CONDITION, 'sample_id': args.sample_id, 'model': MODEL,
              'source': source, 'synthetic_fix': subject['synthetic_fix'],
              'subject_repo': str(subject['repo']), 'test_stub': args.test_stub,
              'cap_usd': args.per_run_cap_usd, 'max_output_tokens': args.max_output_tokens,
              'timeout_seconds': args.timeout_seconds, 'python_hash_seed': args.hash_seed,
              'input_metadata_sha256': subject['metadata_sha256'],
              'input_metadata_path': str(subject['metadata_path']),
              'boundary': 'Original algorithm/client trimming/selection. Model transport, paths, platform grammar and outer repetition scheduling adapted.'}
    if not args.execute:
        print(json.dumps({'state': 'preflight-only', 'model_invoked': False, **config}, indent=2))
        return 0
    directory = args.run_dir.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    for name in ('source', 'repos', 'dataset', 'save_logs', 'tmp_dir'):
        (directory / name).mkdir()
    for name in FILES:
        shutil.copy2(SOURCE / name, directory / 'source' / name)
    (directory / 'repos/subject').symlink_to(subject['repo'], target_is_directory=True)
    write_json(directory / 'dataset/final_all_dataset.json', [{'repo_name': 'subject', 'fix_commit_hash': subject['synthetic_fix']}])
    config.update(state='running', scientific_result=False)
    write_json(directory / 'run.json', config)
    env = safe_environment(keep_api_key=not args.test_stub)
    env.update(LLM4SZZ_ORIGINAL_WORKER=CONDITION, PYTHONHASHSEED=str(args.hash_seed), PYTHONDONTWRITEBYTECODE='1')
    started = time.monotonic()
    try:
        with (directory / 'stdout.log').open('wb') as out, (directory / 'stderr.log').open('wb') as err:
            process = subprocess.Popen([str(PYTHON), str(Path(__file__).resolve()), '_worker', str(directory)],
                                       cwd=directory, env=env, stdout=out, stderr=err, start_new_session=True)
            try:
                code = process.wait(timeout=args.timeout_seconds)
            except BaseException as exc:
                if process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                process.wait()
                if isinstance(exc, subprocess.TimeoutExpired):
                    raise BaselineError('outer timeout reached; artifacts preserved') from exc
                raise
        if code != 0:
            raise BaselineError('original pipeline failed; inspect preserved stderr/errors')
        snapshot = repository_snapshot(Path(subject['repo']), subject['synthetic_fix'], subject['source_fix'])
        if not all(v for k, v in snapshot.items() if k != 'head'):
            raise BaselineError('subject repository postflight failed')
        config.update(state='completed_stub' if args.test_stub else 'completed',
                      scientific_result=not args.test_stub, prediction=load_json(directory / 'prediction.json'),
                      postflight=snapshot, seconds=time.monotonic() - started)
    except BaseException as exc:
        config.update(state='failed', error_type=type(exc).__name__, seconds=time.monotonic() - started)
        raise
    finally:
        write_json(directory / 'run.json', config)
    print(json.dumps({'state': config['state'], 'manifest': str(directory / 'run.json')}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        if sys.argv[1:2] == ['_worker']:
            raise SystemExit(worker(sys.argv[2]))
        raise SystemExit(main())
    except (BaselineError, OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        raise SystemExit(1)
