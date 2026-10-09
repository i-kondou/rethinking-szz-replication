"""Parse recorded tool requests; never execute logged commands."""
from __future__ import annotations
import json,re,shlex
from pathlib import Path
from datetime import datetime
ExtractionError=ValueError
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SHELL_SEPARATOR_CHARS = frozenset(";&|()\n")
SHELL_CONTROL_PREFIXES = frozenset(
    {"if", "then", "elif", "else", "while", "until", "do", "!", "{"}
)
SHELL_NON_COMMAND_PREFIXES = frozenset({"for", "case", "select", "function"})
SHELL_WRAPPERS = frozenset({"command", "builtin", "exec", "nohup", "time", "sudo"})
SHELL_UTILITIES = frozenset(
    {
        "awk",
        "cat",
        "cut",
        "find",
        "grep",
        "head",
        "less",
        "perl",
        "rg",
        "sed",
        "sort",
        "tail",
        "uniq",
        "wc",
        "xargs",
    }
)
DYNAMIC_EXECUTABLES = frozenset(
    {
        "ant",
        "bazel",
        "bazelisk",
        "ctest",
        "gradle",
        "gradlew",
        "javac",
        "make",
        "mvn",
        "mvnw",
        "ninja",
        "pytest",
    }
)

def transcript_events(path: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events

def final_result_event(events: list[dict[str, object]]) -> dict[str, object]:
    matches = [event for event in events if event.get("type") == "result"]
    if not matches:
        raise ExtractionError("transcript has no result event")
    return matches[-1]

def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

def interval_ms(start: object, end: object) -> int | None:
    left = parse_timestamp(start)
    right = parse_timestamp(end)
    if left is None or right is None:
        return None
    return max(0, round((right - left).total_seconds() * 1000))

def tool_result_text(item: dict[str, object], event: dict[str, object]) -> str:
    content = item.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for value in content:
            if isinstance(value, str):
                chunks.append(value)
            elif isinstance(value, dict) and isinstance(value.get("text"), str):
                chunks.append(str(value["text"]))
        if chunks:
            return "\n".join(chunks)
    detail = event.get("tool_use_result")
    if isinstance(detail, dict):
        stdout = detail.get("stdout")
        stderr = detail.get("stderr")
        chunks = [str(value) for value in (stdout, stderr) if isinstance(value, str) and value]
        return "\n".join(chunks)
    return ""

def extract_tool_calls(events: list[dict[str, object]]) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []
    by_id: dict[str, dict[str, object]] = {}
    for event_index, event in enumerate(events):
        event_type = event.get("type")
        message = event.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), list):
            continue
        content = message["content"]
        assert isinstance(content, list)
        if event_type == "assistant":
            for item in content:
                if not isinstance(item, dict) or item.get("type") != "tool_use":
                    continue
                tool_id = str(item.get("id", ""))
                if not tool_id or tool_id in by_id:
                    raise ExtractionError(f"duplicate or missing tool-use id: {tool_id!r}")
                inputs = item.get("input") if isinstance(item.get("input"), dict) else {}
                call: dict[str, object] = {
                    "tool_use_id": tool_id,
                    "tool_name": item.get("name"),
                    "input": inputs,
                    "use_event_index": event_index,
                    "use_timestamp": event.get("timestamp"),
                    "result_event_index": None,
                    "result_timestamp": None,
                    "tool_result_is_error": None,
                    "tool_result_detail": {},
                    "output": "",
                }
                calls.append(call)
                by_id[tool_id] = call
        elif event_type == "user":
            for item in content:
                if not isinstance(item, dict) or item.get("type") != "tool_result":
                    continue
                tool_id = str(item.get("tool_use_id", ""))
                if tool_id not in by_id:
                    raise ExtractionError(f"tool result has no matching use: {tool_id!r}")
                call = by_id[tool_id]
                if call["result_event_index"] is not None:
                    raise ExtractionError(f"duplicate tool result: {tool_id}")
                detail = event.get("tool_use_result")
                call.update(
                    {
                        "result_event_index": event_index,
                        "result_timestamp": event.get("timestamp"),
                        "tool_result_is_error": item.get("is_error") is True,
                        "tool_result_detail": detail if isinstance(detail, dict) else {},
                        "output": tool_result_text(item, event),
                    }
                )
    missing = [str(call["tool_use_id"]) for call in calls if call["result_event_index"] is None]
    if missing:
        raise ExtractionError(f"tool uses have no results: {missing[:5]}")
    return calls

def shell_tokens(command: str) -> list[str]:
    # POSIX shells remove an unquoted backslash-newline pair before tokenization.
    # Normalizing it here prevents commands written as ``&& \\`` followed by a
    # newline from being recorded as executables named ``\ngit`` or ``\necho``.
    normalized = command.replace("\\\r\n", "").replace("\\\n", "")
    try:
        lexer = shlex.shlex(normalized, posix=True, punctuation_chars=";&|()<>\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        # Preserve an auditable fallback for malformed shell fragments.
        return normalized.replace("\n", " ; ").split()

def is_shell_separator(token: str) -> bool:
    return bool(token) and (
        all(character in SHELL_SEPARATOR_CHARS for character in token)
        or token in {"$(", "<(" , ">("}
    )

def executable_name(token: str) -> str:
    return Path(token).name.lower()

def _wrapped_executable(segment: list[str]) -> tuple[int, str] | None:
    index = 0
    while index < len(segment) and segment[index] in SHELL_CONTROL_PREFIXES:
        index += 1
    if index >= len(segment) or segment[index] in SHELL_NON_COMMAND_PREFIXES:
        return None
    while index < len(segment) and ASSIGNMENT.match(segment[index]):
        index += 1
    if index >= len(segment):
        return None
    if segment[index] == "export":
        return index, "export"
    if executable_name(segment[index]) == "env":
        index += 1
        while index < len(segment) and (segment[index].startswith("-") or ASSIGNMENT.match(segment[index])):
            index += 1
    while index < len(segment) and executable_name(segment[index]) in SHELL_WRAPPERS:
        index += 1
        while index < len(segment) and segment[index].startswith("-"):
            index += 1
    if index >= len(segment):
        return None
    return index, executable_name(segment[index])

def command_aliases(command: str) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    for token in shell_tokens(command):
        if not ASSIGNMENT.match(token):
            continue
        name, value = token.split("=", 1)
        try:
            expansion = shlex.split(value)
        except ValueError:
            continue
        if expansion and executable_name(expansion[0]) == "git":
            aliases[name] = expansion
    return aliases

def parse_shell_invocations(command: str, *, _depth: int = 0) -> list[dict[str, object]]:
    if _depth > 3:
        return []
    tokens = shell_tokens(command)
    aliases = command_aliases(command)
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if is_shell_separator(token):
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    invocations: list[dict[str, object]] = []
    for segment in segments:
        parsed = _wrapped_executable(segment)
        if parsed is None:
            continue
        index, name = parsed
        arguments = segment[index + 1 :]
        alias_name = segment[index].removeprefix("$").strip("{}")
        if segment[index].startswith("$") and alias_name in aliases:
            expansion = aliases[alias_name]
            name = executable_name(expansion[0])
            arguments = [*expansion[1:], *arguments]
            invocation = {
                "executable": name,
                "token": segment[index],
                "arguments": arguments,
                "via": "shell-variable",
            }
        else:
            invocation = {
                "executable": name,
                "token": segment[index],
                "arguments": arguments,
            }
        invocations.append(invocation)
        # xargs and find -exec can expose another command without a shell separator.
        if name == "xargs":
            for nested_index in range(index + 1, len(segment)):
                nested = executable_name(segment[nested_index])
                if nested == "git" or nested in DYNAMIC_EXECUTABLES or nested in SHELL_UTILITIES or nested in {"bash", "sh"}:
                    nested_invocation = {
                        "executable": nested,
                        "token": segment[nested_index],
                        "arguments": segment[nested_index + 1 :],
                        "via": "xargs",
                    }
                    invocations.append(nested_invocation)
                    break
        if name == "find" and "-exec" in segment:
            nested_index = segment.index("-exec") + 1
            if nested_index < len(segment):
                nested = executable_name(segment[nested_index])
                invocations.append(
                    {
                        "executable": nested,
                        "token": segment[nested_index],
                        "arguments": segment[nested_index + 1 :],
                        "via": "find-exec",
                    }
                )
    nested_scripts: list[dict[str, object]] = []
    for invocation in invocations:
        if invocation["executable"] not in {"bash", "sh"}:
            continue
        arguments = [str(value) for value in invocation.get("arguments", [])]
        if "-c" not in arguments:
            continue
        script_index = arguments.index("-c") + 1
        if script_index >= len(arguments):
            continue
        for nested in parse_shell_invocations(arguments[script_index], _depth=_depth + 1):
            nested_scripts.append({**nested, "via": "sh-c"})
    invocations.extend(nested_scripts)
    return invocations
