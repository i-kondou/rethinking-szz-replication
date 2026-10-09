#!/usr/bin/env python3
"""Run pinned PySZZ variants on a prepared case. No model; default is a plan."""
import argparse
import json
import os
from pathlib import Path
import re
import runpy
import signal
import subprocess
import sys
import time
from runtime import ROOT, impl, common, load, require, save, sha, score
from prepare_baselines import verify as verify_bundle
import run_pyszz as original

VARIANTS = ('b', 'ag', 'ma', 'r', 'l', 'ra')


def worker(directory):
    spec = load(directory / 'launch.json')
    source = Path(spec['source'])
    sys.path.insert(0, str(source))
    os.chdir(directory)
    if spec['variant'] == 'ra':
        # Retain the recorded local-origin adapter and strict Miner checks.
        from szz.ra_szz import RASZZ
        from run_raszz_final_v2 import check_refactorings, create_json
        initialize, extract = RASZZ.__init__, RASZZ._extract_refactorings
        counter = 0
        def local_origin(self, *args, **kwargs):
            initialize(self, *args, **kwargs)
            copy = Path(self.repository_path).resolve()
            require(copy.is_relative_to(directory / '_szztemp'), 'Unexpected worker copy')
            require(not list(self.repository.remotes), 'Unexpected remote')
            self.repository.git.config('remote.origin.url', 'https://example.invalid/raszz-local.git')
            create_json(directory / 'local-origin.json', {'copy': str(copy), 'network_operation': False})
        def observed_extract(self, commits):
            nonlocal counter
            counter += 1
            event = {'commits': sorted(commits)}
            try:
                value = extract(self, commits)
                event['raw_response'] = value
                check_refactorings(value, commits, self.repository)
                return value
            except BaseException as exc:
                event['error'] = repr(exc)
                raise
            finally:
                create_json(directory / 'refactoring-events' / f'{counter:05d}.json', event)
        RASZZ.__init__, RASZZ._extract_refactorings = local_origin, observed_extract
    sys.argv = [str(source / 'main.py'), 'worker-input.json', spec['config'], 'repos']
    runpy.run_path(str(source / 'main.py'), run_name='__main__')


def main():
    if sys.argv[1:2] == ['_worker']:
        worker(Path(sys.argv[2]).resolve())
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--variants', nargs='+', choices=VARIANTS, default=list(VARIANTS))
    parser.add_argument('--workspace', type=Path, default=ROOT / 'dataset')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--ra-timeout-seconds', type=int, choices=(600, 3600), default=600)
    args = parser.parse_args()
    require(args.id.isdecimal(), 'Invalid case ID')
    if not args.execute:
        print(json.dumps({'mode': 'plan-only', 'id': args.id, 'variants': args.variants, 'model_calls': 0}))
        return 0
    workspace = args.workspace.resolve()
    require(args.output is not None, 'Specify a fresh output directory')
    output = args.output.resolve()
    require(not output.is_relative_to(ROOT) or output.is_relative_to(ROOT/'outputs'),
            'Inside this package, outputs must be under outputs/')
    protected = [ROOT / n for n in ('analysis', 'preprocess', 'experiments', 'results', 'dataset/metadata', 'dataset/dio-verified', '.cache')]
    protected += [workspace / n for n in ('prepared', 'repositories', 'message_free', 'baselines')]
    require(not any(output.is_relative_to(p) for p in protected), 'Output is inside protected input')
    require(not output.exists(), 'Output already exists')
    source, proof = verify_bundle(workspace, 'pyszz-v2')
    require(proof['origin']['commit'] == original.PYSZZ_REVISION, 'PySZZ pin differs')
    runtime = original.inspect_python(Path(sys.executable), original.DEFAULT_LOCK)
    runtime['tools'] = {name: original.inspect_tool(name, flags) for name, flags in
                        [('srcml', ['--version']), ('java', ['-version']), ('git', ['--version'])]}
    dataset, messages, _ = common.read_package()
    case = common.select_cases(dataset, 'all', [args.id])[0]
    repo = common.subject_path(workspace, case, None)
    common.validate_subject(repo, case, messages[args.id])
    output.mkdir(parents=True)
    results = []
    for variant in dict.fromkeys(args.variants):
        directory = output / variant
        directory.mkdir()
        config = impl() / 'config/pyszz' / ('ra-final-v2.yml' if variant == 'ra' else variant + '.yml')
        original.validate_config(config, variant)
        link = directory / 'repos' / case['repository']
        link.parent.mkdir(parents=True)
        link.symlink_to(repo, target_is_directory=True)
        save(directory / 'worker-input.json', [{'repo_name': case['repository'], 'fix_commit_hash': case['synthetic_bfc']}])
        save(directory / 'launch.json', {'source': str(source), 'variant': variant, 'config': str(config),
              'config_sha256': sha(config), 'source_commit': original.PYSZZ_REVISION,
              'source_proof': proof, 'runtime': runtime,
              'timeout_seconds': args.ra_timeout_seconds if variant == 'ra' else 600})
        env = common.git_env()
        env.update(JAVA_OPTS='-Xmx2g', PYTHONDONTWRITEBYTECODE='1')
        start = time.monotonic()
        with (directory / 'stdout.log').open('xb') as out, (directory / 'stderr.log').open('xb') as err:
            process = subprocess.Popen([sys.executable, __file__, '_worker', str(directory)],
                                       env=env, stdout=out, stderr=err, start_new_session=True)
            try:
                code = process.wait(timeout=args.ra_timeout_seconds if variant == 'ra' else 600)
            except BaseException:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                save(directory / 'failure.json', {'reason': 'timeout-or-interruption', 'model_calls': 0})
                raise
        error = (directory / 'stderr.log').read_text(errors='replace')
        require(code == 0 and not re.search(r'\bERROR\b|Exception|timed out|unable to analyze', error, re.I),
                f'PySZZ {variant} failed; inspect logs')
        paths = list((directory / 'out').glob('*.json'))
        require(len(paths) == 1, 'Unexpected output count')
        _, prediction = original.validate_official_output(load(paths[0]), repository=case['repository'], fix_hash=case['synthetic_bfc'])
        for commit in prediction:
            common.git(repo, 'cat-file', '-e', commit + '^{commit}')
        common.validate_subject(repo, case, messages[args.id])
        result = {'variant': variant, 'sample_id': args.id, 'predicted_bics': prediction,
                  'metrics': score(prediction, case['oracle_bics']), 'elapsed_seconds': time.monotonic() - start,
                  'model_calls': 0, 'source_commit': original.PYSZZ_REVISION,
                  'output_sha256': sha(paths[0])}
        save(directory / 'evaluation.json', result)
        results.append(result)
        print(variant + ': passed', flush=True)
    save(output / 'summary.json', results)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
