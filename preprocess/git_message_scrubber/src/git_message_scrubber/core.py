"""Rewrite object messages into a fresh store; never copy original commit objects.

Trees and blobs travel through a non-thin Git pack. Commit/tag objects are read
as bytes, rewritten, and stored in Git's standard compressed loose-object format.
No checkout, filter, hook, fetch, or model operation runs against the source.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zlib

from . import __version__


class ScrubError(RuntimeError):
    pass


def environment():
    # Do not inherit GIT_DIR, GIT_WORK_TREE, injected -c settings, alternates, etc.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1",
               GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", LC_ALL="C")
    return env


def command(repo, *args):
    return ["git", "-c", "safe.directory=*", "-c", "core.hooksPath=/dev/null",
            "-c", "core.fsmonitor=false", "-c", "gc.auto=0", "-c",
            "protocol.allow=never", "-C", str(repo), *args]


def git(repo, *args, data=None, check=True):
    result = subprocess.run(command(repo, *args), input=data, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=environment())
    if check and result.returncode:
        raise ScrubError(f"git {' '.join(args[:3])}: " + result.stderr.decode(errors="replace").strip())
    return result.stdout if check else result


def resolve(repo, revision):
    if revision.startswith("-") or "\n" in revision or "\0" in revision:
        raise ScrubError("Invalid revision")
    return git(repo, "rev-parse", "--verify", "--end-of-options",
               revision + "^{commit}").decode().strip()


def refs(repo):
    rows = git(repo, "for-each-ref", "--format=%(refname)%00%(objectname)")
    return dict(row.decode().split("\0") for row in rows.splitlines())


def heads(repo):
    oid = git(repo, "rev-parse", "--verify", "HEAD", check=False)
    sym = git(repo, "symbolic-ref", "-q", "HEAD", check=False)
    return {"oid": oid.stdout.decode().strip() if oid.returncode == 0 else None,
            "symbolic": sym.stdout.decode().strip() if sym.returncode == 0 else None}


def lines_input(values):
    return ("\n".join(values) + "\n").encode("ascii")


def split_object(raw):
    try:
        header, message = raw.split(b"\n\n", 1)
    except ValueError as exc:
        raise ScrubError("Malformed object without header/message separator") from exc
    groups = []
    for line in header.split(b"\n"):
        if line.startswith(b" ") and groups:
            groups[-1] += b"\n" + line
        else:
            groups.append(line)
    return groups, message


def field(groups, name):
    vals = [g[len(name) + 1:] for g in groups if g.startswith(name + b" ")]
    if len(vals) != 1:
        raise ScrubError(f"Expected exactly one {name!r} header")
    return vals[0]


REMOVED_HEADERS = {b"gpgsig", b"gpgsig-sha256", b"mergetag"}
IDENTITY_HEADER = b"git-message-scrubber-id"
COLLISION_POLICIES = ("error", "identity-header")


def commit_bytes(raw, mapping, keep=False):
    groups, message = split_object(raw)
    out = []
    for group in groups:
        key = group.split(b" ", 1)[0]
        if key in REMOVED_HEADERS:
            continue
        if key == b"parent":
            old = group[7:].decode("ascii")
            if old not in mapping:
                raise ScrubError(f"Parent absent from selected history: {old}")
            group = b"parent " + mapping[old].encode("ascii")
        out.append(group)
    return b"\n".join(out) + b"\n\n" + (message if keep else b"")


def object_id(algorithm, kind, raw):
    return hashlib.new(algorithm, kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def distinct_commit(raw, mapping, keep, seen, algorithm, collision_policy):
    """Add a local integer header only when the transformed ID already exists.

    The integer contains no old ID, message, label, timestamp or global rank.
    Selection is replayed by verify; it never merges nodes or modifies dates.
    """
    if collision_policy not in COLLISION_POLICIES:
        raise ScrubError("Unsupported collision policy")
    changed = commit_bytes(raw, mapping, keep)
    oid = object_id(algorithm, "commit", changed)
    if oid not in seen:
        return changed, oid, None
    if collision_policy == "error":
        raise ScrubError("Message removal coalesces distinct commits. Aborting instead of changing graph/metadata.")
    headers, message = changed.split(b"\n\n", 1)
    if any(g.split(b" ", 1)[0] == IDENTITY_HEADER for g in split_object(changed)[0]):
        raise ScrubError("Colliding source commit already has the reserved identity header")
    nonce = 1
    while True:
        disambiguated = headers + b"\n" + IDENTITY_HEADER + b" " + str(nonce).encode() + b"\n\n" + message
        oid = object_id(algorithm, "commit", disambiguated)
        if oid not in seen:
            return disambiguated, oid, nonce
        nonce += 1


def tag_bytes(raw, target):
    groups, _ = split_object(raw)
    # Annotation bodies, including signatures, are erased too. Tag names remain.
    return b"\n".join(b"object " + target.encode() if g.startswith(b"object ") else g
                       for g in groups) + b"\n\n"


class ObjectReader:
    def __init__(self, repo):
        self.errors = tempfile.TemporaryFile()
        self.proc = subprocess.Popen(command(repo, "cat-file", "--batch"),
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self.errors, env=environment())

    def get(self, oid):
        self.proc.stdin.write(oid.encode("ascii") + b"\n")
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().split()
        if len(header) != 3 or not header[2].isdigit():
            raise ScrubError(f"Cannot read Git object {oid}: {header!r}")
        size = int(header[2])
        data = self.proc.stdout.read(size)
        if len(data) != size or self.proc.stdout.read(1) != b"\n":
            raise ScrubError(f"Truncated Git object {oid}")
        return header[1].decode("ascii"), data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.proc.stdin.close()
        self.proc.stdout.close()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.errors.close()


def object_store(repo):
    return Path(git(repo, "rev-parse", "--absolute-git-dir").decode().strip())


def write_object(gitdir, algorithm, kind, raw):
    content = kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw
    oid = hashlib.new(algorithm, content).hexdigest()
    target = gitdir / "objects" / oid[:2] / oid[2:]
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        with target.open("xb") as handle:
            handle.write(zlib.compress(content))
    return oid


def inspect(source, revision=None, keep_messages=()):
    source = Path(source).resolve(strict=True)
    if git(source, "rev-parse", "--is-bare-repository").strip() == b"false":
        source = Path(git(source, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    gd = object_store(source)
    common = Path(git(source, "rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip())
    if git(source, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise ScrubError("Shallow repositories are unsupported; obtain full history first")
    if (common / "info" / "grafts").exists():
        raise ScrubError("Legacy grafts are unsupported")
    cfg = git(source, "config", "--get-regexp", r"^(extensions\.partialclone|remote\..*\.promisor)$", check=False)
    if cfg.returncode == 0:
        raise ScrubError("Partial/promisor clones are unsupported; materialize objects first")
    all_refs = refs(source)
    if any(r.startswith("refs/replace/") for r in all_refs):
        raise ScrubError("Replace refs are unsupported; materialize the intended history first")
    head = heads(source)
    if revision:
        chosen = {"refs/heads/sanitized": resolve(source, revision)}
        output_head = {"symbolic": "refs/heads/sanitized", "oid": chosen["refs/heads/sanitized"]}
    else:
        chosen = {r: o for r, o in all_refs.items() if r.startswith(("refs/heads/", "refs/tags/"))}
        output_head = head.copy()
    roots = sorted(set(chosen.values()) | ({output_head["oid"]} if output_head["oid"] else set()))
    if not roots:
        raise ScrubError("No committed history or supported refs to export")
    commits = git(source, "rev-list", "--topo-order", "--reverse", "--stdin", data=lines_input(roots)).decode().splitlines()
    keep = sorted({resolve(source, r) for r in keep_messages})
    if not set(keep) <= set(commits):
        raise ScrubError("A --keep-message revision is outside the selected history")
    algorithm = git(source, "rev-parse", "--show-object-format").decode().strip()
    if algorithm not in {"sha1", "sha256"}:
        raise ScrubError(f"Unsupported Git object format: {algorithm}")
    return {"source": str(source), "source_git_dir": str(gd), "source_common_dir": str(common),
            "algorithm": algorithm, "source_refs": all_refs, "source_head": head,
            "refs": chosen, "head": output_head, "roots": roots, "commits": commits,
            "keep_messages": keep, "revision": revision,
            "excluded_refs": sorted(set(all_refs) - set(chosen))}


def transfer_files(source, target, roots):
    objects = git(source, "rev-list", "--objects", "--no-object-names", "--stdin", data=lines_input(roots))
    checks = git(source, "cat-file", "--batch-check=%(objectname) %(objecttype)", data=objects)
    selected = []
    for row in checks.splitlines():
        oid, kind = row.split()
        if kind == b"missing":
            raise ScrubError(f"Missing object {oid.decode()}")
        if kind in {b"blob", b"tree"}:
            selected.append(oid)
    # Disk-backed input and stderr avoid large pipe writes or stderr deadlocks.
    with tempfile.TemporaryFile() as ids, tempfile.TemporaryFile() as errors:
        ids.write(b"\n".join(selected) + b"\n")
        ids.seek(0)
        exporter = subprocess.Popen(command(source, "pack-objects", "--stdout", "--no-reuse-delta"),
                                    stdin=ids, stdout=subprocess.PIPE, stderr=errors, env=environment())
        try:
            importer = subprocess.run(command(target, "index-pack", "--stdin"), stdin=exporter.stdout,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment())
            exporter.stdout.close()
            code = exporter.wait()
            if code or importer.returncode:
                errors.seek(0)
                raise ScrubError("Object transfer failed: " + (errors.read() + importer.stderr).decode(errors="replace"))
        finally:
            if exporter.poll() is None:
                exporter.kill()
                exporter.wait()
    return len(selected)


def ensure_outside(output, plan):
    if output.exists() or output.is_symlink():
        raise ScrubError(f"Output already exists (never overwritten): {output}")
    for name in ("source", "source_git_dir", "source_common_dir"):
        loc = Path(plan[name])
        if output == loc or output.is_relative_to(loc) or loc.is_relative_to(output):
            raise ScrubError("Source and output must not contain one another")


def source_unchanged(plan):
    if refs(plan["source"]) != plan["source_refs"] or heads(plan["source"]) != plan["source_head"]:
        raise ScrubError("Source refs/HEAD changed while processing; retry with a stable source")


def create(source, output, *, revision=None, keep_messages=(), bare=False, collision_policy="error"):
    if collision_policy not in COLLISION_POLICIES:
        raise ScrubError("Unsupported collision policy")
    plan = inspect(source, revision, keep_messages)
    source = Path(plan["source"])
    output = Path(output).absolute()
    # Resolve parent symlinks before checking containment. Never follow an output symlink.
    output = output.parent.resolve() / output.name
    ensure_outside(output, plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()  # Exclusive reservation; no clobber even if another process races.
    owned_inode = output.stat().st_ino
    try:
        (output / "INCOMPLETE").write_text("Do not use until manifest.json reports complete.\n")
        repo = output / "repo"
        repo.mkdir()
        meta = output / "metadata"
        meta.mkdir()
        init = ["init", "--quiet", "--template=", "--initial-branch=sanitized",
                f"--object-format={plan['algorithm']}"]
        git(repo, *init, *(["--bare"] if bare else []))
        git(repo, "config", "core.logAllRefUpdates", "false")
        gd = object_store(repo)
        file_count = transfer_files(source, repo, plan["roots"])
        mapping = {}
        seen = set()
        identity_headers = {}
        removed_headers = {}
        keep = set(plan["keep_messages"])
        with ObjectReader(source) as reader:
            for oid in plan["commits"]:
                kind, raw = reader.get(oid)
                if kind != "commit":
                    raise ScrubError(f"Expected commit: {oid}")
                for group in split_object(raw)[0]:
                    key = group.split(b" ", 1)[0]
                    if key in REMOVED_HEADERS:
                        label = key.decode()
                        removed_headers[label] = removed_headers.get(label, 0) + 1
                changed, new, nonce = distinct_commit(raw, mapping, oid in keep, seen,
                                                     plan["algorithm"], collision_policy)
                if write_object(gd, plan["algorithm"], "commit", changed) != new:
                    raise ScrubError("Written commit identity mismatch")
                if nonce is not None:
                    identity_headers[oid] = nonce
                seen.add(new)
                mapping[oid] = new
            tag_map = {}

            def mapped(oid):
                if oid in mapping:
                    return mapping[oid]
                if oid in tag_map:
                    return tag_map[oid]
                kind, raw = reader.get(oid)
                if kind in {"blob", "tree"}:
                    return oid
                if kind != "tag":
                    raise ScrubError(f"Unmapped ref target: {oid}")
                target = mapped(field(split_object(raw)[0], b"object").decode())
                tag_map[oid] = write_object(gd, plan["algorithm"], "tag", tag_bytes(raw, target))
                return tag_map[oid]

            new_refs = {name: mapped(oid) for name, oid in plan["refs"].items()}
        for name, oid in new_refs.items():
            git(repo, "update-ref", name, oid)
        if plan["head"]["symbolic"]:
            git(repo, "symbolic-ref", "HEAD", plan["head"]["symbolic"])
        elif plan["head"]["oid"]:
            git(repo, "update-ref", "--no-deref", "HEAD", mapping[plan["head"]["oid"]])
        # read-tree avoids checkout hooks and source-local attributes/filter config.
        if not bare and plan["head"]["oid"]:
            git(repo, "read-tree", "--reset", "-u", "HEAD")
        with (meta / "commit-map.tsv").open("x") as handle:
            handle.write("old\tnew\n")
            for old, new in mapping.items():
                handle.write(f"{old}\t{new}\n")
        with (meta / "tag-map.tsv").open("x") as handle:
            handle.write("old\tnew\n")
            for old, new in tag_map.items():
                handle.write(f"{old}\t{new}\n")
        source_unchanged(plan)
        manifest = {"schema_version": 1, "tool_version": __version__, "state": "verifying",
                    "git_version": git(repo, "--version").decode().strip(),
                    "source": str(source), "object_format": plan["algorithm"],
                    "scope": {"revision": revision, "roots": plan["roots"], "source_refs": plan["refs"],
                              "source_head": plan["head"], "excluded_refs": plan["excluded_refs"]},
                    "policy": {"commit_messages": "empty", "keep_messages": plan["keep_messages"],
                               "tag_messages": "empty", "removed_commit_headers": sorted(k.decode() for k in REMOVED_HEADERS),
                               "commit_identity_collision": collision_policy},
                    "identity_headers": identity_headers,
                    "output_refs": new_refs, "bare": bare,
                    "counts": {"commits": len(mapping), "annotated_tags": len(tag_map),
                               "trees_and_blobs": file_count, "removed_headers": removed_headers,
                               "identity_headers_added": len(identity_headers)},
                    "map_sha256": hashlib.sha256((meta / "commit-map.tsv").read_bytes()).hexdigest(),
                    "tag_map_sha256": hashlib.sha256((meta / "tag-map.tsv").read_bytes()).hexdigest()}
        (meta / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        report = verify(output, source, allow_incomplete=True)
        manifest["state"] = "complete"
        manifest["verification"] = report
        (meta / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (output / "INCOMPLETE").unlink()
        return manifest
    except BaseException:
        # Only remove the exact output directory reserved by this invocation.
        if not output.is_symlink() and output.exists() and output.stat().st_ino == owned_inode:
            shutil.rmtree(output)
        raise


def read_map(path, checksum):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != checksum:
        raise ScrubError(f"Map checksum mismatch: {path.name}")
    rows = data.decode().splitlines()
    if not rows or rows[0] != "old\tnew":
        raise ScrubError("Invalid map header")
    mapping = dict(row.split("\t") for row in rows[1:])
    if len(mapping) != len(rows) - 1 or len(set(mapping.values())) != len(mapping):
        raise ScrubError("Map is not one-to-one")
    return mapping


def verify(bundle, source, *, allow_incomplete=False):
    bundle, source = Path(bundle).resolve(), Path(source).resolve()
    repo, meta = bundle / "repo", bundle / "metadata"
    manifest = json.loads((meta / "manifest.json").read_text())
    if manifest.get("schema_version") != 1:
        raise ScrubError("Unsupported manifest schema")
    if not allow_incomplete and (manifest.get("state") != "complete" or (bundle / "INCOMPLETE").exists()):
        raise ScrubError("Incomplete output bundle")
    mapping = read_map(meta / "commit-map.tsv", manifest["map_sha256"])
    tag_map = read_map(meta / "tag-map.tsv", manifest["tag_map_sha256"])
    if refs(repo) != manifest["output_refs"]:
        raise ScrubError("Unexpected or changed output refs")
    expected_refs = {name: mapping.get(old, tag_map.get(old, old))
                     for name, old in manifest["scope"]["source_refs"].items()}
    if manifest["output_refs"] != expected_refs:
        raise ScrubError("Output refs do not match the mapped source refs")
    expected_head = manifest["scope"]["source_head"]
    expected_head = {"symbolic": expected_head["symbolic"], "oid": mapping.get(expected_head["oid"])}
    if heads(repo) != expected_head:
        raise ScrubError("Output HEAD mismatch")
    source_commits = set(git(source, "rev-list", "--stdin", data=lines_input(manifest["scope"]["roots"])).decode().splitlines())
    if source_commits != set(mapping):
        raise ScrubError("Commit map does not cover the selected source history")
    keep = set(manifest["policy"]["keep_messages"])
    if not keep <= set(mapping):
        raise ScrubError("Message exceptions are outside the selected history")
    if git(repo, "rev-parse", "--show-object-format").decode().strip() != manifest["object_format"]:
        raise ScrubError("Object format mismatch")
    if (git(repo, "rev-parse", "--is-bare-repository").strip() == b"true") != manifest["bare"]:
        raise ScrubError("Bare/worktree mode mismatch")
    collision_policy = manifest["policy"].get("commit_identity_collision", "error")
    if collision_policy not in COLLISION_POLICIES:
        raise ScrubError("Unsupported collision policy")
    replay_mapping, seen, identity_headers = {}, set(), {}
    with ObjectReader(source) as old_reader, ObjectReader(repo) as new_reader:
        for old, new in mapping.items():
            kind, before = old_reader.get(old)
            new_kind, after = new_reader.get(new)
            expected, expected_id, nonce = distinct_commit(before, replay_mapping, old in keep, seen,
                                                          manifest["object_format"], collision_policy)
            if kind != "commit" or new_kind != "commit" or after != expected or new != expected_id:
                raise ScrubError(f"Commit content / tree / metadata / parent mismatch: {old}")
            replay_mapping[old] = new
            seen.add(new)
            if nonce is not None:
                identity_headers[old] = nonce
        for old, new in tag_map.items():
            kind, before = old_reader.get(old)
            new_kind, after = new_reader.get(new)
            old_target = field(split_object(before)[0], b"object").decode()
            target = mapping.get(old_target, tag_map.get(old_target, old_target))
            if kind != "tag" or new_kind != "tag" or after != tag_bytes(before, target):
                raise ScrubError(f"Tag mismatch: {old}")
    if identity_headers != manifest.get("identity_headers", {}) or len(identity_headers) != manifest["counts"].get("identity_headers_added", 0):
        raise ScrubError("Identity header audit mismatch")
    gd = object_store(repo)
    if (gd / "objects" / "info" / "alternates").exists() or (gd / "logs").exists():
        raise ScrubError("Alternates/reflogs could expose original history")
    if git(repo, "remote").strip():
        raise ScrubError("Output must have no remote")
    for name in ("shallow", "info/grafts", "filter-repo", "FETCH_HEAD", "ORIG_HEAD"):
        if (gd / name).exists():
            raise ScrubError(f"Unexpected Git metadata: {name}")
    objects = git(repo, "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)")
    actual_commits, actual_tags, all_objects = set(), set(), set()
    for row in objects.decode().splitlines():
        oid, kind = row.split()
        all_objects.add(oid)
        if kind == "commit": actual_commits.add(oid)
        if kind == "tag": actual_tags.add(oid)
    if actual_commits != set(mapping.values()) or actual_tags != set(tag_map.values()):
        raise ScrubError("Extra/missing commit or tag objects (possibly original messages)")
    roots = set(manifest["output_refs"].values()) | ({expected_head["oid"]} if expected_head["oid"] else set())
    reachable = set(git(repo, "rev-list", "--objects", "--no-object-names", "--stdin", data=lines_input(sorted(roots))).decode().splitlines())
    if reachable != all_objects:
        raise ScrubError("Unreachable or missing output objects")
    git(repo, "fsck", "--full", "--strict", "--no-reflogs")
    if not manifest["bare"] and expected_head["oid"]:
        git(repo, "diff-index", "--quiet", "HEAD", "--")
        if git(repo, "ls-files", "--others", "--exclude-standard").strip():
            raise ScrubError("Unexpected untracked files in output worktree")
    return {"passed": True, "commits_checked": len(mapping), "tags_checked": len(tag_map),
            "original_objects_absent_unless_identical": True, "trees_metadata_parents_preserved": True,
            "identity_headers_added": len(identity_headers)}
