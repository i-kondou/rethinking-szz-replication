"""ABC v5: single-commit patch display is inspection, not history search.

The frozen v4 engine remains unchanged. Only the display-option allowlist for
one explicit revision with a one-commit limit is extended. Path/query selectors
remain history search, even when their saved output happens to match that revision.
"""
from __future__ import annotations

import abc_rules_only_v4 as base

Context = base.Context
syntax = base.syntax
DISPLAY = base.DISPLAY | {'-p', '--patch', '-u'}


def single_log(args, bindings):
    """Accept only an explicit single revision, limit one, and display options.

    Parse option values in place: a format value that happens to be '-p' must
    not be removed or mistaken for a patch flag. Unknown/query/path options are
    deliberately rejected, retaining the v4 history-search fallback.
    """
    caps, revisions, i = [], [], 0
    while i < len(args):
        arg = args[i]
        if arg in {'-1', '-n1', '--max-count=1'}:
            caps.append(1)
        elif arg in {'-n', '--max-count'} and args[i+1:i+2] == ['1']:
            caps.append(1)
            i += 1
        elif arg in {'--format', '--pretty', '--date'} and i+1 < len(args):
            i += 1
        elif arg.startswith(('--format=', '--pretty=', '--date=')) or arg in DISPLAY:
            pass
        elif base.REV.fullmatch(arg):
            revisions.append(arg)
        elif (base.BOUND.fullmatch(arg) and arg in bindings
              and all(base.REV.fullmatch(v) for v in bindings[arg])):
            revisions.append(arg)
        else:
            return None
        i += 1
    return revisions[0] if caps and len(revisions) == 1 else None


class Engine(base.Engine):
    def git(self, args, fragment, cwd, bindings):
        sub, opts, _ = syntax.git_parts(['git', *args])
        if sub == 'log' and (rev := single_log(opts, bindings)):
            target = self.target_b([rev], bindings)
            return base.operation('B', 'B.single_commit_log', fragment, target,
                                  [] if target else ['commit_target_unresolved'])
        return super().git(args, fragment, cwd, bindings)
