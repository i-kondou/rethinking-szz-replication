#!/usr/bin/env python3
"""Preflight and run exactly one sanitized ClaudeSZZ subject session.

Preflight is the default and never invokes Claude. A real session requires
Claude.ai Pro/Max/Team/Enterprise subscription authentication, --execute, an
explicit full model ID, a positive USD budget cap, a new run directory, and an
exact resource-use acknowledgement. API/Console/cloud credentials are rejected.
The subject gets only the sanitized prompt on stdin and one sandboxed Bash tool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence


PROMPT_KIND = "claude-szz-sanitized-subject-prompt"
MASK_TOKEN = "[COMMIT_HASH_MASKED]"
RESOURCE_ACKNOWLEDGEMENT = "I_ACKNOWLEDGE_CLAUDE_RESOURCE_USE"
SUBSCRIPTION_AUTH_METHOD = "claude.ai"
ALLOWED_SUBSCRIPTION_TYPES = {"pro", "max", "team", "enterprise"}
RECOMMENDED_PRIMARY_MODEL = "claude-sonnet-5"
DEFAULT_EFFORT = "high"
MINIMUM_CLAUDE_VERSION_BY_MODEL = {
    "claude-sonnet-5": (2, 1, 197),
}
REQUIRED_CLAUDE_FLAGS = (
    "--allowedTools",
    "--include-hook-events",
    "--include-partial-messages",
    "--max-budget-usd",
    "--no-session-persistence",
    "--output-format",
    "--permission-mode",
    "--setting-sources",
    "--settings",
    "--strict-mcp-config",
    "--tools",
)
FORBIDDEN_AVAILABLE_TOOLS = {
    "Agent",
    "Edit",
    "NotebookEdit",
    "Read",
    "Skill",
    "WebFetch",
    "WebSearch",
    "Write",
}
SUBJECT_SYSTEM_PROMPT = """\
You are the subject in a controlled bug-inducing commit identification study.
Use only the Bash tool and only local, read-only Git or file-inspection commands
inside the current repository. Do not use the network, spawn subagents, modify
files, change refs, write memory, or inspect paths outside the current
repository. Treat HEAD as the supplied synthetic bug-fixing commit. Conclude
with the exact sections requested in the user prompt and report uncertainty.
"""


class SubjectRunError(RuntimeError):
    """Raised when a subject run is unsafe, invalid, or incomplete."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_atomic(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{path.name}.", dir=path.parent, delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def write_json(path: Path, value: object) -> None:
    write_atomic(
        path,
        (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
    )


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise SubjectRunError(
            f"git command failed ({result.returncode}): {' '.join(args)}\n{stderr}"
        )
    return result


def git_text(repo: Path, *args: str) -> str:
    return run_git(repo, *args).stdout.decode("utf-8", errors="replace").strip()


def object_exists(repo: Path, object_id: str) -> bool:
    return run_git(repo, "cat-file", "-e", object_id, check=False).returncode == 0


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def git_snapshot(repo: Path, synthetic_fix: str, source_fix: str) -> dict[str, object]:
    head = git_text(repo, "rev-parse", "HEAD^{commit}")
    return {
        "head": head,
        "head_matches_synthetic_fix": head == synthetic_fix,
        "working_tree_clean": not bool(git_text(repo, "status", "--porcelain")),
        "source_bfc_object_absent": not object_exists(repo, source_fix),
        "no_remotes": not bool(git_text(repo, "remote")),
        "no_object_alternates": not (repo / ".git/objects/info/alternates").exists(),
    }


def load_and_validate_subject(
    metadata_path: Path, expected_sample_id: str | None = None
) -> dict[str, object]:
    metadata_path = metadata_path.expanduser().resolve()
    metadata = load_json(metadata_path)
    if not isinstance(metadata, dict):
        raise SubjectRunError("prompt metadata is not a JSON object")
    if metadata.get("schema_version") != 1 or metadata.get("kind") != PROMPT_KIND:
        raise SubjectRunError("unsupported or unexpected prompt metadata")

    sample_id = str(metadata.get("sample_id", ""))
    if not sample_id or (expected_sample_id is not None and sample_id != expected_sample_id):
        raise SubjectRunError("prompt metadata sample ID does not match")
    preflight = metadata.get("preflight")
    if not isinstance(preflight, dict) or not preflight or not all(preflight.values()):
        raise SubjectRunError("prompt metadata contains a failed or missing preflight")

    try:
        prompt_path = Path(str(metadata["prompt_path"])).expanduser().resolve()
        repo = Path(str(metadata["subject_repository_path"])).expanduser().resolve()
        prompt_sha256 = str(metadata["prompt_sha256"])
        source_fix = str(metadata["source_fix_hash"])
        synthetic_fix = str(metadata["synthetic_fix_hash"])
        oracle_hashes = [str(value) for value in metadata["oracle_bic_hashes"]]
        masked_tokens = [str(value) for value in metadata["masked_source_tokens"]]
    except (KeyError, TypeError) as exc:
        raise SubjectRunError("malformed prompt metadata") from exc

    if not prompt_path.is_file():
        raise SubjectRunError(f"sanitized prompt is missing: {prompt_path}")
    if sha256_file(prompt_path) != prompt_sha256:
        raise SubjectRunError("sanitized prompt checksum does not match metadata")
    if not (repo / ".git").is_dir():
        raise SubjectRunError(f"sanitized subject repository is missing: {repo}")
    if path_is_within(metadata_path, repo) or path_is_within(prompt_path, repo):
        raise SubjectRunError("analyst prompt artifacts must be outside the subject repository")

    prompt = prompt_path.read_text(encoding="utf-8")
    prompt_lower = prompt.lower()
    if MASK_TOKEN not in prompt:
        raise SubjectRunError("sanitized prompt has no mask token")
    leaks: list[str] = []
    if source_fix.lower() in prompt_lower:
        leaks.append("source BFC hash")
    leaks.extend(
        f"Oracle BIC {value}" for value in oracle_hashes if value.lower() in prompt_lower
    )
    leaks.extend(
        f"masked token {value}" for value in masked_tokens if value.lower() in prompt_lower
    )
    if leaks:
        raise SubjectRunError("prompt leakage preflight failed: " + ", ".join(leaks))

    snapshot = git_snapshot(repo, synthetic_fix, source_fix)
    if not all(value for key, value in snapshot.items() if key != "head"):
        failed = [key for key, value in snapshot.items() if key != "head" and not value]
        raise SubjectRunError("subject repository preflight failed: " + ", ".join(failed))

    return {
        "metadata_path": metadata_path,
        "metadata_sha256": sha256_file(metadata_path),
        "metadata": metadata,
        "sample_id": sample_id,
        "prompt_path": prompt_path,
        "prompt_sha256": prompt_sha256,
        "prompt": prompt,
        "repo": repo,
        "source_fix": source_fix,
        "synthetic_fix": synthetic_fix,
        "snapshot": snapshot,
    }


def parse_claude_version(output: str) -> str:
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", output)
    if not match:
        raise SubjectRunError(f"could not parse Claude Code version: {output.strip()!r}")
    return match.group(1)


def version_tuple(version: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise SubjectRunError(f"invalid Claude Code version: {version!r}")
    return tuple(int(value) for value in match.groups())


def model_runtime_readiness(model: str, claude_version: str) -> dict[str, object]:
    minimum = MINIMUM_CLAUDE_VERSION_BY_MODEL.get(model)
    ready = minimum is None or version_tuple(claude_version) >= minimum
    return {
        "model": model,
        "claude_code_version": claude_version,
        "minimum_claude_code_version": (
            ".".join(str(value) for value in minimum) if minimum else None
        ),
        "ready": ready,
    }


def validate_model_runtime(model: str, claude_version: str) -> dict[str, object]:
    readiness = model_runtime_readiness(model, claude_version)
    if not readiness["ready"]:
        raise SubjectRunError(
            f"model {model} requires Claude Code >= "
            f"{readiness['minimum_claude_code_version']}; observed {claude_version}"
        )
    return readiness


def validate_subscription_auth(auth: object) -> dict[str, object]:
    if not isinstance(auth, dict) or not auth.get("loggedIn"):
        raise SubjectRunError("Claude Code is not logged in")
    auth_method = str(auth.get("authMethod", "")).lower()
    api_provider = str(auth.get("apiProvider", ""))
    subscription_type = str(auth.get("subscriptionType", "")).lower()
    if auth_method != SUBSCRIPTION_AUTH_METHOD:
        raise SubjectRunError(
            "subscription-only gate rejected the active Claude credential: "
            "log in with a Claude.ai subscription, not Console/API/cloud credentials"
        )
    if subscription_type not in ALLOWED_SUBSCRIPTION_TYPES:
        raise SubjectRunError(
            "subscription-only gate requires Pro, Max, Team, or Enterprise; "
            f"observed subscription type: {subscription_type or 'missing'}"
        )
    if api_provider.lower() != "firstparty":
        raise SubjectRunError(
            "subscription-only gate requires Anthropic first-party routing"
        )
    return {
        "logged_in": True,
        "auth_method": auth_method,
        "api_provider": api_provider,
        "subscription_type": subscription_type,
        "subscription_only_gate_passed": True,
    }


def inspect_claude(claude_bin: str, env: dict[str, str]) -> dict[str, object]:
    executable = shutil.which(claude_bin)
    if executable is None:
        raise SubjectRunError(f"Claude Code executable was not found: {claude_bin}")
    version_result = subprocess.run(
        [executable, "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if version_result.returncode != 0:
        raise SubjectRunError("claude --version failed: " + version_result.stderr.strip())
    help_result = subprocess.run(
        [executable, "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if help_result.returncode != 0:
        raise SubjectRunError("claude --help failed: " + help_result.stderr.strip())
    missing_flags = [flag for flag in REQUIRED_CLAUDE_FLAGS if flag not in help_result.stdout]
    if missing_flags:
        raise SubjectRunError(
            "Claude Code lacks required runner flags: " + ", ".join(missing_flags)
        )
    auth_result = subprocess.run(
        [executable, "auth", "status"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if auth_result.returncode != 0:
        raise SubjectRunError("claude auth status failed: " + auth_result.stderr.strip())
    try:
        auth = json.loads(auth_result.stdout)
    except json.JSONDecodeError as exc:
        raise SubjectRunError("claude auth status did not return JSON") from exc
    validated_auth = validate_subscription_auth(auth)
    return {
        "executable": str(Path(executable).resolve()),
        "version": parse_claude_version(version_result.stdout),
        "auth": validated_auth,
    }


def sanitized_environment() -> dict[str, str]:
    allowed_names = {
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "LOGNAME",
        "PATH",
        "SHELL",
        "TERM",
        "TMPDIR",
        "USER",
    }
    env = {key: value for key, value in os.environ.items() if key in allowed_names}
    env.update(
        {
            "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
            "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
            "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
            "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1",
            "DISABLE_AUTOUPDATER": "1",
            "DISABLE_EXTRA_USAGE_COMMAND": "1",
            # Git otherwise follows HOME into ~/.gitconfig, which the subject
            # sandbox intentionally cannot read. Disable host-level Git
            # configuration while preserving the subject repository's local
            # .git/config.
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
        }
    )
    return env


def build_settings(repo: Path) -> dict[str, object]:
    return {
        "autoMemoryEnabled": False,
        "disableAllHooks": True,
        "permissions": {
            "allow": ["Bash"],
            "ask": [],
            "deny": sorted(FORBIDDEN_AVAILABLE_TOOLS),
        },
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "autoAllowBashIfSandboxed": True,
            "allowUnsandboxedCommands": False,
            "excludedCommands": [],
            "filesystem": {
                "denyRead": ["~/"],
                "allowRead": [str(repo)],
                "denyWrite": [str(repo)],
            },
            "network": {
                "allowedDomains": [],
                "deniedDomains": ["*"],
                "allowUnixSockets": [],
                "allowAllUnixSockets": False,
                "allowLocalBinding": False,
            },
            "allowAppleEvents": False,
        },
    }


def parse_budget(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        budget = Decimal(value)
    except InvalidOperation as exc:
        raise SubjectRunError("--max-budget-usd must be a decimal number") from exc
    if not budget.is_finite() or budget <= 0:
        raise SubjectRunError("--max-budget-usd must be positive and finite")
    return budget


def validate_execution_gate(args: argparse.Namespace, budget: Decimal | None) -> Path:
    if not args.execute:
        if args.acknowledge_resource_use or args.run_dir:
            raise SubjectRunError(
                "--acknowledge-resource-use and --run-dir are only valid with --execute"
            )
        return Path()
    if not args.model or not re.fullmatch(r"claude-[a-z0-9-]+", args.model):
        raise SubjectRunError("--execute requires an explicit full Claude model ID")
    if budget is None:
        raise SubjectRunError("--execute requires --max-budget-usd")
    if args.acknowledge_resource_use != RESOURCE_ACKNOWLEDGEMENT:
        raise SubjectRunError(
            "--execute requires --acknowledge-resource-use " + RESOURCE_ACKNOWLEDGEMENT
        )
    if args.run_dir is None:
        raise SubjectRunError("--execute requires --run-dir")
    run_dir = args.run_dir.expanduser().resolve()
    if run_dir.exists():
        raise SubjectRunError(f"refusing to replace existing run directory: {run_dir}")
    return run_dir


def build_command(
    *,
    claude: dict[str, object],
    settings_path: Path,
    mcp_path: Path,
    debug_path: Path,
    model: str,
    effort: str,
    budget: Decimal,
) -> list[str]:
    return [
        str(claude["executable"]),
        "--print",
        "--model",
        model,
        "--effort",
        effort,
        "--max-budget-usd",
        str(budget),
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-hook-events",
        "--include-partial-messages",
        "--tools",
        "Bash",
        "--allowedTools",
        "Bash",
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
        SUBJECT_SYSTEM_PROMPT,
        "--debug-file",
        str(debug_path),
    ]


def public_command(command: list[str]) -> list[str]:
    result = command.copy()
    try:
        index = result.index("--append-system-prompt") + 1
        result[index] = f"<system-prompt sha256={sha256_bytes(SUBJECT_SYSTEM_PROMPT.encode())}>"
    except (ValueError, IndexError):
        pass
    return result


def validate_transcript(
    transcript_path: Path,
    *,
    expected_model: str,
    expected_version: str,
    max_budget: Decimal,
) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    invalid_lines: list[int] = []
    for number, line in enumerate(transcript_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines.append(number)
            continue
        if isinstance(entry, dict):
            entries.append(entry)
        else:
            invalid_lines.append(number)

    init_entries = [
        entry
        for entry in entries
        if entry.get("type") == "system" and entry.get("subtype") == "init"
    ]
    result_entries = [entry for entry in entries if entry.get("type") == "result"]
    init = init_entries[-1] if init_entries else {}
    result = result_entries[-1] if result_entries else {}
    available_tools = {str(value) for value in init.get("tools", [])}
    mcp_servers = init.get("mcp_servers", [])

    tool_use_ids: set[str] = set()
    tool_result_ids: set[str] = set()
    tool_names: set[str] = set()
    unsandboxed_requests = 0
    git_config_access_failures = 0
    for entry in entries:
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content", [])
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use":
                tool_id = str(item.get("id", ""))
                if tool_id:
                    tool_use_ids.add(tool_id)
                tool_names.add(str(item.get("name", "")))
                tool_input = item.get("input")
                if isinstance(tool_input, dict) and tool_input.get("dangerouslyDisableSandbox"):
                    unsandboxed_requests += 1
            elif item.get("type") == "tool_result":
                result_id = str(item.get("tool_use_id", ""))
                if result_id:
                    tool_result_ids.add(result_id)
                result_content = item.get("content", "")
                if isinstance(result_content, str):
                    result_text = result_content
                else:
                    result_text = json.dumps(result_content, ensure_ascii=False)
                result_text_lower = result_text.lower()
                if (
                    ".gitconfig" in result_text_lower
                    and "unable to access" in result_text_lower
                    and (
                        "operation not permitted" in result_text_lower
                        or "permission denied" in result_text_lower
                    )
                ):
                    git_config_access_failures += 1

    reported_cost = result.get("total_cost_usd")
    try:
        cost_within_budget = reported_cost is not None and Decimal(str(reported_cost)) <= max_budget
    except InvalidOperation:
        cost_within_budget = False
    checks = {
        "all_lines_are_json_objects": not invalid_lines,
        "exactly_one_init_event": len(init_entries) == 1,
        "result_event_present": bool(result_entries),
        "result_reports_success": result.get("subtype") == "success"
        and not bool(result.get("is_error")),
        "model_matches": init.get("model") == expected_model,
        "claude_version_matches": init.get("claude_code_version") == expected_version,
        "permission_mode_is_dont_ask": init.get("permissionMode") == "dontAsk",
        "only_bash_available": available_tools == {"Bash"},
        "no_mcp_servers": not bool(mcp_servers),
        "only_bash_used": tool_names.issubset({"Bash"}),
        "every_tool_use_has_result": tool_use_ids.issubset(tool_result_ids),
        "no_unsandboxed_request": unsandboxed_requests == 0,
        "no_host_git_config_access_failure": git_config_access_failures == 0,
        "reported_cost_within_budget": cost_within_budget,
    }
    return {
        "checks": checks,
        "valid": all(checks.values()),
        "entry_count": len(entries),
        "invalid_line_numbers": invalid_lines,
        "tool_use_count": len(tool_use_ids),
        "tool_result_count": len(tool_result_ids),
        "tool_names": sorted(tool_names),
        "host_git_config_access_failure_count": git_config_access_failures,
        "reported_cost_usd": reported_cost,
        "session_id": result.get("session_id") or init.get("session_id"),
        "num_turns": result.get("num_turns"),
        "duration_ms": result.get("duration_ms"),
    }


def execute_run(
    *,
    args: argparse.Namespace,
    budget: Decimal,
    run_dir: Path,
    subject: dict[str, object],
    claude: dict[str, object],
    env: dict[str, str],
) -> dict[str, object]:
    repo = subject["repo"]
    assert isinstance(repo, Path)
    run_dir.mkdir(parents=True, exist_ok=False)
    settings_path = run_dir / "settings.json"
    mcp_path = run_dir / "mcp.json"
    prompt_copy_path = run_dir / "prompt.md"
    transcript_partial = run_dir / "transcript.jsonl.partial"
    transcript_path = run_dir / "transcript.jsonl"
    event_log_partial = run_dir / "received-events.jsonl.partial"
    event_log_path = run_dir / "received-events.jsonl"
    stderr_partial = run_dir / "stderr.log.partial"
    stderr_path = run_dir / "stderr.log"
    debug_path = run_dir / "debug.log"
    manifest_path = run_dir / "run.json"

    settings = build_settings(repo)
    write_json(settings_path, settings)
    write_json(mcp_path, {"mcpServers": {}})
    write_atomic(prompt_copy_path, str(subject["prompt"]).encode("utf-8"))
    command = build_command(
        claude=claude,
        settings_path=settings_path,
        mcp_path=mcp_path,
        debug_path=debug_path,
        model=args.model,
        effort=args.effort,
        budget=budget,
    )
    started_at = utc_now()
    manifest: dict[str, object] = {
        "schema_version": 1,
        "kind": "claude-szz-sanitized-subject-run",
        "state": "running",
        "sample_id": subject["sample_id"],
        "started_at": started_at,
        "finished_at": None,
        "runner": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "input": {
            "prompt_sha256": subject["prompt_sha256"],
            "prompt_copy": str(prompt_copy_path),
            "synthetic_fix_hash": subject["synthetic_fix"],
            "subject_repository_path": str(repo),
        },
        "claude": {
            "executable": claude["executable"],
            "version": claude["version"],
            "auth": claude["auth"],
            "model": args.model,
            "effort": args.effort,
            "max_budget_usd": str(budget),
            "command": public_command(command),
        },
        "billing_boundary": {
            "required_auth_method": SUBSCRIPTION_AUTH_METHOD,
            "allowed_subscription_types": sorted(ALLOWED_SUBSCRIPTION_TYPES),
            "subscription_gate_passed": True,
            "api_key_environment_forwarded": False,
            "cloud_provider_environment_forwarded": False,
            "fast_mode_disabled": True,
            "extra_usage_command_disabled": True,
            "account_level_usage_credits_state": "not observable from claude auth status",
        },
        "isolation": {
            "settings_path": str(settings_path),
            "settings_sha256": sha256_file(settings_path),
            "mcp_config_path": str(mcp_path),
            "mcp_config_sha256": sha256_file(mcp_path),
            "setting_sources": [],
            "available_tools_requested": ["Bash"],
            "auto_memory_disabled": True,
            "claude_md_loading_disabled": True,
            "background_tasks_disabled": True,
            "fast_mode_disabled": True,
            "nonessential_traffic_disabled": True,
            "session_persistence_disabled": True,
            "git_global_config_disabled": env.get("GIT_CONFIG_GLOBAL") == os.devnull,
            "git_system_config_disabled": env.get("GIT_CONFIG_SYSTEM") == os.devnull,
            "repository_local_git_config_preserved": True,
        },
        "preflight": subject["snapshot"],
        "process": None,
        "transcript_validation": None,
        "postflight": None,
    }
    write_json(manifest_path, manifest)

    start = time.monotonic()
    timed_out = False
    interrupted = False
    exit_code: int | None = None
    collector_errors: list[str] = []
    with (
        transcript_partial.open("wb") as stdout_handle,
        event_log_partial.open("wb") as event_log_handle,
        stderr_partial.open("wb") as stderr_handle,
    ):
        process = subprocess.Popen(
            command,
            cwd=repo,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_handle,
            env=env,
            start_new_session=True,
        )

        def collect_stdout() -> None:
            assert process.stdout is not None
            try:
                for line_number, raw_line in enumerate(process.stdout, 1):
                    received_at = utc_now()
                    stdout_handle.write(raw_line)
                    stdout_handle.flush()
                    try:
                        event: object = json.loads(raw_line)
                        envelope = {
                            "received_at": received_at,
                            "line_number": line_number,
                            "event": event,
                        }
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        envelope = {
                            "received_at": received_at,
                            "line_number": line_number,
                            "unparsed_utf8": raw_line.decode("utf-8", errors="replace").rstrip("\n"),
                        }
                    event_log_handle.write(
                        (json.dumps(envelope, ensure_ascii=False) + "\n").encode("utf-8")
                    )
                    event_log_handle.flush()
            except BaseException as exc:  # Preserve collector failures in run metadata.
                collector_errors.append(repr(exc))

        collector = threading.Thread(
            target=collect_stdout,
            name="claude-szz-event-collector",
            daemon=True,
        )
        collector.start()
        assert process.stdin is not None
        process.stdin.write(str(subject["prompt"]).encode("utf-8"))
        process.stdin.close()
        try:
            process.wait(timeout=args.timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        except KeyboardInterrupt:
            interrupted = True
            os.killpg(process.pid, signal.SIGTERM)
            process.wait()
        collector.join(timeout=10)
        if collector.is_alive():
            collector_errors.append("event collector did not stop within 10 seconds")
        if process.stdout is not None:
            process.stdout.close()
        exit_code = process.returncode

    os.replace(stderr_partial, stderr_path)
    if exit_code == 0 and not timed_out and not interrupted and not collector_errors:
        os.replace(transcript_partial, transcript_path)
        os.replace(event_log_partial, event_log_path)
    else:
        transcript_path = transcript_partial
        event_log_path = event_log_partial

    duration_seconds = time.monotonic() - start
    transcript_validation = validate_transcript(
        transcript_path,
        expected_model=args.model,
        expected_version=str(claude["version"]),
        max_budget=budget,
    )
    postflight = git_snapshot(
        repo, str(subject["synthetic_fix"]), str(subject["source_fix"])
    )
    process_ok = exit_code == 0 and not timed_out and not interrupted and not collector_errors
    postflight_ok = all(value for key, value in postflight.items() if key != "head")
    completed = process_ok and bool(transcript_validation["valid"]) and postflight_ok
    manifest.update(
        {
            "state": "completed" if completed else "failed-validation",
            "finished_at": utc_now(),
            "process": {
                "exit_code": exit_code,
                "timed_out": timed_out,
                "interrupted": interrupted,
                "timeout_seconds": args.timeout_seconds,
                "duration_seconds": duration_seconds,
                "collector_errors": collector_errors,
                "stdout_path": str(transcript_path),
                "stdout_sha256": sha256_file(transcript_path),
                "received_events_path": str(event_log_path),
                "received_events_sha256": sha256_file(event_log_path),
                "stderr_path": str(stderr_path),
                "stderr_sha256": sha256_file(stderr_path),
                "debug_path": str(debug_path),
                "debug_sha256": sha256_file(debug_path) if debug_path.exists() else None,
            },
            "transcript_validation": transcript_validation,
            "postflight": postflight,
        }
    )
    write_json(manifest_path, manifest)
    if not completed:
        raise SubjectRunError(f"subject run failed validation; inspect {manifest_path}")
    return manifest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-id")
    parser.add_argument("--prompt-metadata", type=Path, required=True)
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--model")
    parser.add_argument(
        "--effort", choices=("low", "medium", "high"), default=DEFAULT_EFFORT
    )
    parser.add_argument("--max-budget-usd")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--acknowledge-resource-use")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.timeout_seconds <= 0:
            raise SubjectRunError("--timeout-seconds must be positive")
        budget = parse_budget(args.max_budget_usd)
        run_dir = validate_execution_gate(args, budget)
        subject = load_and_validate_subject(args.prompt_metadata, args.sample_id)
        env = sanitized_environment()
        claude = inspect_claude(args.claude_bin, env)
        recommended_model_readiness = model_runtime_readiness(
            RECOMMENDED_PRIMARY_MODEL, str(claude["version"])
        )
        settings = build_settings(subject["repo"])
        preflight_report = {
            "valid": True,
            "mode": "execute" if args.execute else "preflight-only",
            "claude_invoked": False,
            "model_resource_cost_usd": "0",
            "recommended_primary_model": RECOMMENDED_PRIMARY_MODEL,
            "default_effort": DEFAULT_EFFORT,
            "recommended_model_runtime": recommended_model_readiness,
            "sample_id": subject["sample_id"],
            "prompt_sha256": subject["prompt_sha256"],
            "synthetic_fix_hash": subject["synthetic_fix"],
            "subject_repository_path": str(subject["repo"]),
            "repository_checks": subject["snapshot"],
            "claude_code": claude,
            "billing_boundary": {
                "subscription_only": True,
                "required_auth_method": SUBSCRIPTION_AUTH_METHOD,
                "allowed_subscription_types": sorted(ALLOWED_SUBSCRIPTION_TYPES),
                "api_key_environment_forwarded": False,
                "cloud_provider_environment_forwarded": False,
                "fast_mode_disabled": True,
                "extra_usage_command_disabled": True,
                "account_level_usage_credits_state": "not observable from claude auth status",
            },
            "requested_isolation": settings,
            "git_config_environment": {
                "GIT_CONFIG_GLOBAL": env.get("GIT_CONFIG_GLOBAL"),
                "GIT_CONFIG_SYSTEM": env.get("GIT_CONFIG_SYSTEM"),
                "repository_local_config_preserved": True,
            },
        }
        if not args.execute:
            print(json.dumps(preflight_report, indent=2, ensure_ascii=False))
            return 0
        assert budget is not None
        validate_model_runtime(args.model, str(claude["version"]))
        manifest = execute_run(
            args=args,
            budget=budget,
            run_dir=run_dir,
            subject=subject,
            claude=claude,
            env=env,
        )
        print(json.dumps({
            "state": manifest["state"],
            "sample_id": manifest["sample_id"],
            "run_manifest": str(run_dir / "run.json"),
            "reported_cost_usd": manifest["transcript_validation"]["reported_cost_usd"],
        }, indent=2, ensure_ascii=False))
        return 0
    except (OSError, json.JSONDecodeError, SubjectRunError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
