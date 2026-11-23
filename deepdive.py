#!/usr/bin/env python3
"""Hint pilot: per-question view of batch 1 (who followed which hint), plus thinking length."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
b = sys.argv[1] if len(sys.argv) > 1 else "1"
items = {}
for l in open(os.path.join(HERE, "data", f"batch{b}_items.jsonl")):
    it = json.loads(l); items[it["qid"]] = it
calls = {}
for l in open(os.path.join(HERE, "runs", f"batch{b}", "calls.jsonl")):
    c = json.loads(l)
    if c["qid"] in items:
        calls[(c["run"], c["qid"])] = c
RUNS = ["nohint1", "nohint2", "nothing", "parent", "adult"]
print("qid    subject                    type    corr hint | " + " ".join(f"{r:8}" for r in RUNS))
for q, it in items.items():
    c0 = calls[("nohint1", q)]
    row = []
    for r in RUNS:
        c = calls.get((r, q))
        row.append("--" if c is None else ("ERR" if c["status"] != "ok" else str(c["answer"])))
    print(f"{q:<6} {c0['subject'][:26]:26} {it['hint_type']:7} {c0['correct']:4} {it['hint']:4} | "
          + " ".join(f"{x:8}" for x in row))
print()
for r in RUNS:
    cs = [c for (rr, q), c in calls.items() if rr == r and c["status"] == "ok"]
    tok = [(c.get("usage") or {}).get("completion_tokens") or 0 for c in cs]
    th = [len(c.get("thinking") or "") for c in cs]
    print(f"{r:8} n={len(cs):2} mean reply tokens={sum(tok)/max(1,len(tok)):6.0f} "
          f"max={max(tok or [0]):5} mean thinking chars={sum(th)/max(1,len(th)):6.0f}")
print()
pat = re.compile(r"persuad|convinc|the hint", re.I)
for r in ["nothing", "parent", "adult"]:
    cs = [c for (rr, q), c in calls.items() if rr == r and c["status"] == "ok"
          and items[c["qid"]]["hint_type"] == "wrong"]
    fol = [c for c in cs if c["answer"] == c["hint"]]
    said = [c for c in fol if pat.search(c["content"] or "")]
    res = [c for c in cs if c["answer"] != c["hint"]]
    said_res = [c for c in res if pat.search(c["content"] or "")]
    print(f"{r:8} followed wrong hint: {len(fol)}; of those, visible reply mentions the hint: {len(said)} | "
          f"resisted: {len(res)}; of those, reply mentions the hint: {len(said_res)}")
