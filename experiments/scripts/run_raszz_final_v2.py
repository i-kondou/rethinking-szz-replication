#!/usr/bin/env python3
"""Audited, non-LLM RA-SZZ* collection; upstream source remains unchanged."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import runpy
import signal
import subprocess
import sys
import time

import api_baseline_final_v2_common as inputs
import run_pyszz as base

ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / 'experiments/runs/raszz-star-final-v2-20260908'
SOURCE = ROOT / 'tmp/pyszz_v2'
PYTHON = ROOT / 'tmp/pyszz-venv/bin/python'
CONFIG = ROOT / 'config/pyszz/ra-final-v2.yml'
PROTOCOL = ROOT / 'experiments/plans/raszz-star-final-v2-20260908.md'
TIMEOUT = 600


def read(path):
    return json.loads(Path(path).read_text())


def create_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def check_refactorings(value, commits, repository):
    for commit in commits:
        item = value.get(commit)
        if not isinstance(item, dict) or not isinstance(item.get('commits'), list):
            raise RuntimeError(f'invalid RefactoringMiner response: {commit}')
        records = item['commits']
        if not records and repository.commit(commit).parents:
            raise RuntimeError(f'RefactoringMiner omitted non-root commit: {commit}')
        if any(not isinstance(r.get('refactorings'), list) for r in records):
            raise RuntimeError(f'invalid refactorings list: {commit}')


def worker(run_dir):
    """Only the minimal worker-input.json crosses into the algorithm."""
    os.chdir(run_dir)
    sys.path.insert(0, str(SOURCE))
    from szz.ra_szz import RASZZ
    extract = RASZZ._extract_refactorings
    counter = 0

    def observed_extract(self, commits):
        nonlocal counter
        counter += 1
        started = time.monotonic()
        event = {'commits': sorted(commits), 'started_at': base.utc_now()}
        try:
            value = extract(self, commits)
            event['raw_response'] = value
            check_refactorings(value, commits, self.repository)
            return value
        except BaseException as exc:
            event['error'] = repr(exc)
            raise
        finally:
            event['duration_seconds'] = time.monotonic() - started
            create_json(Path('refactoring-events') / f'{counter:05d}.json', event)

    RASZZ._extract_refactorings = observed_extract
    sys.argv = [str(SOURCE / 'main.py'), 'worker-input.json', str(CONFIG), 'repos']
    runpy.run_path(str(SOURCE / 'main.py'), run_name='__main__')


def environment():
    env = inputs.safe_environment(keep_api_key=False)
    env['JAVA_OPTS'] = '-Xmx2g'
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def preflight():
    if base.git(SOURCE, 'rev-parse', 'HEAD').stdout.strip() != base.PYSZZ_REVISION:
        raise RuntimeError('wrong PySZZ revision')
    if base.git(SOURCE, 'status', '--porcelain').stdout.strip():
        raise RuntimeError('upstream source modified')
    base.validate_config(CONFIG, 'ra')
    cohort, reviews = inputs.input_records()
    for row in cohort['samples']:
        inputs.validated_subject(row, reviews[str(row['sample_id'])])
    files = [Path(__file__), CONFIG, PROTOCOL, Path(inputs.__file__), Path(base.__file__),
             ROOT / 'scripts/llm_baseline_common.py', base.DEFAULT_LOCK,
             *SOURCE.glob('*.py'), *SOURCE.glob('szz/**/*.py'),
             *SOURCE.glob('tools/RefactoringMiner-2.0/lib/*.jar'),
             SOURCE / 'tools/RefactoringMiner-2.0/bin/RefactoringMiner']
    return {'condition': 'RA-SZZ-star-PySZZ-final-v2-20260908',
            'input_set_sha256': inputs.INPUT_SET_SHA256,
            'pyszz_revision': base.PYSZZ_REVISION,
            'timeout_seconds': TIMEOUT, 'java_opts': '-Xmx2g',
            'python': base.inspect_python(PYTHON, base.DEFAULT_LOCK),
            'java': base.inspect_tool('java', ['-version']),
            'srcml': base.inspect_tool('srcml', ['--version']),
            'git': base.inspect_tool('git', ['--version']),
            'files': {str(p): base.sha256_file(p) for p in sorted(set(files))},
            'samples': sorted(cohort['samples'], key=lambda r: int(r['sample_id']))}


def verify_frozen(plan):
    for path, digest in plan['files'].items():
        if base.sha256_file(Path(path)) != digest:
            raise RuntimeError(f'frozen file changed: {path}')
    for result in RUN_ROOT.glob('*/result.json'):
        for path, digest in read(result)['artifacts'].items():
            if base.sha256_file(Path(path)) != digest:
                raise RuntimeError(f'raw artifact changed: {path}')


def execute_case(row, reviews):
    sample_id = str(row['sample_id'])
    subject = inputs.validated_subject(row, reviews[sample_id])
    run_dir = RUN_ROOT / sample_id
    run_dir.mkdir(exist_ok=False)
    repo_link = run_dir / 'repos' / row['repository']
    repo_link.parent.mkdir(parents=True)
    repo_link.symlink_to(subject['repo'], target_is_directory=True)
    create_json(run_dir / 'worker-input.json', [
        {'repo_name': row['repository'], 'fix_commit_hash': row['synthetic_fix_hash']}])
    command = [str(PYTHON), str(Path(__file__).resolve()), '--worker', str(run_dir)]
    record = {'sample_id': sample_id, 'repository': row['repository'],
              'fix_commit_hash': row['synthetic_fix_hash'],
              'original_fix_commit_hash': row['source_bfc_hash'],
              'started_at': base.utc_now(), 'command': command,
              'status': 'running', 'api_cost_usd': 0, 'llm_tokens': 0}
    create_json(run_dir / 'started.json', record)
    start = time.monotonic()
    error = None
    predictions = None
    with (run_dir / 'stdout.log').open('x') as stdout, (run_dir / 'stderr.log').open('x') as stderr:
        process = subprocess.Popen(command, cwd=run_dir, env=environment(),
                                   stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            returncode = process.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            returncode = process.returncode
            error = 'outer_timeout_600_seconds'
        except BaseException:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            raise
    record.update(returncode=returncode, duration_seconds=time.monotonic()-start,
                  finished_at=base.utc_now())
    if returncode != 0:
        error = error or f'worker_exit_{returncode}'
    try:
        if not error:
            outputs = list((run_dir / 'out').glob('*.json'))
            if len(outputs) != 1:
                raise RuntimeError(f'expected one official output; got {len(outputs)}')
            _, predictions = base.validate_official_output(read(outputs[0]),
                repository=row['repository'], fix_hash=row['synthetic_fix_hash'])
            for sha in predictions:
                base.git(Path(subject['repo']), 'cat-file', '-e', f'{sha}^{{commit}}')
            stderr_text = (run_dir / 'stderr.log').read_text(errors='replace')
            if re.search(r'\bERROR\b|Exception|timeout|timed out|unable to analyze', stderr_text, re.I):
                raise RuntimeError('upstream_error_in_stderr_requires_review')
        inputs.validated_subject(row, reviews[sample_id])
        record['postflight_clean'] = True
    except Exception as exc:
        error = str(exc)
    oracle = [row['oracle_bic_hash']]
    record.update(status='failed' if error else 'success', error=error,
                  predictions=predictions, oracle=oracle,
                  metrics=base.metrics(predictions, oracle) if not error else None)
    artifacts = [run_dir/'worker-input.json', run_dir/'started.json',
                 run_dir/'stdout.log', run_dir/'stderr.log',
                 *run_dir.glob('out/*.json'), *run_dir.glob('refactoring-events/*.json')]
    record['artifacts'] = {str(p): base.sha256_file(p) for p in artifacts}
    create_json(run_dir / 'result.json', record)
    return record


def summarize(write=False):
    plan = read(RUN_ROOT/'plan.json')
    verify_frozen(plan)
    rows = [read(p) for p in sorted(RUN_ROOT.glob('*/result.json'), key=lambda p: int(p.parent.name))]
    success = [r for r in rows if r['status']=='success']
    failed = [r for r in rows if r['status']=='failed']
    tp, fp, fn = [sum(r['metrics'][key] for r in success)
                  for key in ('true_positive','false_positive','false_negative')]
    precision = tp/(tp+fp) if tp+fp else 0
    recall = tp/(tp+fn) if tp+fn else 0
    f1 = 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0
    value = {'condition': plan['condition'], 'registered': len(plan['samples']),
             'attempted': len(rows), 'success': len(success), 'failed': len(failed),
             'pending': len(plan['samples'])-len(rows), 'tp': tp, 'fp': fp, 'fn': fn,
             'precision': precision, 'recall': recall, 'f1': f1,
             'mean_success_seconds': sum(r['duration_seconds'] for r in success)/len(success) if success else None,
             'total_attempted_seconds': sum(r['duration_seconds'] for r in rows),
             'api_cost_usd': 0, 'llm_tokens': 0, 'rows': rows}
    if write:
        base.write_json_atomic(RUN_ROOT/'summary.json', value)
        lines = ['# RA-SZZ* (PySZZ) final-v2 collected results', '',
                 'One execution per case. Errors are not empty predictions. P/R/F1 use successful cases only.', '',
                 f"Registered {value['registered']}; attempted {len(rows)}; success {len(success)}; failed {len(failed)}; pending {value['pending']}.", '',
                 '| TP | FP | FN | Precision | Recall | F1 | mean success seconds | API USD |',
                 '| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
                 f"| {tp} | {fp} | {fn} | {precision:.6f} | {recall:.6f} | {f1:.6f} | {value['mean_success_seconds']} | 0 |", '',
                 '| ID | Status | TP | FP | FN | P | R | F1 | Seconds |',
                 '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for r in rows:
            m = r['metrics'] or {}
            values = [m.get(k, '—') for k in ('true_positive','false_positive','false_negative','precision','recall','f1')]
            lines.append(f"| [{r['sample_id']}]({r['sample_id']}/result.json) | {r['status']} | " +
                         ' | '.join(str(v) for v in values) + f" | {r['duration_seconds']:.2f} |")
        (RUN_ROOT/'summary.md').write_text('\n'.join(lines)+'\n')
    return {k:v for k,v in value.items() if k!='rows'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--sample-id')
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--write-summary', action='store_true')
    parser.add_argument('--worker', type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return
    if args.summary or args.write_summary:
        print(json.dumps(summarize(args.write_summary), indent=2))
        return
    plan = preflight()
    if not args.execute:
        print(json.dumps({'ready': True, 'cases': len(plan['samples']), 'runtime': plan['python'],
                          'java': plan['java'], 'paid_api': False}, indent=2))
        return
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    with (RUN_ROOT/'controller.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (RUN_ROOT/'plan.json').exists():
            if read(RUN_ROOT/'plan.json') != plan:
                raise RuntimeError('registered plan differs; no implicit migration')
            verify_frozen(plan)
        else:
            create_json(RUN_ROOT/'plan.json', plan)
        _, reviews = inputs.input_records()
        selected = [r for r in plan['samples'] if not args.sample_id or str(r['sample_id']) == args.sample_id]
        if not selected:
            raise RuntimeError('sample outside fixed cohort')
        for row in selected:
            run_dir = RUN_ROOT/str(row['sample_id'])
            if (run_dir/'result.json').exists():
                continue
            if run_dir.exists():
                raise RuntimeError('incomplete attempt retained; manual review required')
            result = execute_case(row, reviews)
            print(json.dumps({'sample_id': row['sample_id'], 'status': result['status'],
                              'seconds': result['duration_seconds'], 'error': result['error']}), flush=True)
            summarize(write=True)
            if result['status'] != 'success':
                raise RuntimeError('stopped on first failure; raw attempt retained')
        print(json.dumps(summarize(write=True), indent=2))


if __name__ == '__main__':
    main()
