#!/usr/bin/env python3
"""Final-v2 input validation and isolated Anthropic transport adaptation.

Never edits a frozen engine or upstream checkout. Derivations are guarded by
exact source hashes and captured in each attempt's provenance.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import types

from llm_baseline_common import BaselineError, load_json, load_subject, sha256_file

ROOT = Path(__file__).resolve().parents[1]
INPUT_SET = ROOT / "experiments/plans/bfc-message-neutralized-final-v2-input-set.json"
INPUT_SET_SHA256 = "3762ad6d71325811b675c1c7b61267e823a578b1b3d86e9f9c66ec8fe2c1a85a"
CONDITION = "EXP002-BFC-MESSAGE-NEUTRALIZED-FINAL-V2-ANTHROPIC-API-V1"
MODEL = "claude-sonnet-5"
BASE_URL = "https://api.anthropic.com/v1/"
RESOURCE_ACK = "I_ACKNOWLEDGE_FINAL_V2_API_BASELINE_RESOURCE_USE"
BILLING_ACK = "I_ACKNOWLEDGE_ANTHROPIC_API_BILLING"
SOURCE_HASHES = {
    "run_agentic_baseline_subject.py": "3be31e90f81d9e52424688ba18da22fefc5940025baf194e4a571669f961cfdb",
    "run_llm_baseline_subject.py": "08e84228e2d0d615884279a19524bab4cc08eaaf52eaabfd9458f02000a4b542",
    "llm_baseline_common.py": "7e0bd5f38cceb32f91095591280a545904ba6a046517022621f33cc1d26f35ef",
    "agentic_baseline_common.py": "c4cc923694c054d4e74162acb371f7be328b503eaf4a5c05d1cfc4dadaeef9ea",
}


def verified_file(path, expected):
    path = Path(path)
    if not path.is_file() or sha256_file(path) != expected:
        raise BaselineError(f"missing or changed frozen input: {path}")
    return path


def input_records():
    value = load_json(verified_file(INPUT_SET, INPUT_SET_SHA256))
    if value.get("condition_id") != "EXP002-BFC-MESSAGE-NEUTRALIZED-FINAL-V2":
        raise BaselineError("wrong input condition")
    review = load_json(verified_file(value["review_path"], value["review_sha256"]))
    verified_file(value["workbook_audit_path"], value["workbook_audit_sha256"])
    verified_file(review["source_workbook_path"], review["source_workbook_sha256"])
    rows = value["samples"]
    reviews = {str(r["sample_id"]): r for r in review["rows"]}
    ids = [str(r["sample_id"]) for r in rows]
    if len(ids) != 79 or len(set(ids)) != 79 or set(ids) != set(reviews):
        raise BaselineError("expected the exact 79 reviewed sample IDs")
    return value, reviews


def normalize(text):
    return "\n".join(line.rstrip(" \t") for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"))


def validated_subject(row, review):
    for key in ("prompt_metadata", "prompt", "subject_manifest"):
        verified_file(row[key], row[key + "_sha256"])
    subject = load_subject(Path(row["prompt_metadata"]), str(row["sample_id"]))
    if Path(subject["repo"]).resolve() != Path(row["subject_repository"]).resolve():
        raise BaselineError("subject repository differs from final-v2 input set")
    if subject["synthetic_fix"] != row["synthetic_fix_hash"]:
        raise BaselineError("synthetic BFC differs from final-v2 input set")
    import subprocess
    manifest = load_json(Path(row["subject_manifest"]))
    raw = subprocess.check_output(["git", "-C", str(subject["repo"]), "cat-file", "commit", subject["synthetic_fix"]])
    message = raw.split(b"\n\n", 1)[1].decode(manifest["message_rewrite"]["source_encoding"])
    if message.endswith("\n"):
        message = message[:-1]
    if normalize(message) != review["neutralized_message"]:
        raise BaselineError(f"HEAD message differs from reviewed Excel: {row['sample_id']}")
    subject["bfc_message"] = message
    return subject


def select_subject(sample_id):
    inputs, reviews = input_records()
    matches = [r for r in inputs["samples"] if str(r["sample_id"]) == sample_id]
    if len(matches) != 1:
        raise BaselineError(f"sample is not in the final-v2 cohort: {sample_id}")
    return validated_subject(matches[0], reviews[sample_id])


def safe_environment(*, keep_api_key=False):
    from llm_baseline_common import sanitized_environment
    env = sanitized_environment(keep_api_key=keep_api_key)
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
    if keep_api_key and os.environ.get("ANTHROPIC_WORKSPACE_ID"):
        env["ANTHROPIC_WORKSPACE_ID"] = os.environ["ANTHROPIC_WORKSPACE_ID"]
    for name in ("FINAL_V2_NEO4J_CONTAINER", "LLM_BASELINE_ALLOW_TEST_STUB"):
        if name in os.environ:
            env[name] = os.environ[name]
    return env


class LegacyUsageResult:
    """Expose the upstream usage() API without changing the agent's result.

    Pydantic AI 2.x returns RunUsage through a property. AgenticSZZ's pinned
    source still calls it as a method after reasoning has already completed.
    Keep this compatibility shim local to the derived runtime, not the SDK or
    the frozen upstream source. Usage limits run inside Agent.run unchanged.
    """

    def __init__(self, result):
        self._result = result

    def __getattr__(self, name):
        return getattr(self._result, name)

    def usage(self):
        value = self._result.usage
        return value() if callable(value) else value


def derive_engine(baseline):
    """Only endpoint/auth/telemetry changes; search and prompt logic unchanged."""
    for name, expected in SOURCE_HASHES.items():
        verified_file(ROOT / "scripts" / name, expected)
    llm4 = baseline == "llm4szz"
    name = "run_llm_baseline_subject.py" if llm4 else "run_agentic_baseline_subject.py"
    path = ROOT / "scripts" / name
    code = path.read_text()
    if llm4:
        # New condition only: the scheduled Sep-1 price rise was cancelled.
        code = code.replace('SONNET5_INPUT_USD_PER_MILLION = Decimal("3")', 'SONNET5_INPUT_USD_PER_MILLION = Decimal("2")')
        code = code.replace('SONNET5_OUTPUT_USD_PER_MILLION = Decimal("15")', 'SONNET5_OUTPUT_USD_PER_MILLION = Decimal("10")')
        code = code.replace('anthropic.Anthropic(api_key=api_key)', 'anthropic.Anthropic(api_key=api_key, base_url="https://api.anthropic.com", max_retries=0, default_headers=workspace_headers())')
    else:
        code = code.replace("OPENROUTER_API_KEY", "ANTHROPIC_API_KEY")
        code = code.replace("OpenRouter", "Anthropic")
        code = code.replace("separate_openrouter_billing", "separate_anthropic_billing")
        code = code.replace('container = f"claude-szz-agentic-szz-{os.getpid()}"', 'container = os.environ["FINAL_V2_NEO4J_CONTAINER"]')
        code = code.replace('api_key=os.environ["ANTHROPIC_API_KEY"],', 'api_key=os.environ["ANTHROPIC_API_KEY"], max_retries=0, default_headers=workspace_headers(),')
    if baseline == "agentic-szz":
        original = "return await original_agent_run(agent_self, *run_args, **run_kwargs)"
        if code.count(original) != 1:
            raise BaselineError("AgenticSZZ usage compatibility anchor changed")
        code = code.replace(original, "return LegacyUsageResult(await original_agent_run(agent_self, *run_args, **run_kwargs))")
    module = types.ModuleType("final_v2_" + baseline.replace("-", "_"))
    module.__file__ = str(path)
    module.LegacyUsageResult = LegacyUsageResult
    exec(compile(code, str(path), "exec"), module.__dict__)
    module.MODEL = MODEL
    module.BASE_URL = BASE_URL
    module.API_BILLING_ACKNOWLEDGEMENT = BILLING_ACK
    module.sanitized_environment = safe_environment
    module.sanitized_openrouter_environment = lambda: safe_environment(keep_api_key=True)
    module.workspace_headers = workspace_headers
    if llm4:
        # Internal subprocesses must re-enter this adaptation, not the old engine.
        module.__file__ = str(ROOT / "scripts/run_api_baseline_final_v2.py")
    return module, code


def workspace_headers():
    value = os.environ.get("ANTHROPIC_WORKSPACE_ID")
    return {"anthropic-workspace-id": value} if value else {}


def provenance(baseline, derived_code):
    return {
        "condition_id": CONDITION,
        "model": MODEL,
        "provider": "Anthropic",
        "interface": "messages" if baseline == "llm4szz" else "anthropic_official_openai_compatibility",
        "base_url": BASE_URL,
        "credential": "ANTHROPIC_API_KEY",
        "input_set_path": str(INPUT_SET),
        "input_set_sha256": sha256_file(INPUT_SET),
        "source_engine_sha256": SOURCE_HASHES,
        "derived_engine_sha256": hashlib.sha256(derived_code.encode()).hexdigest(),
        "adapter_sha256": sha256_file(Path(__file__)),
        "runner_sha256": sha256_file(ROOT / "scripts/run_api_baseline_final_v2.py"),
        "runtime_compatibility": "pydantic_usage_property_v1" if baseline == "agentic-szz" else None,
        "price_snapshot": {"date": "2026-09-05", "input_usd_per_million": "2", "output_usd_per_million": "10", "url": "https://platform.claude.com/docs/en/about-claude/pricing"},
        "limitations": [
            "Matched-backbone adaptation, not original-model replication.",
            "AgentSZZ/AgenticSZZ compatibility API hoists system messages and ignores strict tool schemas; no prompt caching or reasoning_effort control. LLM4SZZ uses native Messages.",
            "Token-derived cost is telemetry, not an invoice or hard billing cap.",
            "No batch or automatic case retries; SDK retries disabled, method-internal retries preserved. A paid canary is required before full experiments.",
        ],
    }
