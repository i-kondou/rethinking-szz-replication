#!/usr/bin/env python3
"""Relocated baseline runners. Default: plan. --test-stub never calls a model."""
from __future__ import annotations
import argparse
from decimal import Decimal
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace
import platform

from runtime import ROOT, SCRIPTS, impl, common, load, require, save, score, sha
from prepare_baselines import verify as verify_bundle
import llm_baseline_common as legacy

METHODS = ('llm4szz', 'agentszz', 'szz-agent', 'simple-szz-agent')
STUDY_GRAMMAR_SHA = '7e293128f1e14c647f0360ff1c58a1b6d8226f1b104a814ef05ddfd90793780f'


def subject(workspace, sid):
    data, messages, _ = common.read_package()
    case = common.select_cases(data, 'all', [sid])[0]
    repo = common.subject_path(workspace, case, None)
    common.validate_subject(repo, case, messages[sid])
    metadata = ROOT / 'dataset/metadata/cases.json'
    return dict(sample_id=sid, repository=case['repository'], repo=repo,
                synthetic_fix=case['synthetic_bfc'], source_fix=case['bfc'],
                oracle_bics=case['oracle_bics'], metadata_path=str(metadata),
                metadata_sha256=sha(metadata), snapshot=legacy.repository_snapshot(
                    repo, case['synthetic_bfc'], case['bfc']))


def source(workspace, method):
    root, proof = verify_bundle(workspace, 'szz-agent' if method == 'simple-szz-agent' else method)
    if method == 'llm4szz':
        require(platform.system() == 'Darwin' and platform.machine() == 'arm64',
                'The bundled study grammar requires macOS on Apple Silicon')
        import run_llm4szz_original as runner
        runner.SOURCE = root
        runner.GRAMMAR = runner.SOURCE / 'build/my-languages.so'
        runner.GRAMMAR_SHA = STUDY_GRAMMAR_SHA
        runner.PYTHON = Path(sys.executable)
        require(sha(runner.GRAMMAR) == STUDY_GRAMMAR_SHA, 'Study grammar differs')
        proof.update(doi=proof['origin']['doi'],
                     source_files={name: sha(root / name) for name in runner.FILES},
                     grammar=str(runner.GRAMMAR), grammar_sha256=STUDY_GRAMMAR_SHA,
                     python_executable=sys.executable,
                     script_sha256=sha(SCRIPTS / 'run_llm4szz_original.py'))
        return runner, proof
    if method == 'agentszz':
        return root, proof
    from materialize_oracle_independent_szz_agent import validate_materialized_source
    proof.update(szz_agent_path=str(root), upstream_commit=proof['origin']['commit'],
                 patch=validate_materialized_source(root))
    return root, proof


def szz_engine():
    import adapter as final
    engine, _ = final.derive_engine()
    engine.__file__ = str(Path(__file__).resolve())
    original = engine.build_szz_subscription_settings
    engine.build_szz_subscription_settings = lambda **kwargs: {**original(**kwargs), 'includeGitInstructions': False}
    return engine


def agent_stub(fix):
    """Exercise an actual tool round trip; the fixture answer is NOT an oracle."""
    from openai.types.chat import ChatCompletionMessage
    calls = 0

    def create(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            message = ChatCompletionMessage(role='assistant', content=None, tool_calls=[{
                'id': 'fixture-show', 'type': 'function', 'function': {
                    'name': 'git_show', 'arguments': json.dumps({'commit': fix, 'stat_only': True})}}])
        else:
            require(any(m.get('role') == 'tool' for m in kwargs['messages']),
                    'AgentSZZ did not return the tool result')
            message = ChatCompletionMessage(role='assistant',
                content=f'BIC: {fix}\nConfidence: high\nType: fixture\nReasoning: adapter test only')
        return SimpleNamespace(choices=[SimpleNamespace(message=message)],
                               usage=SimpleNamespace(prompt_tokens=0, completion_tokens=0,
                                                     total_tokens=0))
    return lambda **_: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def worker(args):
    s = subject(args.workspace, args.id)
    upstream, proof = source(args.workspace, args.method)
    run = args.output / 'run'
    if args.method == 'llm4szz':
        runner = upstream
        runner.select_subject = lambda sid: s
        runner.verify_source = lambda: proof
        runner.__file__ = str(Path(__file__).resolve())
        command = ['--sample-id', args.id, '--execute', '--run-dir', str(run),
                   '--per-run-cap-usd', '5', '--acknowledge-resource-use', runner.RESOURCE_ACK]
        command += ['--test-stub'] if args.test_stub else ['--acknowledge-api-billing', runner.BILLING_ACK]
        require(runner.main(command) == 0, 'LLM4SZZ failed')
        prediction = load(run / 'prediction.json')['predicted_bics']
    elif args.method == 'agentszz':
        import api_baseline_final_v2_common as final
        engine, _ = final.derive_engine('agentszz')
        if args.test_stub:
            engine._stub_openai_factory = lambda _: agent_stub(s['synthetic_fix'])
        run.mkdir()
        result = engine.run_agentszz(source=upstream, subject=s, run_dir=run,
                                    cap=Decimal('5'), test_stub=args.test_stub)
        save(run / 'prediction.json', result)
        prediction = result['predicted_bics']
    else:
        engine = szz_engine()
        engine.load_subject = lambda *_: s
        engine.validate_source_manifest = lambda *_: source(args.workspace, args.method)[1]
        import adapter as final
        deadline = time.monotonic() + 3600 if args.method == 'szz-agent' else None
        engine.execute_process = lambda command, **kwargs: final.execute_process(
            command, **kwargs, deadline=deadline,
            total_timeout_seconds=3600 if deadline is not None else None)
        os.environ['LLM_BASELINE_ALLOW_TEST_STUB'] = '1' if args.test_stub else '0'
        command = ['--baseline', args.method, '--sample-id', args.id, '--prompt-metadata', s['metadata_path'],
                   '--python-bin', sys.executable, '--run-dir', str(run), '--execute',
                   '--per-run-cap-usd', '5', '--timeout-seconds', '3600',
                   '--acknowledge-resource-use', engine.RESOURCE_ACKNOWLEDGEMENT]
        command += (['--test-stub', '--test-stub-stage1-outcome', args.stage1] if args.test_stub else
                    ['--confirm-usage-credits-disabled', engine.USAGE_CREDITS_ACKNOWLEDGEMENT])
        require(engine.main(command) == 0, 'SZZ-Agent pipeline failed')
        record = load(run / 'run.json')
        if args.method == 'simple-szz-agent':
            record['simple_szz_agent_flow']['oracle_coverage_gate'] = 'removed_by_pinned_oracle_independent_patch'
            legacy.write_json(run / 'run.json', record)
        prediction = record['prediction']['predicted_bics']
    subject(args.workspace, args.id)
    # Scoring is outside the algorithm and never supplied in model input.
    save(args.output / 'evaluation.json', dict(method=args.method, sample_id=args.id,
         test_stub=args.test_stub, scientific_result=not args.test_stub,
         predicted_bics=prediction, oracle_bics=s['oracle_bics'], metrics=score(prediction, s['oracle_bics']),
         source_proof=proof, model_calls=0 if args.test_stub else None,
         adapter_boundary='Bundled study source and adapters; original search logic and oracle-independent patch. '
                          'No historical HTTP capture or automatic retries.'))
    return 0


def parse(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=METHODS, required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--workspace', type=Path, default=ROOT / 'dataset')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--test-stub', action='store_true')
    parser.add_argument('--stage1', choices=('select', 'abstain'), default='select')
    parser.add_argument('--acknowledge-resource-use', action='store_true')
    parser.add_argument('--acknowledge-api-billing', action='store_true')
    parser.add_argument('--confirm-usage-credits-disabled', action='store_true')
    args = parser.parse_args(argv)
    args.workspace = args.workspace.resolve()
    if args.output:
        args.output = args.output.resolve()
    return args


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ['_worker']:
        # Invoked by the pinned LLM4SZZ launcher, not the public entry point.
        config = load(Path(argv[1]) / 'run.json')
        import run_llm4szz_original as runner
        runner.GRAMMAR = Path(config['source']['grammar'])
        runner.GRAMMAR_SHA = STUDY_GRAMMAR_SHA
        return runner.worker(argv[1])
    if argv and argv[0].startswith('_internal-'):
        return szz_engine().main(argv)
    child = argv[:1] == ['_run']
    args = parse(argv[1:] if child else argv)
    require(args.id.isdecimal(), 'Invalid case ID')
    if not args.execute and not args.test_stub:
        print(json.dumps(dict(method=args.method, case=args.id, mode='plan-only', model_calls=0,
                              workspace=str(args.workspace)), indent=2))
        return 0
    require(args.output is not None, '--output must be specified')
    require(not args.output.is_relative_to(ROOT) or args.output.is_relative_to(ROOT/'outputs'),
            'Inside this package, outputs must be under outputs/')
    protected = [ROOT / name for name in ('analysis', 'preprocess', 'experiments', 'results', 'dataset/metadata', 'dataset/dio-verified', '.cache')]
    protected += [args.workspace / name for name in ('prepared', 'repositories', 'message_free', 'baselines')]
    require(not any(args.output.is_relative_to(p) for p in protected), 'Output is inside a protected input')
    if not args.test_stub:
        require(args.acknowledge_resource_use, 'Live runs require resource acknowledgment')
        if args.method in ('llm4szz', 'agentszz'):
            require(args.acknowledge_api_billing and os.environ.get('ANTHROPIC_API_KEY'),
                    'API baselines require billing acknowledgment and ANTHROPIC_API_KEY')
        else:
            require(args.confirm_usage_credits_disabled, 'Confirm disabled subscription extra usage')
    if child:
        require(os.environ.get('REPLICATION_BASELINE_CHILD') == '1', 'Not a launched worker')
        return worker(args)
    require(not args.output.exists(), 'Choose a fresh output directory; no automatic retries')
    subject(args.workspace, args.id)
    source(args.workspace, args.method)
    args.output.mkdir(parents=True)
    env = legacy.sanitized_environment(keep_api_key=not args.test_stub)
    env.update(REPLICATION_BASELINE_CHILD='1', PYTHONDONTWRITEBYTECODE='1', PYTHONHASHSEED='0')
    started = time.monotonic()
    timeout = None if args.method == 'simple-szz-agent' else 3600 if args.method == 'szz-agent' else 600
    state, code = 'failed', None
    try:
        with (args.output / 'stdout.log').open('xb') as out, (args.output / 'stderr.log').open('xb') as err:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '_run', *argv],
                                       env=env, stdout=out, stderr=err, start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except BaseException:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                raise
        require(code == 0, f'Worker failed; see {args.output / "stderr.log"}')
        require((args.output / 'evaluation.json').is_file(), 'Missing evaluation')
        state = 'completed_stub' if args.test_stub else 'completed'
    finally:
        save(args.output / 'status.json', dict(state=state, exit_code=code,
             elapsed_seconds=time.monotonic() - started, timeout_seconds=timeout,
             test_stub=args.test_stub, model_calls=0 if args.test_stub else None))
    print(json.dumps(dict(state=state, output=str(args.output)), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
