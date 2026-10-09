#!/usr/bin/env python3
"""Shared provenance and safety helpers for AgentSZZ and AgenticSZZ adapters."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from llm_baseline_common import BaselineError, load_json, run_git, sha256_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_MANIFEST = PROJECT_ROOT / "config/agentic-baseline-sources.json"
MODEL = "anthropic/claude-sonnet-5"
BASE_URL = "https://openrouter.ai/api/v1"
BASELINES = ("agentszz", "agentic-szz")
RESOURCE_ACKNOWLEDGEMENT = "I_ACKNOWLEDGE_AGENTIC_BASELINE_RESOURCE_USE"
API_BILLING_ACKNOWLEDGEMENT = "I_ACKNOWLEDGE_OPENROUTER_API_BILLING"
INPUT_USD_PER_MILLION = Decimal("2")
OUTPUT_USD_PER_MILLION = Decimal("10")
MAX_OUTPUT_TOKENS = 4096


def parse_positive_decimal(value: str | None, label: str) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise BaselineError(f"{label} must be a decimal number") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise BaselineError(f"{label} must be positive and finite")
    return parsed


def recursive_tree_sha256(root: Path) -> str:
    """Hash executable source while ignoring caches and platform metadata."""
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise BaselineError(f"source tree is missing: {root}")
    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name not in {".DS_Store"}
        and not path.name.startswith("._")
        and path.suffix in {".py", ".txt", ".md", ".sh"}
    )
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def inspect_python(python_bin: Path, modules: list[str]) -> dict[str, object]:
    # Do not resolve the venv's ``bin/python`` symlink: executing the resolved
    # base interpreter loses the virtual environment's site-packages.
    python_bin = python_bin.expanduser()
    if not python_bin.is_absolute():
        python_bin = Path.cwd() / python_bin
    if not python_bin.is_file():
        raise BaselineError(f"baseline Python is missing: {python_bin}")
    script = (
        "import importlib,json,platform; "
        f"names={modules!r}; "
        "mods={n:importlib.import_module(n) for n in names}; "
        "print(json.dumps({'version':platform.python_version(),"
        "'modules':{n:getattr(m,'__version__','unknown') for n,m in mods.items()}}))"
    )
    result = subprocess.run(
        [str(python_bin), "-c", script],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise BaselineError(f"runtime dependency check failed: {result.stderr.strip()}")
    value = json.loads(result.stdout)
    value["executable"] = str(python_bin)
    return value


def docker_image_identity(image: str) -> dict[str, object]:
    result = subprocess.run(
        ["docker", "image", "inspect", image],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise BaselineError(f"required Docker image is missing: {image}")
    rows = json.loads(result.stdout)
    if not isinstance(rows, list) or len(rows) != 1:
        raise BaselineError(f"could not inspect Docker image: {image}")
    row = rows[0]
    return {
        "reference": image,
        "id": row.get("Id"),
        "repo_digests": sorted(row.get("RepoDigests") or []),
        "architecture": row.get("Architecture"),
        "os": row.get("Os"),
    }


def validate_source_manifest(
    path: Path = DEFAULT_SOURCE_MANIFEST,
) -> dict[str, object]:
    path = path.expanduser().resolve()
    value = load_json(path)
    if not isinstance(value, dict):
        raise BaselineError("agentic baseline source manifest is not an object")
    if value.get("schema_version") != 1 or value.get("kind") != (
        "claude-szz-agentic-baseline-source-acquisition"
    ):
        raise BaselineError("unsupported agentic baseline source manifest")
    model = value.get("model_condition")
    if not isinstance(model, dict) or model.get("model_id") != MODEL:
        raise BaselineError(f"source manifest is not frozen to {MODEL}")
    if model.get("base_url") != BASE_URL or model.get("repetitions_per_sample") != 3:
        raise BaselineError("source manifest model endpoint or repetitions changed")

    sources = value.get("sources")
    if not isinstance(sources, dict):
        raise BaselineError("source manifest entries are missing")

    agentszz = sources.get("agentszz")
    if not isinstance(agentszz, dict):
        raise BaselineError("AgentSZZ source entry is missing")
    archive = Path(str(agentszz.get("local_archive_path", ""))).expanduser().resolve()
    if not archive.is_file() or sha256_file(archive) != agentszz.get("archive_sha256"):
        raise BaselineError("official AgentSZZ archive is missing or changed")
    agent_root = Path(str(agentszz.get("local_source_path", ""))).expanduser().resolve()
    if recursive_tree_sha256(agent_root) != agentszz.get("source_tree_sha256"):
        raise BaselineError("official AgentSZZ executable source tree changed")

    agentic = sources.get("agentic_szz")
    if not isinstance(agentic, dict):
        raise BaselineError("AgenticSZZ source entry is missing")
    agentic_root = Path(str(agentic.get("local_path", ""))).expanduser().resolve()
    if not (agentic_root / ".git").is_dir():
        raise BaselineError("AgenticSZZ checkout is missing")
    if run_git(agentic_root, "rev-parse", "HEAD") != agentic.get("commit"):
        raise BaselineError("AgenticSZZ checkout is at the wrong commit")
    if run_git(agentic_root, "status", "--porcelain", "--untracked-files=no"):
        raise BaselineError("AgenticSZZ tracked checkout is dirty")
    if run_git(agentic_root, "rev-parse", "HEAD^{tree}") != agentic.get("git_tree"):
        raise BaselineError("AgenticSZZ Git tree changed")

    runtimes = value.get("runtimes")
    if not isinstance(runtimes, dict):
        raise BaselineError("runtime registrations are missing")
    requirements = PROJECT_ROOT / str(
        runtimes.get("agentic_szz_requirements_path", "")
    )
    if (
        not requirements.is_file()
        or sha256_file(requirements)
        != runtimes.get("agentic_szz_requirements_sha256")
    ):
        raise BaselineError("AgenticSZZ Python requirements lock changed")
    agentszz_python = inspect_python(
        Path(str(runtimes.get("agentszz_python", ""))), ["openai", "git"]
    )
    agentic_python = inspect_python(
        Path(str(runtimes.get("agentic_szz_python", ""))),
        ["graphiti_core", "pydantic_ai", "neo4j", "git", "openai"],
    )
    docker = docker_image_identity(str(runtimes.get("neo4j_image", "")))
    expected_digest = str(runtimes.get("neo4j_repo_digest", ""))
    if expected_digest and expected_digest not in docker["repo_digests"]:
        raise BaselineError("Neo4j image digest does not match source manifest")

    return {
        "manifest_path": str(path),
        "manifest_sha256": sha256_file(path),
        "agentszz_source_path": str(agent_root),
        "agentszz_source_tree_sha256": agentszz.get("source_tree_sha256"),
        "agentic_szz_path": str(agentic_root),
        "agentic_szz_commit": agentic.get("commit"),
        "agentic_szz_git_tree": agentic.get("git_tree"),
        "agentszz_python": agentszz_python,
        "agentic_szz_python": agentic_python,
        "agentic_szz_requirements_path": str(requirements),
        "agentic_szz_requirements_sha256": sha256_file(requirements),
        "neo4j": docker,
    }


def sanitized_openrouter_environment() -> dict[str, str]:
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
        "OPENROUTER_API_KEY",
    }
    return {key: value for key, value in os.environ.items() if key in allowed}


def wait_for_neo4j(container: str, timeout_seconds: int = 90) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = subprocess.run(
            [
                "docker",
                "exec",
                container,
                "cypher-shell",
                "-u",
                "neo4j",
                "-p",
                "claudeszz-agentic-szz",
                "RETURN 1;",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise BaselineError(f"Neo4j container did not become ready: {container}")


def remove_container(container: str) -> None:
    subprocess.run(
        ["docker", "rm", "-f", "-v", container],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
