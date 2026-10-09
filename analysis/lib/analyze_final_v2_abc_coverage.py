"""Read-only Git context and static shell parsing used by ABC classification."""
from functools import lru_cache
from pathlib import Path
import os,re,shlex,subprocess

HEXREV = re.compile(r"(?:[0-9a-fA-F]{7,40}|HEAD)(?:[~^][0-9]*)*")

VALUE_FLAGS = {"-n", "--max-count", "--skip", "--since", "--until", "--after", "--before",
               "--author", "--committer", "--grep", "--format", "-S", "-G",
               "-L", "--date", "--encoding", "--diff-filter", "--max-age", "--min-age",
               "-U", "--unified", "--word-diff-regex"}

READERS = {"cat", "sed", "grep", "rg", "head", "tail", "awk"}

FILTERS = READERS | {"wc", "sort", "uniq", "cut", "tr", "less", "more", "tee"}

AUX = {"echo", "printf", "pwd", "ls", "find", "true", "false", "which", "command",
       "test", "[", "wc", "sort", "uniq", "date", "git"}

def split_shell(command):
    """Split only unquoted top-level separators, retaining pipeline groups."""
    s = command.replace("\\\r\n", "").replace("\\\n", "")
    groups, stages, buf, quote, i, conditional = [], [], [], None, 0, False
    while i < len(s):
        c = s[i]
        if c == "\\" and quote != "'" and i + 1 < len(s):
            buf.extend(s[i:i+2]); i += 2; continue
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
            i += 1; continue
        if c in "'\"":
            quote = c; buf.append(c); i += 1; continue
        if c == "#" and (not buf or buf[-1].isspace()):
            while i < len(s) and s[i] != "\n":
                i += 1
            continue
        # Redirect descriptors are not background operators.
        if c == "&" and buf and buf[-1] in "><":
            buf.append(c); i += 1; continue
        if c in "(){}" or c == chr(96):
            raise ValueError("complex_shell_structure")
        if c in ";\n|&":
            op = s[i:i+2] if s[i:i+2] in {"&&", "||", "|&", ";;"} else c
            if op in {"&", "|&", ";;"}:
                raise ValueError("parallel_or_complex_shell")
            if "".join(buf).strip():
                stages.append("".join(buf).strip())
            buf = []
            if op != "|":
                if stages:
                    groups.append(stages)
                stages = []
                conditional |= op in {"&&", "||"}
            i += len(op); continue
        buf.append(c); i += 1
    if quote:
        raise ValueError("unbalanced_shell_quote")
    if "".join(buf).strip():
        stages.append("".join(buf).strip())
    if stages:
        groups.append(stages)
    for group in groups:
        for stage in group:
            if re.match(r"^(?:for|while|until|if|then|else|fi|do|done|case|function)\b", stage):
                raise ValueError("loop_or_control_flow")
    return groups, conditional

def token_command(stage):
    lex = shlex.shlex(stage, posix=True, punctuation_chars="<>")
    lex.whitespace_split = True
    lex.commenters = ""
    tokens = list(lex)
    args, i = [], 0
    while i < len(tokens):
        if tokens[i] in {">", ">>", "<", "<<"}:
            if args and args[-1].isdigit():
                args.pop()
            if i+1 >= len(tokens):
                raise ValueError("incomplete_redirection")
            if tokens[i] in {"<", "<<"}:
                raise ValueError("input_redirection_review")
            i += 2; continue
        args.append(tokens[i]); i += 1
    while args and re.match(r"^[A-Za-z_]\w*=", args[0]):
        args.pop(0)
    if args and Path(args[0]).name == "env":
        args.pop(0)
        while args and re.match(r"^[A-Za-z_]\w*=", args[0]):
            args.pop(0)
    return args

def git_parts(tokens):
    args = tokens[1:]
    cwd = None
    while args and args[0].startswith("-"):
        flag = args.pop(0)
        if flag in {"-C", "-c", "--git-dir", "--work-tree"}:
            if not args:
                raise ValueError("git_global_argument")
            value = args.pop(0)
            if flag == "-C":
                if cwd is not None:
                    raise ValueError("multiple_git_C")
                cwd = value
            if flag == "-c" and value.split("=", 1)[0].lower() not in {
                    "safe.directory", "core.quotepath", "core.pager", "color.ui"}:
                raise ValueError("git_config_context_review")
            if flag in {"--git-dir", "--work-tree"}:
                raise ValueError("alternate_git_context")
        elif flag not in {"--no-pager", "--no-replace-objects", "--literal-pathspecs"}:
            raise ValueError("unsupported_git_global_option")
    if not args:
        raise ValueError("missing_git_subcommand")
    return args[0], args[1:], cwd

def positional(args, subcommand="log"):
    """Return explicit paths, positional revision/path tokens, and -L paths."""
    before = args[:args.index("--")] if "--" in args else args
    paths = args[args.index("--")+1:] if "--" in args else []
    values, line_paths, i = [], [], 0
    while i < len(before):
        arg = before[i]
        if arg == "-L" or (arg.startswith("-L") and len(arg) > 2):
            if arg == "-L":
                i += 1
                if i >= len(before):
                    raise ValueError("missing_line_range")
                value = before[i]
            else:
                value = arg[2:]
            if subcommand == "blame":
                i += 1
                continue
            if ":" not in value:
                raise ValueError("line_range_path_unknown")
            line_paths.append(value.rsplit(":", 1)[1])
        elif arg in VALUE_FLAGS:
            i += 1
            if i >= len(before):
                raise ValueError("missing_option_value")
        elif not arg.startswith("-"):
            values.append(arg)
        i += 1
    return paths, values, line_paths

class Context:
    def __init__(self, repo, fix, source):
        self.repo, self.fix, self.source = Path(repo).resolve(), fix, source
        fields = self.git("rev-list", "--parents", "-n", "1", fix).strip().split()
        if not fields or fields[0] != fix:
            raise ValueError("Frozen BFC unavailable")
        self.parents = fields[1:]
        self.files = set()
        if len(self.parents) == 1:
            fields = self.git("diff", "--no-ext-diff", "--no-textconv", "--name-status",
                              "-z", "-M", self.parents[0], fix).split("\0")
            i = 0
            while i < len(fields) and fields[i]:
                count = 2 if fields[i][0] in "RC" else 1
                self.files.update(fields[i+1:i+1+count])
                i += 1 + count

    @lru_cache(maxsize=None)
    def git(self, *args):
        env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1",
                   GIT_OPTIONAL_LOCKS="0")
        p = subprocess.run(["git", "--no-replace-objects", "-c", "core.fsmonitor=false",
                            "-C", str(self.repo), *args], capture_output=True, text=True,
                           env=env, timeout=20)
        return p.stdout if p.returncode == 0 else ""

    def resolve(self, value, stable=True):
        if not stable or not HEXREV.fullmatch(value):
            return None
        if value == self.source:
            return self.fix
        value = re.sub(r"^HEAD(?=$|[~^])", self.fix, value)
        resolved = self.git("rev-parse", "--verify", value+"^{commit}").strip()
        return resolved if re.fullmatch(r"[0-9a-f]{40}", resolved) else None

    def path(self, value, cwd):
        if not value or "$" in value or re.search(r"[*?\[\]]", value) or value.startswith(":"):
            return None
        if cwd is None and not Path(value).is_absolute():
            return None
        path = Path(os.path.normpath(str(Path(value) if Path(value).is_absolute() else Path(cwd)/value)))
        try:
            return path.relative_to(self.repo).as_posix()
        except ValueError:
            return None

    def kind(self, path):
        if path == ".":
            return "tree"
        for rev in [self.fix, *self.parents[:1]]:
            value = self.git("cat-file", "-t", rev+":"+path).strip()
            if value in {"blob", "tree"}:
                return value
        return None

    def scope(self, paths, cwd):
        if not paths:
            return "unrestricted", []
        if len(self.parents) != 1:
            return None, ["bfc_parent_ambiguous"]
        hits = []
        for raw in paths:
            path = self.path(raw, cwd)
            if path is None:
                return None, ["path_expression_or_context"]
            if path in self.files:
                hits.append(True)
            elif self.kind(path) == "blob":
                hits.append(False)
            else:
                return None, ["directory_or_historical_path"]
        return ("mixed" if any(hits) and not all(hits) else
                "bfc_files" if all(hits) else "other_files"), []
