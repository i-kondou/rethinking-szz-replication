#!/usr/bin/env python3
"""Portable, opt-in Claude Code reruns. Default: print a plan, no Claude invocation."""

from __future__ import annotations

import argparse
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'preprocess'))
from common import (ROOT, DATA, DEFAULT_WORKSPACE, git, json_bytes, load, read_package,
    require, select_cases, sha, subject_path, validate_subject, within, write_new)

VENDOR = ROOT / "experiments/scripts/run_sanitized_subject.py"
VENDOR_SHA = "9c875055e5c41304ccc62a5aa7d262e0a970b9ff6637b7e3d816d1a00223d097"
ACK = "I_ACKNOWLEDGE_CLAUDE_RESOURCE_USE"
CREDITS_ACK = "I_CONFIRMED_USAGE_CREDITS_DISABLED"


def load_runner():
    require(sha(VENDOR.read_bytes()) == VENDOR_SHA, "Frozen runner checksum differs")
    spec = importlib.util.spec_from_file_location("frozen_subject_runner", VENDOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def settings_for(base, repo, workspace, results_root=None):
    settings = base(repo)
    # The historical runner denied home reads. Explicit denials also cover a
    # shared checkout or cache on an external volume, not just under home.
    protected = [ROOT, workspace]
    if results_root is not None:
        protected.append(results_root)
    settings["sandbox"]["filesystem"]["denyRead"] = ["~/", *sorted({str(p.resolve()) for p in protected})]
    settings["sandbox"]["filesystem"]["allowRead"] = [str(repo.resolve())]
    return settings


def validate_gate(args):
    require(args.replicates in (1, 2, 3), "--replicates must be 1, 2 or 3")
    if not args.execute:
        return
    require(args.acknowledge_resource_use == ACK, "Execution needs --acknowledge-resource-use " + ACK)
    require(args.confirm_usage_credits_disabled == CREDITS_ACK,
            "Manually disable account usage credits, then supply --confirm-usage-credits-disabled " + CREDITS_ACK)
    require(args.results_root is not None and not args.results_root.exists(),
            "--execute requires a NEW --results-root; existing runs are never overwritten")
    require(args.model is not None and args.max_budget_usd is not None,
            "--execute requires explicit --model and --max-budget-usd")


def save_readable_outputs(run_dir):
    """Project recorded completed messages; never infer unrecorded reasoning."""
    raw = (run_dir / "transcript.jsonl").read_bytes()
    events, terminal = [], None
    for number, line in enumerate(raw.splitlines(), 1):
        record = json.loads(line)
        if record.get("type") == "result":
            terminal = record
        if record.get("type") not in {"assistant", "user"}:
            continue
        content = record.get("message", {}).get("content", [])
        if not isinstance(content, list):
            content = [{"type": "text", "text": content}]
        for index, block in enumerate(content):
            events.append({"sequence": len(events) + 1, "source_line": number,
                           "source_content_index": index, "role": record["type"], "block": block})
    require(terminal is not None and isinstance(terminal.get("result"), str), "Missing final answer text")
    write_new(run_dir / "result.md", terminal["result"].encode("utf-8"))
    write_new(run_dir / "trajectory.json", json_bytes({"schema_version": 1,
        "raw_sha256": sha(raw), "events": events, "final_answer": terminal["result"],
        "note": "Recorded explanations and tool interactions only; missing private reasoning is not inferred."}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subset", choices=("all", "disagreement"))
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--case-sensitive-root", type=Path)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--results-root", type=Path)
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--model")
    parser.add_argument("--max-budget-usd")
    parser.add_argument("--validate-inputs", action="store_true", help="Deep-check prepared repositories without Claude")
    parser.add_argument("--check-runtime", action="store_true", help="Read CLI version/help/auth only; no model call")
    parser.add_argument("--allow-runtime-change", action="store_true", help="Explicitly allow a different CLI/model/budget; label it non-historical")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--message-free", action="store_true")
    parser.add_argument("--acknowledge-resource-use")
    parser.add_argument("--confirm-usage-credits-disabled")
    args = parser.parse_args()
    try:
        validate_gate(args)
        dataset, messages, manifest = read_package()
        cases = select_cases(dataset, args.subset, args.ids)
        historical = load(DATA / "historical-condition.json")
        runner = load_runner()
        args.model = args.model or historical["model"]
        args.max_budget_usd = args.max_budget_usd or historical["per_attempt_reported_cost_cap_usd"]
        budget = runner.parse_budget(args.max_budget_usd)
        require(budget is not None and budget.is_finite(), "Budget must be a finite positive number")
        require(args.model.startswith("claude-") and all(c.isalnum() or c == "-" for c in args.model),
                "Use a full Claude model ID")
        changes = []
        if args.model != historical["model"]:
            changes.append("model")
        if budget != Decimal(historical["per_attempt_reported_cost_cap_usd"]):
            changes.append("budget")
        require(not changes or args.allow_runtime_change, "Changed model/budget requires --allow-runtime-change")
        args.effort = historical["effort"]
        args.timeout_seconds = historical["claude_process_timeout_seconds"]
        workspace = args.workspace.resolve()
        results_root = args.results_root.resolve() if args.results_root else None
        paths = {c["id"]: subject_path(workspace, c, args.case_sensitive_root) for c in cases}
        validate = validate_subject
        if args.message_free:
            import remove_messages
            from copy import deepcopy
            cases = deepcopy(cases)
            def validate(repo, case, message):
                original = next(c for c in dataset['cases'] if c['id'] == case['id'])
                remove_messages.prepare(workspace, original, message)
            for case in cases:
                bundle = workspace / 'message_free' / case['id']
                record = load(bundle / 'metadata/check.json')
                case.update(synthetic_bfc=record['new_bfc'],
                            prompt_path=str(bundle / 'metadata/prompt.md'),
                            prompt_sha256=record['prompt_sha256'])
                paths[case['id']] = bundle / 'repo'
        for path in paths.values():
            require(not within(ROOT, path), "Shared analyst checkout cannot be the subject")
            if results_root:
                require(not within(results_root, path), "Results must be outside every subject repository")
        if results_root:
            require(not within(results_root, ROOT), "Store new private run logs outside the shared checkout")
        settings_base = runner.build_settings
        runner.build_settings = lambda repo: settings_for(settings_base, repo, workspace, results_root)
        runner.run_git = lambda repo, *a, check=True: git(repo, *a, check=check)
        plan = {"mode": "execute" if args.execute else "no-model-plan",
            "subset": args.subset, "case_ids": [c["id"] for c in cases],
            "replicates": args.replicates, "new_executions": len(cases) * args.replicates,
            "model": args.model, "effort": args.effort, "per_attempt_reported_cost_trigger_usd": str(budget),
            "sum_of_per_attempt_triggers_usd": str(len(cases) * args.replicates * budget),
            "cost_note": "Reported cost equivalent, not subscription charges or a strict aggregate billing cap",
            "timeout_seconds": args.timeout_seconds, "automatic_retries": False,
            "api_body_capture": False, "historical_harness_exact_reproduction": False,
            "runtime_changes": changes, "data_manifest_sha256": sha((DATA / 'manifest.json').read_bytes()),
            "message_free": args.message_free,
            "input_validation": "not requested", "sandbox_live_verified": False}
        if args.validate_inputs or args.execute:
            for case in cases:
                validate(paths[case["id"]], case, messages[case["id"]])
            plan["input_validation"] = "all selected subjects passed deep checks"
        env = runner.sanitized_environment()
        claude = None
        if args.check_runtime or args.execute:
            claude = runner.inspect_claude(args.claude_bin, env)
            if claude["version"] != historical["claude_code_version"]:
                changes.append("claude_code_version")
                require(args.allow_runtime_change, "Historical CLI is 2.1.232; a different version needs --allow-runtime-change")
            plan["runtime"] = claude
        print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
        if not args.execute:
            return 0
        require(sys.platform in {"darwin", "linux"}, "Execution is supported only on macOS/Linux with Claude sandbox support")
        results_root.mkdir(parents=True, exist_ok=False)
        runner.write_json(results_root / "plan.json", plan)
        completed = []
        for rep in range(1, args.replicates + 1):
            for case in cases:
                sid, repo = case["id"], paths[case["id"]]
                # Verify again immediately before each fresh session.
                validate(repo, case, messages[sid])
                prompt = (DATA / case["prompt_path"]).read_bytes()
                require(sha(prompt) == case['prompt_sha256'], 'Prompt checksum differs')
                subject = {"sample_id": sid, "repo": repo, "prompt": prompt.decode("utf-8"),
                    "prompt_sha256": sha(prompt), "synthetic_fix": case["synthetic_bfc"], "source_fix": case["bfc"],
                    "snapshot": runner.git_snapshot(repo, case["synthetic_bfc"], case["bfc"])}
                run_dir = results_root / sid / f"r{rep:02}"
                print(f"Starting {sid}:r{rep:02}; saving to {run_dir}", flush=True)
                try:
                    run = runner.execute_run(args=args, budget=budget, run_dir=run_dir,
                                             subject=subject, claude=claude, env=env)
                    validate(repo, case, messages[sid])
                    save_readable_outputs(run_dir)
                    completed.append({"id": sid, "replicate": rep, "state": "completed",
                                      "reported_cost_usd": run["transcript_validation"]["reported_cost_usd"]})
                except Exception as exc:
                    completed.append({"id": sid, "replicate": rep, "state": "failed-or-needs-review", "error": str(exc)})
                    runner.write_json(results_root / "batch.json", {"runs": completed, "stopped_on_failure": True})
                    raise  # Fail closed, no automatic quota retry or further spending.
                runner.write_json(results_root / "batch.json", {"runs": completed, "stopped_on_failure": False})
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
