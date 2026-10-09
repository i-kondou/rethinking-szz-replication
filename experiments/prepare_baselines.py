#!/usr/bin/env python3
"""Verify and extract the bundled study implementations. No network or model calls."""
import argparse
import json
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile

from runtime import ROOT, load, require, sha

ARCHIVES = ROOT / 'experiments/implementations'


def bundle(name):
    record = load(ARCHIVES / 'manifest.json')[name]
    archive = ARCHIVES / record['archive']
    require(sha(archive) == record['sha256'], f'Bundle checksum differs: {name}')
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        require(len(names) == len(set(names)), 'Duplicate archive members')
        for entry in zf.infolist():
            rel = PurePosixPath(entry.filename)
            require(not rel.is_absolute() and '..' not in rel.parts and '\\' not in entry.filename,
                    'Unsafe archive path')
            require(not stat.S_ISLNK(entry.external_attr >> 16), 'Archive contains a symlink')
        manifest = json.loads(zf.read('bundle.json'))
        require(manifest['name'] == name, 'Bundle name differs')
        require(set(names) == {'bundle.json', *manifest['files']}, 'Bundle inventory differs')
    return archive, record, manifest


def verify(workspace, name):
    archive, record, manifest = bundle(name)
    root = workspace / 'baselines' / name
    require(root.is_dir() and not root.is_symlink(),
            f'Missing implementation: run experiments/prepare_baselines.py --extract ({name})')
    with zipfile.ZipFile(archive) as zf:
        require((root / 'bundle.json').read_bytes() == zf.read('bundle.json'), 'Bundle manifest changed')
    expected = {'bundle.json', *manifest['files']}
    actual = set()
    for path in root.rglob('*'):
        require(not path.is_symlink(), f'Unexpected symlink: {path}')
        if path.is_file():
            actual.add(path.relative_to(root).as_posix())
    require(actual == expected, f'Extracted inventory changed: {name}')
    for rel, metadata in manifest['files'].items():
        require(sha(root / rel) == metadata['sha256'], f'Modified bundled file: {name}/{rel}')
        if rel.startswith('adapter/'):
            package_file = ROOT / rel.removeprefix('adapter/')
            require(package_file.is_file() and sha(package_file) == metadata['sha256'],
                    f'Execution adapter differs from the bundle: {package_file}')
    return root / 'source', {'bundle': str(archive), 'bundle_sha256': record['sha256'],
                              'origin': manifest['origin']}


def extract(workspace, name):
    archive, _, manifest = bundle(name)
    destination = workspace / 'baselines' / name
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.extract-', dir=destination.parent) as tmp:
            staged = Path(tmp) / name
            staged.mkdir()
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(staged)
            for rel, metadata in manifest['files'].items():
                (staged / rel).chmod(0o755 if metadata['executable'] else 0o644)
            require(not destination.exists(), 'A concurrent extraction appeared')
            staged.rename(destination)
    return verify(workspace, name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=ROOT / 'dataset')
    parser.add_argument('--extract', action='store_true')
    args = parser.parse_args()
    records = load(ARCHIVES / 'manifest.json')
    for name in records:
        bundle(name)
        if args.extract:
            extract(args.workspace.resolve(), name)
    print(json.dumps({'mode': 'extracted-and-verified' if args.extract else 'verified',
                      'implementations': list(records), 'model_calls': 0}, indent=2))


if __name__ == '__main__':
    main()
