#!/usr/bin/env python3
"""Plan or clone and prepare exact final-v2 repositories. Never invokes a model."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from common import (DEFAULT_WORKSPACE, commit_parts, git, git_commit_hash, gtext,
    json_bytes, read_package, remove_signatures, require, select_cases, sha,
    subject_path, validate_subject, within, write_new)


def source_path(workspace, case, source_root=None):
    if source_root:
        path = Path(source_root).resolve() / case["repository"]
        return path if path.is_dir() else path.with_name(path.name + ".git")
    return Path(workspace).resolve() / "repositories" / (case["repository"] + ".git")


def validate_source(source, case):
    require(source.is_dir(), f"Missing source clone: {source}")
    require(gtext(source, "rev-parse", "--is-shallow-repository") == "false", "Shallow clone is not sufficient")
    require(git(source, "config", "--get", "extensions.partialClone", check=False).returncode != 0,
            "Partial clone is not sufficient")
    require(git(source, "config", "--get-regexp", "^remote\\..*\\.promisor$", check=False).returncode != 0,
            "Promisor clone is not sufficient")
    raw = git(source, "cat-file", "commit", case["bfc"]).stdout
    require(git_commit_hash(raw) == case["bfc"] and sha(raw) == case["source_commit_sha256"],
            "Source BFC bytes do not match the frozen input")
    return raw


def is_case_sensitive(directory):
    with tempfile.TemporaryDirectory(prefix=".case-probe-", dir=directory) as temp:
        path = Path(temp) / "CaseProbe"
        path.write_bytes(b"")
        return not (Path(temp) / "caseprobe").exists()


def build_subject(source, destination, case, message):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    require(not within(destination, source) and not within(source, destination),
            "Source and subject repositories must be disjoint")
    if destination.exists():
        return {**validate_subject(destination, case, message), "reused_verified_subject": True}
    raw = validate_source(source, case)
    header, original, tree, parents = commit_parts(raw)
    require(original == message["original_message"].encode("utf-8"), "Original message differs")
    require(tree == case["tree"] and parents == case["parents"], "Source tree or parents differ")
    synthetic = remove_signatures(header) + b"\n\n" + message["modified_message"].encode("utf-8")
    require(git_commit_hash(synthetic) == case["synthetic_bfc"] and
            sha(synthetic) == case["synthetic_commit_sha256"], "Rewritten commit does not reproduce")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if case.get("requires_case_sensitive_filesystem"):
        require(is_case_sensitive(destination.parent),
                f"ID {case['id']} needs a case-sensitive filesystem; use --case-sensitive-root")
    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=destination.parent) as temp:
        temp = Path(temp)
        staging, checkout = temp / "staging.git", temp / "repo"
        git(temp, "init", "--bare", "--template=", staging)
        git(staging, "fetch", "--no-tags", "--no-write-fetch-head", source, case["bfc"])
        created = git(staging, "hash-object", "-t", "commit", "-w", "--stdin", data=synthetic).stdout.decode().strip()
        require(created == case["synthetic_bfc"], "Git computed a different synthetic commit")
        git(staging, "update-ref", "refs/heads/subject-bfc", created)
        # --no-local forces an upload-pack transfer of only this branch's reachable
        # objects. The original BFC remains only in our disposable staging repo.
        # Neither a reset nor an in-place history rewrite is performed on source.
        git(temp, "clone", "--template=", "--no-local", "--single-branch", "--no-tags",
            "--branch", "subject-bfc", staging, checkout)
        git(checkout, "remote", "remove", "origin")
        git(checkout, "reflog", "expire", "--expire=now", "--all")
        result = validate_subject(checkout, case, message)
        if case['id'] == '3459':
            from fsck_policy import verify_prepared
            result['inherited_fsck_exception'] = verify_prepared(source, checkout, case['id'], git)
        else:
            git(checkout, "fsck", "--full", "--no-reflogs", "--no-dangling")
        require(not destination.exists(), f"Concurrent subject appeared: {destination}")
        checkout.rename(destination)
    return {**result, "reused_verified_subject": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ids", nargs="+", help="Prepare these study case IDs")
    group.add_argument("--all", action="store_true")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--case-sensitive-root", type=Path)
    parser.add_argument("--source-root", type=Path, help="Read-only local owner/repository cache; no downloads")
    parser.add_argument("--verify", action="store_true", help="Verify existing subjects without cloning or writing")
    parser.add_argument("--execute", action="store_true", help="Prepare from existing original clones")
    parser.add_argument("--min-free-gib", type=float, default=10)
    args = parser.parse_args()
    try:
        require(not (args.verify and args.execute), "--verify cannot be combined with write modes")
        require(args.min_free_gib >= 0, "Invalid resource limit")
        dataset, messages, _ = read_package()
        cases = select_cases(dataset, "all", args.ids)
        workspace = args.workspace.resolve()
        plan = {"mode": "execute" if args.execute else "verify" if args.verify else "plan-only",
                "model_invoked": False, "case_count": len(cases),
                "unique_source_repositories": len({c['repository'] for c in cases}),
                "workspace": str(workspace), "download_enabled": False,
                "cases": [{"id": c["id"], "repository": c["repository"], "clone_url": c["clone_url"],
                    "source": str(source_path(workspace, c, args.source_root)),
                    "subject": str(subject_path(workspace, c, args.case_sensitive_root)),
                    "requires_case_sensitive_filesystem": c["requires_case_sensitive_filesystem"]} for c in cases]}
        print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
        if not args.execute and not args.verify:
            return 0
        failures = []
        for case in cases:
            sid = case["id"]
            destination = subject_path(workspace, case, args.case_sensitive_root)
            try:
                if args.verify:
                    result = validate_subject(destination, case, messages[sid])
                else:
                    workspace.mkdir(parents=True, exist_ok=True)
                    require(shutil.disk_usage(workspace).free >= args.min_free_gib * 1024**3,
                            "Free disk space is below --min-free-gib; existing data is preserved")
                    if destination.exists():
                        result = validate_subject(destination, case, messages[sid])
                    else:
                        source = source_path(workspace, case, args.source_root)
                        validate_source(source, case)
                        result = build_subject(source, destination, case, messages[sid])
                print(json.dumps({"id": sid, **result}), flush=True)
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                failures.append({"id": sid, "error": str(exc)})
                print(json.dumps(failures[-1]), flush=True)
        print(json.dumps({"selected": len(cases), "passed": len(cases) - len(failures),
                          "failures": failures, "model_invoked": False}, indent=2))
        return 1 if failures else 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
