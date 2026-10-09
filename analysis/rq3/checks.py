"""Verify archived Java observations and source snapshots, without rerunning Java."""
import itertools,json,re
from common import ROOT,load,require,sha
VIVIDUS="analysis/rq3/tests/2557"
REPRO="analysis/rq3/tests/history"
def read(path):return load(ROOT/path)

def check_bookkeeper():
    attempt = 'analysis/rq3/tests/2911/attempt002'
    observations = read(attempt + '/observations.json')
    points = ['c1', 'c2_parent', 'c2', 'oracle_parent', 'oracle', 'bfc_parent', 'bfc']
    expected = set(itertools.product(points, ['object', 'long', 'int'], [True, False], [1, 2]))
    actual = {(r['point'], r['mode'], r['trace'], r['repeat']) for r in observations}
    require(len(observations) == 84 and actual == expected, 'Incomplete BookKeeper matrix')
    for row in observations:
        raw = read(attempt + '/' + row['raw'])
        require(raw['exit'] == 0 and not raw['timeout'], 'Failed BookKeeper harness')
        parsed = json.loads(raw['stdout'])
        require(all(row.get(k) == v for k, v in parsed.items()), 'BookKeeper summary/raw mismatch')
        require(row['task_count'] == 1, 'BookKeeper task count mismatch')
        wrapped = row['trace'] and (row['point'] in {'c1', 'c2_parent', 'bfc'} or row['mode'] == 'object')
        require(len(row['queued_nanos']) == len(row['execution_nanos']) == int(wrapped), 'BookKeeper timing count mismatch')
        if wrapped:
            require(row['queued_within_elapsed'] == (row['point'] == 'bfc'), 'BookKeeper timing boundary mismatch')
    snapshots = read(attempt + '/source-manifest.json')
    for item in snapshots:
        require(sha(ROOT / attempt / item['snapshot']) == item['sha256'], 'Changed BookKeeper source snapshot')
    return {'observations': len(observations), 'source_snapshots': len(snapshots)}


def check_vividus():
    observations = read(VIVIDUS + '/results.json')
    expected = set(itertools.product(['bfc', 'bfc_parent', 'claude', 'claude_parent', 'oracle', 'oracle_parent', 'variables_parent'],
                                    ['plain', 'parameter', 'examples'], [False, True], [1, 2]))
    keys = {(r['point'], r['mode'], r['initialized'], r['repeat']) for r in observations}
    require(len(observations) == 84 and keys == expected, 'Incomplete Vividus matrix')
    for row in observations:
        name = f"{row['point']}-{row['mode']}-init{str(row['initialized']).lower()}-r{row['repeat']}.json"
        raw = read(VIVIDUS + '/attempt04/' + name)
        require(raw['exit'] == 0 and not raw.get('timeout', False), 'Failed Vividus harness')
        failure = row['mode'] == 'examples' and not row['initialized'] and row['point'] not in {'variables_parent', 'bfc'}
        require(('DESCRIPTION_ERROR' in raw['stdout']) == failure, 'Vividus error boundary mismatch')
        require(('DESCRIPTION_OK' in raw['stdout']) != failure, 'Vividus success boundary mismatch')
        require(row['outcome'] == ('NPE' if failure else 'description_created'), 'Vividus summary/raw mismatch')
    for point, repeat in itertools.product(['oracle_parent', 'bfc'], [1, 2]):
        raw = read(VIVIDUS + f'/attempt04/{point}-execution-control-r{repeat}.json')
        require(raw['exit'] == 0 and 'EXECUTION_CONTROL_OK' in raw['stdout'], 'Missing Vividus positive control')
        require('COUNTS beforeStory=3 conversions=1 stepExecutions=1' in raw['stdout'], 'Vividus positive control mismatch')
    snapshots = read(VIVIDUS + '/attempt04/source-manifest.json')
    for item in snapshots:
        path = ROOT / VIVIDUS / 'attempt04' / item['point'] / 'sources' / item['path']
        require(sha(path) == item['sha256'], 'Changed Vividus source snapshot')
    return {'observations': len(observations), 'positive_controls': 4, 'source_snapshots': len(snapshots)}


def check_candidate_tests():
    groups = [(907, 'claude-candidates-usage-20260912/usage-history-01'),
              (3530, 'java-causal-expansion-20260912/expansion-history-01')]
    total = 0
    for case, group in groups:
        for point, repeat in itertools.product(['C_parent', 'C', 'I_parent', 'I'], [1, 2, 3]):
            raw = read(f'{REPRO}/runs/{group}/{case}/{point}/test-{repeat}.json')
            require(not raw['timeout'] and raw['returncode'] in {0, 1}, 'Candidate test did not complete')
            match = re.search(r'MEASURE tests=(\d+) failures=(\d+) ignored=(\d+) assumptions=(\d+)', raw['stdout'])
            require(match is not None and int(match[1]) > 0, 'Missing JUnit observations')
            require((int(match[2]) == 0) == (point == 'C_parent'), 'Unexpected candidate test boundary')
            total += 1
    return {'saved_test_processes': total}


