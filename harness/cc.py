"""Thin driver around headless Claude Code (`claude -p`, stream-json in and out).

One call of run_session() == one Claude Code process == one conversation. All prompts are
sent through stdin one after another (waiting for each `result`), so hooks behave exactly
like in an interactive session: SessionStart fires once, UserPromptSubmit once per prompt.
"""
from __future__ import annotations

import gzip
import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
PLUGIN_DIR = BENCH / "gemkeeper"  # git submodule, pinned to the benchmarked plugin commit
SETTINGS = BENCH / "harness" / "settings.bench.json"

MODEL = os.environ.get("BENCH_MODEL", "sonnet")
EFFORT = os.environ.get("BENCH_EFFORT", "medium")
CLAUDE = os.environ.get("BENCH_CLAUDE", "claude")


class RateLimited(RuntimeError):
    pass


def clean_env() -> dict:
    """Environment for child processes: drop everything Claude/gemkeeper-specific from the
    parent session (CLAUDE_EFFORT, CLAUDECODE, messaging sockets, ...)."""
    env = {k: v for k, v in os.environ.items()
           if not (k.upper().startswith("CLAUDE") or k.upper().startswith("GEMKEEPER"))}
    env["DISABLE_AUTOUPDATER"] = "1"
    # Which Claude Code config/account runs the sessions (default ~/.claude). Sessions can only be
    # resumed within the same config dir, so one rep must never switch it midway.
    if os.environ.get("BENCH_CLAUDE_CONFIG_DIR"):
        env["CLAUDE_CONFIG_DIR"] = os.environ["BENCH_CLAUDE_CONFIG_DIR"]
    # no claude.ai connectors (the ~/.claude account had none; keeps tools and context comparable)
    env["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"
    return env


def build_cmd(plugin: bool, resume: str | None, fork: bool, extra: list[str] | None = None) -> list[str]:
    cmd = [CLAUDE, "-p", "--input-format", "stream-json", "--output-format", "stream-json",
           "--verbose", "--include-hook-events",
           "--model", MODEL, "--effort", EFFORT,
           "--dangerously-skip-permissions",
           "--settings", str(SETTINGS),
           "--disallowedTools", "Agent"]
    if plugin:
        cmd += ["--plugin-dir", str(PLUGIN_DIR)]
    if resume:
        cmd += ["--resume", resume]
        if fork:
            cmd += ["--fork-session"]
    return cmd + (extra or [])


def _ctx(usage: dict) -> int:
    return int(usage.get("input_tokens", 0)) + int(usage.get("cache_read_input_tokens", 0)) + \
        int(usage.get("cache_creation_input_tokens", 0))


def run_session(cwd: Path, prompts: list[str], log_path: Path, *, plugin: bool = False,
                resume: str | None = None, fork: bool = False, parent_cost: float = 0.0,
                turn_timeout: float = 1800, on_turn=None, extra: list[str] | None = None,
                env_extra: dict | None = None) -> dict:
    """Runs prompts in one conversation. Returns a summary dict; raw events go to log_path (.jsonl.gz)."""
    cmd = build_cmd(plugin, resume, fork, extra)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path = log_path.with_suffix("").with_suffix(".stderr.txt")
    t0 = time.time()
    with open(stderr_path, "w", encoding="utf-8") as errf:
        proc = subprocess.Popen(cmd, cwd=str(cwd), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=errf, text=True, encoding="utf-8", errors="replace",
                                env={**clean_env(), **(env_extra or {})}, bufsize=1)
    lines: queue.Queue = queue.Queue()

    def reader():
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=reader, daemon=True).start()

    summary = {"cmd": cmd[1:], "cwd": str(cwd), "plugin": plugin, "resume": resume, "fork": fork,
               "parent_cost": parent_cost, "session_id": None, "turns": [], "hooks": [], "error": None,
               "compact": None}
    seen_msgs: dict[str, int] = {}
    tool_uses: dict[str, dict] = {}
    out = gzip.open(log_path, "wt", encoding="utf-8")
    eof = False
    try:
        for i, prompt in enumerate(prompts):
            if eof:
                summary["error"] = summary["error"] or "process exited early"
                break
            proc.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": prompt}}) + "\n")
            proc.stdin.flush()
            turn = {"i": i, "prompt_chars": len(prompt), "ctx": [], "tools": [], "result": None}
            deadline = time.time() + turn_timeout
            while True:
                try:
                    line = lines.get(timeout=max(1, deadline - time.time()))
                except queue.Empty:
                    summary["error"] = f"turn {i} timed out after {turn_timeout}s"
                    proc.kill()
                    eof = True
                    break
                if line is None:
                    eof = True
                    summary["error"] = summary["error"] or f"process exited during turn {i}"
                    break
                out.write(line)
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                typ, sub = ev.get("type"), ev.get("subtype")
                if ev.get("session_id"):
                    summary["session_id"] = ev["session_id"]
                if typ == "system" and sub == "hook_response":
                    summary["hooks"].append({"turn": i, "hook": ev.get("hook_name"),
                                             "chars": len(ev.get("output") or ""),
                                             "output": (ev.get("output") or "")[:4000]})
                elif typ == "system" and sub == "compact_boundary":
                    summary["compact"] = ev.get("compact_metadata")
                elif typ == "assistant":
                    msg = ev.get("message", {})
                    mid = msg.get("id")
                    if mid and mid not in seen_msgs and msg.get("usage"):
                        seen_msgs[mid] = _ctx(msg["usage"])
                        turn["ctx"].append(seen_msgs[mid])
                    for block in msg.get("content", []):
                        if block.get("type") == "text" and block.get("text"):
                            turn.setdefault("texts", []).append(block["text"])
                        if block.get("type") == "tool_use":
                            full = json.dumps(block.get("input"), ensure_ascii=False)
                            rec = {"id": block.get("id"), "name": block.get("name"),
                                   "input": full[:2000], "input_chars": len(full), "result_chars": 0,
                                   "mentions_ledger": ".gemkeeper" in full or (block.get("name") == "Skill" and "gems" in full)}
                            tool_uses[block.get("id")] = rec
                            turn["tools"].append(rec)
                elif typ == "user":
                    for block in (ev.get("message", {}).get("content") or []):
                        if isinstance(block, dict) and block.get("type") == "tool_result":
                            rec = tool_uses.get(block.get("tool_use_id"))
                            if rec is not None:
                                c = block.get("content")
                                rec["result_chars"] = len(c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
                elif typ == "result":
                    turn["result"] = {
                        "text": ev.get("result"), "is_error": ev.get("is_error"),
                        "subtype": sub, "num_turns": ev.get("num_turns"),
                        "duration_ms": ev.get("duration_ms"), "total_cost_usd": ev.get("total_cost_usd"),
                        "api_error_status": ev.get("api_error_status"), "usage": ev.get("usage"),
                        "model_usage": ev.get("modelUsage"),
                    }
                    break
            summary["turns"].append(turn)
            if on_turn:
                on_turn(i, turn)
            res = turn["result"] or {}
            if res.get("is_error"):
                status = res.get("api_error_status")
                text = str(res.get("text") or "")
                if status == 429 or "rate limit" in text.lower() or "usage limit" in text.lower():
                    summary["error"] = f"rate limited in turn {i}: {text[:300]}"
                    break
            if eof:
                break
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=120)
        except subprocess.TimeoutExpired:
            proc.kill()
        out.close()

    costs = [t["result"]["total_cost_usd"] for t in summary["turns"] if t.get("result") and t["result"].get("total_cost_usd") is not None]
    summary["cost_cumulative"] = costs[-1] if costs else None
    summary["cost"] = round(costs[-1] - parent_cost, 6) if costs else None
    summary["wall_s"] = round(time.time() - t0, 1)
    summary["exit_code"] = proc.returncode
    first = summary["turns"][0]["ctx"] if summary["turns"] else []
    last = summary["turns"][-1]["ctx"] if summary["turns"] else []
    summary["ctx_first"] = first[0] if first else None
    summary["ctx_last"] = last[-1] if last else None
    if summary["error"] and summary["error"].startswith("rate limited"):
        e = RateLimited(summary["error"])
        e.cost = summary.get("cost")
        raise e
    return summary


def run_judge(prompt: str, system: str, schema: dict, cwd: Path, log_path: Path) -> dict:
    """One-shot `claude -p` without tools, own system prompt, structured JSON output."""
    cmd = [CLAUDE, "-p", "--output-format", "json", "--model", MODEL, "--effort", EFFORT,
           "--settings", str(SETTINGS), "--tools", "", "--system-prompt", system,
           "--json-schema", json.dumps(schema), "--no-session-persistence"]
    cwd.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(cmd, cwd=str(cwd), input=prompt, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=clean_env(), timeout=1800)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps({"stdout": p.stdout, "stderr": p.stderr[-4000:], "prompt": prompt}, ensure_ascii=False), encoding="utf-8")
    data = json.loads(p.stdout)
    structured = data.get("structured_output")
    if structured is None:
        text = data.get("result") or ""
        start, end = text.find("{"), text.rfind("}")
        structured = json.loads(text[start:end + 1])
    return {"output": structured, "cost": data.get("total_cost_usd"), "is_error": data.get("is_error")}
