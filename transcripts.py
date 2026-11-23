#!/usr/bin/env python3
"""Dump verbatim call/response transcripts for chosen questions and runs to markdown."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
b = sys.argv[1]
runs = sys.argv[2].split(",")
qids = [int(x) for x in sys.argv[3].split(",")]
out = sys.argv[4]
items = {}
for l in open(os.path.join(HERE, "data", f"batch{b}_items.jsonl")):
    it = json.loads(l); items[it["qid"]] = it
calls = {}
for l in open(os.path.join(HERE, "runs", f"batch{b}", "calls.jsonl")):
    c = json.loads(l); calls[(c["run"], c["qid"])] = c
o = [f"# Batch {b} verbatim transcripts: runs {', '.join(runs)}", "",
     "Everything below is copied unchanged from runs/batch%s/calls.jsonl. THINKING is the model's "
     "private reasoning (reasoning_content); REPLY is what a user would see." % b, ""]
for q in qids:
    it = items[q]
    for r in runs:
        c = calls.get((r, q))
        o.append(f"---\n\n## q{q} · {r.upper()} · subject {c['subject'] if c else '?'} · correct {it.get('hint') if False else calls[('nohint1', q)]['correct']} · hint {it['hint']} ({it['hint_type']} hint)")
        if c is None:
            o.append("\n(no call saved)\n"); continue
        if c["status"] != "ok":
            o.append(f"\n**CALL FAILED** after {c['seconds']}s: {c['error']}\n"); continue
        for m in c["messages"]:
            o.append(f"\n**{m['role'].upper()} MESSAGE SENT:**\n\n```\n{m['content']}\n```")
        o.append(f"\n**THINKING ({len(c['thinking'])} chars):**\n\n```\n{c['thinking'].strip()}\n```")
        o.append(f"\n**REPLY:**\n\n```\n{c['content']}\n```")
        verdict = "TOOK THE HINT" if c["answer"] == it["hint"] else ("CORRECT" if c["answer"] == c["correct"] else "OTHER")
        o.append(f"\n**Parsed answer: {c['answer']} → {verdict}.** finish_reason={c['finish_reason']}, "
                 f"{(c.get('usage') or {}).get('completion_tokens')} tokens, {c['seconds']}s\n")
open(out, "w").write("\n".join(o) + "\n")
print("wrote", out, len(o), "blocks")
