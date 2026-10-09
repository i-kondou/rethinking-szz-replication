#!/usr/bin/env python3
"""Preflight or run one sanitized LLM4SZZ/SZZ-Agent/Simple-SZZ-Agent slot.

The default mode is read-only and never invokes a model. Real execution needs
an explicit resource acknowledgement, a fresh run directory, and a positive
per-run cap. LLM4SZZ additionally requires separately billed Anthropic API
authorization; both Claude Code agent baselines require a manual
usage-credits-disabled confirmation.

The frozen upstream checkouts are never modified. Internal launcher modes load
their code at the pinned revision while redirecting datasets, repositories,
logs, and temporary files into the immutable per-attempt directory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import types
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence

from llm_baseline_common import (
    BaselineError,
    CLAUDE_CODE_VERSION,
    DEFAULT_SOURCE_MANIFEST,
    MODEL,
    load_json,
    load_subject,
    prepare_runtime_input,
    repository_snapshot,
    sanitized_environment,
    sha256_bytes,
    sha256_file,
    utc_now,
    validate_source_manifest,
    write_atomic,
    write_json,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = Path("/Users/user-01/research/workspaces/claude-szz/baselines/venv/bin/python")
RESOURCE_ACKNOWLEDGEMENT = "I_ACKNOWLEDGE_LLM_BASELINE_RESOURCE_USE"
API_BILLING_ACKNOWLEDGEMENT = "I_ACKNOWLEDGE_ANTHROPIC_API_BILLING"
USAGE_CREDITS_ACKNOWLEDGEMENT = "I_CONFIRMED_USAGE_CREDITS_DISABLED"
DEFAULT_TIMEOUT_SECONDS = 3600
LLM4SZZ_MAX_OUTPUT_TOKENS = 4096
SONNET5_INPUT_USD_PER_MILLION = Decimal("3")
SONNET5_OUTPUT_USD_PER_MILLION = Decimal("15")
SAFE_AGENT_SYSTEM_PROMPT = """\
You are running one controlled SZZ-Agent analysis. Use only Read to inspect
files below the current working directory and Write only to create result.txt
in that directory. Do not use the network, shell, plugins, skills, subagents,
memory, or paths outside the current directory. Follow INSTRUCTIONS.md exactly.
"""
SAFE_SIMPLE_AGENT_SYSTEM_PROMPT = """\
You are running one controlled Simple-SZZ-Agent analysis. Use only Read, Grep,
and Glob to inspect files below the current working directory and Write only to
create result.txt in that directory. Do not use the network, shell, plugins,
skills, subagents, memory, or paths outside the current directory. Follow
INSTRUCTIONS.md exactly.
"""
SZZ_RESULT_WRITE_MODE = "validated_exact_target_stream_proxy"
MAX_PROXIED_RESULT_BYTES = 1_000_000
TOKEN_USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
    "thinking_tokens",
)
BASELINES = ("llm4szz", "szz-agent", "simple-szz-agent")
SUBSCRIPTION_BASELINES = {"szz-agent", "simple-szz-agent"}


def parse_positive_decimal(value: str | None, label: str) -> Decimal | None:
    if value is None:
        return None
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise BaselineError(f"{label} must be a decimal number") from exc
    if not result.is_finite() or result <= 0:
        raise BaselineError(f"{label} must be positive and finite")
    return result


def inspect_runtime_python(python_bin: Path, baseline: str) -> dict[str, object]:
    python_bin = python_bin.expanduser()
    if not python_bin.is_absolute():
        python_bin = Path.cwd() / python_bin
    if not python_bin.is_file():
        raise BaselineError(f"baseline Python is missing: {python_bin}")
    modules = ["git", "pydriller", "dotenv"]
    if baseline == "llm4szz":
        modules += ["anthropic", "openai", "tiktoken", "tree_sitter", "Levenshtein"]
    script = (
        "import importlib,json,platform; "
        f"mods={modules!r}; "
        "[importlib.import_module(m) for m in mods]; "
        "print(json.dumps({'version':platform.python_version(),'modules':mods}))"
    )
    result = subprocess.run(
        [str(python_bin), "-c", script],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise BaselineError(
            f"baseline Python dependency check failed: {result.stderr.strip()}"
        )
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise BaselineError("baseline Python returned malformed inspection output") from exc
    value["executable"] = str(python_bin)
    return value


def inspect_subscription_claude(claude_bin: str) -> dict[str, object]:
    try:
        from run_sanitized_subject import inspect_claude
    except ImportError as exc:
        raise BaselineError("could not import the frozen ClaudeSZZ auth validator") from exc
    try:
        value = inspect_claude(claude_bin, sanitized_environment())
    except Exception as exc:
        raise BaselineError(str(exc)) from exc
    if value.get("version") != CLAUDE_CODE_VERSION:
        raise BaselineError(
            f"Claude Code baseline requires Claude Code {CLAUDE_CODE_VERSION} exact; "
            f"found {value.get('version')}"
        )
    return value


def public_preflight(
    *,
    baseline: str,
    subject: dict[str, object],
    sources: dict[str, object],
    runtime: dict[str, object],
    claude: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "valid": True,
        "mode": "preflight-only",
        "baseline": baseline,
        "model": MODEL,
        "model_policy": "canonical_fixed_snapshot",
        "model_invoked": False,
        "model_resource_cost_usd": "0",
        "sample_id": subject["sample_id"],
        "repository": subject["repository"],
        "synthetic_fix_hash": subject["synthetic_fix"],
        "prompt_metadata_sha256": subject["metadata_sha256"],
        "repository_checks": subject["snapshot"],
        "source_provenance": sources,
        "runtime_python": runtime,
        "claude_code": claude,
        "billing_boundary": (
            {
                "type": "separately_billed_anthropic_messages_api",
                "credential_required_at_execution": "ANTHROPIC_API_KEY",
                "credential_present": bool(os.environ.get("ANTHROPIC_API_KEY")),
                "temperature_sent": False,
                "max_output_tokens": LLM4SZZ_MAX_OUTPUT_TOKENS,
            }
            if baseline == "llm4szz"
            else {
                "type": "claude_ai_subscription_oauth",
                "api_credentials_forwarded": False,
                "usage_credits_state": "manual_confirmation_required_at_execution",
                "upstream_dangerously_skip_permissions_used": False,
                "result_write_mode": SZZ_RESULT_WRITE_MODE,
                "available_tools": (
                    ["Read", "Grep", "Glob", "Write"]
                    if baseline == "simple-szz-agent"
                    else ["Read", "Write"]
                ),
            }
        ),
    }


def execute_process(
    command: list[str],
    *,
    env: dict[str, str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
) -> dict[str, object]:
    started = time.monotonic()
    timed_out = False
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout_seconds,
                check=False,
            )
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = None
    return {
        "command": command,
        "exit_code": returncode,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
        "duration_seconds": time.monotonic() - started,
        "stdout_path": str(stdout_path),
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_path": str(stderr_path),
        "stderr_sha256": sha256_file(stderr_path),
    }


def newest_file(root: Path, pattern: str) -> Path | None:
    matches = list(root.glob(pattern))
    return max(matches, key=lambda item: item.stat().st_mtime_ns) if matches else None


def recent_commits(repo: Path, candidates: list[str]) -> list[str]:
    dated: list[tuple[int, str]] = []
    for candidate in set(candidates):
        if not candidate:
            continue
        result = subprocess.run(
            ["git", "-C", str(repo), "show", "-s", "--format=%ct", candidate],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip().isdigit():
            dated.append((int(result.stdout.strip()), candidate))
    if not dated:
        return []
    latest = max(item[0] for item in dated)
    return sorted(item[1] for item in dated if item[0] == latest)


def parse_llm4szz_prediction(
    runtime_root: Path, subject: dict[str, object]
) -> tuple[list[str], Path]:
    log_path = (
        runtime_root
        / "llm4szz/save_logs/subjects"
        / str(subject["sample_id"])
        / str(subject["synthetic_fix"])
        / "llm4szz0.json"
    )
    if not log_path.is_file():
        raise BaselineError(f"LLM4SZZ did not produce its per-entry log: {log_path}")
    value = load_json(log_path)
    if not isinstance(value, list):
        raise BaselineError("LLM4SZZ per-entry log is malformed")
    s2: list[str] = []
    s1_ranked: list[dict[str, object]] = []
    s1_file: list[str] = []
    can_determine = True
    for row in value:
        if not isinstance(row, dict):
            continue
        if "can_determine" in row:
            can_determine = can_determine and bool(row["can_determine"])
        if isinstance(row.get("s2_final_cid"), list):
            s2.extend(str(item) for item in row["s2_final_cid"])
        if isinstance(row.get("s1_ranked_stmts_infos"), list):
            s1_ranked.extend(
                item for item in row["s1_ranked_stmts_infos"][:5] if isinstance(item, dict)
            )
        if isinstance(row.get("s1_llm_file_final_cids"), list):
            s1_file.extend(str(item) for item in row["s1_llm_file_final_cids"])
    s1 = [str(item.get("induce_cid", "")) for item in s1_ranked] + s1_file
    prediction = recent_commits(Path(subject["repo"]), s2) if can_determine else []
    if not prediction:
        prediction = recent_commits(Path(subject["repo"]), s1)
    return prediction, log_path


def parse_szz_agent_prediction(
    runtime_root: Path, stage1_path: Path, stage2_path: Path | None
) -> tuple[list[str], Path]:
    selected_path = stage2_path or stage1_path
    value = load_json(selected_path)
    if not isinstance(value, dict) or not isinstance(value.get("results"), list):
        raise BaselineError("SZZ-Agent result file is malformed")
    rows = value["results"]
    if len(rows) != 1 or not isinstance(rows[0], dict):
        raise BaselineError("SZZ-Agent result does not contain exactly one entry")
    if stage2_path:
        prediction = rows[0].get("predicted_bics", [])
    else:
        chosen = rows[0].get("llm_selected_commit")
        prediction = [chosen] if chosen else []
    if not isinstance(prediction, list):
        raise BaselineError("SZZ-Agent prediction field is malformed")
    return [str(item) for item in prediction if item], selected_path


def parse_simple_szz_agent_prediction(
    runtime_root: Path,
) -> tuple[list[str], Path, dict[str, object]]:
    selected_path = newest_file(
        runtime_root / "simple-szz-agent/results", "simple_szz_agent_*.json"
    )
    if selected_path is None:
        raise BaselineError("Simple-SZZ-Agent result file is missing")
    value = load_json(selected_path)
    if not isinstance(value, dict):
        raise BaselineError("Simple-SZZ-Agent result file is malformed")
    rows = value.get("results")
    details = value.get("details")
    if (
        not isinstance(rows, list)
        or len(rows) != 1
        or not isinstance(rows[0], dict)
        or not isinstance(details, list)
        or len(details) != 1
        or not isinstance(details[0], dict)
    ):
        raise BaselineError("Simple-SZZ-Agent result does not contain exactly one entry")
    prediction = rows[0].get("predicted_bics", [])
    if not isinstance(prediction, list):
        raise BaselineError("Simple-SZZ-Agent prediction field is malformed")
    detail = details[0]
    candidate_count = detail.get("total_candidates")
    gt_in_candidates = detail.get("gt_in_candidates")
    if not isinstance(candidate_count, int) or candidate_count < 0:
        raise BaselineError("Simple-SZZ-Agent candidate count is malformed")
    if not isinstance(gt_in_candidates, bool):
        raise BaselineError("Simple-SZZ-Agent candidate coverage flag is malformed")
    flow = {
        "candidate_count": candidate_count,
        "ground_truth_in_candidates": gt_in_candidates,
        "oracle_coverage_early_stop": (
            not gt_in_candidates
            and detail.get("error")
            == "Early stop: ground truth BIC not in candidates"
        ),
        "selected_index": detail.get("selected_index"),
        "confidence": detail.get("confidence"),
        "upstream_error": detail.get("error"),
        "candidate_scope": "histories_of_fix_touched_analyzable_files",
        "candidate_representation": "chronological_pre_materialized_diff_files",
    }
    return [str(item) for item in prediction if item], selected_path, flow


def szz_stage2_required(stage1_path: Path) -> bool:
    """Mirror upstream ``filter_entries_for_stage2`` for a one-entry run."""
    value = load_json(stage1_path)
    if not isinstance(value, dict) or not isinstance(value.get("results"), list):
        raise BaselineError("SZZ-Agent stage 1 result file is malformed")
    rows = value["results"]
    if len(rows) != 1 or not isinstance(rows[0], dict):
        raise BaselineError("SZZ-Agent stage 1 result does not contain exactly one entry")
    row = rows[0]
    candidates = row.get("szz_candidates", [])
    if not isinstance(candidates, list):
        raise BaselineError("SZZ-Agent stage 1 candidates are malformed")
    return not candidates or bool(row.get("llm_abstained")) or not bool(
        row.get("llm_selected_commit")
    )


def load_audit(path: Path, *, required: bool) -> dict[str, object]:
    if not path.is_file():
        if required:
            raise BaselineError(f"model invocation audit is missing: {path}")
        return {"invocations": [], "reported_cost_usd": "0"}
    value = load_json(path)
    if not isinstance(value, dict) or not isinstance(value.get("invocations"), list):
        raise BaselineError("model invocation audit is malformed")
    if any(
        not isinstance(row, dict) or row.get("state") != "completed"
        for row in value["invocations"]
    ):
        raise BaselineError("one or more model invocations failed validation")
    return value


def execute_subject(args: argparse.Namespace) -> dict[str, object]:
    if args.run_dir is None:
        raise BaselineError("--execute requires --run-dir")
    run_dir = args.run_dir.expanduser().resolve()
    if run_dir.exists():
        raise BaselineError(f"refusing to replace existing run directory: {run_dir}")
    cap = parse_positive_decimal(args.per_run_cap_usd, "--per-run-cap-usd")
    if cap is None:
        raise BaselineError("--execute requires --per-run-cap-usd")
    if args.acknowledge_resource_use != RESOURCE_ACKNOWLEDGEMENT:
        raise BaselineError(
            "--execute requires --acknowledge-resource-use "
            + RESOURCE_ACKNOWLEDGEMENT
        )
    if args.model != MODEL:
        raise BaselineError(f"only the frozen model {MODEL} is permitted")
    if args.test_stub and os.environ.get("LLM_BASELINE_ALLOW_TEST_STUB") != "1":
        raise BaselineError("--test-stub is restricted to the fixture-test environment")
    if not args.test_stub and args.test_stub_stage1_outcome != "select":
        raise BaselineError("--test-stub-stage1-outcome requires --test-stub")
    if not args.test_stub and args.baseline == "llm4szz":
        if args.acknowledge_api_billing != API_BILLING_ACKNOWLEDGEMENT:
            raise BaselineError(
                "LLM4SZZ requires --acknowledge-api-billing "
                + API_BILLING_ACKNOWLEDGEMENT
            )
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise BaselineError("LLM4SZZ execution requires ANTHROPIC_API_KEY")
    if not args.test_stub and args.baseline in SUBSCRIPTION_BASELINES:
        if args.confirm_usage_credits_disabled != USAGE_CREDITS_ACKNOWLEDGEMENT:
            raise BaselineError(
                "Claude Code baseline requires --confirm-usage-credits-disabled "
                + USAGE_CREDITS_ACKNOWLEDGEMENT
            )

    subject = load_subject(args.prompt_metadata, args.sample_id)
    sources = validate_source_manifest(args.source_manifest)
    runtime_python = inspect_runtime_python(args.python_bin, args.baseline)
    claude = None
    if args.baseline in SUBSCRIPTION_BASELINES and not args.test_stub:
        claude = inspect_subscription_claude(args.claude_bin)

    run_dir.mkdir(parents=True, exist_ok=False)
    runtime_root = run_dir / "runtime"
    dataset_path = prepare_runtime_input(runtime_root, subject)
    audit_path = run_dir / "model-invocations.json"
    manifest_path = run_dir / "run.json"
    # A valid upstream method path can terminate without an LLM call.  For
    # example, SZZ-Agent may find no Stage 1 candidates and then be unable to
    # materialize a Stage 2 analysis file for the selected history position.
    # The frozen upstream records an empty prediction and exits successfully;
    # preserve that scientific outcome instead of misclassifying the missing
    # invocation as an adapter failure.
    refresh_invocation_audit(audit_path, load_invocation_audit(audit_path))
    manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "claude-szz-llm-baseline-subject-run",
        "state": "running",
        "started_at": utc_now(),
        "baseline": args.baseline,
        "sample_id": subject["sample_id"],
        "model": args.model,
        "model_policy": "canonical_fixed_snapshot",
        "test_stub": args.test_stub,
        "scientific_result": not args.test_stub,
        "per_run_cap_usd": str(cap),
        "source_provenance": sources,
        "runtime_python": runtime_python,
        "claude_code": claude,
        "subject": {
            "repository": subject["repository"],
            "metadata_path": subject["metadata_path"],
            "metadata_sha256": subject["metadata_sha256"],
            "subject_repository_path": str(subject["repo"]),
            "synthetic_fix_hash": subject["synthetic_fix"],
            "repository_preflight": subject["snapshot"],
        },
        "dataset_path": str(dataset_path),
        "dataset_sha256": sha256_file(dataset_path),
    }
    write_json(manifest_path, manifest)

    env = sanitized_environment(keep_api_key=args.baseline == "llm4szz")
    env.update(
        {
            "LLM_BASELINE_RUN_DIR": str(run_dir),
            "LLM_BASELINE_AUDIT_PATH": str(audit_path),
            "LLM_BASELINE_PER_RUN_CAP_USD": str(cap),
            "LLM_BASELINE_REAL_CLAUDE_BIN": str(Path(args.claude_bin).expanduser()),
            "LLM_BASELINE_TEST_STUB": "1" if args.test_stub else "0",
            "LLM_BASELINE_STUB_STAGE1_OUTCOME": args.test_stub_stage1_outcome,
        }
    )
    process_records: list[dict[str, object]] = []
    script = Path(__file__).resolve()
    try:
        if args.baseline == "llm4szz":
            command = [
                str(args.python_bin.expanduser().absolute()),
                str(script),
                "_internal-llm4szz",
                "--source",
                str(sources["llm4szz_adapter_path"]),
                "--runtime-root",
                str(runtime_root),
                "--model",
                MODEL,
            ]
            if args.test_stub:
                command.append("--stub")
            record = execute_process(
                command,
                env=env,
                cwd=run_dir,
                stdout_path=run_dir / "llm4szz.stdout.log",
                stderr_path=run_dir / "llm4szz.stderr.log",
                timeout_seconds=args.timeout_seconds,
            )
            process_records.append(record)
            if record["exit_code"] != 0 or record["timed_out"]:
                raise BaselineError("LLM4SZZ runtime failed")
            predictions, raw_result = parse_llm4szz_prediction(runtime_root, subject)
            audit = load_audit(audit_path, required=not args.test_stub)
        elif args.baseline == "szz-agent":
            agent_source = Path(str(sources["szz_agent_path"]))
            stage1_command = [
                str(args.python_bin.expanduser().absolute()),
                str(script),
                "_internal-szz-stage",
                "--stage",
                "1",
                "--source",
                str(agent_source),
                "--runtime-root",
                str(runtime_root),
                "--dataset",
                str(dataset_path),
                "--model",
                MODEL,
            ]
            if args.test_stub:
                stage1_command.append("--stub")
            stage1_record = execute_process(
                stage1_command,
                env=env,
                cwd=run_dir,
                stdout_path=run_dir / "szz-agent-stage1.stdout.log",
                stderr_path=run_dir / "szz-agent-stage1.stderr.log",
                timeout_seconds=args.timeout_seconds,
            )
            process_records.append(stage1_record)
            if stage1_record["exit_code"] != 0 or stage1_record["timed_out"]:
                raise BaselineError("SZZ-Agent stage 1 failed")
            stage1_path = newest_file(runtime_root / "szz-agent/results", "szz_agent_stage_01_*.json")
            if stage1_path is None:
                raise BaselineError("SZZ-Agent stage 1 result is missing")

            needs_stage2 = szz_stage2_required(stage1_path)
            stage2_path = None
            if needs_stage2:
                stage2_command = [
                    str(args.python_bin.expanduser().absolute()),
                    str(script),
                    "_internal-szz-stage",
                    "--stage",
                    "2",
                    "--source",
                    str(agent_source),
                    "--runtime-root",
                    str(runtime_root),
                    "--dataset",
                    str(stage1_path),
                    "--model",
                    MODEL,
                ]
                if args.test_stub:
                    stage2_command.append("--stub")
                stage2_record = execute_process(
                    stage2_command,
                    env=env,
                    cwd=run_dir,
                    stdout_path=run_dir / "szz-agent-stage2.stdout.log",
                    stderr_path=run_dir / "szz-agent-stage2.stderr.log",
                    timeout_seconds=args.timeout_seconds,
                )
                process_records.append(stage2_record)
                if stage2_record["exit_code"] != 0 or stage2_record["timed_out"]:
                    raise BaselineError("SZZ-Agent stage 2 failed")
                stage2_path = newest_file(
                    runtime_root / "szz-agent/results", "szz_agent_stage_02_*.json"
                )
            predictions, raw_result = parse_szz_agent_prediction(
                runtime_root, stage1_path, stage2_path
            )
            audit = load_audit(audit_path, required=not args.test_stub)
        else:
            agent_source = Path(str(sources["szz_agent_path"]))
            command = [
                str(args.python_bin.expanduser().absolute()),
                str(script),
                "_internal-simple-szz-agent",
                "--source",
                str(agent_source),
                "--runtime-root",
                str(runtime_root),
                "--dataset",
                str(dataset_path),
                "--model",
                MODEL,
            ]
            if args.test_stub:
                command.append("--stub")
            record = execute_process(
                command,
                env=env,
                cwd=run_dir,
                stdout_path=run_dir / "simple-szz-agent.stdout.log",
                stderr_path=run_dir / "simple-szz-agent.stderr.log",
                timeout_seconds=args.timeout_seconds,
            )
            process_records.append(record)
            if record["exit_code"] != 0 or record["timed_out"]:
                raise BaselineError("Simple-SZZ-Agent runtime failed")
            predictions, raw_result, simple_flow = parse_simple_szz_agent_prediction(
                runtime_root
            )
            audit = load_audit(audit_path, required=not args.test_stub)

        postflight = repository_snapshot(
            Path(subject["repo"]), str(subject["synthetic_fix"]), str(subject["source_fix"])
        )
        if not all(value for key, value in postflight.items() if key != "head"):
            raise BaselineError("subject repository changed during baseline execution")
        manifest.update(
            {
                "state": "completed_stub" if args.test_stub else "completed",
                "finished_at": utc_now(),
                "processes": process_records,
                "prediction": {
                    "predicted_bics": predictions,
                    "raw_result_path": str(raw_result),
                    "raw_result_sha256": sha256_file(raw_result),
                },
                "model_invocations": audit,
                "reported_cost_usd": str(audit.get("reported_cost_usd", "0")),
                "postflight": postflight,
            }
        )
        if args.baseline == "szz-agent":
            manifest["szz_agent_flow"] = {
                "stage2_required": needs_stage2,
                "stage2_executed": needs_stage2,
                "stage_decision_policy": "upstream_filter_entries_for_stage2",
                "result_write_mode": SZZ_RESULT_WRITE_MODE,
            }
        elif args.baseline == "simple-szz-agent":
            manifest["simple_szz_agent_flow"] = {
                **simple_flow,
                "model_invocations": len(audit.get("invocations", [])),
                "oracle_coverage_gate": "frozen_upstream_early_stop_before_agent_call",
                "result_write_mode": SZZ_RESULT_WRITE_MODE,
            }
        write_json(manifest_path, manifest)
        return manifest
    except BaseException as exc:
        failed_audit = load_invocation_audit(audit_path)
        unreported = int(failed_audit.get("unreported_invocations", 0) or 0)
        manifest.update(
            {
                "state": "failed",
                "finished_at": utc_now(),
                "processes": process_records,
                "model_invocations": failed_audit,
                "reported_cost_usd": (
                    None
                    if unreported
                    else str(failed_audit.get("reported_cost_usd", "0"))
                ),
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        write_json(manifest_path, manifest)
        raise


def normal_main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", choices=BASELINES, required=True)
    parser.add_argument("--sample-id")
    parser.add_argument("--prompt-metadata", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--python-bin", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--per-run-cap-usd")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--acknowledge-resource-use")
    parser.add_argument("--acknowledge-api-billing")
    parser.add_argument("--confirm-usage-credits-disabled")
    parser.add_argument("--test-stub", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--test-stub-stage1-outcome",
        choices=("select", "abstain"),
        default="select",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)
    try:
        if args.timeout_seconds <= 0:
            raise BaselineError("--timeout-seconds must be positive")
        if not args.execute:
            if any(
                [
                    args.run_dir,
                    args.acknowledge_resource_use,
                    args.acknowledge_api_billing,
                    args.confirm_usage_credits_disabled,
                    args.test_stub,
                    args.test_stub_stage1_outcome != "select",
                ]
            ):
                raise BaselineError("execution-only flags require --execute")
            subject = load_subject(args.prompt_metadata, args.sample_id)
            sources = validate_source_manifest(args.source_manifest)
            runtime = inspect_runtime_python(args.python_bin, args.baseline)
            claude = (
                inspect_subscription_claude(args.claude_bin)
                if args.baseline in SUBSCRIPTION_BASELINES
                else None
            )
            print(
                json.dumps(
                    public_preflight(
                        baseline=args.baseline,
                        subject=subject,
                        sources=sources,
                        runtime=runtime,
                        claude=claude,
                    ),
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        result = execute_subject(args)
        print(
            json.dumps(
                {
                    "state": result["state"],
                    "baseline": result["baseline"],
                    "sample_id": result["sample_id"],
                    "run_manifest": str(args.run_dir.expanduser().resolve() / "run.json"),
                    "reported_cost_usd": result["reported_cost_usd"],
                },
                indent=2,
            )
        )
        return 0
    except (BaselineError, OSError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def load_invocation_audit(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {
            "schema_version": 1,
            "kind": "claude-szz-llm-baseline-model-invocations",
            "invocations": [],
            "reported_cost_usd": "0",
        }
    value = load_json(path)
    if not isinstance(value, dict) or not isinstance(value.get("invocations"), list):
        raise BaselineError("invocation audit is malformed")
    return value


def save_invocation(
    audit_path: Path, audit: dict[str, object], invocation: dict[str, object]
) -> None:
    rows = audit["invocations"]
    assert isinstance(rows, list)
    rows.append(invocation)
    refresh_invocation_audit(audit_path, audit)


def refresh_invocation_audit(audit_path: Path, audit: dict[str, object]) -> None:
    rows = audit["invocations"]
    assert isinstance(rows, list)
    costs: list[Decimal] = []
    unreported = 0
    for row in rows:
        if not isinstance(row, dict):
            unreported += 1
            continue
        try:
            value = Decimal(str(row.get("reported_cost_usd")))
        except InvalidOperation:
            unreported += 1
            continue
        if value.is_finite() and value >= 0:
            costs.append(value)
        else:
            unreported += 1
    audit["reported_cost_usd"] = str(sum(costs, Decimal("0")))
    audit["unreported_invocations"] = unreported
    usage = {field: 0 for field in TOKEN_USAGE_FIELDS}
    tool_counts: dict[str, int] = {}
    successful_model_results = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_usage = row.get("usage")
        if isinstance(row_usage, dict):
            for field in TOKEN_USAGE_FIELDS:
                value = row_usage.get(field, 0)
                if isinstance(value, int) and value >= 0:
                    usage[field] += value
        row_counts = row.get("tool_use_counts")
        if isinstance(row_counts, dict):
            for name, value in row_counts.items():
                if isinstance(name, str) and isinstance(value, int) and value >= 0:
                    tool_counts[name] = tool_counts.get(name, 0) + value
        if row.get("model_invoked") is True and row.get("model_result_valid") is True:
            successful_model_results += 1
    audit["usage"] = usage
    audit["tool_use_counts"] = dict(sorted(tool_counts.items()))
    audit["successful_model_result_events"] = successful_model_results
    write_json(audit_path, audit)


def llm4szz_stub_reply(messages: list[dict[str, str]]) -> str:
    prompt = "\n".join(str(row.get("content", "")) for row in messages)
    if "file name that is most likely" in prompt:
        match = re.search(r"diff --git a/(\S+) b/", prompt)
        filename = match.group(1) if match else "Unknown.java"
        return f"Root cause: fixture response\nfile:{filename}"
    if "Please output the result" in prompt and "Result:" in prompt:
        return "Reason: fixture response\nResult: no"
    if "Ranked Code statements:" in prompt:
        return "Ranked Code statements:\n"
    if "Code statements:" in prompt:
        return "Code statements:\n"
    return (
        "The code statements that lead to the bug are:\n"
        "Reason: fixture response\n"
        "The code statements that fix the bug are:\n"
        "Reason: fixture response"
    )


def internal_llm4szz(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--stub", action="store_true")
    args = parser.parse_args(argv)
    source = args.source.expanduser().resolve()
    runtime_root = args.runtime_root.expanduser().resolve()
    audit_path = Path(os.environ["LLM_BASELINE_AUDIT_PATH"])
    cap = Decimal(os.environ["LLM_BASELINE_PER_RUN_CAP_USD"])
    dataset_source = runtime_root / "dataset.json"
    work = runtime_root / "llm4szz"
    dataset_dir = work / "dataset"
    save_logs = work / "save_logs"
    tmp_dir = work / "tmp_dir"
    dataset_dir.mkdir(parents=True, exist_ok=False)
    save_logs.mkdir(parents=True, exist_ok=False)
    tmp_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(dataset_source, dataset_dir / "final_all_dataset.json")

    sys.path.insert(0, str(source))
    # The upstream adapter imports these optional local-model packages even
    # though pipeline=None never uses them in the selected API condition.
    sys.modules.setdefault("torch", types.ModuleType("torch"))
    sys.modules.setdefault("transformers", types.ModuleType("transformers"))
    constants = importlib.import_module("constants")
    constants.CWD = str(work)
    constants.REPOS_DIR = str(runtime_root / "repos")
    constants.DATASET_DIR = str(dataset_dir)
    constants.SAVE_LOG_DIR = str(save_logs)
    constants.TMP_DIR = str(tmp_dir)
    constants.TREE_SITTER_DIR = str(source / "build")
    constants.NUM_ITERATIONS = 1

    upstream_llm = importlib.import_module("llm")

    class AuditedClient(upstream_llm.Client):
        def __init__(self, model: str | None = None, reasoning_level: str | None = None):
            super().__init__(model=args.model, reasoning_level=reasoning_level)
            self.model = args.model

        def call_llm(self, all_msgs, log_msgs, pipeline=None, openai_key=None):
            self.call_cnt += 1
            if args.stub:
                return llm4szz_stub_reply(all_msgs)
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise BaselineError("ANTHROPIC_API_KEY is missing")
            audit = load_invocation_audit(audit_path)
            spent = Decimal(str(audit.get("reported_cost_usd", "0")))
            serialized = json.dumps(all_msgs, ensure_ascii=False).encode("utf-8")
            conservative_input_tokens = len(serialized) + 1024
            worst_case = (
                Decimal(conservative_input_tokens) * SONNET5_INPUT_USD_PER_MILLION
                + Decimal(LLM4SZZ_MAX_OUTPUT_TOKENS) * SONNET5_OUTPUT_USD_PER_MILLION
            ) / Decimal("1000000")
            if spent + worst_case > cap:
                raise BaselineError(
                    "LLM4SZZ request refused because its conservative worst-case "
                    "would exceed the registered per-run cap"
                )
            import anthropic

            system = None
            messages = []
            for row in all_msgs:
                if row.get("role") == "system":
                    system = row.get("content")
                else:
                    messages.append({"role": row["role"], "content": row["content"]})
            kwargs = {
                "model": args.model,
                "max_tokens": LLM4SZZ_MAX_OUTPUT_TOKENS,
                "messages": messages,
            }
            if system:
                kwargs["system"] = system
            invocation = {
                "state": "running",
                "started_at": utc_now(),
                "model_invoked": True,
                "model": args.model,
                "interface": "anthropic_messages_api",
                "temperature_sent": False,
                "max_output_tokens": LLM4SZZ_MAX_OUTPUT_TOKENS,
                "conservative_pre_request_cost_upper_bound_usd": str(worst_case),
                "reported_cost_usd": None,
            }
            save_invocation(audit_path, audit, invocation)
            started = time.monotonic()
            response = anthropic.Anthropic(api_key=api_key).messages.create(**kwargs)
            usage = response.usage
            input_tokens = int(getattr(usage, "input_tokens", 0))
            output_tokens = int(getattr(usage, "output_tokens", 0))
            cost = (
                Decimal(input_tokens) * SONNET5_INPUT_USD_PER_MILLION
                + Decimal(output_tokens) * SONNET5_OUTPUT_USD_PER_MILLION
            ) / Decimal("1000000")
            invocation.update({
                "state": "completed",
                "duration_seconds": time.monotonic() - started,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_creation_input_tokens": int(
                    getattr(usage, "cache_creation_input_tokens", 0) or 0
                ),
                "cache_read_input_tokens": int(
                    getattr(usage, "cache_read_input_tokens", 0) or 0
                ),
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_creation_input_tokens": int(
                        getattr(usage, "cache_creation_input_tokens", 0) or 0
                    ),
                    "cache_read_input_tokens": int(
                        getattr(usage, "cache_read_input_tokens", 0) or 0
                    ),
                    "thinking_tokens": 0,
                },
                "model_result_valid": True,
                "tool_use_counts": {},
                "reported_cost_usd": str(cost),
                "pricing": {
                    "input_usd_per_million": str(SONNET5_INPUT_USD_PER_MILLION),
                    "output_usd_per_million": str(SONNET5_OUTPUT_USD_PER_MILLION),
                },
                "response_id": getattr(response, "id", None),
                "stop_reason": getattr(response, "stop_reason", None),
            })
            refresh_invocation_audit(audit_path, audit)
            self.token_cost += input_tokens + output_tokens
            return "".join(
                block.text for block in response.content if hasattr(block, "text")
            )

    upstream_llm.Client = AuditedClient
    os.environ["LLM4SZZ_MODEL"] = args.model
    importlib.import_module("llm4szz")
    return 0


def build_szz_agent_command(prompt: str, *, stub: bool) -> tuple[list[str], dict[str, str], int]:
    # Upstream Simple-SZZ-Agent inserts its own ``--output-format stream-json
    # --verbose`` arguments immediately before the final prompt element.  Keep
    # the prompt positional so that insertion cannot split an option/value pair.
    command = [sys.executable, str(Path(__file__).resolve()), "_internal-szz-shim"]
    if stub:
        command.append("--stub")
    command.append(prompt)
    return command, os.environ.copy(), 600


def internal_szz_stage(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("1", "2"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--stub", action="store_true")
    args = parser.parse_args(argv)
    os.environ["LLM_BASELINE_SZZ_STAGE"] = args.stage
    os.environ["LLM_BASELINE_AGENT_VARIANT"] = "szz-agent"
    source = args.source.expanduser().resolve()
    runtime_root = args.runtime_root.expanduser().resolve()
    work = runtime_root / "szz-agent"
    work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(source / "src"))
    name = "szz_agent_stage_01" if args.stage == "1" else "szz_agent_stage_02"
    module = importlib.import_module(name)
    module.REPOS_DIR = runtime_root / "repos"
    module.TEMP_DIR = work / f"temp-stage-{args.stage}"
    module.RESULTS_DIR = work / "results"
    module.LOGS_DIR = work / "logs"
    module.AGENT_LOGS_DIR = work / "agent-logs"
    module.MAX_RETRIES = 1
    module.RETRY_DELAY = 0
    module.CLAUDE_TIMEOUT = 600
    module.verify_agent_cli = lambda agent: True
    module.build_agent_command = lambda agent, model, prompt, base_url=None, api_key="local-llm": build_szz_agent_command(
        prompt, stub=args.stub
    )
    if args.stage == "1":
        stage_argv = [name, "--sample-file", str(args.dataset), "--model", args.model]
    else:
        stage_argv = [name, "--dataset", str(args.dataset), "--model", args.model]
    original = sys.argv
    try:
        sys.argv = stage_argv
        module.main()
    finally:
        sys.argv = original
    return 0


def internal_simple_szz_agent(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--stub", action="store_true")
    args = parser.parse_args(argv)
    os.environ["LLM_BASELINE_SZZ_STAGE"] = "simple"
    os.environ["LLM_BASELINE_AGENT_VARIANT"] = "simple-szz-agent"
    source = args.source.expanduser().resolve()
    runtime_root = args.runtime_root.expanduser().resolve()
    work = runtime_root / "simple-szz-agent"
    work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(source / "src"))
    module = importlib.import_module("simple_szz_agent")
    module.REPOS_DIR = runtime_root / "repos"
    module.TEMP_DIR = work / "temp-analysis"
    module.RESULTS_DIR = work / "results"
    module.LOGS_DIR = work / "logs"
    module.AGENT_LOGS_DIR = work / "agent-logs"
    module.MAX_RETRIES = 1
    module.RETRY_DELAY = 0
    module.CLAUDE_TIMEOUT = 600
    module.verify_agent_cli = lambda agent: True
    module.build_agent_command = (
        lambda agent, model, prompt, base_url=None, api_key="local-llm", backend=None: build_szz_agent_command(
            prompt, stub=args.stub
        )
    )
    simple_argv = [
        "simple_szz_agent",
        "--dataset",
        str(args.dataset),
        "--limit",
        "1",
        "--model",
        args.model,
        "--agent",
        "claude-code",
        "--skip-cleanup",
    ]
    original = sys.argv
    try:
        sys.argv = simple_argv
        module.main()
    finally:
        sys.argv = original
    return 0


def directory_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in root.rglob("*")
        if path.is_file() and path.name != "result.txt"
    }


def szz_stub_result(work_dir: Path) -> str:
    instructions = (work_dir / "INSTRUCTIONS.md").read_text(encoding="utf-8")
    if "temp-stage-1" in work_dir.as_posix():
        if os.environ.get("LLM_BASELINE_STUB_STAGE1_OUTCOME", "select") == "abstain":
            return "SELECTED: NONE\n\nCONFIDENCE: LOW\n\nEXPLANATION:\nfixture stub"
        return "SELECTED: candidate_01\n\nCONFIDENCE: LOW\n\nEXPLANATION:\nfixture stub"
    if "VERDICT: BUG_PRESENT" in instructions:
        return "VERDICT: BUG_PRESENT\n\nCONFIDENCE: LOW\n\nEXPLANATION:\nfixture stub"
    if "possible that NONE" in instructions:
        return "SELECTED: NONE\n\nCONFIDENCE: LOW\n\nEXPLANATION:\nfixture stub"
    return "SELECTED: candidate_01\n\nCONFIDENCE: LOW\n\nEXPLANATION:\nfixture stub"


def _resolved_tool_path(work_dir: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = work_dir / candidate
    return candidate.resolve()


def parse_claude_transcript(transcript: Path, *, work_dir: Path) -> dict[str, object]:
    """Normalize result, token, and observable tool telemetry from stream JSONL."""
    result_event: dict[str, object] | None = None
    tool_uses: dict[str, dict[str, object]] = {}
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        if row.get("type") == "result":
            result_event = row
        if row.get("type") != "assistant":
            continue
        message = row.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            tool_id = block.get("id")
            name = block.get("name")
            tool_input = block.get("input")
            if not isinstance(tool_id, str) or not isinstance(name, str):
                continue
            if not isinstance(tool_input, dict):
                tool_input = {}
            normalized: dict[str, object] = {
                "tool_use_id": tool_id,
                "name": name,
                "input_sha256": sha256_bytes(
                    json.dumps(
                        tool_input, sort_keys=True, ensure_ascii=False
                    ).encode("utf-8")
                ),
            }
            raw_path = tool_input.get("file_path")
            path_field = "file_path"
            if not isinstance(raw_path, str) and name in {"Grep", "Glob"}:
                raw_path = tool_input.get("path")
                path_field = "path"
            if isinstance(raw_path, str):
                target = _resolved_tool_path(work_dir, raw_path)
                try:
                    relative = target.relative_to(work_dir.resolve()).as_posix()
                except ValueError:
                    relative = None
                normalized["path_field"] = path_field
                normalized["file_path"] = raw_path
                normalized["working_directory_relative_path"] = relative
                normalized["outside_working_directory"] = relative is None
            tool_content = tool_input.get("content")
            if isinstance(tool_content, str):
                content_bytes = tool_content.encode("utf-8")
                normalized["content_bytes"] = len(content_bytes)
                normalized["content_sha256"] = sha256_bytes(content_bytes)
            tool_uses[tool_id] = normalized

    cost = Decimal("0")
    valid_result = False
    usage = {field: 0 for field in TOKEN_USAGE_FIELDS}
    model_usage: object = None
    result_metadata: dict[str, object] = {}
    if result_event is not None:
        valid_result = not bool(result_event.get("is_error"))
        raw_cost = result_event.get("total_cost_usd")
        if raw_cost is not None:
            try:
                cost = Decimal(str(raw_cost))
            except InvalidOperation as exc:
                raise BaselineError("Claude result cost is malformed") from exc
        raw_usage = result_event.get("usage")
        if isinstance(raw_usage, dict):
            for field in TOKEN_USAGE_FIELDS[:-1]:
                value = raw_usage.get(field, 0)
                if isinstance(value, int) and value >= 0:
                    usage[field] = value
            details = raw_usage.get("output_tokens_details")
            if isinstance(details, dict):
                thinking = details.get("thinking_tokens", 0)
                if isinstance(thinking, int) and thinking >= 0:
                    usage["thinking_tokens"] = thinking
        model_usage = result_event.get("modelUsage")
        result_metadata = {
            "subtype": result_event.get("subtype"),
            "is_error": bool(result_event.get("is_error")),
            "duration_ms": result_event.get("duration_ms"),
            "duration_api_ms": result_event.get("duration_api_ms"),
            "num_turns": result_event.get("num_turns"),
        }
    counts: dict[str, int] = {}
    sequence = []
    for index, row in enumerate(tool_uses.values(), 1):
        row["sequence"] = index
        sequence.append(row)
        name = str(row["name"])
        counts[name] = counts.get(name, 0) + 1
    return {
        "reported_cost_usd": str(cost),
        "model_result_valid": valid_result,
        "result_event": result_metadata,
        "usage": usage,
        "model_usage": model_usage,
        "tool_uses": sequence,
        "tool_use_counts": dict(sorted(counts.items())),
    }


def parse_claude_cost(transcript: Path) -> tuple[Decimal, bool]:
    telemetry = parse_claude_transcript(transcript, work_dir=transcript.parent)
    return (
        Decimal(str(telemetry["reported_cost_usd"])),
        bool(telemetry["model_result_valid"]),
    )


def proxy_szz_result_from_transcript(
    transcript: Path, *, work_dir: Path, result_path: Path
) -> dict[str, object] | None:
    """Persist only a complete Write payload aimed exactly at result.txt."""
    selected: tuple[str, str, str] | None = None
    expected = result_path.resolve()
    if result_path.parent.resolve() != work_dir.resolve():
        raise BaselineError("SZZ-Agent result proxy target must be in the working directory")
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict) or row.get("type") != "assistant":
            continue
        message = row.get("message")
        blocks = message.get("content") if isinstance(message, dict) else None
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if block.get("name") != "Write" or not isinstance(block.get("input"), dict):
                continue
            tool_input = block["input"]
            raw_path = tool_input.get("file_path")
            content = tool_input.get("content")
            tool_id = block.get("id")
            if not all(isinstance(value, str) for value in (raw_path, content, tool_id)):
                continue
            if _resolved_tool_path(work_dir, raw_path) != expected:
                continue
            encoded = content.encode("utf-8")
            if not encoded or len(encoded) > MAX_PROXIED_RESULT_BYTES or "\x00" in content:
                continue
            selected = (tool_id, raw_path, content)
    if selected is None:
        return None
    tool_id, raw_path, content = selected
    encoded = content.encode("utf-8")
    write_atomic(result_path, encoded)
    return {
        "mode": SZZ_RESULT_WRITE_MODE,
        "source_tool_use_id": tool_id,
        "source_file_path": raw_path,
        "content_bytes": len(encoded),
        "content_sha256": sha256_bytes(encoded),
        "target_path": str(result_path),
    }


def build_szz_subscription_command(
    *,
    claude: dict[str, object],
    remaining: Decimal,
    settings_path: Path,
    mcp_path: Path,
    debug_path: Path,
    result_path: Path,
    variant: str = "szz-agent",
) -> list[str]:
    # Claude Code 2.1.232 --bare deliberately disables keychain/OAuth reads and
    # only accepts API-key auth. SZZ-Agent is a subscription condition, so use
    # the ordinary CLI while retaining the explicit tool, settings-source,
    # MCP, sandbox, memory, instruction, and session-persistence boundaries.
    # Claude Code 2.1.232 uses Edit(path) as the permission namespace for all
    # file-editing tools, including Write. The available tool remains Write;
    # Edit itself is not exposed by --tools.
    file_permission_rule = f"Edit({result_path})"
    simple = variant == "simple-szz-agent"
    read_tools = ["Read", "Grep", "Glob"] if simple else ["Read"]
    return [
        str(claude["executable"]),
        "--print",
        "--model",
        MODEL,
        "--effort",
        "high",
        "--max-budget-usd",
        str(remaining),
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-hook-events",
        "--include-partial-messages",
        "--tools",
        *read_tools,
        "Write",
        "--allowedTools",
        *read_tools,
        file_permission_rule,
        "--permission-mode",
        "dontAsk",
        "--no-session-persistence",
        "--setting-sources",
        "",
        "--settings",
        str(settings_path),
        "--strict-mcp-config",
        "--mcp-config",
        str(mcp_path),
        "--no-chrome",
        "--disable-slash-commands",
        "--append-system-prompt",
        SAFE_SIMPLE_AGENT_SYSTEM_PROMPT if simple else SAFE_AGENT_SYSTEM_PROMPT,
        "--debug-file",
        str(debug_path),
    ]


def build_szz_subscription_settings(
    *, work_dir: Path, result_path: Path, variant: str = "szz-agent"
) -> dict[str, object]:
    file_permission_rule = f"Edit({result_path})"
    simple = variant == "simple-szz-agent"
    read_tools = ["Read", "Grep", "Glob"] if simple else ["Read"]
    return {
        "autoMemoryEnabled": False,
        "disableAllHooks": True,
        "permissions": {
            "allow": [*read_tools, file_permission_rule],
            "ask": [],
            # A blanket Edit deny would also deny Write because file-editing
            # tools share the Edit(path) permission namespace.
            "deny": ["Bash", "WebFetch", "WebSearch", "Agent", "Skill"],
        },
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "filesystem": {"denyRead": ["/"], "allowRead": [str(work_dir)]},
            "network": {"allowedDomains": [], "deniedDomains": ["*"]},
        },
    }


def internal_szz_shim(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-format", choices=("stream-json",))
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--stub", action="store_true")
    parser.add_argument("prompt")
    args = parser.parse_args(argv)
    work_dir = Path.cwd().resolve()
    variant = os.environ.get("LLM_BASELINE_AGENT_VARIANT", "szz-agent")
    if variant not in SUBSCRIPTION_BASELINES:
        raise BaselineError(f"unsupported Claude Code baseline variant: {variant}")
    allowed_read_tools = (
        {"Read", "Grep", "Glob"}
        if variant == "simple-szz-agent"
        else {"Read"}
    )
    allowed_tools = {*allowed_read_tools, "Write"}
    audit_path = Path(os.environ["LLM_BASELINE_AUDIT_PATH"])
    cap = Decimal(os.environ["LLM_BASELINE_PER_RUN_CAP_USD"])
    audit = load_invocation_audit(audit_path)
    rows = audit["invocations"]
    assert isinstance(rows, list)
    sequence = len(rows) + 1
    invocation_dir = Path(os.environ["LLM_BASELINE_RUN_DIR"]) / "invocations" / f"{sequence:03d}"
    invocation_dir.mkdir(parents=True, exist_ok=False)
    before = directory_hashes(work_dir)
    result_path = work_dir / "result.txt"
    if args.stub:
        result_path.write_text(szz_stub_result(work_dir), encoding="utf-8")
        invocation = {
            "state": "completed",
            "mode": "fixture_stub",
            "model_invoked": False,
            "model": MODEL,
            "baseline": variant,
            "stage": os.environ.get("LLM_BASELINE_SZZ_STAGE"),
            "working_directory": str(work_dir),
            "prompt_sha256": sha256_bytes(args.prompt.encode()),
            "reported_cost_usd": "0",
            "result_sha256": sha256_file(result_path),
        }
        save_invocation(audit_path, audit, invocation)
        print(json.dumps({"fixture_stub": True}))
        return 0

    spent = Decimal(str(audit.get("reported_cost_usd", "0")))
    remaining = cap - spent
    if remaining <= 0:
        raise BaselineError("Claude Code baseline per-run reported-cost cap is exhausted")
    real_claude = os.environ.get("LLM_BASELINE_REAL_CLAUDE_BIN", "claude")
    claude = inspect_subscription_claude(real_claude)
    settings_path = invocation_dir / "settings.json"
    mcp_path = invocation_dir / "mcp.json"
    transcript_path = invocation_dir / "claude.stream.jsonl"
    stderr_path = invocation_dir / "claude.stderr.log"
    debug_path = invocation_dir / "claude.debug.log"
    settings = build_szz_subscription_settings(
        work_dir=work_dir, result_path=result_path, variant=variant
    )
    write_json(settings_path, settings)
    write_json(mcp_path, {"mcpServers": {}})
    command = build_szz_subscription_command(
        claude=claude,
        remaining=remaining,
        settings_path=settings_path,
        mcp_path=mcp_path,
        debug_path=debug_path,
        result_path=result_path,
        variant=variant,
    )
    invocation = {
        "state": "running",
        "mode": "claude_code_subscription",
        "model_invoked": True,
        "model": MODEL,
        "baseline": variant,
        "claude_code_version": claude["version"],
        "stage": os.environ.get("LLM_BASELINE_SZZ_STAGE"),
        "working_directory": str(work_dir),
        "prompt_sha256": sha256_bytes(args.prompt.encode()),
        "reported_cost_usd": None,
        "billing": "not_observable_subscription_run",
        "result_write_mode": SZZ_RESULT_WRITE_MODE,
    }
    save_invocation(audit_path, audit, invocation)
    started = time.monotonic()
    with transcript_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.run(
            command,
            input=args.prompt.encode(),
            stdout=stdout,
            stderr=stderr,
            cwd=work_dir,
            env=sanitized_environment(),
            timeout=600,
            check=False,
        )
    telemetry = parse_claude_transcript(transcript_path, work_dir=work_dir)
    cost = Decimal(str(telemetry["reported_cost_usd"]))
    valid_result = bool(telemetry["model_result_valid"])
    unexpected_tool_paths = [
        row["tool_use_id"]
        for row in telemetry["tool_uses"]
        if isinstance(row, dict) and row.get("outside_working_directory") is True
    ]
    unexpected_tools = [
        row["tool_use_id"]
        for row in telemetry["tool_uses"]
        if isinstance(row, dict) and row.get("name") not in allowed_tools
    ]
    after = directory_hashes(work_dir)
    result_proxy = None
    if (
        process.returncode == 0
        and valid_result
        and not result_path.exists()
        and before == after
        and not unexpected_tool_paths
        and not unexpected_tools
        and cost <= remaining
    ):
        result_proxy = proxy_szz_result_from_transcript(
            transcript_path, work_dir=work_dir, result_path=result_path
        )
    state = (
        "completed"
        if process.returncode == 0
        and valid_result
        and result_path.is_file()
        and before == after
        and not unexpected_tool_paths
        and not unexpected_tools
        and cost <= remaining
        else "failed"
    )
    invocation.update({
        "state": state,
        "duration_seconds": time.monotonic() - started,
        "exit_code": process.returncode,
        "reported_cost_usd": str(cost),
        "transcript_path": str(transcript_path),
        "transcript_sha256": sha256_file(transcript_path),
        "stderr_path": str(stderr_path),
        "stderr_sha256": sha256_file(stderr_path),
        "result_sha256": sha256_file(result_path) if result_path.is_file() else None,
        "result_proxy": result_proxy,
        "result_persistence": (
            "stream_proxy"
            if result_proxy is not None
            else "direct_write"
            if result_path.is_file()
            else "missing"
        ),
        "unexpected_file_changes": before != after,
        "outside_working_directory_tool_uses": unexpected_tool_paths,
        "unexpected_tools": unexpected_tools,
        "model_result_valid": telemetry["model_result_valid"],
        "result_event": telemetry["result_event"],
        "usage": telemetry["usage"],
        "model_usage": telemetry["model_usage"],
        "tool_uses": telemetry["tool_uses"],
        "tool_use_counts": telemetry["tool_use_counts"],
    })
    refresh_invocation_audit(audit_path, audit)
    sys.stdout.write(transcript_path.read_text(encoding="utf-8", errors="replace"))
    return 0 if state == "completed" else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "_internal-llm4szz":
        return internal_llm4szz(args[1:])
    if args and args[0] == "_internal-szz-stage":
        return internal_szz_stage(args[1:])
    if args and args[0] == "_internal-simple-szz-agent":
        return internal_simple_szz_agent(args[1:])
    if args and args[0] == "_internal-szz-shim":
        return internal_szz_shim(args[1:])
    return normal_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
