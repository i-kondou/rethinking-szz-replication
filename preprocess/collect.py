#!/usr/bin/env python3
"""Download the pinned DIO dataset and clone selected study repositories."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile

DATASET = Path(__file__).resolve().parents[1] / 'dataset'
DIO_URL = 'https://ndownloader.figshare.com/files/38333798'
ARCHIVE_SHA256 = '5366766ec7a6cbc405e1a1923456628b941de04873c686e53886d2dcc7bc6633'
MEMBER = 'detailed-database/language-filtered.json'
MEMBER_SHA256 = '87c5b319db5f1007d4104453726368a2235ed18b8d142917c9bde183ad2e69d3'
# Preserve the study cohort; do not retry excluded cases or change its labels.
EXCLUSIONS = {
    '478': 'The study could not obtain a complete repository clone.',
    '3536': 'Repository acquisition failed during the study.',
}
REPOSITORY_OVERRIDES = {
    'DanVanAtta/triplea': 'triplea-game/triplea',
    'imagej/imagej': 'imagej/imagej2',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checksum(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_once(path, data):
    if path.exists():
        require(path.read_bytes() == data, f'Existing file differs: {path}')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)


def read_archive(path):
    require(checksum(path) == ARCHIVE_SHA256, 'DIO archive checksum mismatch')
    with zipfile.ZipFile(path) as source:
        members = [name for name in source.namelist()
                   if name == MEMBER or name.endswith('/' + MEMBER)]
        require(len(members) == 1, 'Expected one DIO dataset member')
        raw = source.read(members[0])  # Read one entry; never extract archive paths.
    require(hashlib.sha256(raw).hexdigest() == MEMBER_SHA256,
            'DIO dataset checksum mismatch')
    return raw


def collect_metadata(directory, offline=False):
    archive = directory / 'downloads/dio-v1.zip'
    if not archive.exists():
        require(not offline, f'Offline archive is missing: {archive}')
        archive.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.download-', dir=archive.parent) as temp:
            staged = Path(temp) / 'dio.zip'
            print('Downloading the DIO dataset...', flush=True)
            with urllib.request.urlopen(DIO_URL, timeout=90) as response, staged.open('wb') as out:
                shutil.copyfileobj(response, out)
            read_archive(staged)
            require(not archive.exists(), 'A concurrent download appeared')
            staged.rename(archive)
    raw = read_archive(archive)
    write_once(directory / 'downloads/language-filtered.json', raw)
    return json.loads(raw)


def select_cases(data):
    java = [row for row in data if row['fix']['files']
            and all(file['lang'] == 'java' for file in row['fix']['files'])]
    cases = [row for row in java if str(row['id']) not in EXCLUSIONS]
    require(len({str(row['id']) for row in cases}) == len(cases), 'Duplicate case IDs')
    return sorted(cases, key=lambda row: int(row['id']))


def repository_url(name):
    require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', name)
            and not any(part in {'.', '..'} for part in name.split('/')),
            'Invalid repository name')
    return 'https://github.com/' + REPOSITORY_OVERRIDES.get(name, name) + '.git'


def git(directory, *args, check=True):
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0', GIT_NO_REPLACE_OBJECTS='1')
    return subprocess.run(
        ['git', '-c', 'core.hooksPath=' + os.devnull, '-c', 'credential.helper=',
         '-c', 'protocol.ext.allow=never', '-C', str(directory), *map(str, args)],
        env=env, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600)


def validate_repository(repo, case):
    require(repo.is_dir() and not repo.is_symlink(), f'Missing repository: {repo}')
    require(git(repo, 'rev-parse', '--is-bare-repository').stdout.strip() == b'true',
            'Expected a bare repository')
    require(git(repo, 'rev-parse', '--is-shallow-repository').stdout.strip() == b'false',
            'A shallow repository is not sufficient')
    for pattern in (r'^extensions\.partial[Cc]lone$', r'^remote\..*\.promisor$'):
        require(git(repo, 'config', '--get-regexp', pattern, check=False).returncode == 1,
                'A partial repository is not sufficient')
    require(not (repo / 'objects/info/alternates').exists(), 'External object storage is not supported')
    bfc = case['fix']['commit']['hash']
    require(re.fullmatch(r'[0-9a-f]{40}', bfc), 'Expected a full BFC hash')
    git(repo, 'cat-file', '-e', bfc + '^{commit}')
    git(repo, 'cat-file', '-e', bfc + '^{tree}')


def clone_case(directory, case, offline=False):
    url = repository_url(case['repository'])
    repo = directory / 'repositories' / (case['repository'] + '.git')
    if repo.exists():
        validate_repository(repo, case)
        return repo
    require(not offline, f'Offline repository is missing: {repo}')
    repo.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.clone-', dir=repo.parent) as temp:
        staged = Path(temp) / 'repo.git'
        print(f"Cloning case {case['id']}: {url}", flush=True)
        git(repo.parent, 'clone', '--bare', '--no-hardlinks', '--template=', url, staged)
        validate_repository(staged, case)
        require(not repo.exists(), 'A concurrent clone appeared')
        staged.rename(repo)
    return repo


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--ids', nargs='+', help='Clone repositories for these study case IDs')
    group.add_argument('--all', action='store_true', help='Clone repositories for all 79 cases')
    parser.add_argument('--offline', action='store_true', help='Use cached inputs without network access')
    parser.add_argument('--dataset-dir', type=Path, default=DATASET)
    args = parser.parse_args(argv)
    directory = args.dataset_dir.resolve()
    data = collect_metadata(directory, args.offline)
    cases = select_cases(data)
    require(len(cases) == 79 and len({row['repository'] for row in cases}) == 70,
            'The selected cohort differs from the study')
    selected = cases if args.all else []
    if args.ids:
        by_id = {str(row['id']): row for row in cases}
        require(len(set(args.ids)) == len(args.ids) and set(args.ids) <= by_id.keys(),
                'Unknown or duplicate study case ID')
        selected = [by_id[sid] for sid in args.ids]
    selection = {'source_url': DIO_URL, 'archive_sha256': ARCHIVE_SHA256,
                 'dataset_sha256': MEMBER_SHA256, 'exclusions': EXCLUSIONS, 'cases': cases}
    write_once(directory / 'selection.json', (json.dumps(selection, indent=2) + '\n').encode())
    for case in selected:
        clone_case(directory, case, args.offline)
        print(f"Case {case['id']}: repository and BFC verified", flush=True)
    print('Selected 79 cases from 70 repositories.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
