#!/usr/bin/env python3
"""Materialize the frozen SZZ-Agent source without Oracle-controlled stopping.

The upstream checkout remains unchanged.  For each run, this module copies only
the five Python files required by SZZ-Agent and Simple-SZZ-Agent into the run
artifact and applies two narrow, checksum-guarded transformations:

* Simple-SZZ-Agent continues candidate selection when the Oracle BIC is absent
  from its generated candidate corpus.
* SZZ-Agent Stage 2 completes its normal search without using Oracle positions
  either to skip the search or to stop after an incorrect branch.

The Oracle remains available to the frozen code for evidence redaction and
post-hoc evaluation, but it no longer controls whether or how long the model is
invoked.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


PATCH_ID = "oracle-independent-search-v1"
REQUIRED_SOURCE_HASHES = {
    "simple_szz_agent.py": "0d305138f8307fe24b0ad655a5a7bab9654eac4dff4c4aa9edff6f0c31613aaf",
    "szz_agent_stage_01.py": "5eebc5067aa319a936c9d2a6e12f806e0b286326511661b37361093ac4319754",
    "szz_agent_stage_02.py": "211a63a769cbd9a87a42747528417e3e55ed8845190807d6094f92c1ddabfd0e",
    "prompts.py": "11a3fbf9e5e0af28c8a84d278481720c336800c248df26b2fb2d37c204949c2a",
    "evaluation_utils.py": "0568c8c84ee8aa9dee5af625fe590b4282f23d3d12812f3c0e07e6ecb74728d3",
}
MANIFEST_NAME = "oracle-independent-source.json"


class OracleIndependentPatchError(RuntimeError):
    """Raised when the frozen source cannot be transformed exactly."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _replace_between(
    text: str,
    *,
    start_marker: str,
    end_marker: str,
    replacement: str,
    label: str,
) -> str:
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise OracleIndependentPatchError(
            f"{label} markers do not occur exactly once in the frozen source"
        )
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement + text[end:]


def patch_simple_source(text: str) -> str:
    start = "    # Early stop: if ground truth BIC is not in candidates, LLM cannot find it\n"
    end = "    # Step 2: Prepare candidate selection directory\n"
    replacement = (
        "    # Oracle-independent evaluation condition: candidate coverage is\n"
        "    # recorded only for post-hoc analysis.  Selection proceeds over the\n"
        "    # method-generated corpus even when it does not contain the Oracle.\n\n"
    )
    patched = _replace_between(
        text,
        start_marker=start,
        end_marker=end,
        replacement=replacement,
        label="Simple-SZZ-Agent Oracle-coverage early stop",
    )
    if "Early stop: ground truth BIC not in candidates" in patched:
        raise OracleIndependentPatchError(
            "Simple-SZZ-Agent Oracle-coverage early stop remains after patching"
        )
    return patched


def patch_stage2_source(text: str) -> str:
    start = "    # Find ALL ground truth BIC positions in candidates (handles multiple BICs)\n"
    end = "    # Run binary search with path mapping and ground truth for early stopping\n"
    replacement = (
        "    # Oracle-independent evaluation condition: start from the complete\n"
        "    # method-generated history without inspecting Oracle reachability.\n"
        "    print(f\"\\n[{entry_id}] Starting BIC finder: {len(candidates)} candidates\")\n"
        "    logging.info(f\"[{entry_id}] Starting BIC finder (fix: {fix_commit[:8]}, "
        "{len(candidates)} candidates)\")\n\n"
        "    # Run binary search without Oracle-aware branch termination.\n"
    )
    patched = _replace_between(
        text,
        start_marker=start,
        end_marker=end,
        replacement=replacement,
        label="SZZ-Agent Stage 2 Oracle-coverage early stop",
    )
    old_argument = "path_mapping=path_mapping, ground_truth_bic_indices=ground_truth_bic_indices,"
    new_argument = "path_mapping=path_mapping, ground_truth_bic_indices=None,"
    if patched.count(old_argument) != 1:
        raise OracleIndependentPatchError(
            "SZZ-Agent Stage 2 Oracle-aware branch argument changed"
        )
    patched = patched.replace(old_argument, new_argument, 1)
    evaluation_marker = "    # Check if found BIC matches ground truth (correct if matches ANY ground truth BIC)\n"
    if patched.count(evaluation_marker) != 1:
        raise OracleIndependentPatchError(
            "SZZ-Agent Stage 2 evaluation marker changed"
        )
    evaluation_prefix = (
        "    # Oracle positions are computed only after the search has finished.\n"
        "    ground_truth_bic_indices = find_all_bic_positions(bic_commits, candidates)\n\n"
    )
    patched = patched.replace(
        evaluation_marker,
        evaluation_prefix + evaluation_marker,
        1,
    )
    forbidden = (
        "Early stop: ground truth BIC not in candidates",
        "ground_truth_bic_indices=ground_truth_bic_indices",
    )
    if any(value in patched for value in forbidden):
        raise OracleIndependentPatchError(
            "SZZ-Agent Stage 2 Oracle-controlled stopping remains after patching"
        )
    return patched


def _manifest(target_root: Path) -> dict[str, Any]:
    path = target_root / MANIFEST_NAME
    if not path.is_file():
        raise OracleIndependentPatchError(f"derived source manifest is missing: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OracleIndependentPatchError("derived source manifest is malformed") from exc
    if not isinstance(value, dict):
        raise OracleIndependentPatchError("derived source manifest is not an object")
    return value


def validate_materialized_source(target_root: Path) -> dict[str, Any]:
    value = _manifest(target_root)
    if value.get("patch_id") != PATCH_ID:
        raise OracleIndependentPatchError("derived source patch ID changed")
    files = value.get("files")
    if not isinstance(files, dict) or set(files) != set(REQUIRED_SOURCE_HASHES):
        raise OracleIndependentPatchError("derived source file manifest changed")
    for name, metadata in files.items():
        path = target_root / "src" / name
        if not isinstance(metadata, dict) or not path.is_file():
            raise OracleIndependentPatchError(f"derived source file is missing: {name}")
        if metadata.get("source_sha256") != REQUIRED_SOURCE_HASHES[name]:
            raise OracleIndependentPatchError(f"frozen source hash changed: {name}")
        if sha256_file(path) != metadata.get("derived_sha256"):
            raise OracleIndependentPatchError(f"derived source hash changed: {name}")
    return value


def materialize(source_root: Path, runtime_root: Path) -> tuple[Path, dict[str, Any]]:
    source = source_root.expanduser().resolve()
    target = runtime_root.expanduser().resolve() / "oracle-independent-szz-agent-source"
    if target.exists():
        return target, validate_materialized_source(target)

    source_dir = source / "src"
    if not source_dir.is_dir():
        raise OracleIndependentPatchError(f"frozen SZZ-Agent source is missing: {source_dir}")
    target_src = target / "src"
    target_src.mkdir(parents=True, exist_ok=False)
    records: dict[str, dict[str, str]] = {}
    for name, expected_sha256 in REQUIRED_SOURCE_HASHES.items():
        source_path = source_dir / name
        if not source_path.is_file() or sha256_file(source_path) != expected_sha256:
            raise OracleIndependentPatchError(f"frozen source differs for {name}")
        target_path = target_src / name
        shutil.copy2(source_path, target_path)
        records[name] = {
            "source_path": str(source_path),
            "source_sha256": expected_sha256,
            "derived_sha256": sha256_file(target_path),
        }

    simple_path = target_src / "simple_szz_agent.py"
    simple_path.write_text(
        patch_simple_source(simple_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    stage2_path = target_src / "szz_agent_stage_02.py"
    stage2_path.write_text(
        patch_stage2_source(stage2_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    records["simple_szz_agent.py"]["derived_sha256"] = sha256_file(simple_path)
    records["szz_agent_stage_02.py"]["derived_sha256"] = sha256_file(stage2_path)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "kind": "claude-szz-oracle-independent-szz-agent-source",
        "patch_id": PATCH_ID,
        "source_root": str(source),
        "derived_root": str(target),
        "oracle_use_policy": (
            "Oracle may be used for evidence redaction and post-hoc evaluation, "
            "but not candidate-coverage gating or search-branch termination"
        ),
        "files": records,
    }
    write_json(target / MANIFEST_NAME, manifest)
    return target, validate_materialized_source(target)
