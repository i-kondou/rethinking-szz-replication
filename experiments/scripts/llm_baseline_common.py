#!/usr/bin/env python3
"""Shared validation and provenance helpers for the EXP002 LLM baselines."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_MANIFEST = PROJECT_ROOT / "config/llm-baseline-sources.json"
DEFAULT_PROMPT_ROOT = PROJECT_ROOT / "data/derived/subject-prompts"
MODEL = "claude-sonnet-5"
CLAUDE_CODE_VERSION = "2.1.232"
REPETITIONS = 3


class BaselineError(RuntimeError):
    """Raised when a frozen baseline invariant or execution gate fails."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def llm4szz_code_tree_sha256(root: Path) -> str:
    paths = sorted(
        [*root.glob("*.py"), root / "build/my-languages.so"],
        key=lambda item: item.relative_to(root).as_posix(),
    )
    digest = hashlib.sha256()
    for path in paths:
        if not path.is_file():
            raise BaselineError(f"LLM4SZZ code-tree input is missing: {path}")
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


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
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"could not load JSON {path}: {exc}") from exc


def run_git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise BaselineError(
            f"git -C {repo} {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def validate_source_manifest(path: Path = DEFAULT_SOURCE_MANIFEST) -> dict[str, object]:
    path = path.expanduser().resolve()
    value = load_json(path)
    if not isinstance(value, dict):
        raise BaselineError("LLM baseline source manifest is not an object")
    if (
        value.get("schema_version") != 1
        or value.get("kind") != "claude-szz-llm-baseline-source-acquisition"
    ):
        raise BaselineError("unsupported LLM baseline source manifest")
    condition = value.get("model_condition")
    if not isinstance(condition, dict):
        raise BaselineError("source manifest model condition is missing")
    expected = {
        "model_id": MODEL,
        "model_id_policy": "canonical_fixed_snapshot",
        "repetitions_per_sample": REPETITIONS,
        "normal_completion_only": True,
        "claude_code_version_for_cli_conditions": CLAUDE_CODE_VERSION,
    }
    for key, expected_value in expected.items():
        if condition.get(key) != expected_value:
            raise BaselineError(f"source manifest {key} is not frozen to {expected_value!r}")

    sources = value.get("sources")
    if not isinstance(sources, dict):
        raise BaselineError("source manifest sources are missing")
    llm4 = sources.get("llm4szz_original")
    agent = sources.get("szz_agent")
    if not isinstance(llm4, dict) or not isinstance(agent, dict):
        raise BaselineError("source manifest baseline entries are missing")

    archive = Path(str(llm4.get("local_archive_path", ""))).expanduser().resolve()
    if not archive.is_file() or sha256_file(archive) != llm4.get("archive_sha256"):
        raise BaselineError("official LLM4SZZ archive is missing or has changed")

    agent_repo = Path(str(agent.get("local_path", ""))).expanduser().resolve()
    if not (agent_repo / ".git").is_dir():
        raise BaselineError(f"SZZ-Agent checkout is missing: {agent_repo}")
    if run_git(agent_repo, "rev-parse", "HEAD") != agent.get("commit"):
        raise BaselineError("SZZ-Agent checkout is not at the frozen commit")
    if run_git(agent_repo, "status", "--porcelain"):
        raise BaselineError("SZZ-Agent frozen checkout is dirty")
    simple = agent_repo / str(agent.get("simple_szz_agent_path", ""))
    prompts = agent_repo / str(agent.get("prompts_path", ""))
    if (
        not simple.is_file()
        or sha256_file(simple) != agent.get("simple_szz_agent_sha256")
    ):
        raise BaselineError("Simple-SZZ-Agent source is missing or changed")
    if not prompts.is_file() or sha256_file(prompts) != agent.get("prompts_sha256"):
        raise BaselineError("SZZ-Agent shared prompts source is missing or changed")
    bundled = agent_repo / str(agent.get("bundled_llm4szz_adapter_path", ""))
    if (
        not bundled.is_file()
        or sha256_file(bundled) != agent.get("bundled_llm4szz_adapter_sha256")
    ):
        raise BaselineError("SZZ-Agent bundled LLM4SZZ adapter is missing or changed")
    adapter = Path(
        str(agent.get("bundled_llm4szz_adapter_extracted_path", ""))
    ).expanduser().resolve()
    required_adapter_files = [
        adapter / "llm4szz.py",
        adapter / "llm.py",
        adapter / "constants.py",
        adapter / "build/my-languages.so",
    ]
    if not all(item.is_file() for item in required_adapter_files):
        raise BaselineError(f"extracted LLM4SZZ adapter is incomplete: {adapter}")
    extracted_code_sha256 = llm4szz_code_tree_sha256(adapter)
    if extracted_code_sha256 != agent.get("bundled_llm4szz_extracted_code_sha256"):
        raise BaselineError("extracted LLM4SZZ executable code tree has changed")

    runtime = value.get("local_runtime_preparation")
    if not isinstance(runtime, dict):
        raise BaselineError("local LLM baseline runtime preparation is not registered")
    registered_files = [
        ("requirements_path", "requirements_sha256"),
        ("common_validator_path", "common_validator_sha256"),
        ("single_subject_runner_path", "single_subject_runner_sha256"),
        ("full_runner_path", "full_runner_sha256"),
        ("test_path", "test_sha256"),
    ]
    for path_key, hash_key in registered_files:
        registered = PROJECT_ROOT / str(runtime.get(path_key, ""))
        if not registered.is_file() or sha256_file(registered) != runtime.get(hash_key):
            raise BaselineError(f"registered runtime file is missing or changed: {path_key}")

    return {
        "manifest_path": str(path),
        "manifest_sha256": sha256_file(path),
        "llm4szz_archive_path": str(archive),
        "llm4szz_archive_sha256": llm4.get("archive_sha256"),
        "llm4szz_adapter_path": str(adapter),
        "llm4szz_adapter_code_sha256": extracted_code_sha256,
        "szz_agent_path": str(agent_repo),
        "szz_agent_commit": agent.get("commit"),
        "simple_szz_agent_path": str(simple),
        "simple_szz_agent_sha256": agent.get("simple_szz_agent_sha256"),
        "szz_agent_prompts_path": str(prompts),
        "szz_agent_prompts_sha256": agent.get("prompts_sha256"),
        "szz_agent_bundled_adapter_sha256": agent.get(
            "bundled_llm4szz_adapter_sha256"
        ),
    }


def repository_snapshot(repo: Path, synthetic_fix: str, source_fix: str) -> dict[str, object]:
    return {
        "head": run_git(repo, "rev-parse", "HEAD"),
        "head_matches_synthetic_fix": run_git(repo, "rev-parse", "HEAD")
        == synthetic_fix,
        "source_fix_absent": subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{source_fix}^{{commit}}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        != 0,
        "clean": not bool(run_git(repo, "status", "--porcelain")),
        "no_remotes": not bool(run_git(repo, "remote")),
        "no_object_alternates": not (repo / ".git/objects/info/alternates").exists(),
    }


def load_subject(metadata_path: Path, sample_id: str | None = None) -> dict[str, object]:
    metadata_path = metadata_path.expanduser().resolve()
    value = load_json(metadata_path)
    if not isinstance(value, dict):
        raise BaselineError("prompt metadata is not an object")
    if (
        value.get("schema_version") != 1
        or value.get("kind") != "claude-szz-sanitized-subject-prompt"
    ):
        raise BaselineError("unexpected prompt metadata schema")
    actual_id = str(value.get("sample_id", ""))
    if not actual_id.isdigit() or (sample_id is not None and actual_id != sample_id):
        raise BaselineError("sample ID does not match prompt metadata")
    preflight = value.get("preflight")
    if not isinstance(preflight, dict) or not preflight or not all(preflight.values()):
        raise BaselineError("prompt metadata preflight is not fully valid")
    prompt_path = Path(str(value.get("prompt_path", ""))).expanduser().resolve()
    if not prompt_path.is_file() or sha256_file(prompt_path) != value.get("prompt_sha256"):
        raise BaselineError("sanitized prompt is missing or has changed")
    repo = Path(str(value.get("subject_repository_path", ""))).expanduser().resolve()
    if not (repo / ".git").is_dir():
        raise BaselineError(f"sanitized subject repository is missing: {repo}")
    source_fix = str(value.get("source_fix_hash", ""))
    synthetic_fix = str(value.get("synthetic_fix_hash", ""))
    oracle = value.get("oracle_bic_hashes")
    if not source_fix or not synthetic_fix or not isinstance(oracle, list) or not oracle:
        raise BaselineError("subject metadata lacks fix/oracle identifiers")
    snapshot = repository_snapshot(repo, synthetic_fix, source_fix)
    if not all(item for key, item in snapshot.items() if key != "head"):
        raise BaselineError(f"sanitized subject repository validation failed: {snapshot}")
    return {
        "sample_id": actual_id,
        "repository": str(value.get("repository", "")),
        "metadata_path": str(metadata_path),
        "metadata_sha256": sha256_file(metadata_path),
        "prompt_path": str(prompt_path),
        "prompt_sha256": value.get("prompt_sha256"),
        "repo": repo,
        "source_fix": source_fix,
        "synthetic_fix": synthetic_fix,
        "oracle_bics": [str(item) for item in oracle],
        "snapshot": snapshot,
    }


def all_subjects(
    prompt_root: Path = DEFAULT_PROMPT_ROOT, expected_count: int = 79
) -> list[dict[str, object]]:
    prompt_root = prompt_root.expanduser().resolve()
    if not prompt_root.is_dir():
        raise BaselineError(f"prompt root does not exist: {prompt_root}")
    subjects = [load_subject(path) for path in prompt_root.glob("*.json")]
    subjects.sort(key=lambda row: int(str(row["sample_id"])))
    if len(subjects) != expected_count:
        raise BaselineError(
            f"expected {expected_count} validated subjects, found {len(subjects)}"
        )
    return subjects


def upstream_dataset_row(subject: dict[str, object]) -> dict[str, object]:
    """Return the common one-entry format accepted by both upstream methods."""
    return {
        "id": str(subject["sample_id"]),
        "repo_name": f"subjects/{subject['sample_id']}",
        "fix_commit_hash": str(subject["synthetic_fix"]),
        "bug_commit_hash": list(subject["oracle_bics"]),
        "bug_fixing_commit": str(subject["synthetic_fix"]),
        "bug_inducing_commit": list(subject["oracle_bics"]),
        "language": ["java"],
        "source_repository": str(subject["repository"]),
    }


def prepare_runtime_input(runtime_root: Path, subject: dict[str, object]) -> Path:
    runtime_root.mkdir(parents=True, exist_ok=False)
    dataset_path = runtime_root / "dataset.json"
    write_json(dataset_path, [upstream_dataset_row(subject)])
    link = runtime_root / "repos/subjects" / str(subject["sample_id"])
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(Path(subject["repo"]), target_is_directory=True)
    return dataset_path


def sanitized_environment(*, keep_api_key: bool = False) -> dict[str, str]:
    allowed = {
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
    if keep_api_key:
        allowed.add("ANTHROPIC_API_KEY")
    env = {key: value for key, value in os.environ.items() if key in allowed}
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
        }
    )
    return env
