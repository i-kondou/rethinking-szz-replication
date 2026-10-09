"""General, bounded ABC rules. No sample IDs, previous labels or model calls.

This is a static requested-activity classifier, not a shell interpreter.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import re
import shlex
import subprocess
from functools import lru_cache

import analyze_final_v2_abc_coverage as syntax

REV = re.compile(r'(?:[0-9a-fA-F]{6,40}|HEAD)(?:[~^][0-9]*)*')
BOUND = re.compile(r'__BOUND_[A-Za-z_]\w*__')
DISPLAY = {'--oneline', '--no-patch', '-s', '--decorate', '--no-decorate',
           '--abbrev-commit', '--no-abbrev-commit', '--parents'}
META_GIT = {'status', 'rev-parse', 'branch', 'ls-tree', 'ls-files', 'merge-base',
            'rev-list', 'config', 'replace'}
READERS = syntax.READERS
FILTERS = syntax.FILTERS


class Context(syntax.Context):
    @lru_cache(maxsize=None)
    def git(self, *args):
        if args[0] not in {'rev-list', 'diff', 'rev-parse', 'cat-file', 'ls-tree'}:
            raise ValueError('non_readonly_git_probe')
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1',
                   GIT_OPTIONAL_LOCKS='0', GIT_NO_LAZY_FETCH='1')
        result = subprocess.run(['git', '--no-replace-objects', '-c', 'core.fsmonitor=false',
                                 '-C', str(self.repo), *args], capture_output=True, text=True,
                                env=env, timeout=20)
        return result.stdout if result.returncode == 0 else ''

    def resolve(self, value, stable=True):
        if not stable or not REV.fullmatch(value):
            return None
        if value == self.source:
            return self.fix
        value = re.sub(r'^HEAD(?=$|[~^])', self.fix, value)
        resolved = self.git('rev-parse', '--verify', '--end-of-options', value+'^{commit}').strip()
        return resolved if re.fullmatch(r'[0-9a-f]{40}', resolved) else None


def operation(activity, rule, fragment, target=None, reasons=(), **extra):
    return dict(activity=activity, target=target, rule=rule, command_fragment=fragment,
                reasons=list(reasons), **extra)


def split(command):
    # Protect parameter braces, not arbitrary shell groups. No expansion/evaluation.
    params = {}
    def protect(match):
        key = f'__PARAM_{len(params)}__'
        params[key] = match.group(0)
        return key
    safe = re.sub(r'\$\{[^{}\n]+\}', protect, command)
    groups, conditional = syntax.split_shell(safe)
    for group in groups:
        for i, stage in enumerate(group):
            for key, value in params.items():
                stage = stage.replace(key, value)
            group[i] = stage
    return groups, conditional


def reader_files(exe, args):
    """Roles for bounded grep/rg/sed/awk/cat/head/tail options; no pattern-as-file."""
    files, i, pattern = [], 0, exe not in {'grep', 'rg', 'sed', 'awk'}
    end = False
    values = {'-A', '-B', '-C', '-m', '--max-count', '--maxdepth', '--max-depth',
              '--include', '--exclude', '--exclude-dir', '-g', '--glob', '-t', '-T',
              '--type', '--type-not', '--encoding', '--color', '-F', '-v'} if exe == 'awk' else {
              '-A', '-B', '-C', '-m', '--max-count', '--maxdepth', '--max-depth',
              '--include', '--exclude', '--exclude-dir', '-g', '--glob', '-t', '-T',
              '--type', '--type-not', '--encoding', '--color'}
    if exe in {'head', 'tail'}:
        values |= {'-n', '-c', '--lines', '--bytes'}
    while i < len(args):
        arg = args[i]
        if not end and arg == '--':
            end = True; i += 1; continue
        if not end and arg in {'-f', '--file'} and exe in {'grep', 'rg', 'sed', 'awk'}:
            raise ValueError('reader_program_or_pattern_file')
        if not end and arg in {'-e', '--regexp', '--expression'}:
            if i+1 >= len(args): raise ValueError('reader_missing_pattern')
            pattern = True; i += 2; continue
        if not end and arg.startswith('-e') and len(arg) > 2:
            pattern = True; i += 1; continue
        if not end and arg in values:
            if i+1 >= len(args): raise ValueError('reader_missing_option_value')
            i += 2; continue
        if not end and arg.startswith('-') and arg != '-':
            i += 1; continue
        if not pattern:
            pattern = True
        else:
            files.append(arg)
        i += 1
    return files


def single_log(args, bindings):
    caps, revisions, i = [], [], 0
    while i < len(args):
        arg = args[i]
        if arg in {'-1', '-n1', '--max-count=1'}:
            caps.append(1)
        elif arg in {'-n', '--max-count'} and args[i+1:i+2] == ['1']:
            caps.append(1); i += 1
        elif arg in {'--format', '--pretty', '--date'} and i+1 < len(args):
            i += 1
        elif arg.startswith(('--format=', '--pretty=', '--date=')) or arg in DISPLAY:
            pass
        elif REV.fullmatch(arg):
            revisions.append(arg)
        elif BOUND.fullmatch(arg) and arg in bindings and all(REV.fullmatch(v) for v in bindings[arg]):
            revisions.append(arg)
        else:
            return None
        i += 1
    return revisions[0] if caps and len(revisions) == 1 else None


def bind_text(text, bindings):
    """Substitute only simple known loop parameters outside single quotes.

    $v:path is dialect-dependent and deliberately not guessed.
    """
    pieces, quote, i = [], None, 0
    while i < len(text):
        ch = text[i]
        if ch == '\\' and quote != "'" and i+1 < len(text):
            pieces.append(text[i:i+2]); i += 2; continue
        if ch in "'\"":
            if quote is None: quote = ch
            elif quote == ch: quote = None
            pieces.append(ch); i += 1; continue
        if ch == '$' and quote != "'":
            match = re.match(r'\$(?:\{([A-Za-z_]\w*)\}|([A-Za-z_]\w*))', text[i:])
            if match and (name := (match[1] or match[2])) in bindings:
                end = i+len(match[0])
                if match[2] and text[end:end+1] == ':':
                    raise ValueError('shell_dialect_parameter_modifier')
                pieces.append(f'__BOUND_{name}__'); i = end; continue
        pieces.append(ch); i += 1
    return ''.join(pieces)


def path_key(raw, cwd):
    raw = re.sub(r'^\$\{TMPDIR\}', '$TMPDIR', raw)
    if raw.startswith('$TMPDIR/'):
        return os.path.normpath(raw)
    if '$' in raw or raw.startswith('~') or BOUND.search(raw):
        return None
    if Path(raw).is_absolute():
        return os.path.normpath(raw)
    return os.path.normpath(str(cwd / raw)) if cwd is not None else None


def stdout_path(stage):
    lex = shlex.shlex(stage, posix=True, punctuation_chars='<>')
    lex.whitespace_split = True; lex.commenters = ''
    tokens = list(lex)
    result = None
    for i, token in enumerate(tokens[:-1]):
        if token in {'>', '>>'}:
            fd = tokens[i-1] if i and tokens[i-1].isdigit() else '1'
            if fd == '1' and tokens[i+1] != '/dev/null':
                result = (tokens[i+1], token == '>>')
    return result


class Engine:
    def __init__(self, context):
        self.ctx = context
        self.cwd = context.repo
        self.stable = True
        self.artifacts = {}
        self.call_no = 0

    def target_b(self, values, bindings):
        expanded = [v for value in values for v in bindings.get(value, [value])]
        resolved = [self.ctx.resolve(v, self.stable) for v in expanded]
        kinds = {'bfc' if r == self.ctx.fix else 'other_commit' for r in resolved if r}
        return next(iter(kinds)) if len(kinds) == 1 and all(resolved) else None

    def git(self, args, fragment, cwd, bindings):
        sub, opts, override = syntax.git_parts(['git', *args])
        if override:
            key = path_key(override, cwd)
            cwd = Path(key) if key and '$' not in key else None
        if sub == 'log' and (rev := single_log(opts, bindings)):
            target = self.target_b([rev], bindings)
            return operation('B', 'B.single_commit_log', fragment, target,
                             [] if target else ['commit_target_unresolved'])
        if sub in {'log', 'blame'}:
            try:
                paths, values, line_paths = syntax.positional(opts, sub)
            except ValueError as exc:
                return operation('A', 'A.history_argument_error', fragment, reasons=[str(exc)])
            # Bare non-revision args may be file paths; dynamic ones remain target-unknown.
            paths += [v for v in values if not REV.fullmatch(v) and '..' not in v]
            if any(BOUND.search(p) or '$' in p for p in paths):
                target, reasons = None, ['dynamic_history_target']
            elif not self.stable:
                target, reasons = None, ['git_context_changed']
            else:
                target, reasons = self.ctx.scope(paths+line_paths, cwd)
            return operation('A', 'A.history', fragment, target, reasons)
        if sub in {'show', 'diff', 'diff-tree'}:
            paths, values, _ = syntax.positional(opts, sub)
            if sub == 'show' and any(':' in v for v in values):
                if all(':' in v and not v.startswith(':') and '$' not in v for v in values):
                    return operation('C', 'C.git_blob', fragment)
                return operation('UNKNOWN', 'unknown.show_object', fragment, reasons=['ambiguous_commit_or_blob'])
            if any('$' in v for v in values):
                return operation('UNKNOWN', 'unknown.dynamic_git_object', fragment, reasons=['dynamic_git_object'])
            target = self.target_b(values or ['HEAD'], bindings)
            return operation('B', 'B.commit_change', fragment, target,
                             [] if target else ['commit_target_unresolved'])
        if sub == 'grep':
            return operation('C', 'C.git_grep', fragment)
        if sub == 'cat-file':
            vals = [v for v in opts if not v.startswith('-')]
            if '-p' in opts and len(vals) == 1:
                if '$' in vals[0]:
                    return operation('UNKNOWN', 'unknown.cat_file_object', fragment, reasons=['dynamic_git_object'])
                if ':' in vals[0]:
                    return operation('C', 'C.cat_file_blob', fragment)
                if REV.fullmatch(vals[0]) or BOUND.fullmatch(vals[0]):
                    return operation('B', 'B.cat_file_commit', fragment, self.target_b(vals, bindings))
            return operation('OTHER', 'other.git_object_metadata', fragment)
        if sub in META_GIT:
            return operation('OTHER', 'other.git_metadata', fragment)
        if sub in {'checkout', 'switch', 'reset'}:
            self.stable = False
        return operation('UNKNOWN', 'unknown.git_command', fragment, reasons=['unsupported_git_command'])

    def reader(self, exe, args, fragment, cwd, current_use):
        files = reader_files(exe, args)
        if not files:
            return operation('C' if exe == 'rg' else 'UNKNOWN', 'reader.default_input', fragment,
                             reasons=[] if exe == 'rg' else ['reader_input_unknown'])
        parts, sources, flags = [], [], []
        for raw in files:
            if raw in {'-', '/dev/stdin'}:
                return operation('UNKNOWN', 'reader.stdin', fragment, reasons=['reader_stdin_without_producer'])
            key = path_key(raw, cwd)
            saved = self.artifacts.get(key)
            if saved:
                if saved['call'] != self.call_no and saved['end'] >= current_use:
                    return operation('UNKNOWN', 'reader.concurrent_source', fragment, reasons=['overlapping_stdout_producer'])
                parts.extend(saved['parts']); sources.append(saved['call'])
                flags.extend(saved['flags'])
            elif raw.startswith(('/tmp/', '/private/tmp/', '$TMPDIR/', '${TMPDIR}/')):
                return operation('UNKNOWN', 'reader.missing_saved_source', fragment, reasons=['saved_source_unknown'])
            elif key is None:
                return operation('UNKNOWN', 'reader.dynamic_input', fragment, reasons=['reader_path_unresolved'])
            else:
                try:
                    relative = Path(key).relative_to(self.ctx.repo)
                except ValueError:
                    return operation('UNKNOWN', 'reader.external_input', fragment, reasons=['external_reader_input'])
                # Requested repository content; existence/read success is a separate axis.
                parts.append(dict(activity='OTHER' if relative.parts[:1] == ('.git',) else 'C', target=None))
        acts = {p['activity'] for p in parts}
        if acts == {'OTHER'}:
            return operation('OTHER', 'other.git_internal_file', fragment)
        if len(acts) != 1 or 'UNKNOWN' in acts:
            return operation('UNKNOWN', 'reader.mixed_source', fragment, reasons=['saved_source_mixed_or_unknown'], source_calls=sources)
        activity = next(iter(acts)); targets = {p.get('target') for p in parts}
        target = next(iter(targets)) if len(targets) == 1 else None
        return operation(activity, 'reader.saved_source' if sources else 'C.repository_reader', fragment,
                         target, [] if activity == 'C' or target else ['inherited_target_unknown'],
                         source_calls=sorted(set(sources)), source_flags=sorted(set(flags)))

    def primitive(self, stage, cwd, bindings, use):
        tokens = syntax.token_command(stage)
        if not tokens:
            return operation('OTHER', 'other.assignment', stage)
        exe, args = Path(tokens[0]).name, tokens[1:]
        if exe == 'git': return self.git(args, stage, cwd, bindings)
        if exe in READERS: return self.reader(exe, args, stage, cwd, use)
        if exe == 'command' and not any(a in {'-v', '-V'} for a in args):
            return operation('UNKNOWN', 'unknown.command_wrapper', stage, reasons=['unsupported_command_wrapper'])
        if exe == 'find' and any(a in {'-exec', '-execdir', '-ok', '-okdir'} for a in args):
            return operation('UNKNOWN', 'unknown.find_wrapper', stage, reasons=['unsupported_find_exec'])
        if exe in syntax.AUX | {'mkdir', 'cd', 'pwd'}:
            return operation('OTHER', 'other.shell_auxiliary', stage)
        if exe in {'java', 'javac', 'mvn'} and any(v in {'-version', '--version', '-v'} for v in args):
            return operation('OTHER', 'other.version', stage)
        return operation('UNKNOWN', 'unknown.shell_command', stage, reasons=['unsupported_shell_command'])

    def simple(self, command, cwd, bindings, use, end, error):
        groups, conditional = split(command)
        operations, changed_cwd = [], False
        for stages in groups:
            initial_tokens = syntax.token_command(stages[0])
            # Expansion in display-only commands cannot change the ABC activity.
            display_only = initial_tokens and Path(initial_tokens[0]).name in {'echo', 'printf'}
            stage = stages[0] if display_only else bind_text(stages[0], bindings)
            bound_values = {f'__BOUND_{k}__': v for k, v in bindings.items()}
            try:
                row = self.primitive(stage, cwd, bound_values, use)
                tokens = syntax.token_command(stage)
                if tokens[:1] == ['cd']:
                    changed_cwd = True
                    key = path_key(tokens[1], cwd) if len(tokens) == 2 else None
                    cwd = Path(key) if key and '$' not in key and not error else None
                for tail in stages[1:]:
                    tt = syntax.token_command(tail)
                    if not tt or Path(tt[0]).name not in FILTERS:
                        row = operation('UNKNOWN', 'unknown.pipeline', ' | '.join(stages), reasons=['unsupported_pipeline_stage'])
                        break
                    if Path(tt[0]).name in READERS:
                        named = [p for p in reader_files(Path(tt[0]).name, tt[1:]) if p not in {'-', '/dev/stdin'}]
                        if named:
                            row = operation('UNKNOWN', 'unknown.pipeline_named_input', ' | '.join(stages), reasons=['pipeline_additional_named_input'])
                            break
                row['command_fragment'] = ' | '.join(stages)
                writer = stdout_path(stages[-1])
                if writer:
                    key = path_key(writer[0], cwd)
                    if key:
                        prior = self.artifacts.get(key)
                        parts = [dict(activity=row['activity'], target=row['target'])]
                        flags = ['source_call_tool_error'] if error else []
                        if writer[1] or conditional:
                            parts = (prior['parts'] if prior else [dict(activity='UNKNOWN', target=None)]) + parts
                        self.artifacts[key] = dict(parts=parts, call=self.call_no, end=end, flags=flags)
                        row['saved_to'] = key
            except (ValueError, IndexError) as exc:
                row = operation('UNKNOWN', 'unknown.primitive', ' | '.join(stages), reasons=[str(exc)])
            operations.append(row)
        return operations, conditional, cwd, changed_cwd

    def classify(self, command, output, use, end, tool_error=False):
        self.call_no += 1
        initial_cwd = self.cwd
        try:
            try:
                ops, held, cwd, changed = self.simple(command, self.cwd, {}, use, end, tool_error)
            except ValueError as exc:
                if str(exc) != 'loop_or_control_flow': raise
                match = re.fullmatch(r'(.*?)\bfor\s+([A-Za-z_]\w*)\s+in\s+(.*?)\s*;\s*do\s*(.*?)\s*done\s*;?\s*', command, re.S)
                if not match: raise ValueError('unsupported_control_flow')
                prefix, variable, raw_values, body = match.groups()
                values = shlex.split(raw_values)
                if not values or any(re.search(r'[$`*?\[\]{}]', v) for v in values):
                    raise ValueError('nonliteral_loop_values')
                ops, _, cwd, changed = self.simple(prefix, self.cwd, {}, use, end, tool_error)
                rows, _, cwd, body_cd = self.simple(body, cwd, {variable: values}, use, end, tool_error)
                for row in rows:
                    row.update(loop_values=values, loop_variable=variable, execution_count=None)
                ops += rows; held = True; changed |= body_cd
            if not ops: ops = [operation('OTHER', 'other.empty', command)]
        except (ValueError, IndexError) as exc:
            ops = [operation('UNKNOWN', 'unknown.shell_structure', command, reasons=[str(exc)])]
            held = True; cwd = self.cwd; changed = False
        # An unsupported read-only syntax does not by itself imply a cwd change.
        # Visible state-changing shell constructs still invalidate persistence.
        if re.search(r'(?:^|[;\n&|])\s*(?:cd|pushd|popd|source|eval|\.)\s', command):
            changed = True
        # We never infer persistence after a visible cwd/state-changing construct.
        if changed: self.cwd = None
        # Standalone saved pwd restores an observed directory generically.
        if command.strip() == 'pwd' and not tool_error and output.strip().startswith('/') and '\n' not in output.strip():
            candidate = Path(output.strip())
            try:
                candidate.relative_to(self.ctx.repo); self.cwd = candidate
            except ValueError:
                self.cwd = None
        activities = {o['activity'] for o in ops if o['activity'] != 'OTHER'}
        return dict(operations=ops, structure_hold=held,
                    activity_complete='UNKNOWN' not in activities,
                    internal_order_unknown=held and len(activities & {'A', 'B', 'C'}) > 1,
                    targets_complete=all(o['activity'] not in {'A', 'B'} or o['target'] is not None for o in ops),
                    initial_cwd=str(initial_cwd) if initial_cwd else None,
                    tool_error=tool_error)
