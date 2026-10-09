"""Result-aware, fail-closed access audit for the new DEC017 condition only.

This does not grant filesystem permissions or change historical outcomes.
The legacy validator is retained; narrowly verified Read events receive an
explicit exception with their original outside-path classification preserved.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from llm_baseline_common import BaselineError, sha256_bytes, write_atomic


POLICY_ID = "dec017-result-aware-read-v1"
OUTER_TIMEOUT_SECONDS = {"claudeszz": None, "simple-szz-agent": None, "szz-agent": 3600}
INNER_TIMEOUT_SECONDS = {"claudeszz": 600, "simple-szz-agent": 600, "szz-agent": 600}
PER_RUN_CAP_USD = "5"


def resource_policy(method: str) -> dict[str, Any]:
    return {
        "outer_timeout_seconds": OUTER_TIMEOUT_SECONDS[method],
        "claude_invocation_timeout_seconds": INNER_TIMEOUT_SECONDS[method],
        "per_run_cap_usd": PER_RUN_CAP_USD,
        "cumulative_cap_usd": None,
        "cost_is_reported_equivalent_not_actual_billing": True,
    }


def _text(block: dict) -> str | None:
    content = block.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list) and all(
        isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
        for b in content
    ):
        return "\n".join(b["text"] for b in content)
    return None


def _target(work: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else work / path).resolve()


def _not_found(result: dict, work: Path) -> bool:
    # Full matching prevents a successful result, partial data plus an error,
    # permission denial, or an assistant's claim from becoming an exception.
    return result.get("is_error") is True and _text(result) in {
        "File does not exist.",
        f"File does not exist. Note: your current working directory is {work}.",
    }


def _saved_result(
    *, target: Path, work: Path, attempt: Path, projects: Path,
    session: str | None, init_cwd: str | None, uses: dict, results: dict,
) -> dict[str, Any] | None:
    """Bind a spill file to the current attempt and a prior completed tool."""
    try:
        parts = target.relative_to(projects.resolve()).parts
    except ValueError:
        return None
    if len(parts) != 4:
        return None
    project, path_session, directory, filename = parts
    prefix = re.sub(r"[^A-Za-z0-9]", "-", str(attempt.resolve()))
    if (not session or path_session != session or directory != "tool-results"
            or not project.startswith(prefix + "-") or init_cwd != str(work)
            or not filename.endswith(".txt")):
        return None
    origin_id = filename[:-4]
    origin = uses.get(origin_id)
    returned = results.get(origin_id, [])
    if (not origin or origin["name"] not in {"Read", "Grep", "Glob"}
            or origin["outside"] or len(returned) != 1
            or returned[0]["block"].get("is_error") is True):
        return None
    origin_text = _text(returned[0]["block"])
    # Match the host-generated spill header, not a path merely mentioned in
    # repository text. Subsequent preview text is not used as authorization.
    if not origin_text or not re.search(
        r"\A<persisted-output>\nOutput too large \([^\r\n]+\)\. Full output saved to: "
        + re.escape(str(target)) + r"\n\nPreview \(first [^\r\n]+\):\n",
        origin_text,
    ):
        return None
    if not target.is_file():
        return None
    data = target.read_bytes()
    return {
        "classification": "verified_same_session_tool_result",
        "source_tool_use_id": origin_id,
        "source_tool_result_line": returned[0]["line"],
        "session_id": session,
        "saved_path": str(target),
        "saved_file_sha256": sha256_bytes(data),
        "saved_file_bytes": len(data),
        "_content": data,
    }


def audit_transcript(
    transcript: Path, *, work_dir: Path, legacy_parser: Callable,
    projects_root: Path | None = None, persist: bool = False,
) -> dict[str, Any]:
    """Preserve raw path facts while making result-aware validity decisions."""
    telemetry = legacy_parser(transcript, work_dir=work_dir)
    work = work_dir.resolve()
    # Canonical invocation layout: attempt/invocations/001/claude.stream.jsonl.
    attempt = transcript.resolve().parents[2]
    projects = projects_root or Path.home() / ".claude/projects"
    uses: dict[str, dict] = {}
    results: dict[str, list] = {}
    exceptions: dict[str, dict] = {}
    session = init_cwd = None
    errors: list[str] = []
    result_rows: list[dict] = []
    for line_number, line in enumerate(transcript.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"malformed_json:{line_number}")
            continue
        if not isinstance(event, dict):
            errors.append(f"non_object_event:{line_number}")
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            if session is not None:
                errors.append("multiple_init_events")
            session, init_cwd = event.get("session_id"), event.get("cwd")
        if event.get("type") == "result":
            result_rows.append(event)
        message = event.get("message")
        blocks = message.get("content") if isinstance(message, dict) else None
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if event.get("type") == "user" and block.get("type") == "tool_result":
                tool_id = block.get("tool_use_id")
                if tool_id not in uses:
                    errors.append(f"unmatched_tool_result:{tool_id}")
                results.setdefault(tool_id, []).append({"line": line_number, "block": block})
            if event.get("type") != "assistant" or block.get("type") != "tool_use":
                continue
            tool_id, name, inp = block.get("id"), block.get("name"), block.get("input")
            if not isinstance(tool_id, str) or not isinstance(inp, dict):
                errors.append(f"malformed_tool_use:{line_number}")
                continue
            if tool_id in uses:
                if uses[tool_id]["block"] != block:
                    errors.append(f"conflicting_tool_use:{tool_id}")
                continue
            raw = inp.get("file_path", inp.get("path"))
            path = _target(work, raw) if isinstance(raw, str) else work
            outside = not path.is_relative_to(work)
            # An omitted Glob path must not conceal an absolute/traversal glob.
            pattern = inp.get("pattern", "")
            if name == "Glob" and isinstance(pattern, str):
                outside |= Path(pattern).is_absolute() or ".." in Path(pattern).parts
            if name in {"Read", "Write"} and not isinstance(raw, str):
                errors.append(f"missing_file_path:{tool_id}")
            if name == "Read" and outside:
                proof = _saved_result(
                    target=path, work=work, attempt=attempt, projects=projects,
                    session=session, init_cwd=init_cwd, uses=uses, results=results,
                )
                if proof:
                    data = proof.pop("_content")
                    if persist:
                        output = transcript.parent / "verified-tool-results" / (proof["saved_file_sha256"] + ".txt")
                        if output.exists() and output.read_bytes() != data:
                            raise BaselineError("saved tool-result audit snapshot changed")
                        if not output.exists():
                            output.parent.mkdir(exist_ok=True)
                            write_atomic(output, data)
                        proof["snapshot_path"] = str(output)
                    exceptions[tool_id] = proof
            uses[tool_id] = {
                "name": name, "outside": outside, "target": path,
                "line": line_number, "block": block,
            }

    for row in telemetry["tool_uses"]:
        tool_id = row["tool_use_id"]
        use = uses.get(tool_id)
        returned = results.get(tool_id, [])
        if use is None or len(returned) != 1:
            errors.append(f"missing_or_ambiguous_result:{tool_id}")
            continue
        response = returned[0]
        row["requested_outside_working_directory"] = use["outside"]
        row["tool_result_line"] = response["line"]
        row["tool_result_is_error"] = response["block"].get("is_error") is True
        row["tool_result_sha256"] = sha256_bytes(json.dumps(response["block"], sort_keys=True).encode())
        exception = exceptions.get(tool_id)
        if use["outside"] and use["name"] == "Read" and not exception:
            if _not_found(response["block"], work):
                exception = {"classification": "read_not_found_no_content"}
        if exception:
            row["access_exception"] = exception
            row["access_policy"] = POLICY_ID
            # Compatibility field used by the unchanged persistence gate.
            # The actual requested path fact is retained separately above.
            row["outside_working_directory"] = False
        else:
            row["outside_working_directory"] = use["outside"]
        if use["name"] == "Write" and use["target"] != work / "result.txt":
            errors.append(f"write_not_exact_result_target:{tool_id}")

    if len(result_rows) != 1 or result_rows[-1].get("subtype") != "success":
        errors.append("missing_or_non_success_result_event")
    telemetry["model_result_valid"] = bool(telemetry["model_result_valid"]) and not errors
    telemetry["access_audit"] = {
        "policy": POLICY_ID, "validation_errors": errors,
        "exception_count": sum("access_exception" in row for row in telemetry["tool_uses"]),
        "permissions_expanded": False,
    }
    return telemetry
