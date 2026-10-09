"""Small, standard-library helpers for the final-v2 replication package."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset/metadata"
DEFAULT_WORKSPACE = ROOT / "dataset"
CONDITION = "EXP002-BFC-MESSAGE-NEUTRALIZED-FINAL-V2-DEC017"
HEX = re.compile(r"[0-9a-f]{40}")


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def load(path):
    return json.loads(Path(path).read_bytes())


def write_new(path, data):
    path = Path(path)
    if path.exists():
        require(path.is_file() and path.read_bytes() == data,
                f"Refusing to overwrite a different file: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)


def within(path, parent):
    return Path(path).resolve().is_relative_to(Path(parent).resolve())


def git_env():
    # Do not inherit GIT_DIR, alternates, injected config or checkout filters.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_CONFIG_NOSYSTEM="1", GIT_LFS_SKIP_SMUDGE="1",
               GIT_TERMINAL_PROMPT="0", GIT_NO_REPLACE_OBJECTS="1")
    return env


def git(repo, *args, data=None, check=True, timeout=1800):
    command = ["git", "-c", "core.hooksPath=" + os.devnull,
               "-c", "core.autocrlf=false", "-c", "core.quotePath=false",
               "-c", "protocol.file.allow=always", "-c", "protocol.ext.allow=never",
               "-C", str(repo), *map(str, args)]
    result = subprocess.run(command, input=data, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=git_env(), timeout=timeout)
    if check and result.returncode:
        raise ValueError(f"Git failed in {repo}: {' '.join(map(str, args))}\n"
                         + result.stderr.decode("utf-8", errors="replace")[-2500:])
    return result


def gtext(repo, *args):
    return git(repo, *args).stdout.decode("utf-8").strip()


def remove_signatures(header):
    groups = []
    for line in header.splitlines():
        if line.startswith(b" ") and groups:
            groups[-1].append(line)
        else:
            groups.append([line])
    return b"\n".join(line for group in groups
                      if group[0].split(b" ", 1)[0] not in {b"gpgsig", b"gpgsig-sha256"}
                      for line in group)


def commit_parts(raw):
    header, message = raw.split(b"\n\n", 1)
    trees = [line[5:].decode("ascii") for line in header.splitlines() if line.startswith(b"tree ")]
    parents = [line[7:].decode("ascii") for line in header.splitlines() if line.startswith(b"parent ")]
    require(len(trees) == 1, "Malformed commit tree header")
    return header, message, trees[0], parents


def git_commit_hash(raw):
    return hashlib.sha1(b"commit " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def read_package(data_dir=DATA):
    data_dir = Path(data_dir)
    manifest = load(data_dir / "manifest.json")
    for rel, digest in manifest["files"].items():
        path = data_dir / rel
        require(within(path, data_dir), "Package path escapes data directory")
        require(sha(path.read_bytes()) == digest, f"Package checksum mismatch: {rel}")
    dataset = load(data_dir / "cases.json")
    messages = load(data_dir / "commit-messages.json")
    require(dataset["condition_id"] == messages["condition_id"] == CONDITION,
            "Unexpected input condition")
    cases = dataset["cases"]
    by_id = {str(row["id"]): row for row in cases}
    message_map = {str(row["id"]): row for row in messages["cases"]}
    require(len(cases) == len(by_id) == manifest["case_count"] == 79, "Expected 79 unique cases")
    require(set(by_id) == set(message_map), "Dataset and message IDs differ")
    for sid, case in by_id.items():
        require(sid.isdigit() and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", case["repository"]),
                "Unsafe case ID or repository name")
        require(all(part not in {".", ".."} for part in case["repository"].split("/")), "Unsafe repository path")
        require(re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", case["clone_url"]),
                "Unexpected clone URL")
        require(all(HEX.fullmatch(v) for v in [case["bfc"], case["synthetic_bfc"], *case["oracle_bics"]]),
                "Expected full SHA-1 commit hashes")
        msg = message_map[sid]
        require(msg["bfc"] == case["bfc"] and msg["synthetic_bfc"] == case["synthetic_bfc"],
                f"Message identity differs: {sid}")
        for key in ("original", "modified"):
            require(sha(msg[key + "_message"].encode("utf-8")) == msg[key + "_message_sha256"],
                    f"Message bytes differ: {sid}/{key}")
        prompt = data_dir / case["prompt_path"]
        require(within(prompt, data_dir) and sha(prompt.read_bytes()) == case["prompt_sha256"],
                f"Prompt checksum differs: {sid}")
    require(sum(c["disagreement"] for c in cases) == manifest["disagreement_count"] == 22,
            "Expected the frozen 22-case disagreement cohort")
    return dataset, message_map, manifest


def select_cases(dataset, subset, ids=None):
    require(subset in {"all", "disagreement"}, "Unknown subset")
    selected = [c for c in dataset["cases"] if subset == "all" or c["disagreement"]]
    if ids:
        wanted = set(map(str, ids))
        require(wanted <= {str(c["id"]) for c in selected}, "ID is not in the selected subset")
        require(len(wanted) == len(ids), "Duplicate --ids")
        selected = [c for c in selected if str(c["id"]) in wanted]
    require(selected, "Empty selection")
    return sorted(selected, key=lambda c: int(c["id"]))


def subject_path(workspace, case, case_sensitive_root=None):
    if case.get("requires_case_sensitive_filesystem") and case_sensitive_root:
        return Path(case_sensitive_root).resolve() / str(case["id"]) / "repo"
    return Path(workspace).resolve() / "prepared" / str(case["id"]) / "repo"


def validate_subject(repo, case, message, *, deep=True):
    repo = Path(repo)
    require(repo.is_dir() and (repo / ".git").is_dir() and not (repo / ".git").is_symlink(),
            f"Expected independent subject repository: {repo}")
    raw = git(repo, "cat-file", "commit", "HEAD").stdout
    header, body, tree, parents = commit_parts(raw)
    require(git_commit_hash(raw) == case["synthetic_bfc"], "Synthetic BFC hash differs")
    require(sha(raw) == case["synthetic_commit_sha256"], "Synthetic commit bytes differ")
    require(tree == case["tree"] and parents == case["parents"], "Code tree or parents differ")
    require(body == message["modified_message"].encode("utf-8"), "Modified message differs")
    require(not gtext(repo, "remote"), "Subject still has a remote")
    require(not (repo / ".git/objects/info/alternates").exists(), "Subject has object alternates")
    require(not (repo / ".git/objects/info/http-alternates").exists(), "Subject has HTTP alternates")
    require(gtext(repo, "rev-parse", "--is-shallow-repository") == "false", "Subject is shallow")
    require(gtext(repo, "symbolic-ref", "HEAD") == "refs/heads/subject-bfc", "Unexpected HEAD ref")
    require(gtext(repo, "for-each-ref", "--format=%(refname):%(objectname)") ==
            "refs/heads/subject-bfc:" + case["synthetic_bfc"], "Extra or changed Git refs")
    require(not git(repo, "status", "--porcelain=v1", "--untracked-files=all", "--ignored").stdout,
            "Subject has changed, untracked or ignored files; nothing will be overwritten")
    require(git(repo, "cat-file", "-e", case["bfc"], check=False).returncode != 0,
            "Original answer-bearing BFC is still present")
    count = int(gtext(repo, "rev-list", "--count", "HEAD"))
    require(count == case["reachable_commit_count"], "Ancestor count differs")
    if deep:
        reachable = set(git(repo, "rev-list", "--objects", "--no-object-names", "HEAD").stdout.splitlines())
        inventory = set(git(repo, "cat-file", "--batch-all-objects", "--batch-check=%(objectname)").stdout.splitlines())
        require(inventory == reachable, "Extra unreachable Git objects remain")
    return {"valid": True, "synthetic_bfc": case["synthetic_bfc"],
            "reachable_commit_count": count, "all_objects_reachable_checked": deep}
