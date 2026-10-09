import argparse
import json
import sys

from . import __version__
from .core import COLLISION_POLICIES, ScrubError, create, inspect, verify


def parser():
    p = argparse.ArgumentParser(description="Build isolated Git repositories without commit messages.")
    p.add_argument("--version", action="version", version=__version__)
    commands = p.add_subparsers(dest="action", required=True)
    for name in ("create", "plan"):
        sub = commands.add_parser(name, help="Create a verified bundle" if name == "create" else "Inspect scope without writing")
        sub.add_argument("--source", required=True, help="Local Git repository; never modified")
        sub.add_argument("--revision", help="Export this commit and all ancestors only, as branch sanitized")
        sub.add_argument("--keep-message", action="append", default=[], metavar="REV", help="Keep one commit's message verbatim; repeatable")
        sub.add_argument("--collision-policy", choices=COLLISION_POLICIES, default="error",
                         help="Default: stop; identity-header preserves distinct commits with an opaque header only when needed")
        if name == "create":
            sub.add_argument("--output", required=True, help="New bundle directory containing repo/ and metadata/")
            sub.add_argument("--bare", action="store_true", help="Do not check out files")
    sub = commands.add_parser("verify", help="Verify against original objects; read-only")
    sub.add_argument("bundle")
    sub.add_argument("--source", required=True, help="Original repository, possibly relocated")
    return p


def main(argv=None):
    a = parser().parse_args(argv)
    try:
        if a.action == "create":
            result = create(a.source, a.output, revision=a.revision, keep_messages=a.keep_message,
                            bare=a.bare, collision_policy=a.collision_policy)
        elif a.action == "plan":
            result = inspect(a.source, a.revision, a.keep_message)
            result["commit_count"] = len(result.pop("commits"))
            result.pop("source_refs")
            result["collision_policy"] = a.collision_policy
            result["collision_analysis_performed"] = False
        else:
            result = verify(a.bundle, a.source)
        print(json.dumps(result, indent=2))
        return 0
    except (ScrubError, OSError, ValueError, KeyError, RecursionError) as exc:
        print(f"git-message-scrubber: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
