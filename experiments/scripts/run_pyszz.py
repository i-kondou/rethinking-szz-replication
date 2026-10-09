#!/usr/bin/env python3
"""Preflight and run PySZZ v2 baselines for one frozen sample.

The default mode is read-only preflight. Execution requires ``--execute`` and
runs each requested variant in a fresh ignored temporary directory. The source
repository is copied by PySZZ and is not modified. A success or failure record
is written to ``experiments/results/pyszz/<variant>/<sample_id>.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SAMPLES = PROJECT_ROOT / "data/selected/java_samples.json"
DEFAULT_REPOS_ROOT = PROJECT_ROOT / "experiments/repos"
DEFAULT_PYSZZ_ROOT = PROJECT_ROOT / "tmp/pyszz_v2"
DEFAULT_PYTHON = PROJECT_ROOT / "tmp/pyszz-venv/bin/python"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "experiments/results/pyszz"
DEFAULT_LOCK = PROJECT_ROOT / "config/pyszz/requirements-pyszz-v2-python311.txt"
PYSZZ_REPOSITORY = "https://github.com/grosa1/pyszz_v2"
PYSZZ_REVISION = "67971581881993231b6918128436e1f06239c781"
VARIANT_LABELS = {
    "b": "B-SZZ",
    "ag": "AG-SZZ",
    "ma": "MA-SZZ",
    "r": "R-SZZ",
    "l": "L-SZZ",
}


class BaselineError(RuntimeError):
    """Raised when a baseline precondition or output is invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(
    args: Sequence[str | os.PathLike[str]],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [str(value) for value in args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise BaselineError(
            f"command failed ({result.returncode}): "
            f"{' '.join(str(value) for value in args)}\n{detail}"
        )
    return result


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", repo, *args], check=check)


def write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
    with tempfile.NamedTemporaryFile(
        prefix=f".{path.name}.", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def load_sample(samples_path: Path, sample_id: int) -> dict[str, object]:
    try:
        rows = json.loads(samples_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"cannot read sample dataset: {samples_path}") from exc
    matches = [row for row in rows if row.get("id") == sample_id]
    if len(matches) != 1:
        raise BaselineError(
            f"expected exactly one sample with id {sample_id}, found {len(matches)}"
        )
    sample = matches[0]
    if not sample.get("bugs"):
        raise BaselineError(f"sample {sample_id} has no Oracle BIC")
    return sample


def sample_fields(sample: dict[str, object]) -> tuple[str, str, list[str]]:
    try:
        repository = str(sample["repository"])
        fix_hash = str(sample["fix"]["commit"]["hash"])  # type: ignore[index]
        oracle = sorted(
            {str(bug["commit"]["hash"]) for bug in sample["bugs"]}  # type: ignore[index]
        )
    except (KeyError, TypeError) as exc:
        raise BaselineError("sample does not match the Oracle dataset schema") from exc
    if not re.fullmatch(r"[^/]+/[^/]+", repository):
        raise BaselineError(f"invalid repository name: {repository!r}")
    for label, values in (("fix", [fix_hash]), ("Oracle", oracle)):
        if not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in values):
            raise BaselineError(f"invalid {label} commit hash in sample")
    return repository, fix_hash, oracle


def resolve_variants(values: Sequence[str]) -> list[str]:
    requested = list(values) or ["all"]
    if "all" in requested:
        if len(requested) != 1:
            raise BaselineError("use --variant all alone or list individual variants")
        return list(VARIANT_LABELS)
    unknown = sorted(set(requested) - set(VARIANT_LABELS))
    if unknown:
        raise BaselineError(f"unknown PySZZ variant(s): {', '.join(unknown)}")
    return list(dict.fromkeys(requested))


def locked_versions(lock_path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for raw_line in lock_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s]+)", line)
        if not match:
            raise BaselineError(f"unsupported requirement in compatibility lock: {line}")
        versions[match.group(1)] = match.group(2)
    return versions


def inspect_python(python: Path, lock_path: Path) -> dict[str, object]:
    expected = locked_versions(lock_path)
    program = (
        "import importlib.metadata as m,json,platform,sys;"
        f"names={json.dumps(list(expected))};"
        "print(json.dumps({'executable':sys.executable,'version':platform.python_version(),"
        "'packages':{n:m.version(n) for n in names}}))"
    )
    result = run([python, "-c", program])
    observed = json.loads(result.stdout)
    mismatches = {
        name: {"expected": version, "observed": observed["packages"].get(name)}
        for name, version in expected.items()
        if observed["packages"].get(name) != version
    }
    if mismatches:
        raise BaselineError(f"Python compatibility lock mismatch: {mismatches}")
    return observed


def inspect_tool(command: str, version_args: Sequence[str]) -> dict[str, object]:
    executable = shutil.which(command)
    if not executable:
        raise BaselineError(f"required command is not on PATH: {command}")
    result = run([executable, *version_args])
    return {
        "executable": executable,
        "version_output": (result.stdout or result.stderr).strip(),
    }


def validate_config(config_path: Path, variant: str) -> None:
    text = config_path.read_text(encoding="utf-8")
    required = (
        f"szz_name: {variant}",
        "file_ext_to_parse:\n  - java",
        "issue_date_filter: false",
    )
    missing = [value for value in required if value not in text]
    if missing:
        raise BaselineError(
            f"baseline config does not pin the Java/no-issue-date condition: {config_path}"
        )


def validate_output_gate(output_path: Path, *, execute: bool, overwrite: bool) -> None:
    if execute and output_path.exists() and not overwrite:
        raise BaselineError(
            f"result already exists; pass --overwrite to replace it: {output_path}"
        )


def preflight(
    *,
    sample: dict[str, object],
    variants: Sequence[str],
    pyszz_root: Path,
    python: Path,
    repos_root: Path,
    output_root: Path,
    lock_path: Path,
    execute: bool,
    overwrite: bool,
) -> dict[str, object]:
    repository, fix_hash, oracle = sample_fields(sample)
    if not (pyszz_root / ".git").is_dir():
        raise BaselineError(f"PySZZ v2 checkout is missing: {pyszz_root}")
    revision = git(pyszz_root, "rev-parse", "HEAD").stdout.strip()
    if revision != PYSZZ_REVISION:
        raise BaselineError(
            f"PySZZ revision mismatch: expected {PYSZZ_REVISION}, observed {revision}"
        )
    source_status = git(pyszz_root, "status", "--porcelain").stdout.strip()
    if source_status:
        raise BaselineError("PySZZ source checkout has local changes")

    source_repo = repos_root / repository
    if not (source_repo / ".git").is_dir():
        raise BaselineError(f"source repository is missing: {source_repo}")
    if git(source_repo, "status", "--porcelain").stdout.strip():
        raise BaselineError(f"source repository is not clean: {source_repo}")
    git(source_repo, "cat-file", "-e", f"{fix_hash}^{{commit}}")
    for commit in oracle:
        git(source_repo, "cat-file", "-e", f"{commit}^{{commit}}")

    if not python.is_file():
        raise BaselineError(f"PySZZ Python interpreter is missing: {python}")
    python_info = inspect_python(python, lock_path)
    git_info = inspect_tool("git", ["--version"])
    srcml_info = inspect_tool("srcml", ["--version"])

    configs: dict[str, object] = {}
    outputs: dict[str, str] = {}
    for variant in variants:
        config_path = PROJECT_ROOT / "config/pyszz" / f"{variant}.yml"
        validate_config(config_path, variant)
        output_path = output_root / variant / f"{sample['id']}.json"
        validate_output_gate(output_path, execute=execute, overwrite=overwrite)
        configs[variant] = {
            "path": str(config_path.resolve()),
            "sha256": sha256_file(config_path),
        }
        outputs[variant] = str(output_path.resolve())

    return {
        "ready": True,
        "sample_id": sample["id"],
        "repository": repository,
        "fix_commit_hash": fix_hash,
        "oracle_bic_hashes": oracle,
        "variants": list(variants),
        "condition": {
            "history": "original repository history including the original BFC",
            "bfc_message": "original; PySZZ does not use commit-message text",
            "file_extensions": ["java"],
            "issue_date_filter": False,
        },
        "implementation": {
            "repository": PYSZZ_REPOSITORY,
            "revision": revision,
            "source_clean": True,
        },
        "runtime": {
            "python": python_info,
            "dependency_lock": str(lock_path.resolve()),
            "dependency_lock_sha256": sha256_file(lock_path),
            "git": git_info,
            "srcml": srcml_info,
        },
        "source_repo": str(source_repo.resolve()),
        "configs": configs,
        "outputs": outputs,
    }


def metrics(prediction: Sequence[str], oracle: Sequence[str]) -> dict[str, object]:
    predicted = set(prediction)
    expected = set(oracle)
    true_positive = len(predicted & expected)
    false_positive = len(predicted - expected)
    false_negative = len(expected - predicted)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(expected) if expected else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "exact_set_match": predicted == expected,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def validate_official_output(
    value: object, *, repository: str, fix_hash: str
) -> tuple[dict[str, object], list[str]]:
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        raise BaselineError("PySZZ output must contain exactly one result row")
    row = value[0]
    if row.get("repo_name") != repository or row.get("fix_commit_hash") != fix_hash:
        raise BaselineError("PySZZ output does not match the requested sample")
    prediction = row.get("inducing_commit_hash")
    if not isinstance(prediction, list) or not all(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value)
        for value in prediction
    ):
        raise BaselineError("PySZZ output contains invalid inducing commit hashes")
    return row, sorted(set(prediction))


def execute_variant(
    *,
    plan: dict[str, object],
    variant: str,
    pyszz_root: Path,
    python: Path,
    repos_root: Path,
    output_root: Path,
) -> dict[str, object]:
    sample_id = int(plan["sample_id"])
    repository = str(plan["repository"])
    fix_hash = str(plan["fix_commit_hash"])
    oracle = list(plan["oracle_bic_hashes"])
    config = plan["configs"][variant]  # type: ignore[index]
    config_path = Path(config["path"])  # type: ignore[index]
    output_path = output_root / variant / f"{sample_id}.json"
    temporary_root = PROJECT_ROOT / "tmp"
    temporary_root.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    started = time.monotonic()
    command: list[str] = []
    stdout = ""
    stderr = ""
    returncode: int | None = None
    raw_output: object | None = None
    prediction: list[str] = []
    error: str | None = None

    with tempfile.TemporaryDirectory(
        prefix=f"pyszz-{sample_id}-{variant}-", dir=temporary_root
    ) as temporary:
        run_dir = Path(temporary)
        input_path = run_dir / "input.json"
        write_json_atomic(
            input_path,
            [{"repo_name": repository, "fix_commit_hash": fix_hash}],
        )
        command = [
            str(python),
            str((pyszz_root / "main.py").resolve()),
            str(input_path.resolve()),
            str(config_path.resolve()),
            str(repos_root.resolve()),
        ]
        result = run(command, cwd=run_dir, check=False)
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
        if returncode != 0:
            error = f"PySZZ exited with status {returncode}"
        else:
            candidates = sorted((run_dir / "out").glob("*.json"))
            if len(candidates) != 1:
                error = f"expected one PySZZ output file, found {len(candidates)}"
            else:
                try:
                    raw_output = json.loads(candidates[0].read_text(encoding="utf-8"))
                    _, prediction = validate_official_output(
                        raw_output, repository=repository, fix_hash=fix_hash
                    )
                except (OSError, json.JSONDecodeError, BaselineError) as exc:
                    error = str(exc)

    record: dict[str, object] = {
        "schema_version": 1,
        "kind": "pyszz-v2-baseline-result",
        "status": "failed" if error else "success",
        "sample_id": sample_id,
        "repository": repository,
        "fix_commit_hash": fix_hash,
        "oracle_bic_hashes": oracle,
        "variant": {
            "id": variant,
            "label": VARIANT_LABELS[variant],
            "config_path": str(config_path.resolve()),
            "config_sha256": config["sha256"],  # type: ignore[index]
        },
        "condition": plan["condition"],
        "implementation": plan["implementation"],
        "runtime": plan["runtime"],
        "execution": {
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": time.monotonic() - started,
            "command": command,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        },
        "prediction_bic_hashes": prediction,
        "metrics": metrics(prediction, oracle) if not error else None,
        "raw_pyszz_output": raw_output,
        "error": error,
    }
    write_json_atomic(output_path, record)
    return record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-id", type=int, required=True)
    parser.add_argument(
        "--variant",
        action="append",
        choices=["all", *VARIANT_LABELS],
        default=[],
        help="repeat for multiple variants; default: all",
    )
    parser.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES)
    parser.add_argument("--repos-root", type=Path, default=DEFAULT_REPOS_ROOT)
    parser.add_argument("--pyszz-root", type=Path, default=DEFAULT_PYSZZ_ROOT)
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        variants = resolve_variants(args.variant)
        sample = load_sample(args.samples.resolve(), args.sample_id)
        # Do not resolve the interpreter symlink: doing so escapes the venv.
        python = args.python.expanduser().absolute()
        plan = preflight(
            sample=sample,
            variants=variants,
            pyszz_root=args.pyszz_root.resolve(),
            python=python,
            repos_root=args.repos_root.resolve(),
            output_root=args.output_root.resolve(),
            lock_path=args.lock.resolve(),
            execute=args.execute,
            overwrite=args.overwrite,
        )
        if not args.execute:
            print(json.dumps({"mode": "preflight", **plan}, indent=2, ensure_ascii=False))
            return 0

        records = []
        for variant in variants:
            record = execute_variant(
                plan=plan,
                variant=variant,
                pyszz_root=args.pyszz_root.resolve(),
                python=python,
                repos_root=args.repos_root.resolve(),
                output_root=args.output_root.resolve(),
            )
            records.append(
                {
                    "variant": variant,
                    "status": record["status"],
                    "prediction_bic_hashes": record["prediction_bic_hashes"],
                    "metrics": record["metrics"],
                    "output": plan["outputs"][variant],  # type: ignore[index]
                    "error": record["error"],
                }
            )
        print(json.dumps({"mode": "execute", "results": records}, indent=2))
        return 1 if any(record["status"] != "success" for record in records) else 0
    except BaselineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
