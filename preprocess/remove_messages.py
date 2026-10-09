#!/usr/bin/env python3
"""Prepare and verify message-free copies; never invoke a model."""
import argparse
from contextlib import nullcontext
from pathlib import Path
import sys

from common import (DEFAULT_WORKSPACE, ROOT, load, read_package, require,
                    select_cases, sha, subject_path, validate_subject, write_new, json_bytes)
sys.path.insert(0, str(Path(__file__).resolve().parent / 'git_message_scrubber/src'))
from git_message_scrubber import core
import fsck_policy


def prepare(workspace, case, message):
    sid = case['id']
    source = subject_path(workspace, case)
    validate_subject(source, case, message)
    bundle = workspace / 'message_free' / sid
    scope = nullcontext(None)
    if sid == '3459':
        fsck_policy.SOURCE, fsck_policy.BUNDLE = source, bundle
        scope = fsck_policy.scoped_fsck(core, sid, bundle, source, fsck_policy.APPROVAL)
    with scope as audit:
        if bundle.exists():
            manifest = load(bundle / 'metadata/manifest.json')
            verified = core.verify(bundle, source)
        else:
            bundle.parent.mkdir(parents=True, exist_ok=True)
            manifest = core.create(source, bundle, collision_policy='identity-header')
            verified = manifest['verification']
        require(manifest['policy']['commit_messages'] == 'empty' and
                not manifest['policy']['keep_messages'], 'Wrong message-removal policy')
        mapping = core.read_map(bundle / 'metadata/commit-map.tsv', manifest['map_sha256'])
        bfc = mapping[case['synthetic_bfc']]
        diff = core.git(bundle / 'repo', 'show', '--no-ext-diff', '--no-textconv', '--stat', '--patch', 'HEAD')
        prompt = (ROOT / 'preprocess/prompt.txt').read_text().format(
            synthetic_fix_hash=bfc, masked_message='', diff=diff.decode('utf-8', errors='replace').strip())
        expected = load(ROOT / 'dataset/metadata/message-free.json')[sid]
        require(bfc == expected['new_bfc'] and sha(prompt.encode()) == expected['prompt_sha256'],
                'Message-free BFC or prompt does not match the experiment')
        write_new(bundle / 'metadata/prompt.md', prompt.encode())
        result = dict(id=sid, new_bfc=bfc, prompt_sha256=expected['prompt_sha256'],
                      commit_map_sha256=manifest['map_sha256'], verified=verified, model_calls=0)
        write_new(bundle / 'metadata/check.json', json_bytes(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ids', nargs='+')
    group.add_argument('--all', action='store_true')
    parser.add_argument('--workspace', type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    data, messages, _ = read_package()
    cases = select_cases(data, 'all', args.ids)
    for case in cases:
        if args.execute:
            result = prepare(args.workspace.resolve(), case, messages[case['id']])
            print(f"Case {case['id']}: empty messages, graph, map and prompt verified")
        else:
            print(f"Case {case['id']}: plan only; add --execute to prepare")


if __name__ == '__main__':
    main()
