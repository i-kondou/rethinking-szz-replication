"""Historical SZZ-Agent adapter, without unrelated launch/history layers."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import types
from runtime import SCRIPTS
import claude_code_final_v2_access_policy as policy
from llm_baseline_common import BaselineError, sha256_file, sha256_bytes

ENGINE_SOURCE = SCRIPTS / 'run_llm_baseline_subject.py'
ENGINE_SHA256 = '08e84228e2d0d615884279a19524bab4cc08eaaf52eaabfd9458f02000a4b542'
THIS_RUNNER = Path(__file__).resolve().parent / 'baselines.py'
CONDITION_ID = 'EXP002-BFC-MESSAGE-NEUTRALIZED-FINAL-V2-DEC017'
transport = sys.modules[__name__]

def derive_engine():
    if sha256_file(ENGINE_SOURCE) != ENGINE_SHA256:
        raise BaselineError("frozen baseline engine changed; review before deriving")
    source = ENGINE_SOURCE.read_text(encoding="utf-8")
    changes = {
        "if args.timeout_seconds <= 0:": "if args.timeout_seconds < 0:",
        '"tool_use_counts": telemetry["tool_use_counts"],':
            '"tool_use_counts": telemetry["tool_use_counts"],\n'
            '        "access_audit": telemetry["access_audit"],',
    }
    for old, new in changes.items():
        if source.count(old) != 1:
            raise BaselineError("baseline derivation anchor changed")
        source = source.replace(old, new, 1)
    engine = types.ModuleType("final_v2_dec017_baseline_engine")
    engine.__file__ = str(ENGINE_SOURCE)
    exec(compile(source, str(ENGINE_SOURCE), "exec"), engine.__dict__)
    engine.__file__ = str(THIS_RUNNER)
    engine.BASELINES = ("simple-szz-agent", "szz-agent")
    legacy_parser = engine.parse_claude_transcript
    engine.parse_claude_transcript = lambda transcript, *, work_dir: policy.audit_transcript(
        transcript, work_dir=work_dir, legacy_parser=legacy_parser, persist=True,
    )
    legacy_preflight = engine.public_preflight
    engine.public_preflight = lambda **kwargs: {
        **legacy_preflight(**kwargs),
        "condition_id": CONDITION_ID,
        "resource_policy": policy.resource_policy(kwargs["baseline"]),
        "access_policy": policy.POLICY_ID,
        "automatic_quota_retry": False,
    }
    legacy_stage2_gate = engine.szz_stage2_required

    def stage2_gate(stage1_path: Path) -> bool:
        # A technical validation failure is not a scientific abstention.
        # Do not spend another stage on an already invalid attempt.
        engine.load_audit(stage1_path.parents[3] / "model-invocations.json", required=True)
        return legacy_stage2_gate(stage1_path)

    engine.szz_stage2_required = stage2_gate
    # Keep every original system instruction except the newly authorized,
    # tightly scoped same-session spill-file exception. No command examples.
    for name in ("SAFE_AGENT_SYSTEM_PROMPT", "SAFE_SIMPLE_AGENT_SYSTEM_PROMPT"):
        prompt = getattr(engine, name)
        old = "memory, or paths outside the current directory."
        if old not in prompt:
            # Simple wraps the preceding list across a line break.
            raise BaselineError("baseline system-prompt exception anchor changed")
        setattr(engine, name, prompt.replace(old,
            "memory, or unrelated paths outside the current directory. "
            "You may read a saved tool-result file only when an earlier tool "
            "result in this same session identifies that exact file and its "
            "source tool searched only the current working directory."))
    return engine, sha256_bytes(source.encode())

def execute_process(command, *, env, cwd, stdout_path, stderr_path,
                    timeout_seconds, deadline, total_timeout_seconds):
    if deadline is not None:
        return transport.execute_process_with_deadline(
            command, env=env, cwd=cwd, stdout_path=stdout_path, stderr_path=stderr_path,
            timeout_seconds=timeout_seconds, deadline=deadline,
            total_timeout_seconds=total_timeout_seconds,
        )
    started = time.monotonic()
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=out, stderr=err,
                                   start_new_session=True)
        try:
            exit_code = process.wait()  # No Simple outer watchdog; inner600 remains.
        except BaseException:
            transport._stop_process_group(process)
            raise
    return {
        "command": command, "exit_code": exit_code, "timed_out": False,
        "timeout_seconds": None, "registered_total_timeout_seconds": None,
        "duration_seconds": time.monotonic() - started,
        "stdout_path": str(stdout_path), "stdout_sha256": sha256_file(stdout_path),
        "stderr_path": str(stderr_path), "stderr_sha256": sha256_file(stderr_path),
    }

def _stop_process_group(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()

def execute_process_with_deadline(
    command: list[str],
    *,
    env: dict[str, str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: int,
    deadline: float,
    total_timeout_seconds: int,
) -> dict[str, object]:
    started = time.monotonic()
    remaining = max(0.0, deadline - started)
    allowed = min(float(timeout_seconds), remaining)
    timed_out = allowed <= 0
    returncode: int | None = None
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        if not timed_out:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
            try:
                returncode = process.wait(timeout=allowed)
            except subprocess.TimeoutExpired:
                timed_out = True
                _stop_process_group(process)
    return {
        "command": command,
        "exit_code": returncode,
        "timed_out": timed_out,
        "timeout_seconds": allowed,
        "registered_total_timeout_seconds": total_timeout_seconds,
        "remaining_total_timeout_seconds_before_start": remaining,
        "duration_seconds": time.monotonic() - started,
        "stdout_path": str(stdout_path),
        "stdout_sha256": sha256_file(stdout_path),
        "stderr_path": str(stderr_path),
        "stderr_sha256": sha256_file(stderr_path),
    }
