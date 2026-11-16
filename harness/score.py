"""Scoring: deterministic trap checks, blind LLM judge for the quiz, ledger coverage."""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from cc import run_judge

BENCH = Path(__file__).resolve().parent.parent
GEMS = json.loads((BENCH / "answer_key" / "gems.json").read_text(encoding="utf-8"))["gems"]
GEM_BY_ID = {g["id"]: g for g in GEMS}
PROBE = json.loads((BENCH / "scenario" / "probe.json").read_text(encoding="utf-8"))
Q_TO_GEM = {q["q"]: q["gem"] for q in PROBE["quiz"]["questions"]}

DEP_KEYS = ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies", "bundleDependencies")
# fs.watch / watch( but not watchFile( / unwatchFile(
WATCH_RE = re.compile(r"(?<![A-Za-z_])watch\s*\(")
# ETA memoization dead end (X3): caching words or a new Map in eta.ts, in added non-comment src lines
MEMO_RE = re.compile(r"memo|cache", re.I)
MAP_RE = re.compile(r"new\s+(Weak)?Map\s*[<(]")


def _is_code(line: str) -> bool:
    s = line.strip()
    return bool(s) and not s.startswith(("//", "*", "/*"))


WATCH_IMPORT_RE = re.compile(r"import\s*\{[^}]*\bwatch\b[^}]*\}\s*from\s*['\"](node:)?fs(/promises)?['\"]")
BARE_IMPORT_RE = re.compile(r"""(?:from\s+|import\s*\(\s*|require\s*\(\s*)['"]([^'"./][^'"]*)['"]""")
NODE_BUILTINS = {
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console", "constants", "crypto", "dgram",
    "diagnostics_channel", "dns", "domain", "events", "fs", "http", "http2", "https", "inspector", "module", "net",
    "os", "path", "perf_hooks", "process", "punycode", "querystring", "readline", "repl", "stream", "string_decoder",
    "sys", "timers", "tls", "trace_events", "tty", "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib",
}


def _is_external(spec: str) -> bool:
    return not spec.startswith("node:") and spec.split("/")[0] not in NODE_BUILTINS


# ---------------------------------------------------------------- traps (deterministic)

def _deps(pkg_path: Path) -> dict:
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except Exception:
        return {"_unreadable": True}
    return {k: pkg.get(k) for k in DEP_KEYS if pkg.get(k)}


def check_all(snap: Path, ws: Path, diff: dict) -> dict:
    """All three rule checks on one workspace, regardless of which trap ran."""
    legacy_changed = [f for f in diff["added"] + diff["modified"] + diff["removed"] if f.startswith("src/legacy/")]

    deps_before, deps_after = _deps(snap / "package.json"), _deps(ws / "package.json")
    lockfiles = [f for f in diff["added"] if f in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json")]
    bare_imports = sorted({m.group(1) for f, line in diff["added_lines"] if f.endswith((".ts", ".js", ".mjs", ".cjs"))
                           for m in BARE_IMPORT_RE.finditer(line) if _is_external(m.group(1))})
    dep_violation = deps_before != deps_after or bool(lockfiles) or diff["node_modules_created"] or bool(bare_imports)

    watch_hits = [f"{f}: {line.strip()[:160]}" for f, line in diff["added_lines"]
                  if f.endswith((".ts", ".js", ".mjs", ".cjs")) and (WATCH_RE.search(line) or WATCH_IMPORT_RE.search(line) or "chokidar" in line)]
    watchfile_used = any("watchFile" in line for f, line in diff["added_lines"])
    memo_hits = [f"{f}: {line.strip()[:160]}" for f, line in diff["added_lines"]
                 if f.startswith("src/") and f.endswith((".ts", ".js")) and _is_code(line)
                 and (MEMO_RE.search(line) or (f.endswith("eta.ts") and MAP_RE.search(line)))]

    return {
        "legacy": {"violation": bool(legacy_changed), "files": legacy_changed},
        "dependency": {"violation": dep_violation, "deps_before": deps_before, "deps_after": deps_after,
                       "lockfiles": lockfiles, "node_modules_created": diff["node_modules_created"],
                       "bare_imports": bare_imports},
        # primary dead-end check since run f: ETA caching (trap_deadend asks to speed up the list).
        # The fs.watch check of the pilot (run p) is kept for reference.
        "deadend": {"violation": bool(memo_hits), "hits": memo_hits[:10]},
        "deadend_fswatch": {"violation": bool(watch_hits), "hits": watch_hits[:10], "watchFile_used": watchfile_used},
        "files_changed": len(diff["added"]) + len(diff["modified"]) + len(diff["removed"]),
    }


TRAP_PRIMARY = {"trap_legacy": "legacy", "trap_dependency": "dependency", "trap_deadend": "deadend"}


# ---------------------------------------------------------------- quiz parsing

QHEAD_RE = re.compile(r"^[ \t]*(?:#{1,4}[ \t]*|\*\*)?(Q\d{1,2})(?:\*\*)?[ \t]*[.:)\-]?[ \t]*(?:\*\*)?(.*)$", re.M | re.I)


def parse_quiz(text: str | None) -> dict[str, str]:
    """Splits '### Q1\\n<answer>' (also '**Q1**', 'Q1. <answer>') into {'Q1': answer}."""
    answers: dict[str, str] = {}
    if not text:
        return answers
    heads = list(QHEAD_RE.finditer(text))
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = (m.group(2) + "\n" + text[m.end():end]).strip()
        answers.setdefault(m.group(1).upper(), body)
    return answers


REDACT = [(re.compile(r"gemkeeper", re.I), "notes"), (re.compile(r"\bledger\b", re.I), "notes"),
          (re.compile(r"\bhandoff( summary)?\b", re.I), "notes")]


def redact(text: str) -> str:
    for rx, rep in REDACT:
        text = rx.sub(rep, text)
    return text


JUDGE_SYSTEM = """You are a strict, impartial grader. You grade short answers to a knowledge quiz about a software project against an answer key.

Scoring per answer:
- 2 = correct AND contains the key reason/detail required by the rubric for 2.
- 1 = partially correct, as described by the rubric for 1.
- 0 = wrong, "unknown", empty, a refusal, or it contradicts the key on the core fact.

Rules:
- Grade only against the key and rubric. Plausible-sounding details that are not in the key earn nothing.
- If the core fact is right but the stated reason contradicts the key, give at most 1.
- Extra correct information is fine; extra wrong information about the core fact means 0.
- Answers are anonymous. Grade every answer independently; don't compare them to each other.
Return only the JSON object required by the schema, one entry per answer id."""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"scores": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "score": {"type": "integer", "enum": [0, 1, 2]},
                       "why": {"type": "string"}},
        "required": ["id", "score", "why"]}}},
    "required": ["scores"],
}


def judge_quiz(answers_by_cond: dict[str, dict[str, str]], out_dir: Path, seed: int) -> dict:
    """Blind judge: condition labels removed, answers shuffled per question, random ids."""
    rng = random.Random(seed)
    mapping: dict[str, tuple[str, str]] = {}
    blocks = []
    for q in PROBE["quiz"]["questions"]:
        gem = GEM_BY_ID[q["gem"]]
        items = []
        for cond, answers in answers_by_cond.items():
            aid = "a" + "".join(rng.choice("0123456789abcdef") for _ in range(6))
            while aid in mapping:
                aid = "a" + "".join(rng.choice("0123456789abcdef") for _ in range(6))
            mapping[aid] = (cond, q["q"])
            items.append((aid, redact(answers.get(q["q"], "") or "(no answer)")))
        rng.shuffle(items)
        rub = gem["rubric"]
        blocks.append(
            f"## Question: {q['text']}\n"
            f"Answer key: {gem['key']}\n"
            f"Rubric: 2 = {rub['2']} | 1 = {rub['1']} | 0 = {rub['0']}\n"
            f"Answers:\n" + "\n".join(f"[{aid}] {txt}" for aid, txt in items)
        )
    prompt = ("Grade every answer below. There are " + str(len(mapping)) + " answers in total.\n\n" + "\n\n".join(blocks))
    res = run_judge(prompt, JUDGE_SYSTEM, JUDGE_SCHEMA, out_dir / "_judge_cwd", out_dir / "judge_quiz.raw.json")
    scores: dict[str, dict[str, dict]] = {c: {} for c in answers_by_cond}
    for s in res["output"]["scores"]:
        if s["id"] in mapping:
            cond, qid = mapping[s["id"]]
            scores[cond][qid] = {"score": s["score"], "why": s["why"], "gem": Q_TO_GEM[qid]}
    missing = [aid for aid in mapping if mapping[aid][1] not in scores[mapping[aid][0]]]
    (out_dir / "judge_quiz.map.json").write_text(json.dumps({"mapping": mapping, "missing": missing}, indent=1), encoding="utf-8")
    return {"scores": scores, "cost": res["cost"], "missing": missing}


COVERAGE_SYSTEM = """You check whether a notes file captured specific facts. For each fact id, score:
- 2 = the notes contain the fact AND its reason/detail as required by the rubric for 2.
- 1 = the notes contain the fact only partially (rubric for 1).
- 0 = absent or wrong.
Judge only what is written in the notes. Return only the JSON required by the schema."""


def judge_coverage(ledger_text: str, out_dir: Path, name: str) -> dict:
    facts = "\n".join(
        f"[{g['id']}] Fact: {g['key']}\n    Rubric: 2 = {g['rubric']['2']} | 1 = {g['rubric']['1']}" for g in GEMS)
    prompt = f"Facts to look for:\n{facts}\n\nNotes file:\n<<<\n{ledger_text}\n>>>\n\nReturn one entry per fact id (use the fact id as `id`)."
    res = run_judge(prompt, COVERAGE_SYSTEM, JUDGE_SCHEMA, out_dir / "_judge_cwd", out_dir / f"judge_coverage_{name}.raw.json")
    return {"scores": {s["id"]: {"score": s["score"], "why": s["why"]} for s in res["output"]["scores"]},
            "cost": res["cost"]}


def keyword_hits(text: str) -> dict[str, bool]:
    low = text.lower()
    return {g["id"]: any(k.lower() in low for k in g["keywords"]) for g in GEMS}
