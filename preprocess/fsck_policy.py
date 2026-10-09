"""Narrow, user-approved exception for two inherited case-3459 URL defects.

The general-purpose scrubber is unchanged. Every unfiltered diagnostic must
match the audited source defects before Git's object-specific skipList is used.
No repository configuration, tracked file, or source object is modified.
"""
from contextlib import contextmanager
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SOURCE = WORKSPACE / "case-sensitive/bfc-message-neutralized-final-v1/3459/repo"
BUNDLE = WORKSPACE / "case-sensitive/commit-message-free-final-v2-20260925/3459"
SKIP_LIST = ROOT / "preprocess/fsck-3459.skipList"
OBJECTS = (
    "5dcb758eea898b3326de85f2af9df58603e2f342",
    "e89e5b05c0df41d886cc97c44e38f0d0de25391e",
)
URL = "https://github.com:georchestra/geofence.git"
FSCK_ARGS = ("fsck", "--full", "--strict", "--no-reflogs")
APPROVAL = {"sample_id": "3459", "approved_date": "2026-09-26",
            "policy": "only-two-inherited-gitmodulesUrl-blobs", "objects": list(OBJECTS)}


def validate_diagnostics(result):
    expected = sorted(f"error in blob {oid}: gitmodulesUrl: disallowed submodule url: {URL}"
                      for oid in OBJECTS)
    # Git uses different failure bits for loose (1) and packed (4) objects.
    if (result.returncode not in (1, 4) or result.stdout
            or sorted(result.stderr.decode("utf-8", errors="strict").splitlines()) != expected):
        raise ValueError("fsck diagnostics differ from the two approved inherited URL defects")


def pins():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__).resolve(), SKIP_LIST)}


def verify_prepared(source, repo, sample_id, git):
    """Check a prepared ancestry-only input with the same two-object exception."""
    if str(sample_id) != "3459":
        raise ValueError("unapproved prepared-input exception")
    if SKIP_LIST.read_text() != "".join(oid + "\n" for oid in OBJECTS):
        raise ValueError("fsck skipList differs from the two approved objects")
    result = git(repo, *FSCK_ARGS, check=False)
    validate_diagnostics(result)
    for oid in OBJECTS:
        raw = git(source, "cat-file", "blob", oid).stdout
        if raw != git(repo, "cat-file", "blob", oid).stdout:
            raise ValueError("approved source/output blob bytes differ")
        computed = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if computed != oid or URL.encode() not in raw:
            raise ValueError("approved blob identity or URL mismatch")
    checked = git(repo, "-c", f"fsck.skipList={SKIP_LIST}", *FSCK_ARGS, check=False)
    if checked.returncode or checked.stdout or checked.stderr:
        raise ValueError("object-scoped fsck still reports a defect")
    return {"approval": APPROVAL, "strict_fsck_with_object_skiplist_passed": True}


@contextmanager
def scoped_fsck(scrubber, sample_id, bundle, source, approval):
    """Yield an audit record; intercept only this output's strict fsck call."""
    if (str(sample_id) != "3459" or Path(bundle).resolve() != BUNDLE.resolve()
            or Path(source).resolve() != SOURCE.resolve() or approval != APPROVAL):
        raise ValueError("unapproved fsck exception scope")
    if SKIP_LIST.read_text() != "".join(oid + "\n" for oid in OBJECTS):
        raise ValueError("fsck skipList differs from the two approved objects")
    original = scrubber.git
    audit = {"approval": APPROVAL, "policy_pins": pins(), "checks": []}

    def git(repo, *args, data=None, check=True):
        if Path(repo).resolve() != (BUNDLE / "repo").resolve() or args != FSCK_ARGS:
            return original(repo, *args, data=data, check=check)
        if data is not None:
            raise ValueError("unexpected fsck input")
        source_check = original(SOURCE, *FSCK_ARGS, check=False)
        output_check = original(repo, *FSCK_ARGS, check=False)
        validate_diagnostics(source_check)
        validate_diagnostics(output_check)
        blobs = {}
        for oid in OBJECTS:
            raw = original(SOURCE, "cat-file", "blob", oid)
            if raw != original(repo, "cat-file", "blob", oid):
                raise ValueError("approved source/output blob bytes differ")
            computed = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if computed != oid or URL.encode() not in raw:
                raise ValueError("approved blob identity or URL mismatch")
            blobs[oid] = hashlib.sha256(raw).hexdigest()
        result = original(repo, "-c", f"fsck.skipList={SKIP_LIST}", *FSCK_ARGS, check=False)
        if result.returncode != 0 or result.stdout or result.stderr:
            raise ValueError("object-scoped fsck still reports a defect")
        audit["checks"].append({
            "unfiltered_source_exit_code": source_check.returncode,
            "unfiltered_output_exit_code": output_check.returncode,
            "unfiltered_diagnostics": output_check.stderr.decode().splitlines(),
            "source_output_blob_sha256": blobs,
            "strict_fsck_with_object_skiplist_passed": True,
            "repository_config_modified": False,
        })
        return result.stdout if check else result

    scrubber.git = git
    try:
        yield audit
        if not audit["checks"]:
            raise ValueError("scoped verification did not invoke strict fsck")
    finally:
        scrubber.git = original
